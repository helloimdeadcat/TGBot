import asyncio
import logging
import re
from urllib.parse import quote, urljoin

import httpx
from selectolax.parser import HTMLParser

from config import Settings
from models import Vacancy
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

BASE_URL = "https://www.stepstone.de"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


class StepStoneScraper(BaseScraper):
    name = "stepstone"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def search(self, keywords: list[str], location: str | None) -> list[Vacancy]:
        vacancies: list[Vacancy] = []
        seen_ids: set[str] = set()

        async with httpx.AsyncClient(
            timeout=30.0,
            headers={"User-Agent": USER_AGENT, "Accept-Language": "de-DE,de;q=0.9"},
            follow_redirects=True,
        ) as client:
            for keyword in keywords:
                if len(vacancies) >= self.settings.max_results_per_source:
                    break

                search_url = self._build_search_url(keyword, location)
                page = 1

                while len(vacancies) < self.settings.max_results_per_source:
                    try:
                        response = await client.get(
                            search_url,
                            params={"page": page} if page > 1 else None,
                        )
                        response.raise_for_status()
                    except httpx.HTTPError as exc:
                        logger.error("StepStone request failed for '%s': %s", keyword, exc)
                        break

                    page_vacancies = self._parse_html(response.text)
                    if not page_vacancies:
                        break

                    for vacancy in page_vacancies:
                        if vacancy.external_id in seen_ids:
                            continue
                        seen_ids.add(vacancy.external_id)
                        vacancies.append(vacancy)
                        if len(vacancies) >= self.settings.max_results_per_source:
                            break

                    if len(page_vacancies) < 10:
                        break

                    page += 1
                    await asyncio.sleep(self.settings.request_delay_seconds)

                await asyncio.sleep(self.settings.request_delay_seconds)

        logger.info("StepStone: found %d vacancies", len(vacancies))
        return vacancies

    def _build_search_url(self, keyword: str, location: str | None) -> str:
        slug = quote(keyword.strip().lower().replace(" ", "-"))
        if location:
            location_slug = quote(location.strip().lower().replace(" ", "-"))
            return f"{BASE_URL}/jobs/{slug}/in-{location_slug}"
        return f"{BASE_URL}/jobs/{slug}"

    def _parse_html(self, html: str) -> list[Vacancy]:
        tree = HTMLParser(html)
        vacancies: list[Vacancy] = []

        cards = tree.css("article[data-at='job-item'], article.responsive-content")
        if not cards:
            cards = tree.css("article")

        for card in cards:
            link = card.css_first("a[data-at='job-item-title'], a[data-testid='job-item-title'], h2 a, a[href*='/stellenangebote--']")
            if not link:
                continue

            title = link.text(strip=True)
            href = link.attributes.get("href", "")
            if not title or not href:
                continue

            url = urljoin(BASE_URL, href)
            external_id = self._extract_id(url, href)

            company_node = card.css_first("[data-at='job-item-company-name'], [data-testid='company-name'], span[data-at='job-item-company-name']")
            location_node = card.css_first("[data-at='job-item-location'], [data-testid='job-location'], span[data-at='job-item-location']")
            salary_node = card.css_first("[data-at='job-item-salary'], [data-testid='job-salary']")

            vacancies.append(
                Vacancy(
                    source=self.name,
                    external_id=external_id,
                    title=title,
                    company=company_node.text(strip=True) if company_node else None,
                    location=location_node.text(strip=True) if location_node else None,
                    url=url,
                    salary=salary_node.text(strip=True) if salary_node else None,
                )
            )

        return vacancies

    def _extract_id(self, url: str, href: str) -> str:
        match = re.search(r"--(\d+)(?:\.html)?", url) or re.search(r"/(\d+)/?$", href)
        if match:
            return match.group(1)
        return url
