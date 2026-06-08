from __future__ import annotations

from rest_framework.exceptions import ValidationError

from apps.support.services import IncomingSupportAttachment, create_support_message_from_telegram

from .bot_client import TelegramBotClient
from .services import confirm_telegram_link, get_active_telegram_link_by_telegram_user_id


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

    if message_text.startswith("/start"):
        _send_start_hint(client=client, chat_id=chat_id)
        return

    telegram_link = get_active_telegram_link_by_telegram_user_id(telegram_user_id=telegram_user_id)
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
    )


def _send_start_hint(*, client: TelegramBotClient, chat_id: int) -> None:
    client.send_message(
        chat_id=chat_id,
        text=(
            "Этот бот принимает сообщения в поддержку после привязки Telegram "
            "в личном кабинете INFINDA."
        ),
    )


def _send_unlinked_hint(*, client: TelegramBotClient, chat_id: int) -> None:
    client.send_message(
        chat_id=chat_id,
        text=(
            "Telegram пока не привязан к аккаунту INFINDA. "
            "Откройте личный кабинет и выполните привязку в разделе Telegram."
        ),
    )


def _send_empty_message_hint(*, client: TelegramBotClient, chat_id: int) -> None:
    client.send_message(
        chat_id=chat_id,
        text="Поддерживаются текстовые сообщения, фото и документы.",
    )


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
    )


def _extract_message_text(*, message: dict) -> str:
    raw_text = message.get("text") or message.get("caption") or ""
    return raw_text.strip()


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
