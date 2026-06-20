"""
Notification channel architecture.
In-app and email implemented. WhatsApp/Discord/Slack are placeholders.
"""
import logging
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger("creatoros.notifications.channels")

# Future channel identifiers
CHANNEL_IN_APP = "in_app"
CHANNEL_EMAIL = "email"
CHANNEL_WHATSAPP = "whatsapp"  # placeholder
CHANNEL_DISCORD = "discord"    # placeholder
CHANNEL_SLACK = "slack"        # placeholder

AVAILABLE_CHANNELS = [CHANNEL_IN_APP, CHANNEL_EMAIL]
FUTURE_CHANNELS = [CHANNEL_WHATSAPP, CHANNEL_DISCORD, CHANNEL_SLACK]


class NotificationChannel(ABC):
    @abstractmethod
    def send(self, user, notification: dict) -> bool:
        ...


class InAppChannel(NotificationChannel):
    """Handled by persisting Notification rows — no external dispatch."""
    def send(self, user, notification: dict) -> bool:
        return True


class EmailChannel(NotificationChannel):
    def send(self, user, notification: dict) -> bool:
        from app.notifications.email_service import send_reminder_email
        return send_reminder_email(
            to_email=user.email,
            subject=notification.get("emailSubject", notification.get("title", "CreatorOS reminder")),
            body=notification.get("emailBody", notification.get("body", "")),
            action_href=notification.get("actionHref"),
        )


class PlaceholderChannel(NotificationChannel):
    """Stub for future integrations."""
    def __init__(self, name: str):
        self.name = name

    def send(self, user, notification: dict) -> bool:
        logger.info(f"[{self.name}] placeholder — not configured")
        return False


def get_channel(channel_id: str) -> Optional[NotificationChannel]:
    channels = {
        CHANNEL_IN_APP: InAppChannel(),
        CHANNEL_EMAIL: EmailChannel(),
        CHANNEL_WHATSAPP: PlaceholderChannel("WhatsApp"),
        CHANNEL_DISCORD: PlaceholderChannel("Discord"),
        CHANNEL_SLACK: PlaceholderChannel("Slack"),
    }
    return channels.get(channel_id)
