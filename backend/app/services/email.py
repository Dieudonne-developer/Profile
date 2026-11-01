from __future__ import annotations

import smtplib
from email.message import EmailMessage

from app.core.config import get_settings
from app.models import ContactMessage, User


def send_contact_email(owner: User, item: ContactMessage) -> bool:
    settings = get_settings()
    password = (settings.smtp_password or "").replace(" ", "").strip()
    smtp_user = (settings.smtp_username or settings.notify_email or owner.email or "").strip()
    to_addr = (settings.notify_email or owner.email or "").strip()
    if not password or not smtp_user or not to_addr:
        print("gmail notify skipped: set SMTP_PASSWORD (Gmail app password) on the API")
        return False

    inbox = f"{settings.public_app_url.rstrip('/')}/app/messages"
    subject = item.subject or "Portfolio contact"
    text = (
        f"New message on your portfolio\n\n"
        f"From: {item.sender_name} <{item.sender_email}>\n"
        f"Subject: {subject}\n\n"
        f"{item.body}\n\n"
        f"Open inbox: {inbox}\n"
    )
    html = f"""
    <p>New message on your portfolio</p>
    <p><strong>From:</strong> {item.sender_name} &lt;{item.sender_email}&gt;<br>
    <strong>Subject:</strong> {subject}</p>
    <p style="white-space:pre-wrap">{item.body}</p>
    <p><a href="{inbox}">Open admin inbox</a></p>
    """

    message = EmailMessage()
    message["Subject"] = f"[Portfolio] {subject}"
    message["From"] = settings.smtp_from or smtp_user
    message["To"] = to_addr
    message["Reply-To"] = item.sender_email
    message.set_content(text)
    message.add_alternative(html, subtype="html")

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
        server.starttls()
        server.login(smtp_user, password)
        server.send_message(message)
    return True
