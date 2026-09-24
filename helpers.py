# Single language map covering both Google Books (ISO 639-1, 2-letter) and
# Open Library (ISO 639-2/B, 3-letter) language codes.
LANGUAGE_MAP = {
    "en": "English",
    "eng": "English",
    "fr": "French",
    "fre": "French",
    "de": "German",
    "ger": "German",
    "es": "Spanish",
    "spa": "Spanish",
    "it": "Italian",
    "ita": "Italian",
    "pt": "Portuguese",
    "por": "Portuguese",
    "nl": "Dutch",
    "dut": "Dutch",
    "ru": "Russian",
    "rus": "Russian",
    "zh": "Chinese",
    "chi": "Chinese",
    "ja": "Japanese",
    "jpn": "Japanese",
    "ko": "Korean",
    "kor": "Korean",
    "ar": "Arabic",
    "ara": "Arabic",
    "hi": "Hindi",
    "hin": "Hindi",
    "bn": "Bengali",
    "ben": "Bengali",
}


def _normalize_date(date_str: str) -> str:
    """Google Books' publishedDate can be 'YYYY', 'YYYY-MM', or
    'YYYY-MM-DD'. Pad missing parts so it's a valid date string."""
    if not date_str:
        return "Not available"
    parts = date_str.split("-")
    year = parts[0]
    month = parts[1] if len(parts) > 1 else "01"
    day = parts[2] if len(parts) > 2 else "01"
    return f"{year}-{month}-{day}"


def _authors(author_list: list[str], fallback: str = "Unknown") -> str:
    """Join multiple author names into a single comma-separated string, to
    match BookInfo.author (a single string field)."""
    return fallback if not author_list else ", ".join(author_list)


def _format_results(results: list[dict], year_only: bool = False) -> str:
    """Render book result dicts into one consistent text block."""
    suffix = " (year only)" if year_only else ""
    return "\n\n".join(
        f"Result {i + 1}:\n"
        f"  Title: {r['title']}\n"
        f"  Author(s): {r['authors']}\n"
        f"  Publisher: {r['publisher']}\n"
        f"  Page count: {r['page_count'] if r['page_count'] else 'Not available'}\n"
        f"  Language: {r['language']}\n"
        f"  Published date: {r['published_date']}{suffix}"
        for i, r in enumerate(results)
    )
