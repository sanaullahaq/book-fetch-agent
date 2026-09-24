import os
import time

import httpx
from langchain_core.tools import tool
from tavily import TavilyClient

from helpers import LANGUAGE_MAP, _authors, _format_results, _normalize_date

GOOGLE_BOOKS_API_URL = "https://www.googleapis.com/books/v1/volumes"


@tool
def search_book(title: str) -> str:
    """Search for a book by title using the Google Books API and return
    metadata (title, authors, publisher, page count, language, published
    date) for the top matching results."""
    params = {"q": f"intitle:{title}", "maxResults": 5}
    api_key = os.getenv("GOOGLE_BOOKS_API_KEY")
    if api_key:
        params["key"] = api_key

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = httpx.get(GOOGLE_BOOKS_API_URL, params=params, timeout=10.0)
            if response.status_code in (429, 500, 502, 503, 504):
                if attempt < max_retries - 1:
                    retry_after = response.headers.get("Retry-After")
                    wait = float(retry_after) if retry_after else 2**attempt
                    time.sleep(wait)
                    continue
                return (
                    "Google Books API is rate-limited/unavailable after "
                    "3 attempts; use search_book_openlibrary instead."
                )
            response.raise_for_status()
            data = response.json()
            break
        except httpx.HTTPError as e:
            return f"Error calling Google Books API: {e}"
    else:
        return (
            "Google Books API is rate-limited/unavailable; "
            "use search_book_openlibrary instead."
        )

    items = data.get("items")
    if not items:
        return f"No books found matching the title '{title}'."

    results = []
    for item in items:
        vi = item.get("volumeInfo", {})
        lang_code = vi.get("language", "")
        results.append(
            {
                "title": vi.get("title", "Unknown"),
                "authors": _authors(vi.get("authors", [])),
                "publisher": vi.get("publisher", "Unknown"),
                "page_count": vi.get("pageCount"),
                "language": LANGUAGE_MAP.get(lang_code, lang_code or "Unknown"),
                "published_date": _normalize_date(vi.get("publishedDate", "")),
            }
        )

    return _format_results(results)


OPEN_LIBRARY_SEARCH_URL = "https://openlibrary.org/search.json"


@tool
def search_book_openlibrary(title: str) -> str:
    """Fallback book search using the Open Library API. Note:
    published_date here is year-only (Jan 1) — the search endpoint
    doesn't expose a full publication date."""
    params = {
        "title": title,
        "limit": 5,
        "fields": "title,author_name,publisher,number_of_pages_median,language,first_publish_year",
    }

    try:
        response = httpx.get(OPEN_LIBRARY_SEARCH_URL, params=params, timeout=10.0)
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as e:
        return f"Error calling Open Library API: {e}"

    docs = data.get("docs")
    if not docs:
        return f"No books found matching the title '{title}' on Open Library."

    results = []
    for doc in docs:
        lang_codes = doc.get("language", [])
        lang = (
            LANGUAGE_MAP.get(lang_codes[0], lang_codes[0]) if lang_codes else "Unknown"
        )
        publishers = doc.get("publisher", ["Unknown"])
        year = doc.get("first_publish_year")
        results.append(
            {
                "title": doc.get("title", "Unknown"),
                "authors": _authors(doc.get("author_name", [])),
                "publisher": publishers[0] if publishers else "Unknown",
                "page_count": doc.get("number_of_pages_median"),
                "language": lang,
                "published_date": f"{year}-01-01" if year else "Not available",
            }
        )

    return _format_results(results, year_only=True)


@tool
def search_book_tavily(title: str) -> str:
    """
    Last-resort fallback book search using Tavily's web search API. Use
    this only after search_book (Google Books) and search_book_openlibrary
    (Open Library) have failed or left gaps in publisher, page_count, or
    language. Results are unstructured web snippets, not typed book
    metadata — extract fields carefully and only when confident.
    """

    try:
        data = TavilyClient().search(
            query=f"{title} book author publisher page count language original publication date"
        )
    except Exception as e:
        return f"Error calling Tavily API: {e}"

    results = data.get("results", [])
    if not results and not data.get("answer"):
        return f"No web results found for '{title}'."

    lines = []
    if data.get("answer"):
        lines.append(f"Summarized answer: {data['answer']}")

    for i, r in enumerate(results, start=1):
        lines.append(
            f"\nResult {i}: {r.get('title', 'Untitled')} ({r.get('url', '')})\n"
            f"{r.get('content', '')[:500]}"
        )

    return "\n".join(lines)
