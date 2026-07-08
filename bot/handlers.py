import logging

from telegram import Update
from telegram.ext import Application, ContextTypes

from bot.sender import send_digest
from config import Settings
from storage.database import VacancyDatabase

logger = logging.getLogger(__name__)


def _is_authorized(update: Update, settings: Settings) -> bool:
    if update.effective_chat is None:
        return False
    return str(update.effective_chat.id) == settings.telegram_chat_id


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not _is_authorized(update, settings):
        return

    location = settings.search_location or "вся Германия"
    sources = ", ".join(settings.enabled_sources)
    keywords = ", ".join(settings.search_keywords)

    await update.message.reply_text(
        "Бот поиска работы запущен.\n\n"
        f"Ключевые слова: {keywords}\n"
        f"Локация: {location}\n"
        f"Источники: {sources}\n"
        f"Ежедневная рассылка: {settings.daily_digest_hour:02d}:"
        f"{settings.daily_digest_minute:02d} ({settings.timezone})\n\n"
        "Команды:\n"
        "/search — поиск прямо сейчас\n"
        "/status — статус базы и последней рассылки"
    )


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    database: VacancyDatabase = context.bot_data["database"]
    if not _is_authorized(update, settings):
        return

    await update.message.reply_text("Ищу новые вакансии...")
    await send_digest(
        context.bot,
        settings,
        database,
        chat_id=update.effective_chat.id,
        manual=True,
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    database: VacancyDatabase = context.bot_data["database"]
    if not _is_authorized(update, settings):
        return

    last_digest = database.get_state("last_digest_at") or "ещё не было"
    await update.message.reply_text(
        f"Вакансий в базе: {database.count_seen()}\n"
        f"Последняя рассылка: {last_digest}\n"
        f"Источники: {', '.join(settings.enabled_sources)}"
    )


async def daily_digest_job(application: Application) -> None:
    settings: Settings = application.bot_data["settings"]
    database: VacancyDatabase = application.bot_data["database"]
    await send_digest(application.bot, settings, database, manual=False)
