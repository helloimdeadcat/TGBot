from dataclasses import dataclass
from datetime import datetime


@dataclass
class Vacancy:
    source: str
    external_id: str
    title: str
    company: str | None
    location: str | None
    url: str
    salary: str | None = None
    posted_at: datetime | None = None
