"""Custom notification tool for the stock picker agent.

Emails the decision to the user via Gmail SMTP when ``GMAIL_ADDRESS``
and ``GMAIL_APP_PASSWORD`` are set (an App Password, not the account
password). Without them it appends the message to
``output/notifications.log`` instead, so the crew runs without any
email configuration.
"""

import os
import smtplib
from datetime import UTC, datetime
from email.message import EmailMessage
from pathlib import Path

from crewai.tools import tool

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465
LOG_FILE = Path("output") / "notifications.log"


def _send_email(address: str, app_password: str, message: str) -> str:
    """Email the message from the configured Gmail address to itself."""
    email = EmailMessage()
    email["From"] = address
    email["To"] = address
    email["Subject"] = "Stock picker decision"
    email.set_content(message)
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=15) as server:
        server.login(address, app_password)
        server.send_message(email)
    return "Notification emailed to the user."


def _log_locally(message: str) -> str:
    """Append the message to the local notifications log."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(tz=UTC).isoformat(timespec="seconds")
    with LOG_FILE.open("a", encoding="utf-8") as log:
        log.write(f"{timestamp} {message}\n")
    return f"Email not configured; notification written to {LOG_FILE}."


@tool("Send Notification")
def send_notification(message: str) -> str:
    """Use this tool to send a notification to the user.

    Args:
        message: The message to be sent as a notification to the user.

    Returns:
        A string indicating how the notification was delivered.
    """
    address = os.getenv("GMAIL_ADDRESS")
    app_password = os.getenv("GMAIL_APP_PASSWORD")
    try:
        if address and app_password:
            return _send_email(address, app_password, message)
        return _log_locally(message)
    except (smtplib.SMTPException, OSError) as exc:
        return f"Notification failed ({exc}); message was: {message}"
