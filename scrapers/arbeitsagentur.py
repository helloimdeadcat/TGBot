import asyncio
import base64
import logging
from datetime import datetime

import httpx

from config import Settings
from models import Vacancy
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

API_URL = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v6/jobs"
API_KEY = "jobboerse-jobsuche"


class ArbeitsagenturScraper(BaseScraper):
    name = "arbeitsagentur"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def search(self, keywords: list[str], location: str | None) -> list[Vacancy]:
        query = " ".join(keywords)
        vacancies: list[Vacancy] = []
        page = 1
        size = min(self.settings.max_results_per_source, 100)

        async with httpx.AsyncClient(timeout=30.0) as client:
            while len(vacancies) < self.settings.max_results_per_source:
                params: dict[str, str | int] = {
                    "was": query,
                    "page": page,
                    "size": size,
                }
                if location:
                    params["wo"] = location
                    params["umkreis"] = 50

                response = await client.get(
                    API_URL,
                    params=params,
                    headers={
                        "X-API-Key": API_KEY,
                        "Accept": "application/json",
                        "User-Agent": "JobSearchBot/1.0",
                    },
                )
                response.raise_for_status()
                data = response.json()

                items = data.get("stellenangebote") or []
                if not items:
                    break

                for item in items:
                    refnr = item.get("referenznummer") or item.get("refnr")
                    if not refnr:
                        continue

                    title = item.get("titel") or item.get("beruf") or "Без названия"
                    company = item.get("arbeitgeber")
                    arbeitsort = item.get("arbeitsort")
                    if isinstance(arbeitsort, dict):
                        job_location = arbeitsort.get("ort")
                    else:
                        job_location = arbeitsort
                    url = self._build_url(refnr)

                    vacancies.append(
                        Vacancy(
                            source=self.name,
                            external_id=str(refnr),
                            title=title,
                            company=company,
                            location=job_location,
                            url=url,
                            salary=None,
                            posted_at=self._parse_date(item.get("aktuelleVeroeffentlichungsdatum")),
                        )
                    )

                    if len(vacancies) >= self.settings.max_results_per_source:
                        break

                max_pages = data.get("maxErgebnisse", 0)
                if page * size >= max_pages or len(items) < size:
                    break

                page += 1
                await asyncio.sleep(self.settings.request_delay_seconds)

        logger.info("Arbeitsagentur: found %d vacancies", len(vacancies))
        return vacancies

    def _build_url(self, refnr: str) -> str:
        encoded = base64.b64encode(refnr.encode()).decode()
        return (
            "https://www.arbeitsagentur.de/jobsuche/jobdetail/"
            f"{encoded}"
        )

    def _parse_date(self, value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
