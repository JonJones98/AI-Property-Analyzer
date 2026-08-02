"""Alerting service (email / SMS / push).

Roadmap (see README): a persisted subscription model (per-user channel
preferences), a rules engine that reacts to ingestion events (new listing,
price reduction, high Homestead Score, back-on-market, status change), and
provider adapters for SendGrid (email), Twilio (SMS), and a push provider.

Not implemented yet: no persisted alert-preferences table exists, and no
notification provider credentials are configured. The route wiring below is
final; wire in a real implementation here once those exist.
"""

from app.core.config import Settings


async def send_test_alert(settings: Settings, channel: str) -> dict:
    if not settings.notifications_enabled:
        raise NotImplementedError(
            "Set NOTIFICATIONS_ENABLED=true and configure a provider "
            "(SendGrid/Twilio/push) to enable alerts."
        )
    raise NotImplementedError(f"'{channel}' alert delivery is not yet implemented.")
