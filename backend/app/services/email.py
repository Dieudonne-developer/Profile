from __future__ import annotations

import json
import smtplib
from email.message import EmailMessage
from types import SimpleNamespace
from urllib.error import URLError
from urllib.request import Request, urlopen

from app.core.config import get_settings
from app.models import ContactMessage, User


def notify_address(owner: User | None = None) -> str:
    settings = get_settings()
    return (
        (settings.notify_email or "").strip()
        or (owner.email if owner else "")
        or settings.smtp_username
        or ""
    ).strip()


def mail_status(owner: User | None = None) -> dict:
    settings = get_settings()
    password = (settings.smtp_password or "").replace(" ", "").strip()
    to_addr = notify_address(owner)
    return {
        "to": to_addr,
        "smtp_ready": bool(password and to_addr),
        "https_fallback": bool(to_addr),
        "configured": bool(to_addr),
    }


def _inbox_url() -> str:
    settings = get_settings()
    base = (settings.public_app_url or "").rstrip("/")
    if not base or "localhost" in base or "127.0.0.1" in base:
        base = "https://profile-zzeb.vercel.app"
    return f"{base}/app/messages"


def _message_bodies(item: ContactMessage) -> tuple[str, str, str]:
    subject = item.subject or "Portfolio contact"
    inbox = _inbox_url()
    text = (
        f"New message on your portfolio\n\n"
        f"From: {item.sender_name} <{item.sender_email}>\n"
        f"Subject: {subject}\n\n"
        f"{item.body}\n\n"
        f"Open inbox: {inbox}\n"
    )
    html = (
        "<p>New message on your portfolio</p>"
        f"<p><strong>From:</strong> {item.sender_name} &lt;{item.sender_email}&gt;<br>"
        f"<strong>Subject:</strong> {subject}</p>"
        f'<p style="white-space:pre-wrap">{item.body}</p>'
        f'<p><a href="{inbox}">Open admin inbox</a></p>'
    )
    return subject, text, html


def _send_smtp(item: ContactMessage, to_addr: str) -> None:
    settings = get_settings()
    password = (settings.smtp_password or "").replace(" ", "").strip()
    smtp_user = (settings.smtp_username or to_addr).strip()
    if not password or not smtp_user:
        raise RuntimeError("SMTP_PASSWORD is not set on the API")

    subject, text, html = _message_bodies(item)
    message = EmailMessage()
    message["Subject"] = f"[Portfolio] {subject}"
    message["From"] = settings.smtp_from or smtp_user
    message["To"] = to_addr
    message["Reply-To"] = item.sender_email
    message.set_content(text)
    message.add_alternative(html, subtype="html")

    errors: list[str] = []
    attempts = (
        (settings.smtp_host, 465, True),
        (settings.smtp_host, settings.smtp_port or 587, False),
    )
    for host, port, use_ssl in attempts:
        try:
            server = (
                smtplib.SMTP_SSL(host, port, timeout=15)
                if use_ssl
                else smtplib.SMTP(host, port, timeout=15)
            )
            with server:
                if not use_ssl:
                    server.starttls()
                server.login(smtp_user, password)
                server.send_message(message)
            return
        except Exception as exc:
            errors.append(f"{host}:{port} {exc}")
    raise RuntimeError("; ".join(errors))


def _send_https(item: ContactMessage, to_addr: str) -> None:
    subject, text, _html = _message_bodies(item)
    payload = json.dumps(
        {
            "name": item.sender_name,
            "email": item.sender_email,
            "_replyto": item.sender_email,
            "_subject": f"[Portfolio] {subject}",
            "message": text,
            "_template": "box",
            "_captcha": "false",
        }
    ).encode("utf-8")
    request = Request(
        f"https://formsubmit.co/ajax/{to_addr}",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=20) as response:
            body = json.loads(response.read().decode("utf-8") or "{}")
    except URLError as exc:
        raise RuntimeError(f"HTTPS mail failed: {exc}") from exc
    if str(body.get("success")).lower() not in {"true", "1"} and body.get("message"):
        # FormSubmit still emails after the first confirmation even when success is true.
        if "error" in str(body).lower():
            raise RuntimeError(body.get("message") or "HTTPS mail failed")


def send_contact_email(owner: User, item: ContactMessage) -> bool:
    to_addr = notify_address(owner)
    if not to_addr:
        print("gmail notify skipped: no NOTIFY_EMAIL")
        return False

    smtp_error = None
    try:
        _send_smtp(item, to_addr)
        return True
    except Exception as exc:
        smtp_error = exc
        print(f"gmail smtp failed: {exc}")

    try:
        _send_https(item, to_addr)
        return True
    except Exception as exc:
        print(f"gmail https failed: {exc}")
        raise RuntimeError(f"{smtp_error}; {exc}") from exc


def test_payload(owner: User) -> ContactMessage:
    return SimpleNamespace(
        sender_name="Portfolio mail test",
        sender_email=owner.email,
        subject="Gmail notification test",
        body="If you received this, contact-form alerts to Gmail are working.",
    )
