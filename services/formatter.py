from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

from config import Settings
from models import Vacancy

SOURCE_LABELS = {
    "arbeitsagentur": "Arbeitsagentur",
    "indeed": "Indeed",
    "stepstone": "StepStone",
}

TELEGRAM_MESSAGE_LIMIT = 4000


def format_digest(
    settings: Settings,
    vacancies: list[Vacancy],
    *,
    errors: list[str] | None = None,
) -> list[str]:
    tz = ZoneInfo(settings.timezone)
    today = datetime.now(tz).strftime("%d.%m.%Y")
    keywords = ", ".join(settings.search_keywords)

    if not vacancies:
        lines = [f"Новых вакансий за {today} не найдено.", "", f"Ключевые слова: {keywords}"]
        if errors:
            lines.extend(["", "Предупреждения:"])
            lines.extend(f"• {error}" for error in errors)
        return ["\n".join(lines)]

    grouped: dict[str, list[Vacancy]] = defaultdict(list)
    for vacancy in vacancies:
        grouped[vacancy.source].append(vacancy)

    header = f"Новые вакансии за {today} — {len(vacancies)} шт.\n"
    messages: list[str] = []
    current = header

    for source in settings.enabled_sources:
        items = grouped.get(source.lower(), [])
        if not items:
            continue

        label = SOURCE_LABELS.get(source.lower(), source)
        section_header = f"\n{label} ({len(items)})\n"
        if len(current) + len(section_header) > TELEGRAM_MESSAGE_LIMIT:
            messages.append(current.rstrip())
            current = section_header
        else:
            current += section_header

        for vacancy in items:
            company = vacancy.company or "Компания не указана"
            location = f", {vacancy.location}" if vacancy.location else ""
            salary = f"\n  {vacancy.salary}" if vacancy.salary else ""
            block = f"• {vacancy.title} — {company}{location}{salary}\n  {vacancy.url}\n"

            if len(current) + len(block) > TELEGRAM_MESSAGE_LIMIT:
                messages.append(current.rstrip())
                current = block
            else:
                current += block

    footer = f"\nКлючевые слова: {keywords}"
    if errors:
        footer += "\n\nПредупреждения:\n" + "\n".join(f"• {error}" for error in errors)

    if len(current) + len(footer) > TELEGRAM_MESSAGE_LIMIT:
        messages.append(current.rstrip())
        messages.append(footer.strip())
    else:
        current += footer
        messages.append(current.rstrip())

    return messages
