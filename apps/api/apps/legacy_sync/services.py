from __future__ import annotations

import csv
import json
import subprocess
from dataclasses import dataclass
from datetime import date as date_cls, datetime as datetime_cls, timedelta
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db import OperationalError
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.devices.models import Device
from apps.activity.models import UserActivity
from apps.profile.models import UserProfile
from apps.telegram.models import TelegramAccountLink
from apps.subscription.models import (
    Subscription,
    SubscriptionHistoryEvent,
    SubscriptionPayment,
    SubscriptionRoute,
)
from apps.subscription.services import (
    SUBSCRIPTION_PLAN_CATALOG,
    TRIAL_MAX_DEVICES,
    TRIAL_PLAN_NAME,
    TRIAL_ROUTE_DEFINITIONS,
    build_public_subscription_url,
    create_unique_public_subscription_token,
    create_subscription_history_event,
    ensure_subscription_routes,
    ensure_default_route_catalog,
    get_connection_route_by_code,
)
from apps.support.models import SupportAttachment, SupportConversation, SupportMessage


DEFAULT_RESTORE_DB_NAME = "infinda_amonora_restore"
User = get_user_model()


@dataclass(frozen=True)
class AmonoraRestoreOverview:
    database_name: str
    table_count: int
    users_count: int
    vpn_clients_count: int
    payment_records_count: int
    support_tickets_count: int


@dataclass(frozen=True)
class InfindaCurrentCounts:
    users_count: int
    subscriptions_count: int
    payments_count: int
    support_conversations_count: int
    devices_count: int


@dataclass(frozen=True)
class AmonoraRestoreComparison:
    restore: AmonoraRestoreOverview
    current: InfindaCurrentCounts


@dataclass(frozen=True)
class AmonoraUserStats:
    total_users: int
    blocked_users: int
    synthetic_users: int
    trial_users: int
    active_subscription_users: int
    referred_users: int
    total_balance_rub: int


@dataclass(frozen=True)
class AmonoraSubscriptionStats:
    total_users_with_subscription_state: int
    active_subscription_users: int
    trial_subscription_users: int
    expired_subscription_users: int
    inactive_subscription_users: int
    pending_payment_users: int


@dataclass(frozen=True)
class AmonoraSupportStats:
    total_tickets: int
    new_tickets: int
    in_progress_tickets: int
    closed_tickets: int
    assigned_tickets: int
    total_messages: int
    messages_with_attachments: int


@dataclass(frozen=True)
class AmonoraDeviceStats:
    total_vpn_clients: int
    unique_users_with_vpn_clients: int
    total_activations: int
    total_activation_count: int
    device_slot_entitlements: int
    active_device_slot_entitlements: int
    vpn_repair_events: int


@dataclass(frozen=True)
class AmonoraPaymentStats:
    total_payments: int
    confirmed_payments: int
    pending_payments: int
    awaiting_user_payment: int
    awaiting_admin_review: int
    canceled_payments: int
    rejected_payments: int
    expired_payments: int
    total_amount_rub: int
    confirmed_amount_rub: int


@dataclass(frozen=True)
class AmonoraUserImportSummary:
    source_users: int
    created_users: int
    updated_users: int
    created_profiles: int
    created_telegram_links: int
    dry_run: bool


@dataclass(frozen=True)
class AmonoraSubscriptionImportSummary:
    source_users: int
    created_subscriptions: int
    created_trial_subscriptions: int
    created_active_subscriptions: int
    created_expired_subscriptions: int
    skipped_inactive_users: int
    skipped_existing_subscriptions: int
    dry_run: bool


@dataclass(frozen=True)
class AmonoraPaymentImportSummary:
    source_payments: int
    imported_payments: int
    imported_paid_payments: int
    imported_pending_payments: int
    imported_canceled_payments: int
    imported_failed_payments: int
    skipped_unsupported_tariffs: int
    skipped_existing_payments: int
    dry_run: bool


@dataclass(frozen=True)
class AmonoraSupportImportSummary:
    source_tickets: int
    created_conversations: int
    created_messages: int
    created_attachments: int
    created_support_admins: int
    closed_conversations: int
    in_progress_conversations: int
    skipped_missing_users: int
    skipped_existing_conversations: int
    dry_run: bool


@dataclass(frozen=True)
class AmonoraDeviceImportSummary:
    source_vpn_clients: int
    created_devices: int
    active_devices: int
    revoked_devices: int
    skipped_missing_users: int
    skipped_existing_devices: int
    dry_run: bool


@dataclass(frozen=True)
class AmonoraDeviceSlotEntitlementImportSummary:
    source_entitlements: int
    updated_subscriptions: int
    created_activities: int
    skipped_missing_users: int
    skipped_existing_activities: int
    dry_run: bool


@dataclass(frozen=True)
class AmonoraVpnRepairImportSummary:
    source_events: int
    created_activities: int
    skipped_missing_users: int
    skipped_existing_activities: int
    dry_run: bool


def inspect_amonora_restore(*, database_name: str = DEFAULT_RESTORE_DB_NAME) -> AmonoraRestoreOverview:
    query = """
        select count(*) from information_schema.tables where table_schema = 'public';
        select count(*) from users;
        select count(*) from vpn_clients;
        select count(*) from payment_records;
        select count(*) from support_tickets;
    """
    completed = _run_psql(
        database_name=database_name,
        sql=query,
    )
    return _parse_overview(
        database_name=database_name,
        output=completed.stdout,
    )


def build_current_infinda_counts() -> InfindaCurrentCounts:
    try:
        return InfindaCurrentCounts(
            users_count=User.objects.count(),
            subscriptions_count=Subscription.objects.count(),
            payments_count=SubscriptionPayment.objects.count(),
            support_conversations_count=SupportConversation.objects.count(),
            devices_count=Device.objects.count(),
        )
    except OperationalError:
        return InfindaCurrentCounts(
            users_count=0,
            subscriptions_count=0,
            payments_count=0,
            support_conversations_count=0,
            devices_count=0,
        )


def compare_amonora_restore_with_current(*, database_name: str = DEFAULT_RESTORE_DB_NAME) -> AmonoraRestoreComparison:
    return AmonoraRestoreComparison(
        restore=inspect_amonora_restore(database_name=database_name),
        current=build_current_infinda_counts(),
    )


def inspect_amonora_user_stats(*, database_name: str = DEFAULT_RESTORE_DB_NAME) -> AmonoraUserStats:
    query = """
        select count(*) from users;
        select count(*) from users where is_blocked = true;
        select count(*) from users where is_synthetic = true;
        select count(*) from users where trial_used = true;
        select count(*) from users where subscription_status = 'active';
        select count(*) from users where referred_by_user_id is not null;
        select coalesce(sum(balance_rub), 0) from users;
    """
    completed = _run_psql(
        database_name=database_name,
        sql=query,
    )
    values = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    if len(values) != 7:
        raise ValueError(f"Unexpected psql output for {database_name}: {completed.stdout!r}")

    return AmonoraUserStats(
        total_users=int(values[0]),
        blocked_users=int(values[1]),
        synthetic_users=int(values[2]),
        trial_users=int(values[3]),
        active_subscription_users=int(values[4]),
        referred_users=int(values[5]),
        total_balance_rub=int(values[6]),
    )


def inspect_amonora_subscription_stats(*, database_name: str = DEFAULT_RESTORE_DB_NAME) -> AmonoraSubscriptionStats:
    query = """
        select count(*) from users where subscription_status is not null;
        select count(*) from users where subscription_status = 'active';
        select count(*) from users where subscription_status = 'trial';
        select count(*) from users where subscription_status = 'expired';
        select count(*) from users where subscription_status = 'inactive';
        select count(*) from users where subscription_status = 'pending_payment';
    """
    completed = _run_psql(
        database_name=database_name,
        sql=query,
    )
    values = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    if len(values) != 6:
        raise ValueError(f"Unexpected psql output for {database_name}: {completed.stdout!r}")

    return AmonoraSubscriptionStats(
        total_users_with_subscription_state=int(values[0]),
        active_subscription_users=int(values[1]),
        trial_subscription_users=int(values[2]),
        expired_subscription_users=int(values[3]),
        inactive_subscription_users=int(values[4]),
        pending_payment_users=int(values[5]),
    )


def inspect_amonora_support_stats(*, database_name: str = DEFAULT_RESTORE_DB_NAME) -> AmonoraSupportStats:
    query = """
        select count(*) from support_tickets;
        select count(*) from support_tickets where status = 'new';
        select count(*) from support_tickets where status = 'in_progress';
        select count(*) from support_tickets where status = 'closed';
        select count(*) from support_tickets where assigned_admin_id is not null;
        select count(*) from support_ticket_messages;
        select count(*) from support_ticket_messages where attachment_file_id is not null or attachment_name is not null;
    """
    completed = _run_psql(
        database_name=database_name,
        sql=query,
    )
    values = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    if len(values) != 7:
        raise ValueError(f"Unexpected psql output for {database_name}: {completed.stdout!r}")

    return AmonoraSupportStats(
        total_tickets=int(values[0]),
        new_tickets=int(values[1]),
        in_progress_tickets=int(values[2]),
        closed_tickets=int(values[3]),
        assigned_tickets=int(values[4]),
        total_messages=int(values[5]),
        messages_with_attachments=int(values[6]),
    )


def inspect_amonora_device_stats(*, database_name: str = DEFAULT_RESTORE_DB_NAME) -> AmonoraDeviceStats:
    query = """
        select count(*) from vpn_clients;
        select count(distinct user_id) from vpn_clients;
        select count(*) from vpn_client_activations;
        select coalesce(sum(activation_count), 0) from vpn_client_activations;
        select count(*) from device_slot_entitlements;
        select count(*) from device_slot_entitlements where status = 'active';
        select count(*) from vpn_repair_events;
    """
    completed = _run_psql(
        database_name=database_name,
        sql=query,
    )
    values = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    if len(values) != 7:
        raise ValueError(f"Unexpected psql output for {database_name}: {completed.stdout!r}")

    return AmonoraDeviceStats(
        total_vpn_clients=int(values[0]),
        unique_users_with_vpn_clients=int(values[1]),
        total_activations=int(values[2]),
        total_activation_count=int(values[3]),
        device_slot_entitlements=int(values[4]),
        active_device_slot_entitlements=int(values[5]),
        vpn_repair_events=int(values[6]),
    )


def inspect_amonora_payment_stats(*, database_name: str = DEFAULT_RESTORE_DB_NAME) -> AmonoraPaymentStats:
    query = """
        select count(*) from payment_records;
        select count(*) from payment_records where payment_status = 'confirmed';
        select count(*) from payment_records where payment_status = 'pending';
        select count(*) from payment_records where payment_status = 'awaiting_user_payment';
        select count(*) from payment_records where payment_status = 'awaiting_admin_review';
        select count(*) from payment_records where payment_status = 'canceled';
        select count(*) from payment_records where payment_status = 'rejected';
        select count(*) from payment_records where payment_status = 'expired';
        select coalesce(sum(amount), 0) from payment_records;
        select coalesce(sum(case when payment_status = 'confirmed' then amount else 0 end), 0) from payment_records;
    """
    completed = _run_psql(
        database_name=database_name,
        sql=query,
    )
    values = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    if len(values) != 10:
        raise ValueError(f"Unexpected psql output for {database_name}: {completed.stdout!r}")

    return AmonoraPaymentStats(
        total_payments=int(values[0]),
        confirmed_payments=int(values[1]),
        pending_payments=int(values[2]),
        awaiting_user_payment=int(values[3]),
        awaiting_admin_review=int(values[4]),
        canceled_payments=int(values[5]),
        rejected_payments=int(values[6]),
        expired_payments=int(values[7]),
        total_amount_rub=int(values[8]),
        confirmed_amount_rub=int(values[9]),
    )


def import_amonora_users(
    *,
    database_name: str = DEFAULT_RESTORE_DB_NAME,
    limit: int | None = None,
    dry_run: bool = False,
) -> AmonoraUserImportSummary:
    source_users = list(_fetch_amonora_user_rows(database_name=database_name, limit=limit))
    if dry_run:
        return AmonoraUserImportSummary(
            source_users=len(source_users),
            created_users=0,
            updated_users=0,
            created_profiles=0,
            created_telegram_links=0,
            dry_run=True,
        )

    created_users = 0
    updated_users = 0
    created_profiles = 0
    created_telegram_links = 0

    for record in source_users:
        user, created = User.objects.get_or_create(
            username=record["username"],
            defaults={
                "email": record["email"],
                "first_name": record["first_name"],
                "last_name": "",
                "is_active": not record["is_blocked"],
                "date_joined": record["date_joined"],
            },
        )

        desired_values = {
            "email": record["email"],
            "first_name": record["first_name"],
            "is_active": not record["is_blocked"],
            "date_joined": record["date_joined"],
        }
        changed_fields: list[str] = []
        for field_name, new_value in desired_values.items():
            if getattr(user, field_name) != new_value:
                setattr(user, field_name, new_value)
                changed_fields.append(field_name)

        if created:
            user.set_unusable_password()
            user.save()
            created_users += 1
        elif changed_fields:
            user.save(update_fields=changed_fields)
            updated_users += 1

        _, profile_created = UserProfile.objects.get_or_create(user=user)
        if profile_created:
            created_profiles += 1

        _, link_created = _upsert_telegram_account_link(
            user=user,
            telegram_user_id=record["telegram_user_id"],
            telegram_username=record["telegram_username"],
            is_active=not record["is_blocked"],
        )
        if link_created:
            created_telegram_links += 1

    return AmonoraUserImportSummary(
        source_users=len(source_users),
        created_users=created_users,
        updated_users=updated_users,
        created_profiles=created_profiles,
        created_telegram_links=created_telegram_links,
        dry_run=False,
    )


def _upsert_telegram_account_link(
    *,
    user: User,
    telegram_user_id: int,
    telegram_username: str,
    is_active: bool,
) -> tuple[TelegramAccountLink, bool]:
    existing_link = TelegramAccountLink.objects.filter(telegram_user_id=telegram_user_id).first()
    if existing_link is None:
        return TelegramAccountLink.objects.create(
            user=user,
            telegram_user_id=telegram_user_id,
            telegram_username=telegram_username,
            telegram_full_name="",
            is_active=is_active,
        ), True

    changed_fields: list[str] = []
    if existing_link.user_id != user.id:
        existing_link.user = user
        changed_fields.append("user")
    if existing_link.telegram_username != telegram_username:
        existing_link.telegram_username = telegram_username
        changed_fields.append("telegram_username")
    if existing_link.is_active != is_active:
        existing_link.is_active = is_active
        changed_fields.append("is_active")
    if existing_link.telegram_full_name != "":
        existing_link.telegram_full_name = ""
        changed_fields.append("telegram_full_name")

    if changed_fields:
        existing_link.save(update_fields=changed_fields)

    return existing_link, False


def import_amonora_subscriptions(
    *,
    database_name: str = DEFAULT_RESTORE_DB_NAME,
    limit: int | None = None,
    dry_run: bool = False,
) -> AmonoraSubscriptionImportSummary:
    source_users = list(_fetch_amonora_subscription_rows(database_name=database_name, limit=limit))
    if dry_run:
        return _build_subscription_import_summary(source_users=source_users, dry_run=True)

    created_subscriptions = 0
    created_trial_subscriptions = 0
    created_active_subscriptions = 0
    created_expired_subscriptions = 0
    skipped_inactive_users = 0
    skipped_existing_subscriptions = 0

    for record in source_users:
        user = User.objects.filter(username=record["username"]).first()
        if user is None:
            continue

        if record["subscription_state"] == "inactive":
            skipped_inactive_users += 1
            continue

        if Subscription.objects.filter(user=user).exists():
            skipped_existing_subscriptions += 1
            continue

        if record["subscription_state"] == "trial":
            subscription = _create_imported_trial_subscription(user=user, record=record)
            created_trial_subscriptions += 1
        else:
            subscription = _create_imported_paid_subscription(user=user, record=record)
            if record["subscription_state"] == "active":
                created_active_subscriptions += 1
            elif record["subscription_state"] == "expired":
                created_expired_subscriptions += 1
            else:
                continue

        created_subscriptions += 1
        if subscription is None:
            continue

    return AmonoraSubscriptionImportSummary(
        source_users=len(source_users),
        created_subscriptions=created_subscriptions,
        created_trial_subscriptions=created_trial_subscriptions,
        created_active_subscriptions=created_active_subscriptions,
        created_expired_subscriptions=created_expired_subscriptions,
        skipped_inactive_users=skipped_inactive_users,
        skipped_existing_subscriptions=skipped_existing_subscriptions,
        dry_run=False,
    )


def import_amonora_payments(
    *,
    database_name: str = DEFAULT_RESTORE_DB_NAME,
    limit: int | None = None,
    dry_run: bool = False,
) -> AmonoraPaymentImportSummary:
    source_payments = list(_fetch_amonora_payment_rows(database_name=database_name, limit=limit))
    if dry_run:
        return _build_payment_import_summary(source_payments=source_payments, dry_run=True)

    imported_payments = 0
    imported_paid_payments = 0
    imported_pending_payments = 0
    imported_canceled_payments = 0
    imported_failed_payments = 0
    skipped_unsupported_tariffs = 0
    skipped_existing_payments = 0
    supported_codes = {plan["code"] for plan in SUBSCRIPTION_PLAN_CATALOG}

    for record in source_payments:
        if record["tariff_code"] not in supported_codes:
            skipped_unsupported_tariffs += 1
            continue

        user = User.objects.filter(username=record["username"]).first()
        if user is None:
            continue

        external_payment_key = record["external_payment_id"] or f"amonora-payment-{record['legacy_id']}"
        payment_defaults = {
            "user": user,
            "plan_code": record["tariff_code"],
            "plan_name": record["plan_name"],
            "amount_rub": record["amount"],
            "duration_days": record["duration_days"],
            "max_devices": record["max_devices"],
            "provider": record["provider"],
            "payment_method": record["payment_method"],
            "status": record["mapped_status"],
            "provider_status": record["provider_status"],
            "provider_payload": record["provider_payload"],
            "paid_at": record["paid_at"] if record["mapped_status"] == SubscriptionPayment.STATUS_PAID else None,
        }
        payment, created = SubscriptionPayment.objects.get_or_create(
            external_payment_id=external_payment_key,
            defaults=payment_defaults,
        )
        if not created:
            skipped_existing_payments += 1
            continue

        imported_payments += 1
        if payment.status == SubscriptionPayment.STATUS_PAID:
            imported_paid_payments += 1
        elif payment.status == SubscriptionPayment.STATUS_PENDING:
            imported_pending_payments += 1
        elif payment.status == SubscriptionPayment.STATUS_CANCELED:
            imported_canceled_payments += 1
        else:
            imported_failed_payments += 1

    return AmonoraPaymentImportSummary(
        source_payments=len(source_payments),
        imported_payments=imported_payments,
        imported_paid_payments=imported_paid_payments,
        imported_pending_payments=imported_pending_payments,
        imported_canceled_payments=imported_canceled_payments,
        imported_failed_payments=imported_failed_payments,
        skipped_unsupported_tariffs=skipped_unsupported_tariffs,
        skipped_existing_payments=skipped_existing_payments,
        dry_run=False,
    )


def import_amonora_support(
    *,
    database_name: str = DEFAULT_RESTORE_DB_NAME,
    limit: int | None = None,
    dry_run: bool = False,
) -> AmonoraSupportImportSummary:
    source_tickets = list(_fetch_amonora_support_tickets(database_name=database_name, limit=limit))
    source_messages = list(_fetch_amonora_support_messages(database_name=database_name, limit=limit))
    if dry_run:
        return _build_support_import_summary(
            source_tickets=source_tickets,
            source_messages=source_messages,
            dry_run=True,
        )

    telegram_user_map = {
        link.telegram_user_id: link.user
        for link in TelegramAccountLink.objects.select_related("user").all()
    }
    created_conversations = 0
    created_messages = 0
    created_attachments = 0
    created_support_admins = 0
    closed_conversations = 0
    in_progress_conversations = 0
    skipped_missing_users = 0
    skipped_existing_conversations = 0
    support_admin_cache: dict[int, User] = {}

    message_rows_by_ticket_id: dict[int, list[dict]] = {}
    for row in source_messages:
        message_rows_by_ticket_id.setdefault(row["ticket_id"], []).append(row)

    for ticket in source_tickets:
        user = telegram_user_map.get(ticket["user_id"])
        if user is None:
            skipped_missing_users += 1
            continue

        conversation, conversation_created = SupportConversation.objects.get_or_create(user=user)
        if conversation.messages.exists():
            skipped_existing_conversations += 1
            continue
        if conversation_created:
            created_conversations += 1

        created_at = ticket["created_at"]
        updated_at = ticket["updated_at"]
        closed_at = ticket["closed_at"]
        conversation.status = ticket["status"]
        conversation.last_message_preview = ticket["last_message_preview"][:255]
        conversation.last_message_at = ticket["updated_at"]
        conversation.closed_at = closed_at if ticket["status"] == SupportConversation.Status.CLOSED else None
        if ticket["assigned_admin_id"] is not None:
            conversation.assigned_admin = _get_or_create_legacy_support_admin(
                legacy_admin_id=ticket["assigned_admin_id"],
                cache=support_admin_cache,
            )
            if conversation.assigned_admin_id is not None:
                created_support_admins = len(support_admin_cache)
        conversation.save(
            update_fields=[
                "status",
                "assigned_admin",
                "last_message_at",
                "last_message_preview",
                "closed_at",
                "updated_at",
            ]
        )
        SupportConversation.objects.filter(pk=conversation.pk).update(
            created_at=created_at,
            updated_at=updated_at,
            closed_at=closed_at if ticket["status"] == SupportConversation.Status.CLOSED else None,
        )

        ticket_message_rows = sorted(
            message_rows_by_ticket_id.get(ticket["id"], []),
            key=lambda row: (row["created_at"], row["legacy_id"]),
        )
        for message_row in ticket_message_rows:
            sender_type = (
                SupportMessage.SenderType.ADMIN
                if message_row["role"] == "admin"
                else SupportMessage.SenderType.USER
            )
            sender_user = None
            sender_display_name = message_row["sender_name"] or "Система поддержки"
            source = SupportMessage.Source.ADMIN
            if sender_type == SupportMessage.SenderType.USER:
                source = (
                    SupportMessage.Source.TELEGRAM_SUPPORT_BOT
                    if _is_telegram_support_message(
                        user=user,
                        sender_id=message_row["sender_id"],
                    )
                    else SupportMessage.Source.WEB
                )
                sender_user = user
            else:
                sender_user = _get_or_create_legacy_support_admin(
                    legacy_admin_id=message_row["sender_id"],
                    cache=support_admin_cache,
                )
                sender_display_name = message_row["sender_name"] or sender_user.username
                if sender_user is not None and sender_user.username.startswith("amonora-support-admin-"):
                    created_support_admins = len(support_admin_cache)

            message = SupportMessage.objects.create(
                conversation=conversation,
                sender_type=sender_type,
                sender_user=sender_user,
                sender_display_name=sender_display_name[:255],
                source=source,
                text=message_row["text"],
            )
            SupportMessage.objects.filter(pk=message.pk).update(created_at=message_row["created_at"])
            created_messages += 1

            if message_row["attachment_name"] or message_row["attachment_file_id"]:
                attachment_file_name = _build_support_attachment_file_name(message_row=message_row)
                attachment = SupportAttachment.objects.create(
                    message=message,
                    file_name=attachment_file_name,
                    content_type=message_row["attachment_mime_type"],
                    size_bytes=message_row["attachment_size"],
                )
                attachment.file.save(
                    attachment_file_name,
                    ContentFile(b"", name=attachment_file_name),
                    save=False,
                )
                attachment.save()
                SupportAttachment.objects.filter(pk=attachment.pk).update(created_at=message_row["created_at"])
                created_attachments += 1

        if ticket["status"] == SupportConversation.Status.CLOSED:
            closed_conversations += 1
        elif ticket["status"] == SupportConversation.Status.IN_PROGRESS:
            in_progress_conversations += 1

    return AmonoraSupportImportSummary(
        source_tickets=len(source_tickets),
        created_conversations=created_conversations,
        created_messages=created_messages,
        created_attachments=created_attachments,
        created_support_admins=len(support_admin_cache),
        closed_conversations=closed_conversations,
        in_progress_conversations=in_progress_conversations,
        skipped_missing_users=skipped_missing_users,
        skipped_existing_conversations=skipped_existing_conversations,
        dry_run=False,
    )


def import_amonora_devices(
    *,
    database_name: str = DEFAULT_RESTORE_DB_NAME,
    limit: int | None = None,
    dry_run: bool = False,
) -> AmonoraDeviceImportSummary:
    source_vpn_clients = list(_fetch_amonora_vpn_clients(database_name=database_name, limit=limit))
    if dry_run:
        return _build_device_import_summary(source_vpn_clients=source_vpn_clients, dry_run=True)

    current_users = {user.username: user for user in User.objects.all()}
    created_devices = 0
    active_devices = 0
    revoked_devices = 0
    skipped_missing_users = 0
    skipped_existing_devices = 0

    for row in source_vpn_clients:
        user = current_users.get(f"amonora-{row['legacy_user_id']}") or current_users.get(row["username"])
        if user is None:
            skipped_missing_users += 1
            continue

        device_data = row["client_data"]
        device_type = str(device_data.get("device_type", ""))
        device_name = str(device_data.get("device_name") or row["client_uuid"])
        icon = _resolve_legacy_device_icon(device_type=device_type)
        platform_name = _resolve_legacy_device_platform_name(device_type=device_type)
        client_name = str(row["protocol"] or "vpn").upper()
        status = Device.Status.REVOKED if device_data.get("retired") else Device.Status.ACTIVE
        revoked_at = row["created_at"] if status == Device.Status.REVOKED else None
        revoked_reason = "legacy-retired" if status == Device.Status.REVOKED else ""

        device, created = Device.objects.get_or_create(
            user=user,
            name=row["client_uuid"],
            defaults={
                "display_name": device_name[:120],
                "icon": icon,
                "ip_address": row["ip_address"],
                "last_seen": row["created_at"],
                "status": status,
                "platform_name": platform_name[:80],
                "platform": platform_name[:80],
                "client_name": client_name[:80],
                "client": client_name[:80],
                "revoked_at": revoked_at,
                "revoked_reason": revoked_reason,
            },
        )
        if created:
            created_devices += 1
        else:
            skipped_existing_devices += 1
            changed_fields: list[str] = []
            desired_values = {
                "display_name": device_name[:120],
                "icon": icon,
                "ip_address": row["ip_address"],
                "last_seen": row["created_at"],
                "status": status,
                "platform_name": platform_name[:80],
                "platform": platform_name[:80],
                "client_name": client_name[:80],
                "client": client_name[:80],
                "revoked_at": revoked_at,
                "revoked_reason": revoked_reason,
            }
            for field_name, new_value in desired_values.items():
                if getattr(device, field_name) != new_value:
                    setattr(device, field_name, new_value)
                    changed_fields.append(field_name)
            if changed_fields:
                device.save(update_fields=changed_fields)

        Device.objects.filter(pk=device.pk).update(
            created_at=row["created_at"],
            updated_at=row["created_at"],
            last_seen=row["created_at"],
            status=status,
            revoked_at=revoked_at,
            revoked_reason=revoked_reason,
        )
        if status == Device.Status.REVOKED:
            revoked_devices += 1
        else:
            active_devices += 1

    return AmonoraDeviceImportSummary(
        source_vpn_clients=len(source_vpn_clients),
        created_devices=created_devices,
        active_devices=active_devices,
        revoked_devices=revoked_devices,
        skipped_missing_users=skipped_missing_users,
        skipped_existing_devices=skipped_existing_devices,
        dry_run=False,
    )


def import_amonora_device_slot_entitlements(
    *,
    database_name: str = DEFAULT_RESTORE_DB_NAME,
    limit: int | None = None,
    dry_run: bool = False,
) -> AmonoraDeviceSlotEntitlementImportSummary:
    source_entitlements = list(
        _fetch_amonora_device_slot_entitlements(database_name=database_name, limit=limit)
    )
    if dry_run:
        return _build_device_slot_entitlement_import_summary(
            source_entitlements=source_entitlements,
            dry_run=True,
        )

    current_users = {user.username: user for user in User.objects.all()}
    created_activities = 0
    updated_subscriptions = 0
    skipped_missing_users = 0
    skipped_existing_activities = 0
    active_slots_by_user_id: dict[int, int] = {}

    for row in source_entitlements:
        user = current_users.get(f"amonora-{row['legacy_user_id']}")
        if user is None:
            skipped_missing_users += 1
            continue

        legacy_activity_id = row["legacy_id"]
        if UserActivity.objects.filter(
            user=user,
            action=UserActivity.Action.VPN_DEVICE_SLOT_UPDATED,
            metadata__legacy_device_slot_entitlement_id=legacy_activity_id,
        ).exists():
            skipped_existing_activities += 1
            continue

        UserActivity.objects.create(
            user=user,
            action=UserActivity.Action.VPN_DEVICE_SLOT_UPDATED,
            description=(
                f"Legacy VPN device slot entitlement #{legacy_activity_id} "
                f"({row['status']}, +{row['slots_count']} slots)."
            ),
            metadata={
                "legacy_device_slot_entitlement_id": legacy_activity_id,
                "legacy_payment_record_id": row["payment_record_id"],
                "status": row["status"],
                "slots_count": row["slots_count"],
                "unit_price_rub": row["unit_price_rub"],
                "total_amount_rub": row["total_amount_rub"],
                "starts_at": row["starts_at"].isoformat() if row["starts_at"] else None,
                "expires_at": row["expires_at"].isoformat() if row["expires_at"] else None,
            },
        )
        created_activities += 1

        if row["status"] == "active":
            active_slots_by_user_id[user.id] = active_slots_by_user_id.get(user.id, 0) + int(row["slots_count"])

    for user_id, active_slots_count in active_slots_by_user_id.items():
        subscription = Subscription.objects.filter(user_id=user_id).first()
        if subscription is None:
            continue
        base_max_devices = _resolve_subscription_base_max_devices(subscription=subscription)
        desired_max_devices = base_max_devices + active_slots_count
        if subscription.max_devices != desired_max_devices:
            subscription.max_devices = desired_max_devices
            subscription.save(update_fields=["max_devices", "updated_at"])
            updated_subscriptions += 1

    return AmonoraDeviceSlotEntitlementImportSummary(
        source_entitlements=len(source_entitlements),
        updated_subscriptions=updated_subscriptions,
        created_activities=created_activities,
        skipped_missing_users=skipped_missing_users,
        skipped_existing_activities=skipped_existing_activities,
        dry_run=False,
    )


def import_amonora_vpn_repair_events(
    *,
    database_name: str = DEFAULT_RESTORE_DB_NAME,
    limit: int | None = None,
    dry_run: bool = False,
) -> AmonoraVpnRepairImportSummary:
    source_events = list(_fetch_amonora_vpn_repair_events(database_name=database_name, limit=limit))
    if dry_run:
        return AmonoraVpnRepairImportSummary(
            source_events=len(source_events),
            created_activities=0,
            skipped_missing_users=0,
            skipped_existing_activities=0,
            dry_run=True,
        )

    current_users = {user.username: user for user in User.objects.all()}
    created_activities = 0
    skipped_missing_users = 0
    skipped_existing_activities = 0

    for row in source_events:
        user = current_users.get(f"amonora-{row['legacy_user_id']}")
        if user is None:
            skipped_missing_users += 1
            continue

        if UserActivity.objects.filter(
            user=user,
            action=UserActivity.Action.VPN_REPAIR_EVENT,
            metadata__legacy_vpn_repair_event_id=row["legacy_id"],
        ).exists():
            skipped_existing_activities += 1
            continue

        UserActivity.objects.create(
            user=user,
            action=UserActivity.Action.VPN_REPAIR_EVENT,
            description=f"Legacy VPN repair event #{row['legacy_id']} ({row['result']}).",
            metadata={
                "legacy_vpn_repair_event_id": row["legacy_id"],
                "result": row["result"],
                "reason": row["reason"],
            },
        )
        created_activities += 1

    return AmonoraVpnRepairImportSummary(
        source_events=len(source_events),
        created_activities=created_activities,
        skipped_missing_users=skipped_missing_users,
        skipped_existing_activities=skipped_existing_activities,
        dry_run=False,
    )


def _build_payment_import_summary(
    *,
    source_payments: list[dict],
    dry_run: bool,
) -> AmonoraPaymentImportSummary:
    supported_codes = {plan["code"] for plan in SUBSCRIPTION_PLAN_CATALOG}
    imported_payments = 0
    imported_paid_payments = 0
    imported_pending_payments = 0
    imported_canceled_payments = 0
    imported_failed_payments = 0
    skipped_unsupported_tariffs = 0

    for record in source_payments:
        if record["tariff_code"] not in supported_codes:
            skipped_unsupported_tariffs += 1
            continue
        imported_payments += 1
        if record["mapped_status"] == SubscriptionPayment.STATUS_PAID:
            imported_paid_payments += 1
        elif record["mapped_status"] == SubscriptionPayment.STATUS_PENDING:
            imported_pending_payments += 1
        elif record["mapped_status"] == SubscriptionPayment.STATUS_CANCELED:
            imported_canceled_payments += 1
        else:
            imported_failed_payments += 1

    return AmonoraPaymentImportSummary(
        source_payments=len(source_payments),
        imported_payments=imported_payments,
        imported_paid_payments=imported_paid_payments,
        imported_pending_payments=imported_pending_payments,
        imported_canceled_payments=imported_canceled_payments,
        imported_failed_payments=imported_failed_payments,
        skipped_unsupported_tariffs=skipped_unsupported_tariffs,
        skipped_existing_payments=0,
        dry_run=dry_run,
    )


def _build_support_import_summary(
    *,
    source_tickets: list[dict],
    source_messages: list[dict],
    dry_run: bool,
) -> AmonoraSupportImportSummary:
    support_admin_ids = {
        ticket["assigned_admin_id"]
        for ticket in source_tickets
        if ticket["assigned_admin_id"] is not None
    }
    support_admin_ids.update(
        message["sender_id"]
        for message in source_messages
        if message["role"] == "admin"
    )
    created_attachments = sum(
        1
        for message in source_messages
        if message["attachment_name"] or message["attachment_file_id"]
    )
    closed_conversations = sum(1 for ticket in source_tickets if ticket["status"] == SupportConversation.Status.CLOSED)
    in_progress_conversations = sum(1 for ticket in source_tickets if ticket["status"] == SupportConversation.Status.IN_PROGRESS)

    return AmonoraSupportImportSummary(
        source_tickets=len(source_tickets),
        created_conversations=len(source_tickets),
        created_messages=len(source_messages),
        created_attachments=created_attachments,
        created_support_admins=len(support_admin_ids),
        closed_conversations=closed_conversations,
        in_progress_conversations=in_progress_conversations,
        skipped_missing_users=0,
        skipped_existing_conversations=0,
        dry_run=dry_run,
    )


def _run_psql(*, database_name: str, sql: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "sudo",
            "-u",
            "postgres",
            "psql",
            "-d",
            database_name,
            "-Atq",
            "-c",
            sql,
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def _build_device_import_summary(
    *,
    source_vpn_clients: list[dict],
    dry_run: bool,
) -> AmonoraDeviceImportSummary:
    active_devices = 0
    revoked_devices = 0
    for row in source_vpn_clients:
        if row["client_data"].get("retired"):
            revoked_devices += 1
        else:
            active_devices += 1

    return AmonoraDeviceImportSummary(
        source_vpn_clients=len(source_vpn_clients),
        created_devices=active_devices + revoked_devices,
        active_devices=active_devices,
        revoked_devices=revoked_devices,
        skipped_missing_users=0,
        skipped_existing_devices=0,
        dry_run=dry_run,
    )


def _resolve_legacy_device_icon(*, device_type: str) -> str:
    normalized = (device_type or "").strip().lower()
    if normalized in {"ios", "android"}:
        return Device.Icon.MOBILE
    if normalized in {"macos", "windows", "desktop", "linux"}:
        return Device.Icon.LAPTOP
    return Device.Icon.DESKTOP


def _resolve_legacy_device_platform_name(*, device_type: str) -> str:
    normalized = (device_type or "").strip().lower()
    if not normalized:
        return "Legacy VPN"
    return normalized.capitalize()


def _resolve_subscription_base_max_devices(*, subscription: Subscription) -> int:
    for plan in SUBSCRIPTION_PLAN_CATALOG:
        if plan["title"] == subscription.plan_name:
            return int(plan["max_devices"])
    return subscription.max_devices


def _build_device_slot_entitlement_import_summary(
    *,
    source_entitlements: list[dict],
    dry_run: bool,
) -> AmonoraDeviceSlotEntitlementImportSummary:
    return AmonoraDeviceSlotEntitlementImportSummary(
        source_entitlements=len(source_entitlements),
        updated_subscriptions=0,
        created_activities=0,
        skipped_missing_users=0,
        skipped_existing_activities=0,
        dry_run=dry_run,
    )


def _parse_overview(*, database_name: str, output: str) -> AmonoraRestoreOverview:
    values = [line.strip() for line in output.splitlines() if line.strip()]
    if len(values) != 5:
        raise ValueError(f"Unexpected psql output for {database_name}: {output!r}")

    return AmonoraRestoreOverview(
        database_name=database_name,
        table_count=int(values[0]),
        users_count=int(values[1]),
        vpn_clients_count=int(values[2]),
        payment_records_count=int(values[3]),
        support_tickets_count=int(values[4]),
    )


def _fetch_amonora_user_rows(*, database_name: str, limit: int | None = None):
    limit_clause = ""
    if limit is not None:
        limit_clause = f"limit {int(limit)}"

    query = f"""
        select
            id,
            telegram_id,
            coalesce(username, ''),
            created_at,
            is_blocked
        from users
        order by id
        {limit_clause};
    """
    completed = subprocess.run(
        [
            "sudo",
            "-u",
            "postgres",
            "psql",
            "-d",
            database_name,
            "-Atq",
            "-F",
            "\t",
            "-c",
            query,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    for raw_line in completed.stdout.splitlines():
        row = raw_line.split("\t")
        if not row:
            continue

        legacy_id = int(row[0])
        telegram_user_id = int(row[1])
        legacy_username = row[2].strip()
        created_at = parse_datetime(row[3].strip())
        if created_at is None:
            raise ValueError(f"Invalid created_at value for legacy user {legacy_id}: {row[3]!r}")
        if timezone.is_naive(created_at):
            created_at = timezone.make_aware(created_at, timezone.get_current_timezone())

        is_blocked = row[4].strip().lower() in {"t", "true", "1", "yes"}
        technical_username = f"amonora-{legacy_id}"

        yield {
            "legacy_id": legacy_id,
            "telegram_user_id": telegram_user_id,
            "telegram_username": legacy_username,
            "username": technical_username,
            "email": f"{technical_username}@infinda.local",
            "first_name": legacy_username[:150],
            "date_joined": created_at,
            "is_blocked": is_blocked,
        }


def _fetch_amonora_subscription_rows(*, database_name: str, limit: int | None = None):
    limit_clause = ""
    if limit is not None:
        limit_clause = f"limit {int(limit)}"

    query = f"""
        select
            id,
            telegram_id,
            coalesce(username, ''),
            created_at,
            coalesce(trial_used, false),
            trial_started_at,
            trial_expires_at,
            subscription_started_at,
            subscription_expires_at,
            coalesce(subscription_status, 'inactive'),
            coalesce(subscription_source, '')
        from users
        order by id
        {limit_clause};
    """
    completed = subprocess.run(
        [
            "sudo",
            "-u",
            "postgres",
            "psql",
            "-d",
            database_name,
            "-Atq",
            "-F",
            "\t",
            "-c",
            query,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    for raw_line in completed.stdout.splitlines():
        row = raw_line.split("\t")
        if not row:
            continue

        legacy_id = int(row[0])
        telegram_user_id = int(row[1])
        legacy_username = row[2].strip()
        created_at = _parse_legacy_datetime(legacy_id=legacy_id, raw_value=row[3].strip())
        trial_used = _parse_legacy_bool(row[4])
        trial_started_at = _parse_optional_legacy_datetime(legacy_id=legacy_id, raw_value=row[5].strip())
        trial_expires_at = _parse_optional_legacy_datetime(legacy_id=legacy_id, raw_value=row[6].strip())
        subscription_started_at = _parse_optional_legacy_datetime(legacy_id=legacy_id, raw_value=row[7].strip())
        subscription_expires_at = _parse_optional_legacy_datetime(legacy_id=legacy_id, raw_value=row[8].strip())
        subscription_state = row[9].strip().lower() or "inactive"
        subscription_source = row[10].strip()

        technical_username = f"amonora-{legacy_id}"
        yield {
            "legacy_id": legacy_id,
            "telegram_user_id": telegram_user_id,
            "username": technical_username,
            "telegram_username": legacy_username,
            "created_at": created_at,
            "trial_used": trial_used,
            "trial_started_at": trial_started_at,
            "trial_expires_at": trial_expires_at,
            "subscription_started_at": subscription_started_at,
            "subscription_expires_at": subscription_expires_at,
            "subscription_state": subscription_state,
            "subscription_source": subscription_source,
        }


def _fetch_amonora_payment_rows(*, database_name: str, limit: int | None = None):
    limit_clause = ""
    if limit is not None:
        limit_clause = f"limit {int(limit)}"

    query = f"""
        select
            id,
            user_id,
            coalesce(external_payment_id, ''),
            coalesce(tariff_code, ''),
            coalesce(payment_method, ''),
            coalesce(payment_status, ''),
            amount,
            coalesce(currency, ''),
            duration_days,
            coalesce(note, ''),
            confirmed_at,
            created_at,
            coalesce(reference, ''),
            coalesce(metadata_json, ''),
            coalesce(reviewed_by_actor_id, ''),
            coalesce(reviewed_by_actor_name, ''),
            reviewed_at,
            coalesce(rejection_reason, ''),
            expires_at,
            list_price_amount,
            balance_reserved_amount,
            balance_applied_amount
        from payment_records
        order by id
        {limit_clause};
    """
    completed = subprocess.run(
        [
            "sudo",
            "-u",
            "postgres",
            "psql",
            "-d",
            database_name,
            "-Atq",
            "-F",
            "\t",
            "-c",
            query,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    reader = csv.reader(completed.stdout.splitlines(), delimiter="\t")
    supported_plan_by_code = {plan["code"]: plan for plan in SUBSCRIPTION_PLAN_CATALOG}
    for row in reader:
        if not row:
            continue

        legacy_id = int(row[0])
        legacy_user_id = int(row[1])
        external_payment_id = row[2].strip()
        tariff_code = row[3].strip()
        payment_method = row[4].strip() or "manual"
        payment_status = row[5].strip().lower()
        amount = int(row[6])
        currency = row[7].strip() or "RUB"
        duration_days = int(row[8])
        note = row[9].strip()
        confirmed_at = _parse_optional_legacy_datetime(legacy_id=legacy_id, raw_value=row[10].strip())
        created_at = _parse_legacy_datetime(legacy_id=legacy_id, raw_value=row[11].strip())
        reference = row[12].strip()
        metadata_json = row[13].strip()
        reviewed_by_actor_id = row[14].strip()
        reviewed_by_actor_name = row[15].strip()
        reviewed_at = _parse_optional_legacy_datetime(legacy_id=legacy_id, raw_value=row[16].strip())
        rejection_reason = row[17].strip()
        expires_at = _parse_optional_legacy_datetime(legacy_id=legacy_id, raw_value=row[18].strip())
        list_price_amount = int(row[19]) if row[19].strip() else 0
        balance_reserved_amount = int(row[20]) if row[20].strip() else 0
        balance_applied_amount = int(row[21]) if row[21].strip() else 0

        plan = supported_plan_by_code.get(tariff_code)
        if plan is None:
            yield {
                "legacy_id": legacy_id,
                "skip": True,
                "tariff_code": tariff_code,
            }
            continue

        user_username = f"amonora-{legacy_user_id}"
        mapped_status = _map_legacy_payment_status(payment_status)
        provider_status = payment_status.upper() if payment_status else ""
        try:
            provider_payload = json.loads(metadata_json) if metadata_json else {}
        except json.JSONDecodeError:
            provider_payload = {"raw_metadata_json": metadata_json}

        provider_payload.update(
            {
                "legacy_payment_id": legacy_id,
                "legacy_user_id": legacy_user_id,
                "legacy_tariff_code": tariff_code,
                "legacy_payment_status": payment_status,
                "legacy_payment_method": payment_method,
                "legacy_currency": currency,
                "legacy_note": note,
                "legacy_reference": reference,
                "legacy_reviewed_by_actor_id": reviewed_by_actor_id,
                "legacy_reviewed_by_actor_name": reviewed_by_actor_name,
                "legacy_reviewed_at": reviewed_at.isoformat() if reviewed_at is not None else None,
                "legacy_rejection_reason": rejection_reason,
                "legacy_expires_at": expires_at.isoformat() if expires_at is not None else None,
                "legacy_list_price_amount": list_price_amount,
                "legacy_balance_reserved_amount": balance_reserved_amount,
                "legacy_balance_applied_amount": balance_applied_amount,
            }
        )

        yield {
            "legacy_id": legacy_id,
            "username": user_username,
            "external_payment_id": external_payment_id,
            "tariff_code": tariff_code,
            "plan_name": plan["title"],
            "amount": amount,
            "duration_days": duration_days or int(plan["duration_days"]),
            "max_devices": int(plan["max_devices"]),
            "provider": SubscriptionPayment.PROVIDER_PLATEGA,
            "payment_method": payment_method,
            "mapped_status": mapped_status,
            "provider_status": provider_status,
            "provider_payload": provider_payload,
            "paid_at": confirmed_at or created_at,
            "created_at": created_at,
            "skip": False,
        }


def _build_subscription_import_summary(
    *,
    source_users: list[dict],
    dry_run: bool,
) -> AmonoraSubscriptionImportSummary:
    created_trial_subscriptions = 0
    created_active_subscriptions = 0
    created_expired_subscriptions = 0
    skipped_inactive_users = 0
    skipped_existing_subscriptions = 0

    for record in source_users:
        if record["subscription_state"] == "inactive":
            skipped_inactive_users += 1
        elif record["subscription_state"] == "trial":
            created_trial_subscriptions += 1
        elif record["subscription_state"] == "active":
            created_active_subscriptions += 1
        elif record["subscription_state"] == "expired":
            created_expired_subscriptions += 1

    created_subscriptions = (
        created_trial_subscriptions
        + created_active_subscriptions
        + created_expired_subscriptions
    )
    return AmonoraSubscriptionImportSummary(
        source_users=len(source_users),
        created_subscriptions=created_subscriptions,
        created_trial_subscriptions=created_trial_subscriptions,
        created_active_subscriptions=created_active_subscriptions,
        created_expired_subscriptions=created_expired_subscriptions,
        skipped_inactive_users=skipped_inactive_users,
        skipped_existing_subscriptions=skipped_existing_subscriptions,
        dry_run=dry_run,
    )


def _create_imported_trial_subscription(*, user, record: dict) -> Subscription:
    ensure_default_route_catalog()
    starts_at = _legacy_datetime_to_date(
        record["trial_started_at"] or record["created_at"],
    )
    ends_at = _legacy_datetime_to_date(
        record["trial_expires_at"] or record["created_at"] + timedelta(days=3),
    )
    public_token = create_unique_public_subscription_token()
    subscription = Subscription.objects.create(
        user=user,
        plan_name=TRIAL_PLAN_NAME,
        starts_at=starts_at,
        ends_at=ends_at,
        max_devices=TRIAL_MAX_DEVICES,
        public_token=public_token,
        main_url=build_public_subscription_url(token=public_token),
    )
    SubscriptionRoute.objects.bulk_create(
        [
            SubscriptionRoute(
                subscription=subscription,
                code=code,
                label=label,
                url=get_connection_route_by_code(code=code).endpoint_url,
                connection_route=get_connection_route_by_code(code=code),
                position=index,
            )
            for index, (code, label) in enumerate(TRIAL_ROUTE_DEFINITIONS, start=1)
        ]
    )
    create_subscription_history_event(
        user=user,
        subscription=subscription,
        event_type=SubscriptionHistoryEvent.EVENT_TRIAL_STARTED,
        plan_code="trial",
        plan_name=TRIAL_PLAN_NAME,
        starts_at=starts_at,
        ends_at=ends_at,
    )
    return subscription


def _create_imported_paid_subscription(*, user, record: dict) -> Subscription:
    ensure_default_route_catalog()
    plan_code, plan_name, max_devices = _guess_subscription_plan(
        starts_at=record["subscription_started_at"] or record["created_at"],
        ends_at=record["subscription_expires_at"] or record["created_at"],
    )
    starts_at = _legacy_datetime_to_date(record["subscription_started_at"] or record["created_at"])
    ends_at = _legacy_datetime_to_date(record["subscription_expires_at"] or record["created_at"])
    public_token = create_unique_public_subscription_token()
    subscription = Subscription.objects.create(
        user=user,
        plan_name=plan_name,
        starts_at=starts_at,
        ends_at=ends_at,
        max_devices=max_devices,
        public_token=public_token,
        main_url=build_public_subscription_url(token=public_token),
    )
    ensure_subscription_routes(subscription=subscription, plan_code=plan_code)
    create_subscription_history_event(
        user=user,
        subscription=subscription,
        event_type=SubscriptionHistoryEvent.EVENT_ACTIVATED,
        plan_code=plan_code,
        plan_name=plan_name,
        starts_at=starts_at,
        ends_at=ends_at,
    )
    return subscription


def _guess_subscription_plan(*, starts_at, ends_at) -> tuple[str, str, int]:
    duration_days = max((_legacy_datetime_to_date(ends_at) - _legacy_datetime_to_date(starts_at)).days, 1)
    if duration_days <= 45:
        plan = SUBSCRIPTION_PLAN_CATALOG[0]
    elif duration_days <= 120:
        plan = SUBSCRIPTION_PLAN_CATALOG[1]
    elif duration_days <= 240:
        plan = SUBSCRIPTION_PLAN_CATALOG[2]
    else:
        plan = SUBSCRIPTION_PLAN_CATALOG[3]

    return plan["code"], plan["title"], int(plan["max_devices"])


def _legacy_datetime_to_date(value):
    if isinstance(value, datetime_cls):
        return value.date()
    if isinstance(value, date_cls):
        return value
    return value


def _parse_legacy_datetime(*, legacy_id: int, raw_value: str):
    parsed = parse_datetime(raw_value)
    if parsed is None:
        raise ValueError(f"Invalid datetime value for legacy user {legacy_id}: {raw_value!r}")
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def _parse_optional_legacy_datetime(*, legacy_id: int, raw_value: str):
    if not raw_value:
        return None
    return _parse_legacy_datetime(legacy_id=legacy_id, raw_value=raw_value)


def _parse_legacy_bool(raw_value: str) -> bool:
    return raw_value.strip().lower() in {"t", "true", "1", "yes"}


def _map_legacy_payment_status(payment_status: str) -> str:
    if payment_status == "confirmed":
        return SubscriptionPayment.STATUS_PAID
    if payment_status == "cancelled":
        return SubscriptionPayment.STATUS_CANCELED
    if payment_status in {"pending", "awaiting_user_payment", "awaiting_admin_review"}:
        return SubscriptionPayment.STATUS_PENDING
    return SubscriptionPayment.STATUS_FAILED


def _fetch_amonora_vpn_clients(*, database_name: str, limit: int | None = None):
    limit_clause = ""
    if limit is not None:
        limit_clause = f"limit {int(limit)}"

    query = f"""
        copy (
            select
                vc.id as legacy_id,
                vc.user_id as legacy_user_id,
                coalesce(u.username, '') as username,
                coalesce(vc.protocol, '') as protocol,
                coalesce(vc.client_uuid, '') as client_uuid,
                coalesce(vc.email, '') as email,
                vc.created_at as created_at,
                coalesce(vc.xui_client_id, '') as xui_client_id,
                coalesce(vc.client_data, '') as client_data
            from vpn_clients vc
            join users u on u.id = vc.user_id
            order by vc.id
            {limit_clause}
        ) to stdout with csv header;
    """
    completed = subprocess.run(
        [
            "sudo",
            "-u",
            "postgres",
            "psql",
            "-d",
            database_name,
            "-Atq",
            "-c",
            query,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    reader = csv.DictReader(StringIO(completed.stdout))
    for row in reader:
        created_at = parse_datetime(row["created_at"].strip())
        if created_at is None:
            raise ValueError(f"Invalid created_at value for legacy vpn client {row['legacy_id']}: {row['created_at']!r}")
        if timezone.is_naive(created_at):
            created_at = timezone.make_aware(created_at, timezone.get_current_timezone())

        client_data_raw = row["client_data"].strip()
        try:
            client_data = json.loads(client_data_raw) if client_data_raw else {}
        except json.JSONDecodeError:
            client_data = {"raw_client_data": client_data_raw}

        yield {
            "legacy_id": int(row["legacy_id"]),
            "legacy_user_id": int(row["legacy_user_id"]),
            "username": row["username"].strip(),
            "protocol": row["protocol"].strip(),
            "client_uuid": row["client_uuid"].strip(),
            "email": row["email"].strip(),
            "created_at": created_at,
            "xui_client_id": row["xui_client_id"].strip(),
            "client_data": client_data,
            "ip_address": "0.0.0.0",
        }


def _fetch_amonora_device_slot_entitlements(*, database_name: str, limit: int | None = None):
    limit_clause = ""
    if limit is not None:
        limit_clause = f"limit {int(limit)}"

    query = f"""
        copy (
            select
                id,
                user_id,
                payment_record_id,
                slots_count,
                unit_price_rub,
                total_amount_rub,
                starts_at,
                expires_at,
                status
            from device_slot_entitlements
            order by id
            {limit_clause}
        ) to stdout with csv header;
    """
    completed = subprocess.run(
        [
            "sudo",
            "-u",
            "postgres",
            "psql",
            "-d",
            database_name,
            "-Atq",
            "-c",
            query,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    reader = csv.DictReader(StringIO(completed.stdout))
    for row in reader:
        starts_at = parse_datetime(row["starts_at"].strip())
        expires_at = parse_datetime(row["expires_at"].strip())
        if starts_at is None or expires_at is None:
            raise ValueError(f"Invalid entitlement datetime for legacy row {row['id']}: {row!r}")
        if timezone.is_naive(starts_at):
            starts_at = timezone.make_aware(starts_at, timezone.get_current_timezone())
        if timezone.is_naive(expires_at):
            expires_at = timezone.make_aware(expires_at, timezone.get_current_timezone())

        yield {
            "legacy_id": int(row["id"]),
            "legacy_user_id": int(row["user_id"]),
            "payment_record_id": int(row["payment_record_id"]) if row["payment_record_id"] else None,
            "slots_count": int(row["slots_count"] or 0),
            "unit_price_rub": int(row["unit_price_rub"] or 0),
            "total_amount_rub": int(row["total_amount_rub"] or 0),
            "starts_at": starts_at,
            "expires_at": expires_at,
            "status": row["status"].strip(),
        }


def _fetch_amonora_vpn_repair_events(*, database_name: str, limit: int | None = None):
    limit_clause = ""
    if limit is not None:
        limit_clause = f"limit {int(limit)}"

    query = f"""
        copy (
            select
                id as legacy_id,
                user_id as legacy_user_id,
                coalesce(result, '') as result,
                coalesce(reason, '') as reason,
                created_at as created_at
            from vpn_repair_events
            order by id
            {limit_clause}
        ) to stdout with csv header;
    """
    completed = subprocess.run(
        [
            "sudo",
            "-u",
            "postgres",
            "psql",
            "-d",
            database_name,
            "-Atq",
            "-c",
            query,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    reader = csv.DictReader(StringIO(completed.stdout))
    for row in reader:
        created_at = parse_datetime(row["created_at"].strip())
        if created_at is None:
            raise ValueError(f"Invalid repair event datetime for legacy row {row['legacy_id']}: {row!r}")
        if timezone.is_naive(created_at):
            created_at = timezone.make_aware(created_at, timezone.get_current_timezone())

        yield {
            "legacy_id": int(row["legacy_id"]),
            "legacy_user_id": int(row["legacy_user_id"]),
            "result": row["result"].strip(),
            "reason": row["reason"].strip(),
            "created_at": created_at,
        }


def _fetch_amonora_support_tickets(*, database_name: str, limit: int | None = None):
    limit_clause = ""
    if limit is not None:
        limit_clause = f"limit {int(limit)}"

    query = f"""
        copy (
            select
            id,
            user_id,
            replace(coalesce(username, ''), E'\n', ' '),
            replace(coalesce(full_name, ''), E'\n', ' '),
            coalesce(status, 'new'),
            assigned_admin_id,
            replace(coalesce(assigned_admin_name, ''), E'\n', ' '),
            replace(coalesce(last_message_preview, ''), E'\n', ' '),
            replace(coalesce(last_user_message_preview, ''), E'\n', ' '),
            replace(coalesce(last_admin_reply_preview, ''), E'\n', ' '),
            replace(coalesce(admin_cards_json, ''), E'\n', ' '),
            created_at,
            updated_at,
            closed_at
        from support_tickets
        order by id
        {limit_clause}
        ) to stdout with csv
    """
    completed = subprocess.run(
        [
            "sudo",
            "-u",
            "postgres",
            "psql",
            "-d",
            database_name,
            "-Atq",
            "-F",
            "\t",
            "-c",
            query,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    reader = csv.reader(StringIO(completed.stdout))
    for row in reader:
        if not row:
            continue

        ticket_id = int(row[0])
        user_id = int(row[1])
        username = row[2].strip()
        full_name = row[3].strip()
        status = row[4].strip().lower() or SupportConversation.Status.NEW
        assigned_admin_id = int(row[5]) if row[5].strip() else None
        assigned_admin_name = row[6].strip()
        last_message_preview = row[7].strip()
        last_user_message_preview = row[8].strip()
        last_admin_reply_preview = row[9].strip()
        admin_cards_json = row[10].strip()
        created_at = _parse_legacy_datetime(legacy_id=ticket_id, raw_value=row[11].strip())
        updated_at = _parse_legacy_datetime(legacy_id=ticket_id, raw_value=row[12].strip())
        closed_at = _parse_optional_legacy_datetime(legacy_id=ticket_id, raw_value=row[13].strip())

        yield {
            "id": ticket_id,
            "user_id": user_id,
            "username": username,
            "full_name": full_name,
            "status": status,
            "assigned_admin_id": assigned_admin_id,
            "assigned_admin_name": assigned_admin_name,
            "last_message_preview": last_message_preview or last_user_message_preview or last_admin_reply_preview,
            "last_user_message_preview": last_user_message_preview,
            "last_admin_reply_preview": last_admin_reply_preview,
            "admin_cards_json": admin_cards_json,
            "created_at": created_at,
            "updated_at": updated_at,
            "closed_at": closed_at,
        }


def _fetch_amonora_support_messages(*, database_name: str, limit: int | None = None):
    limit_clause = ""
    if limit is not None:
        limit_clause = f"limit {int(limit)}"

    query = f"""
        copy (
            select
            id,
            ticket_id,
            role,
            sender_id,
            replace(coalesce(sender_name, ''), E'\n', ' '),
            coalesce(content_type, ''),
            replace(coalesce(text, ''), E'\n', ' '),
            created_at,
            coalesce(attachment_file_id, ''),
            coalesce(attachment_file_unique_id, ''),
            coalesce(attachment_kind, ''),
            replace(coalesce(attachment_name, ''), E'\n', ' '),
            coalesce(attachment_mime_type, ''),
            coalesce(attachment_size, 0)
        from support_ticket_messages
        order by ticket_id, created_at, id
        {limit_clause}
        ) to stdout with csv
    """
    completed = subprocess.run(
        [
            "sudo",
            "-u",
            "postgres",
            "psql",
            "-d",
            database_name,
            "-Atq",
            "-F",
            "\t",
            "-c",
            query,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    reader = csv.reader(StringIO(completed.stdout))
    for row in reader:
        if not row:
            continue

        message_id = int(row[0])
        ticket_id = int(row[1])
        role = row[2].strip().lower()
        sender_id = int(row[3])
        sender_name = row[4].strip()
        content_type = row[5].strip()
        text = row[6]
        created_at = _parse_legacy_datetime(legacy_id=message_id, raw_value=row[7].strip())
        attachment_file_id = row[8].strip()
        attachment_file_unique_id = row[9].strip()
        attachment_kind = row[10].strip()
        attachment_name = row[11].strip()
        attachment_mime_type = row[12].strip()
        attachment_size = int(row[13]) if row[13].strip() else 0

        yield {
            "legacy_id": message_id,
            "ticket_id": ticket_id,
            "role": role,
            "sender_id": sender_id,
            "sender_name": sender_name,
            "content_type": content_type,
            "text": text,
            "created_at": created_at,
            "attachment_file_id": attachment_file_id,
            "attachment_file_unique_id": attachment_file_unique_id,
            "attachment_kind": attachment_kind,
            "attachment_name": attachment_name,
            "attachment_mime_type": attachment_mime_type,
            "attachment_size": attachment_size,
        }


def _get_or_create_legacy_support_admin(*, legacy_admin_id: int, cache: dict[int, User]) -> User:
    admin_user = cache.get(legacy_admin_id)
    if admin_user is not None:
        return admin_user

    username = f"amonora-support-admin-{legacy_admin_id}"
    admin_user, _created = User.objects.get_or_create(
        username=username,
        defaults={
            "email": f"{username}@infinda.local",
            "first_name": "Legacy",
            "last_name": f"Support {legacy_admin_id}",
            "is_active": False,
            "is_staff": True,
            "is_superuser": True,
        },
    )
    if not admin_user.has_usable_password():
        admin_user.set_unusable_password()
        admin_user.save(
            update_fields=[
                "password",
                "email",
                "first_name",
                "last_name",
                "is_active",
                "is_staff",
                "is_superuser",
            ]
        )
    cache[legacy_admin_id] = admin_user
    return admin_user


def _is_telegram_support_message(*, user: User, sender_id: int) -> bool:
    return TelegramAccountLink.objects.filter(
        user=user,
        telegram_user_id=sender_id,
        is_active=True,
    ).exists()


def _build_support_attachment_file_name(*, message_row: dict) -> str:
    if message_row["attachment_name"]:
        return message_row["attachment_name"]
    if message_row["attachment_file_id"]:
        return f"{message_row['attachment_file_id']}.bin"
    return f"support-attachment-{message_row['legacy_id']}.bin"
