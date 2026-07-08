import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from config import Settings
from models import Vacancy
from scrapers.registry import get_scrapers
from services.keyword_filter import matches_keywords
from storage.database import VacancyDatabase

logger = logging.getLogger(__name__)


class JobSearchOrchestrator:
    def __init__(self, settings: Settings, database: VacancyDatabase) -> None:
        self.settings = settings
        self.database = database

    async def run_search(self) -> tuple[list[Vacancy], list[str]]:
        scrapers = get_scrapers(self.settings)
        new_vacancies: list[Vacancy] = []
        errors: list[str] = []

        for scraper in scrapers:
            try:
                found = await scraper.search(
                    self.settings.search_keywords,
                    self.settings.search_location,
                )
                for vacancy in found:
                    if not matches_keywords(vacancy, self.settings.search_keywords):
                        continue
                    if self.database.is_seen(vacancy.source, vacancy.external_id):
                        continue
                    new_vacancies.append(vacancy)
                    self.database.mark_seen(vacancy, sent=False)
            except Exception as exc:
                message = f"{scraper.name}: {exc}"
                logger.exception("Scraper failed: %s", scraper.name)
                errors.append(message)

        return new_vacancies, errors

    def mark_sent(self, vacancies: list[Vacancy]) -> None:
        for vacancy in vacancies:
            self.database.mark_seen(vacancy, sent=True)
        self.database.set_state(
            "last_digest_at",
            datetime.now(ZoneInfo(self.settings.timezone)).isoformat(),
        )
