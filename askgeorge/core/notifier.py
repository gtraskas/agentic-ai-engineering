"""Email notifications to George via Gmail SMTP."""

from __future__ import annotations

import logging
import os
import smtplib
from email.message import EmailMessage

from askgeorge.core.config import SMTP_HOST, SMTP_PORT

logger = logging.getLogger(__name__)


class EmailNotifier:
    """Emails notifications from George's Gmail to itself via SMTP.

    Uses a Gmail App Password (GMAIL_ADDRESS / GMAIL_APP_PASSWORD env vars).
    Falls back to the application log when not configured, so nothing is ever
    written to the container's ephemeral filesystem.
    """

    def __init__(self) -> None:
        self._address: str | None = os.getenv("GMAIL_ADDRESS")
        self._app_password: str | None = os.getenv("GMAIL_APP_PASSWORD")

    @property
    def is_configured(self) -> bool:
        """Return True if Gmail SMTP credentials are present."""
        return bool(self._address and self._app_password)

    def notify(self, subject: str, body: str) -> None:
        """Send a notification email, or log it as a fallback.

        Args:
            subject: Email subject line.
            body: Plain-text email body.
        """
        if not self.is_configured:
            logger.info("Notification (email not configured): %s — %s", subject, body)
            return
        email = EmailMessage()
        email["From"] = self._address
        email["To"] = self._address
        email["Subject"] = subject
        email.set_content(body)
        try:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=15) as server:
                server.login(self._address or "", self._app_password or "")
                server.send_message(email)
        except (smtplib.SMTPException, OSError) as exc:
            logger.error("Email notification failed: %s", exc)
