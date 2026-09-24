# Book Fetch Agent

Packaged LLM agent that returns structured book metadata for a given title.

## Objective

Book Fetch Agent turns a book title into structured metadata (title, author, publisher, page count, language, published date) using an LLM agent backed by multiple data sources. It exists because no single free book API reliably covers all titles: Google Books is tried first, Open Library is a fallback, and Tavily web search is the last resort for obscure, non-English, or very recent books. The agent returns a validated, typed record (or a `not_found` result) instead of a free-form text answer.

## Tech Stack

- **Language**: Python 3.14
- **Agent framework**: LangChain (`create_agent`), LangChain Core (custom `@tool` functions)
- **Model**: Gemini 3.5 Flash Lite via `langchain-google-genai`
- **Structured output**: Pydantic v2 (`response_format=BookInfo`)
- **HTTP / config**: `httpx`, `python-dotenv`
- **External services**: Google Books API, Open Library API, Tavily web search API
- **Optional**: LangSmith tracing (`LANGSMITH_TRACING=true`)

## Setup

Dependencies are pinned in `requirements.txt`.

1. Clone the repository:

   ```bash
   git clone <repo-url>
   cd book-fetch-agent
   ```

2. Create a virtual environment, activate it, and install the pinned dependencies from the `requirements.txt` file in the repo:

   ```bash
   python3.14 -m venv env
   source env/bin/activate
   pip install -r requirements.txt
   ```

3. Create a `.env` file at the project root (`.gitignore` excludes it). Settings read at runtime via `load_dotenv()`:

   ```bash
   GOOGLE_API_KEY=...            # required — Gemini model auth
   TAVILY_API_KEY=...            # required — used by the Tavily fallback tool
   GOOGLE_BOOKS_API_KEY=...      # optional — improves Google Books rate limits
   # Optional LangSmith tracing:
   LANGSMITH_TRACING=true
   LANGSMITH_ENDPOINT=https://api.smith.langchain.com
   LANGSMITH_API_KEY=...
   LANGSMITH_PROJECT=books-api
   ```

4. No database or migrations are involved; the only runtime dependencies are the three external book/web search APIs above.

## Usage

Run the CLI with a book title as arguments (defaults to a demo title if none given):

```bash
python agent.py "The indispensable Calvin and Hobbes"
```

Code is split across three modules: `agent.py` (entry point, agent definition, `BookInfo` schema), `tools.py` (the three search tools), and `helpers.py` (language map and result formatting).

The agent prints the structured `BookInfo` record as JSON, e.g.:

```bash
{
  "title": "The Indispensable Calvin and Hobbes",
  "author": "Bill Watterson",
  "publisher": "...",
  "page_count": 256,
  "language": "English",
  "published_date": "1992-10-01",
  "not_found": false
}
```

An interactive Jupyter notebook (`agent.ipynb`) provides the same workflow for experimentation.

### Tests

TODO — the repository currently contains no test files, no test runner, and no lint/build scripts.