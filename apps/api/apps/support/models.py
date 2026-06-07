from django.conf import settings
from django.db import models


class SupportConversation(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Новый"
        IN_PROGRESS = "in_progress", "В работе"
        CLOSED = "closed", "Закрыт"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="support_conversation",
        verbose_name="Пользователь",
    )
    status = models.CharField(
        "Статус",
        max_length=24,
        choices=Status.choices,
        default=Status.NEW,
    )
    assigned_admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="assigned_support_conversations",
        null=True,
        blank=True,
        verbose_name="Ответственный администратор",
    )
    last_message_at = models.DateTimeField("Последнее сообщение", null=True, blank=True)
    last_message_preview = models.CharField("Превью последнего сообщения", max_length=255, blank=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)
    closed_at = models.DateTimeField("Закрыто", null=True, blank=True)

    class Meta:
        ordering = ("-last_message_at", "-updated_at", "-id")
        verbose_name = "Диалог поддержки"
        verbose_name_plural = "Диалоги поддержки"

    def __str__(self) -> str:
        return f"SupportConversation<{self.user_id}:{self.status}>"


def support_attachment_upload_to(instance, filename: str) -> str:
    return f"support/{instance.message.conversation.user_id}/{instance.message_id}/{filename}"


class SupportMessage(models.Model):
    class SenderType(models.TextChoices):
        USER = "user", "Пользователь"
        ADMIN = "admin", "Администратор"

    class Source(models.TextChoices):
        WEB = "web", "Web"
        TELEGRAM_SUPPORT_BOT = "telegram_support_bot", "Telegram support bot"
        ADMIN = "admin", "Admin"

    conversation = models.ForeignKey(
        SupportConversation,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="Диалог",
    )
    sender_type = models.CharField(
        "Тип отправителя",
        max_length=16,
        choices=SenderType.choices,
    )
    sender_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="support_messages",
        null=True,
        blank=True,
        verbose_name="Пользователь системы",
    )
    sender_display_name = models.CharField("Имя отправителя", max_length=255)
    source = models.CharField("Источник", max_length=32, choices=Source.choices)
    text = models.TextField("Текст", blank=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        ordering = ("created_at", "id")
        verbose_name = "Сообщение поддержки"
        verbose_name_plural = "Сообщения поддержки"

    def __str__(self) -> str:
        return f"SupportMessage<{self.conversation_id}:{self.sender_type}>"


class SupportAttachment(models.Model):
    message = models.ForeignKey(
        SupportMessage,
        on_delete=models.CASCADE,
        related_name="attachments",
        verbose_name="Сообщение",
    )
    file = models.FileField("Файл", upload_to=support_attachment_upload_to)
    file_name = models.CharField("Имя файла", max_length=255)
    content_type = models.CharField("MIME-тип", max_length=255, blank=True)
    size_bytes = models.PositiveIntegerField("Размер", default=0)
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        ordering = ("created_at", "id")
        verbose_name = "Вложение поддержки"
        verbose_name_plural = "Вложения поддержки"

    def __str__(self) -> str:
        return f"SupportAttachment<{self.message_id}:{self.file_name}>"

