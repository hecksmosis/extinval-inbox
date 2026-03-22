from __future__ import annotations

import email
import imaplib
import json
from email.policy import default
from pathlib import Path

from app.core.config import settings
from app.models.entities import AttachmentPayload, EmailMessage


class InboxConnector:
    def __init__(self) -> None:
        self.checkpoint_path = settings.checkpoint_path

    def load_checkpoint(self) -> dict:
        if self.checkpoint_path.exists():
            return json.loads(self.checkpoint_path.read_text())
        return {"last_uid": None}

    def save_checkpoint(self, last_uid: str) -> None:
        self.checkpoint_path.write_text(json.dumps({"last_uid": last_uid}, indent=2))

    def fetch_new_messages(self) -> list[EmailMessage]:
        if settings.email_provider != "imap":
            return []
        checkpoint = self.load_checkpoint()
        connection = imaplib.IMAP4_SSL(settings.email_host, settings.email_port)
        connection.login(settings.email_username, settings.email_password)
        connection.select("INBOX")
        criteria = f"UID {int(checkpoint['last_uid']) + 1}:*" if checkpoint["last_uid"] else "ALL"
        _, data = connection.uid("search", None, criteria)
        uids = data[0].split()
        messages: list[EmailMessage] = []
        last_uid = checkpoint["last_uid"]
        for uid in uids:
            _, raw_data = connection.uid("fetch", uid, "(RFC822)")
            raw_bytes = raw_data[0][1]
            raw_path = settings.audit_dir / f"{uid.decode()}.eml"
            raw_path.write_bytes(raw_bytes)
            messages.append(self._parse_email(raw_bytes, raw_path))
            last_uid = uid.decode()
        connection.logout()
        if last_uid:
            self.save_checkpoint(last_uid)
        return messages

    def _parse_email(self, raw_bytes: bytes, raw_path: Path) -> EmailMessage:
        message = email.message_from_bytes(raw_bytes, policy=default)
        body_text = ""
        attachments: list[AttachmentPayload] = []
        for part in message.walk():
            content_disposition = part.get_content_disposition()
            if part.get_content_type() == "text/plain" and content_disposition != "attachment":
                body_text += part.get_content()
            elif content_disposition == "attachment":
                filename = part.get_filename() or "attachment.bin"
                attachment_path = settings.audit_dir / filename
                payload = part.get_payload(decode=True)
                attachment_path.write_bytes(payload)
                attachments.append(
                    AttachmentPayload(
                        filename=filename,
                        content_type=part.get_content_type(),
                        path=attachment_path,
                    )
                )
        return EmailMessage(
            message_id=message.get("Message-ID", raw_path.stem),
            subject=message.get("Subject", ""),
            sender=message.get("From", ""),
            received_at=message.get("Date", ""),
            body_text=body_text,
            attachments=attachments,
            raw_path=raw_path,
        )
