from __future__ import annotations

import smtplib
from email.message import EmailMessage

from config import settings
from core.errors import DeliveryUnavailable


def _send_email_sync(*, to_email: str, subject: str, body: str) -> None:
    if not settings.has_smtp_email:
        raise DeliveryUnavailable()

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_from_email
    message["To"] = to_email
    message.set_content(body)

    if settings.smtp_use_tls:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port) as smtp:
            if settings.smtp_username:
                smtp.login(settings.smtp_username, settings.smtp_password or "")
            smtp.send_message(message)
        return

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        if settings.smtp_use_starttls:
            smtp.starttls()
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password or "")
        smtp.send_message(message)


async def send_password_reset_email(*, to_email: str, reset_link: str) -> None:
    body = "\n".join(
        [
            "You requested a soulmatesmd.singles password reset.",
            "",
            "Open this link to choose a new password:",
            reset_link,
            "",
            f"This link expires in {settings.password_reset_ttl_hours} hour(s).",
            "If you did not request this, you can ignore this email.",
        ]
    )
    _send_email_sync(
        to_email=to_email,
        subject="Reset your soulmatesmd.singles password",
        body=body,
    )
