from models import Vacancy


def matches_keywords(vacancy: Vacancy, keywords: list[str]) -> bool:
    if not keywords:
        return True

    haystack = " ".join(
        part for part in [vacancy.title, vacancy.company or ""] if part
    ).lower()

    return any(keyword.lower() in haystack for keyword in keywords)
