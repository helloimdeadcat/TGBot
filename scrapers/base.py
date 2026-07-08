from abc import ABC, abstractmethod

from models import Vacancy


class BaseScraper(ABC):
    name: str

    @abstractmethod
    async def search(self, keywords: list[str], location: str | None) -> list[Vacancy]:
        raise NotImplementedError

    def extract_id(self, vacancy: Vacancy) -> str:
        return vacancy.external_id
