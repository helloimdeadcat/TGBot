import logging

from telegram import Bot

from config import Settings
from services.formatter import format_digest
from services.orchestrator import JobSearchOrchestrator
from storage.database import VacancyDatabase

logger = logging.getLogger(__name__)


async def send_digest(
    bot: Bot,
    settings: Settings,
    database: VacancyDatabase,
    *,
    chat_id: str | int | None = None,
    manual: bool = False,
) -> int:
    orchestrator = JobSearchOrchestrator(settings, database)
    vacancies, errors = await orchestrator.run_search()
    messages = format_digest(settings, vacancies, errors=errors)
    target_chat = chat_id or settings.telegram_chat_id

    for message in messages:
        await bot.send_message(
            chat_id=target_chat,
            text=message,
            disable_web_page_preview=True,
        )

    orchestrator.mark_sent(vacancies)
    logger.info("Digest sent: %d new vacancies (manual=%s)", len(vacancies), manual)
    return len(vacancies)
