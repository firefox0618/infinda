from django import forms
from django.contrib import admin
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.utils.html import format_html, format_html_join
from rest_framework.exceptions import ValidationError

from .models import SupportAttachment, SupportConversation, SupportMessage
from .services import (
    assign_support_conversation_to_admin,
    close_support_conversation,
    ensure_support_conversation_admin_access,
    get_support_delivery_channel,
    reply_to_support_conversation,
)

User = get_user_model()


class SupportMultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class SupportMultipleFileField(forms.FileField):
    widget = SupportMultipleFileInput

    def clean(self, data, initial=None):
        if not data:
            return []

        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(item, initial) for item in data]

        return [single_file_clean(data, initial)]


class SupportAttachmentInline(admin.TabularInline):
    model = SupportAttachment
    extra = 0
    fields = ("file", "file_name", "content_type", "size_bytes", "created_at")
    readonly_fields = ("file_name", "content_type", "size_bytes", "created_at")


class SupportMessageInline(admin.TabularInline):
    model = SupportMessage
    extra = 0
    can_delete = False
    fields = (
        "sender_type",
        "sender_display_name",
        "source",
        "text",
        "attachments_summary",
        "created_at",
    )
    readonly_fields = fields
    ordering = ("created_at", "id")

    def has_add_permission(self, request, obj=None):
        return False

    @admin.display(description="Вложения")
    def attachments_summary(self, obj):
        attachments = obj.attachments.all()
        if not attachments:
            return "—"

        return format_html_join(
            format_html("<br>"),
            '<a href="{}" target="_blank" rel="noreferrer">{}</a>',
            ((attachment.file.url, attachment.file_name) for attachment in attachments),
        )


class SupportConversationAdminForm(forms.ModelForm):
    reassign_to_admin = forms.ModelChoiceField(
        required=False,
        queryset=User.objects.none(),
        label="Переназначить оператору",
        help_text="Если нужно передать тикет другому сотруднику, выберите его здесь.",
    )
    assign_to_me = forms.BooleanField(
        required=False,
        label="Принять диалог на себя",
    )
    response_text = forms.CharField(
        required=False,
        label="Быстрый ответ оператором",
        widget=forms.Textarea(attrs={"rows": 5}),
    )
    response_attachments = SupportMultipleFileField(
        required=False,
        label="Вложения к ответу",
        help_text="Можно приложить один или несколько файлов к ответу оператора.",
    )
    close_after_reply = forms.BooleanField(
        required=False,
        label="Закрыть после ответа",
    )

    class Meta:
        model = SupportConversation
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["reassign_to_admin"].queryset = User.objects.filter(
            is_staff=True,
        ).order_by("username")


@admin.register(SupportConversation)
class SupportConversationAdmin(admin.ModelAdmin):
    form = SupportConversationAdminForm
    list_display = (
        "id",
        "user",
        "status_badge",
        "assigned_admin",
        "last_message_at",
        "updated_at",
    )
    list_filter = ("status", "assigned_admin", "updated_at")
    search_fields = ("user__email", "user__username", "last_message_preview")
    autocomplete_fields = ("user", "assigned_admin")
    inlines = [SupportMessageInline]
    readonly_fields = (
        "ticket_summary",
        "user_summary",
        "workflow_summary",
        "latest_user_message_text",
        "last_message_at",
        "last_message_preview",
        "created_at",
        "updated_at",
        "closed_at",
    )
    fieldsets = (
        (
            "Тикет",
            {
                "fields": (
                    "user",
                    "status",
                    "assigned_admin",
                    "ticket_summary",
                    "created_at",
                    "updated_at",
                    "closed_at",
                )
            },
        ),
        (
            "Контекст",
            {
                "fields": (
                    "user_summary",
                    "workflow_summary",
                    "latest_user_message_text",
                    "last_message_at",
                    "last_message_preview",
                )
            },
        ),
        (
            "Быстрые действия оператора",
            {
                "fields": (
                    "reassign_to_admin",
                    "assign_to_me",
                    "response_text",
                    "response_attachments",
                    "close_after_reply",
                )
            },
        ),
    )
    actions = ("assign_conversations_to_me", "mark_conversations_closed")

    @admin.display(description="Статус")
    def status_badge(self, obj):
        palette = {
            SupportConversation.Status.NEW: ("#1d4ed8", "#dbeafe"),
            SupportConversation.Status.IN_PROGRESS: ("#b45309", "#fef3c7"),
            SupportConversation.Status.CLOSED: ("#166534", "#dcfce7"),
        }
        color, background = palette.get(obj.status, ("#334155", "#e2e8f0"))
        return format_html(
            '<span style="display:inline-block;padding:4px 10px;border-radius:999px;'
            'font-weight:700;color:{};background:{};">{}</span>',
            color,
            background,
            obj.get_status_display(),
        )

    @admin.display(description="Сводка тикета")
    def ticket_summary(self, obj):
        messages_count = obj.messages.count()
        return format_html(
            "<strong>Тикет:</strong> #{}<br>"
            "<strong>Сообщений:</strong> {}<br>"
            "<strong>Создан:</strong> {}",
            obj.id,
            messages_count,
            obj.created_at.strftime("%d.%m.%Y %H:%M") if obj.created_at else "—",
        )

    @admin.display(description="Пользователь и канал")
    def user_summary(self, obj):
        delivery_channel = get_support_delivery_channel(conversation=obj)
        channel_label = (
            "Telegram"
            if delivery_channel == SupportMessage.Source.TELEGRAM_SUPPORT_BOT
            else "Сайт"
        )
        user_label = obj.user.get_full_name() or obj.user.username or obj.user.email
        return format_html(
            "<strong>Пользователь:</strong> {}<br>"
            "<strong>Email:</strong> {}<br>"
            "<strong>Канал:</strong> {}",
            user_label,
            obj.user.email,
            channel_label,
        )

    @admin.display(description="Сводка по тикету")
    def workflow_summary(self, obj):
        delivery_channel = get_support_delivery_channel(conversation=obj)
        channel_label = (
            "Telegram"
            if delivery_channel == SupportMessage.Source.TELEGRAM_SUPPORT_BOT
            else "Сайт"
        )
        assigned_label = (
            obj.assigned_admin.get_full_name()
            or obj.assigned_admin.username
            if obj.assigned_admin
            else "Не назначен"
        )
        status_label = obj.get_status_display()
        return format_html(
            "<strong>Статус:</strong> {}<br>"
            "<strong>Канал ответа:</strong> {}<br>"
            "<strong>Ответственный:</strong> {}",
            status_label,
            channel_label,
            assigned_label,
        )

    @admin.display(description="Последнее сообщение пользователя")
    def latest_user_message_text(self, obj):
        latest_user_message = (
            obj.messages.filter(sender_type=SupportMessage.SenderType.USER)
            .order_by("-created_at", "-id")
            .first()
        )
        if latest_user_message is None:
            return "Сообщений от пользователя пока нет."

        text = (latest_user_message.text or "").strip()
        if text:
            return text

        if latest_user_message.attachments.exists():
            return "Пользователь отправил сообщение только с вложениями."

        return "Пустое сообщение."

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change, **kwargs)
        if obj and obj.assigned_admin_id and obj.assigned_admin_id != request.user.id:
            if "response_text" in form.base_fields:
                form.base_fields["response_text"].help_text = (
                    "Диалог закреплен за другим оператором. "
                    "Для ответа сначала переназначьте тикет."
                )
        return form

    @admin.action(description="Принять выбранные диалоги в работу")
    def assign_conversations_to_me(self, request, queryset):
        assigned_count = 0
        skipped_count = 0
        for conversation in queryset:
            if conversation.assigned_admin_id and conversation.assigned_admin_id != request.user.id:
                skipped_count += 1
                continue
            assign_support_conversation_to_admin(
                conversation=conversation,
                admin_user=request.user,
            )
            assigned_count += 1

        if assigned_count:
            self.message_user(
                request,
                f"В работу приняты диалоги: {assigned_count}.",
                level=messages.SUCCESS,
            )
        if skipped_count:
            self.message_user(
                request,
                f"Пропущено диалогов, уже закрепленных за другим оператором: {skipped_count}.",
                level=messages.WARNING,
            )

    @admin.action(description="Закрыть выбранные диалоги")
    def mark_conversations_closed(self, request, queryset):
        closed_count = 0
        skipped_count = 0
        for conversation in queryset:
            try:
                ensure_support_conversation_admin_access(
                    conversation=conversation,
                    admin_user=request.user,
                )
            except ValidationError:
                skipped_count += 1
                continue
            close_support_conversation(
                conversation=conversation,
                closed_by=request.user,
            )
            closed_count += 1

        if closed_count:
            self.message_user(
                request,
                f"Закрыто диалогов: {closed_count}.",
                level=messages.SUCCESS,
            )
        if skipped_count:
            self.message_user(
                request,
                f"Пропущено диалогов без доступа: {skipped_count}.",
                level=messages.WARNING,
            )

    def save_model(self, request, obj, form, change):
        reassign_to_admin = form.cleaned_data.get("reassign_to_admin")
        assign_to_me = form.cleaned_data.get("assign_to_me", False)
        response_text = (form.cleaned_data.get("response_text") or "").strip()
        response_attachments = list(form.cleaned_data.get("response_attachments") or [])
        close_after_reply = form.cleaned_data.get("close_after_reply", False)

        if reassign_to_admin is not None:
            obj.assigned_admin = reassign_to_admin
            if obj.status != SupportConversation.Status.CLOSED:
                obj.status = SupportConversation.Status.IN_PROGRESS
        elif assign_to_me and (
            obj.assigned_admin_id is None or obj.assigned_admin_id == request.user.id
        ):
            obj.assigned_admin = request.user
            if obj.status == SupportConversation.Status.NEW:
                obj.status = SupportConversation.Status.IN_PROGRESS

        super().save_model(request, obj, form, change)

        if reassign_to_admin is not None:
            self.message_user(
                request,
                (
                    f"Тикет переназначен оператору: "
                    f"{reassign_to_admin.get_full_name() or reassign_to_admin.username}."
                ),
                level=messages.SUCCESS,
            )

        if not response_text and not response_attachments:
            return

        try:
            reply_to_support_conversation(
                admin_user=request.user,
                conversation=obj,
                text=response_text,
                attachments=response_attachments,
                assign_to_admin=assign_to_me or reassign_to_admin == request.user,
                close_after_reply=close_after_reply,
            )
        except ValidationError as exc:
            self.message_user(
                request,
                str(exc.detail),
                level=messages.ERROR,
            )
            return
        self.message_user(
            request,
            "Ответ отправлен пользователю.",
            level=messages.SUCCESS,
        )


@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "sender_type", "sender_display_name", "source", "created_at")
    list_filter = ("sender_type", "source", "created_at")
    search_fields = ("conversation__user__email", "conversation__user__username", "text", "sender_display_name")
    autocomplete_fields = ("conversation", "sender_user")
    inlines = [SupportAttachmentInline]
    readonly_fields = ("sender_type", "sender_user", "sender_display_name", "source", "created_at")

    def save_model(self, request, obj, form, change):
        if change:
            super().save_model(request, obj, form, change)
            return

        created_conversation = reply_to_support_conversation(
            admin_user=request.user,
            conversation=obj.conversation,
            text=obj.text,
        )
        created_message = created_conversation.messages.order_by("-created_at", "-id").first()
        obj.pk = created_message.pk
        obj.sender_type = created_message.sender_type
        obj.sender_user = created_message.sender_user
        obj.sender_display_name = created_message.sender_display_name
        obj.source = created_message.source
        obj.created_at = created_message.created_at
