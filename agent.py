"""Book Information Retrieval Agent -- CLI.

Fetch structured book details by title, using Google Books, Open Library,
and (as a last resort) Tavily web search.

Usage:
    python agent.py "The indispensable Calvin and Hobbes"
"""

import json
import sys
from datetime import date

from dotenv import load_dotenv
from langchain.agents import create_agent
from pydantic import BaseModel

from tools import search_book, search_book_openlibrary, search_book_tavily

load_dotenv()


SYSTEM_PROMPT = """
    You are a Book Information Retrieval Agent. Your only job is to find accurate, factual information about a book given its title and return it in a structured format.

    ## Task
    The user will give you a book title. Your job:
    1. Identify the correct book — if multiple editions or books share a similar title, if it's genuinely ambiguous and no tool result resolves it, pick the most well-known / most recent edition and note the assumption in your reasoning (not in the final structured output).
    2. Use your available tools to search for and verify the book's details. Never rely on memory alone for facts like page count or publisher — always confirm with a tool call when a search tool is available.

    ## Rules
    - Do not fabricate or guess values. If a tool returns no result for the given title, say so instead of inventing plausible-sounding data.
    - If a field's exact value can't be found (e.g. page count varies by edition), use the most commonly cited/paperback edition value and be consistent — don't mix data from two different editions for the same book. When nothing reliable exists, leave that field null (or "Unknown"/"Not available" for required strings) rather than guessing.
    - If the title doesn't match any known book, return a BookInfo with not_found=true (title set to the searched/matched title, all other fields null/"Unknown") instead of returning a guessed BookInfo object.
    - Join multiple authors into a single comma-separated string in the author field.
    - Do not add commentary, opinions, or a review of the book — only the requested factual fields.
    - If the user's title is misspelled or partial, use your best judgment to match it to the intended book and proceed.

    ## Tools
    You have access to three book search tools, to be tried in this order:
    1. search_book — searches Google Books. Always try this first.
    2. search_book_openlibrary — fallback search on Open Library. Use it only
    if search_book returns no results, or its results are missing
    page_count or language.
    3. search_book_tavily — general web search fallback, built for LLM
    consumption. Use this only as a last resort, after both book-specific
    tools have failed or left gaps — e.g. for obscure, non-English, or
    very recent titles not yet indexed by the book APIs. Because this
    returns web snippets rather than structured metadata, only extract
    page_count/publisher/language values you're confident are accurate;
    never guess from ambiguous text.

    Don't call all three tools by default — only escalate to the next one
    when the previous tool leaves a genuine gap.
"""


class BookInfo(BaseModel):
    title: str
    author: str
    publisher: str | None = None
    page_count: int | None = None
    language: str | None = None
    published_date: date | None = None
    not_found: bool = False


agent = create_agent(
    model="google_genai:gemini-3.5-flash-lite",
    tools=[search_book, search_book_openlibrary, search_book_tavily],
    system_prompt=SYSTEM_PROMPT,
    response_format=BookInfo,
)


def main() -> None:
    title = " ".join(sys.argv[1:]).strip() or "The indispensable Calvin and Hobbes"
    result = agent.invoke({"messages": [{"role": "user", "content": title}]})
    text = result["messages"][-1].content_blocks[0]["text"]
    print(json.dumps(json.loads(text), indent=2))


if __name__ == "__main__":
    main()
