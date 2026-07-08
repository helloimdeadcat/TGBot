import logging

from config import Settings
from scrapers.arbeitsagentur import ArbeitsagenturScraper
from scrapers.base import BaseScraper
from scrapers.indeed import IndeedScraper
from scrapers.stepstone import StepStoneScraper

logger = logging.getLogger(__name__)

SCRAPER_CLASSES: dict[str, type[BaseScraper]] = {
    "arbeitsagentur": ArbeitsagenturScraper,
    "indeed": IndeedScraper,
    "stepstone": StepStoneScraper,
}


def get_scrapers(settings: Settings) -> list[BaseScraper]:
    scrapers: list[BaseScraper] = []
    for source in settings.enabled_sources:
        scraper_cls = SCRAPER_CLASSES.get(source.lower())
        if scraper_cls is None:
            logger.warning("Unknown source '%s', skipping", source)
            continue
        scrapers.append(scraper_cls(settings))
    return scrapers
