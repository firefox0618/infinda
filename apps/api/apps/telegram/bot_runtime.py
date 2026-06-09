from __future__ import annotations

from rest_framework.exceptions import APIException
from rest_framework.exceptions import ValidationError

from apps.support.services import IncomingSupportAttachment, create_support_message_from_telegram

from .bot_client import TelegramBotClient
from .services import (
    build_telegram_checkout_message,
    build_telegram_devices_summary,
    build_telegram_link_help_text,
    build_telegram_linked_reply_keyboard,
    build_telegram_main_menu_text,
    build_telegram_subscription_plans_text,
    build_telegram_subscription_summary,
    build_telegram_sync_result,
    build_telegram_unlinked_reply_keyboard,
    build_telegram_device_repair_result,
    build_telegram_support_hint,
    confirm_telegram_link,
    get_active_telegram_link_by_telegram_user_id,
    TELEGRAM_MENU_BUTTON_DEVICES,
    TELEGRAM_MENU_BUTTON_LINK_HELP,
    TELEGRAM_MENU_BUTTON_MENU,
    TELEGRAM_MENU_BUTTON_PLANS,
    TELEGRAM_MENU_BUTTON_SUBSCRIPTION,
    TELEGRAM_MENU_BUTTON_SUPPORT,
    TELEGRAM_MENU_BUTTON_SYNC,
)


def process_telegram_update(*, update: dict, client: TelegramBotClient) -> None:
    message = update.get("message")
    if not message:
        return

    chat = message.get("chat") or {}
    sender = message.get("from") or {}
    chat_id = chat.get("id")
    telegram_user_id = sender.get("id")

    if chat_id is None or telegram_user_id is None:
        return

    message_text = _extract_message_text(message=message)
    link_token = _extract_start_link_token(message_text)

    if link_token is not None:
        _handle_link_command(client=client, chat_id=chat_id, sender=sender, token=link_token)
        return

    telegram_link = get_active_telegram_link_by_telegram_user_id(telegram_user_id=telegram_user_id)
    if _try_handle_product_command(
        client=client,
        chat_id=chat_id,
        message_text=message_text,
        telegram_link=telegram_link,
    ):
        return

    if telegram_link is None:
        _send_unlinked_hint(client=client, chat_id=chat_id)
        return

    attachments = _extract_supported_attachments(message=message, client=client)
    if not message_text and not attachments:
        _send_empty_message_hint(client=client, chat_id=chat_id)
        return

    _forward_support_message(
        client=client,
        chat_id=chat_id,
        telegram_link=telegram_link,
        sender=sender,
        message_text=message_text,
        attachments=attachments,
        telegram_user_id=telegram_user_id,
    )


def _handle_link_command(*, client: TelegramBotClient, chat_id: int, sender: dict, token: str) -> None:
    try:
        confirm_telegram_link(
            token=token,
            telegram_user_id=sender["id"],
            telegram_username=sender.get("username", ""),
            telegram_full_name=_build_full_name(sender=sender),
        )
    except ValidationError:
        client.send_message(
            chat_id=chat_id,
            text=(
                "Не удалось завершить привязку. "
                "Сформируйте новую ссылку в личном кабинете и повторите попытку."
            ),
        )
        return

    client.send_message(
        chat_id=chat_id,
        text=(
            "Telegram успешно привязан. Теперь можно писать сюда сообщения для поддержки INFINDA."
        ),
        reply_markup=build_telegram_linked_reply_keyboard(),
    )


def _send_start_hint(*, client: TelegramBotClient, chat_id: int) -> None:
    client.send_message(
        chat_id=chat_id,
        text=(
            "Этот бот принимает сообщения в поддержку после привязки Telegram "
            "в личном кабинете INFINDA."
        ),
        reply_markup=build_telegram_unlinked_reply_keyboard(),
    )


def _send_linked_start_hint(*, client: TelegramBotClient, chat_id: int) -> None:
    client.send_message(
        chat_id=chat_id,
        text=(
            "INFINDA bot подключен к вашему аккаунту.\n"
            f"{build_telegram_main_menu_text()}"
        ),
        reply_markup=build_telegram_linked_reply_keyboard(),
    )


def _send_unlinked_hint(*, client: TelegramBotClient, chat_id: int) -> None:
    client.send_message(
        chat_id=chat_id,
        text=(
            "Telegram пока не привязан к аккаунту INFINDA. "
            "Откройте личный кабинет и выполните привязку в разделе Telegram."
        ),
        reply_markup=build_telegram_unlinked_reply_keyboard(),
    )


def _send_empty_message_hint(*, client: TelegramBotClient, chat_id: int) -> None:
    client.send_message(
        chat_id=chat_id,
        text="Поддерживаются текстовые сообщения, фото и документы.",
    )


def _try_handle_product_command(
    *,
    client: TelegramBotClient,
    chat_id: int,
    message_text: str,
    telegram_link,
) -> bool:
    normalized_text = (message_text or "").strip()
    if normalized_text == TELEGRAM_MENU_BUTTON_LINK_HELP:
        client.send_message(
            chat_id=chat_id,
            text=build_telegram_link_help_text(),
            reply_markup=build_telegram_unlinked_reply_keyboard(),
        )
        return True

    normalized_lower = normalized_text.lower()
    if normalized_text == TELEGRAM_MENU_BUTTON_SUBSCRIPTION:
        normalized_lower = "/subscription"
    elif normalized_text == TELEGRAM_MENU_BUTTON_DEVICES:
        normalized_lower = "/devices"
    elif normalized_text == TELEGRAM_MENU_BUTTON_PLANS:
        normalized_lower = "/plans"
    elif normalized_text == TELEGRAM_MENU_BUTTON_SYNC:
        normalized_lower = "/sync"
    elif normalized_text == TELEGRAM_MENU_BUTTON_SUPPORT:
        normalized_lower = "/support"
    elif normalized_text == TELEGRAM_MENU_BUTTON_MENU:
        normalized_lower = "/menu"

    if not normalized_lower.startswith("/"):
        return False

    parts = normalized_lower.split(maxsplit=1)
    command = parts[0].split("@", 1)[0].lower()
    command_args = ""
    if normalized_text.startswith("/"):
        raw_parts = normalized_text.split(maxsplit=1)
        command_args = raw_parts[1].strip() if len(raw_parts) > 1 else ""
    if command == "/start":
        if telegram_link is None:
            _send_start_hint(client=client, chat_id=chat_id)
        else:
            _send_linked_start_hint(client=client, chat_id=chat_id)
        return True

    if telegram_link is None:
        return False

    if command == "/menu":
        client.send_message(
            chat_id=chat_id,
            text=build_telegram_main_menu_text(),
            reply_markup=build_telegram_linked_reply_keyboard(),
        )
        return True

    if command == "/subscription":
        client.send_message(
            chat_id=chat_id,
            text=build_telegram_subscription_summary(user=telegram_link.user),
            reply_markup=build_telegram_linked_reply_keyboard(),
        )
        return True

    if command == "/devices":
        client.send_message(
            chat_id=chat_id,
            text=build_telegram_devices_summary(user=telegram_link.user),
            reply_markup=build_telegram_linked_reply_keyboard(),
        )
        return True

    if command == "/plans":
        client.send_message(
            chat_id=chat_id,
            text=build_telegram_subscription_plans_text(),
            reply_markup=build_telegram_linked_reply_keyboard(),
        )
        return True

    if command == "/buy":
        if not command_args:
            client.send_message(
                chat_id=chat_id,
                text="Укажите код тарифа. Пример: /buy 3m",
                reply_markup=build_telegram_linked_reply_keyboard(),
            )
            return True
        try:
            client.send_message(
                chat_id=chat_id,
                text=build_telegram_checkout_message(
                    user=telegram_link.user,
                    plan_code=command_args,
                ),
                reply_markup=build_telegram_linked_reply_keyboard(),
            )
        except (ValidationError, APIException) as exc:
            client.send_message(
                chat_id=chat_id,
                text=f"Не удалось подготовить оплату: {_stringify_error(exc)}",
                reply_markup=build_telegram_linked_reply_keyboard(),
            )
        return True

    if command == "/sync":
        client.send_message(
            chat_id=chat_id,
            text=build_telegram_sync_result(user=telegram_link.user),
            reply_markup=build_telegram_linked_reply_keyboard(),
        )
        return True

    if command == "/repair":
        if not command_args or not command_args.isdigit():
            client.send_message(
                chat_id=chat_id,
                text="Укажите ID устройства. Пример: /repair 12",
                reply_markup=build_telegram_linked_reply_keyboard(),
            )
            return True
        try:
            client.send_message(
                chat_id=chat_id,
                text=build_telegram_device_repair_result(
                    user=telegram_link.user,
                    device_id=int(command_args),
                ),
                reply_markup=build_telegram_linked_reply_keyboard(),
            )
        except ValidationError as exc:
            client.send_message(
                chat_id=chat_id,
                text=f"Не удалось запустить восстановление: {_stringify_error(exc)}",
                reply_markup=build_telegram_linked_reply_keyboard(),
            )
        return True

    if command == "/support":
        client.send_message(
            chat_id=chat_id,
            text=build_telegram_support_hint(),
            reply_markup=build_telegram_linked_reply_keyboard(),
        )
        return True

    return False


def _forward_support_message(
    *,
    client: TelegramBotClient,
    chat_id: int,
    telegram_link,
    sender: dict,
    message_text: str,
    attachments: list[IncomingSupportAttachment],
    telegram_user_id: int,
) -> None:
    create_support_message_from_telegram(
        user=telegram_link.user,
        sender_display_name=_build_sender_display_name(sender=sender),
        text=message_text,
        attachments=attachments,
        telegram_user_id=telegram_user_id,
    )
    client.send_message(
        chat_id=chat_id,
        text="Сообщение передано в поддержку INFINDA.",
        reply_markup=build_telegram_linked_reply_keyboard(),
    )


def _extract_message_text(*, message: dict) -> str:
    raw_text = message.get("text") or message.get("caption") or ""
    return raw_text.strip()


def _stringify_error(exc: Exception) -> str:
    detail = getattr(exc, "detail", None)
    if isinstance(detail, dict):
        first_value = next(iter(detail.values()), "Ошибка")
        if isinstance(first_value, list) and first_value:
            return str(first_value[0])
        return str(first_value)
    if detail is not None:
        return str(detail)
    return str(exc)


def _extract_start_link_token(message_text: str) -> str | None:
    if not message_text:
        return None

    parts = message_text.split(maxsplit=1)
    command = parts[0]
    if not command.startswith("/start"):
        return None

    if len(parts) < 2:
        return None

    payload = parts[1].strip()
    if not payload.startswith("link_"):
        return None

    token = payload.removeprefix("link_").strip()
    return token or None


def _build_full_name(*, sender: dict) -> str:
    first_name = str(sender.get("first_name", "")).strip()
    last_name = str(sender.get("last_name", "")).strip()
    return " ".join(part for part in (first_name, last_name) if part).strip()


def _build_sender_display_name(*, sender: dict) -> str:
    full_name = _build_full_name(sender=sender)
    username = str(sender.get("username", "")).strip()

    if full_name and username:
        return f"{full_name} (@{username})"
    if full_name:
        return full_name
    if username:
        return f"@{username}"
    return "Telegram"


def _extract_supported_attachments(*, message: dict, client: TelegramBotClient) -> list[IncomingSupportAttachment]:
    attachments: list[IncomingSupportAttachment] = []

    document = message.get("document")
    if document:
        attachments.append(
            _download_attachment(
                client=client,
                file_id=document["file_id"],
                file_name=document.get("file_name") or f"telegram-document-{document['file_id']}",
                content_type=document.get("mime_type", "") or "application/octet-stream",
            )
        )

    photos = message.get("photo") or []
    if photos:
        photo = photos[-1]
        attachments.append(
            _download_attachment(
                client=client,
                file_id=photo["file_id"],
                file_name=f"telegram-photo-{photo.get('file_unique_id') or photo['file_id']}.jpg",
                content_type="image/jpeg",
            )
        )

    return attachments


def _download_attachment(
    *,
    client: TelegramBotClient,
    file_id: str,
    file_name: str,
    content_type: str,
) -> IncomingSupportAttachment:
    file_payload = client.get_file(file_id=file_id)
    file_bytes = client.download_file(file_path=file_payload["file_path"])
    return IncomingSupportAttachment(
        file_name=file_name,
        content_type=content_type,
        content_bytes=file_bytes,
    )
