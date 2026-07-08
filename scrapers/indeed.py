import asyncio
import json
import logging
import re
from datetime import datetime
from urllib.parse import urljoin

import httpx
from selectolax.parser import HTMLParser

from config import Settings
from models import Vacancy
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

BASE_URL = "https://de.indeed.com"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


class IndeedScraper(BaseScraper):
    name = "indeed"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def search(self, keywords: list[str], location: str | None) -> list[Vacancy]:
        query = " ".join(keywords)
        vacancies: list[Vacancy] = []
        start = 0

        async with httpx.AsyncClient(
            timeout=30.0,
            headers={"User-Agent": USER_AGENT, "Accept-Language": "de-DE,de;q=0.9"},
            follow_redirects=True,
        ) as client:
            while len(vacancies) < self.settings.max_results_per_source:
                params = {"q": query, "start": start}
                if location:
                    params["l"] = location

                try:
                    response = await client.get(f"{BASE_URL}/jobs", params=params)
                    response.raise_for_status()
                except httpx.HTTPError as exc:
                    logger.error("Indeed request failed: %s", exc)
                    break

                page_vacancies = self._parse_response(response.text)
                if not page_vacancies:
                    break

                vacancies.extend(page_vacancies)
                if len(page_vacancies) < 10:
                    break

                start += 10
                await asyncio.sleep(self.settings.request_delay_seconds)

        vacancies = vacancies[: self.settings.max_results_per_source]
        logger.info("Indeed: found %d vacancies", len(vacancies))
        return vacancies

    def _parse_response(self, html: str) -> list[Vacancy]:
        embedded = self._parse_embedded_json(html)
        if embedded:
            return embedded
        return self._parse_html(html)

    def _parse_embedded_json(self, html: str) -> list[Vacancy]:
        match = re.search(
            r'window\.mosaic\.providerData\["mosaic-provider-jobcards"\]\s*=\s*(\{.*?\});',
            html,
            re.DOTALL,
        )
        if not match:
            match = re.search(r'id="mosaic-data"[^>]*>(\{.*?\})</script>', html, re.DOTALL)
        if not match:
            return []

        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError:
            return []

        results = (
            data.get("metaData", {})
            .get("mosaicProviderJobCardsModel", {})
            .get("results", [])
        )
        vacancies: list[Vacancy] = []
        for item in results:
            job_key = item.get("jobkey") or item.get("jobKey")
            title = item.get("title") or item.get("displayTitle")
            if not job_key or not title:
                continue

            company = item.get("company") or item.get("companyName")
            location = item.get("formattedLocation") or item.get("jobLocationCity")
            salary = item.get("salarySnippet", {}).get("text") if isinstance(item.get("salarySnippet"), dict) else item.get("salarySnippet")
            url = item.get("link") or f"{BASE_URL}/viewjob?jk={job_key}"
            if url.startswith("/"):
                url = urljoin(BASE_URL, url)

            vacancies.append(
                Vacancy(
                    source=self.name,
                    external_id=str(job_key),
                    title=title,
                    company=company,
                    location=location,
                    url=url,
                    salary=salary,
                    posted_at=self._parse_relative_date(item.get("pubDate") or item.get("formattedRelativeTime")),
                )
            )
        return vacancies

    def _parse_html(self, html: str) -> list[Vacancy]:
        tree = HTMLParser(html)
        vacancies: list[Vacancy] = []

        for card in tree.css("div.job_seen_beacon, div.cardOutline, li.css-5lfss0"):
            link = card.css_first("a[data-jk], a.jcs-JobTitle")
            if not link:
                continue

            job_key = link.attributes.get("data-jk")
            title = link.text(strip=True)
            if not job_key or not title:
                continue

            company_node = card.css_first('[data-testid="company-name"], span.companyName')
            location_node = card.css_first('[data-testid="text-location"], div.companyLocation')
            salary_node = card.css_first('[data-testid="attribute_snippet_testid"], div.salary-snippet')

            href = link.attributes.get("href", "")
            url = urljoin(BASE_URL, href) if href.startswith("/") else href

            vacancies.append(
                Vacancy(
                    source=self.name,
                    external_id=str(job_key),
                    title=title,
                    company=company_node.text(strip=True) if company_node else None,
                    location=location_node.text(strip=True) if location_node else None,
                    url=url or f"{BASE_URL}/viewjob?jk={job_key}",
                    salary=salary_node.text(strip=True) if salary_node else None,
                )
            )

        return vacancies

    def _parse_relative_date(self, value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
