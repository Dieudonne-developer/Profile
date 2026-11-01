from __future__ import annotations

import smtplib
from email.message import EmailMessage
from types import SimpleNamespace

import httpx

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
    to_addr = notify_address(owner)
    return {
        "to": to_addr,
        "smtp_ready": bool(settings.mail_password() and to_addr),
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
    password = settings.mail_password()
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

    host = settings.smtp_host
    port = settings.smtp_port or 587
    server = smtplib.SMTP(host, port, timeout=8)
    with server:
        server.starttls()
        server.login(smtp_user, password)
        server.send_message(message)


def _send_https(item: ContactMessage, to_addr: str) -> None:
    subject, text, _html = _message_bodies(item)
    payload = {
        "name": item.sender_name,
        "email": item.sender_email,
        "_replyto": item.sender_email,
        "_subject": f"[Portfolio] {subject}",
        "message": text,
        "_template": "box",
        "_captcha": "false",
    }
    headers = {
        "Accept": "application/json",
        "User-Agent": "PortfolioContact/1.0",
    }
    with httpx.Client(timeout=15.0, follow_redirects=True, headers=headers) as client:
        response = client.post(f"https://formsubmit.co/ajax/{to_addr}", json=payload)
        if response.status_code >= 400:
            response = client.post(
                f"https://formsubmit.co/{to_addr}",
                data=payload,
            )
    if response.status_code >= 400:
        raise RuntimeError(f"HTTPS mail HTTP {response.status_code}: {response.text[:240]}")
    try:
        body = response.json()
    except ValueError:
        return
    blob = str(body).lower()
    if "error" in blob and "success" not in blob:
        raise RuntimeError(body.get("message") or "HTTPS mail failed")


def send_contact_email(owner: User, item: ContactMessage) -> bool:
    to_addr = notify_address(owner)
    if not to_addr:
        print("gmail notify skipped: no NOTIFY_EMAIL")
        return False

    errors: list[str] = []
    try:
        _send_https(item, to_addr)
        return True
    except Exception as exc:
        errors.append(f"https: {exc}")
        print(f"gmail https failed: {exc}")

    if get_settings().mail_password():
        try:
            _send_smtp(item, to_addr)
            return True
        except Exception as exc:
            errors.append(f"smtp: {exc}")
            print(f"gmail smtp failed: {exc}")

    raise RuntimeError("; ".join(errors) or "Gmail send failed")


def test_payload(owner: User) -> ContactMessage:
    return SimpleNamespace(
        sender_name="Portfolio mail test",
        sender_email=owner.email,
        subject="Gmail notification test",
        body="If you received this, contact-form alerts to Gmail are working.",
    )
