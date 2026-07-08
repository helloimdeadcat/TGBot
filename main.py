import logging
import sys
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram.ext import Application, CommandHandler

from bot.handlers import search_command, start_command, status_command
from config import get_settings
from scheduler.daily_job import schedule_daily_digest
from storage.database import VacancyDatabase

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


async def post_init(application: Application) -> None:
    settings = application.bot_data["settings"]
    tz = ZoneInfo(settings.timezone)
    scheduler = AsyncIOScheduler(timezone=tz)
    schedule_daily_digest(
        scheduler,
        application,
        settings.daily_digest_hour,
        settings.daily_digest_minute,
        tz,
    )
    scheduler.start()
    application.bot_data["scheduler"] = scheduler


async def post_shutdown(application: Application) -> None:
    scheduler = application.bot_data.get("scheduler")
    if scheduler is not None:
        scheduler.shutdown(wait=False)


def main() -> None:
    settings = get_settings()
    database = VacancyDatabase(settings.database_path)

    application = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )
    application.bot_data["settings"] = settings
    application.bot_data["database"] = database

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("search", search_command))
    application.add_handler(CommandHandler("status", status_command))

    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
