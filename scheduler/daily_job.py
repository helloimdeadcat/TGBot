import logging

from telegram.ext import Application

from bot.handlers import daily_digest_job

logger = logging.getLogger(__name__)


def schedule_daily_digest(scheduler, application: Application, hour: int, minute: int, timezone) -> None:
    scheduler.add_job(
        daily_digest_job,
        trigger="cron",
        hour=hour,
        minute=minute,
        timezone=timezone,
        args=[application],
        id="daily_digest",
        replace_existing=True,
    )
    logger.info("Daily digest scheduled at %02d:%02d %s", hour, minute, timezone)
