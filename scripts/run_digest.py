"""One-shot digest runner for GitHub Actions (no polling bot)."""
import asyncio
import logging
import sys

from telegram import Bot

from bot.sender import send_digest
from config import get_settings
from storage.database import VacancyDatabase

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def main() -> None:
    settings = get_settings()
    database = VacancyDatabase(settings.database_path)
    bot = Bot(token=settings.telegram_bot_token)

    count = await send_digest(bot, settings, database, manual=False)
    logger.info("Finished: %d new vacancies sent", count)


if __name__ == "__main__":
    asyncio.run(main())
