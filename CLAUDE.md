# GUM (General User Models) — Agent Onboarding

## What this project is

GUM is a Python research package (`gum-ai` on PyPI) that builds a persistent, continuously-updated model of a user by observing their computer interactions. It converts raw observations (screenshots, calendar events, etc.) into confidence-weighted **propositions** about the user's knowledge, preferences, and activities. The paper is at arXiv:2505.10831.

## Repository layout

```
gum/                  # Main Python package
  gum.py              # Core gum class — orchestrates the whole pipeline
  models.py           # SQLAlchemy ORM: Observation, Proposition, FTS5 indexes
  schemas.py          # Pydantic schemas for LLM I/O (Update, PropositionSchema, RelationSchema, AuditSchema)
  db_utils.py         # Async DB queries: BM25 search, MMR reranking, recency
  batcher.py          # ObservationBatcher — persist-queue-backed batch accumulator
  cli.py              # `gum` CLI entry point (listen / query / recent modes)
  observers/
    observer.py       # Abstract Observer base class (asyncio.Queue + _worker abstract method)
    screen.py         # Screen observer: macOS screen capture + GPT-4o-mini vision analysis
    calendar.py       # Calendar observer: polls an ICS URL, diffs events
  prompts/
    gum.py            # PROPOSE_PROMPT, SIMILAR_PROMPT, REVISE_PROMPT, AUDIT_PROMPT
    screen.py         # TRANSCRIPTION_PROMPT, SUMMARY_PROMPT
web/                  # React/Vite frontend for "GUMBOs" (proactive assistants demo)
docs/                 # MkDocs documentation site
pyproject.toml        # Package metadata — package name is gum-ai, version 0.1.11
skypilot-tmp.yaml     # SkyPilot config for self-hosting models on cloud GPUs
```

## Core architecture

### Data flow
1. **Observers** capture raw interactions → push `Update` objects onto an `asyncio.Queue`
2. **`gum._default_handler`** receives updates → pushes them onto `ObservationBatcher` (persistent queue)
3. **`gum._batch_processing_loop`** waits for `min_batch_size` accumulation → calls `_process_batch`
4. **`_process_batch`** runs the LLM pipeline:
   - `_construct_propositions` (PROPOSE_PROMPT) — generate draft propositions from the batch
   - `_generate_and_search` — BM25-search existing propositions to build a candidate pool
   - `_filter_propositions` (SIMILAR_PROMPT) — classify pairs as IDENTICAL / SIMILAR / UNRELATED
   - `_handle_identical` — attach observations to existing matching propositions
   - `_handle_similar` (REVISE_PROMPT) — merge/revise similar propositions, delete old ones
   - `_handle_different` — attach observations to new propositions

### Database (SQLite + FTS5)
- Tables: `observations`, `propositions`, `observation_proposition` (many-to-many)
- FTS5 virtual tables: `propositions_fts`, `observations_fts` with porter ASCII tokenizer
- Stored at `~/.cache/gum/gum.db` by default
- WAL mode enabled; async via `aiosqlite` + `sqlalchemy[asyncio]`
- `search_propositions_bm25` applies BM25 scoring, exponential time-decay (based on proposition `decay` field), then MMR reranking

### Proposition fields
- `text`: the proposition statement
- `reasoning`: evidence justifying it
- `confidence`: 1–10, how strongly supported
- `decay`: 1–10, how quickly the proposition becomes stale (1 = short-lived)
- `revision_group`: UUID grouping related revisions
- `version`: starts at 1

### ObservationBatcher
- Backed by `persist-queue` (SQLite-based) under `~/.cache/gum/batches/`
- Survives process restarts — always check for leftover items on startup
- Triggers `_batch_ready_event` when queue size ≥ `min_batch_size`
- Default: `min_batch_size=5`, `max_batch_size=15`

## Environment variables

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key (fallback for both GUM and Screen) |
| `USER_NAME` | Full name of the user being modeled |
| `MODEL_NAME` | LLM model for the GUM core (default: `gpt-4o-mini`) |
| `GUM_LM_API_BASE` | Base URL for OpenAI-compatible API (for core GUM; enables local LMs) |
| `GUM_LM_API_KEY` | API key for the above |
| `SCREEN_LM_API_BASE` | Override API base specifically for the Screen observer |
| `SCREEN_LM_API_KEY` | Override API key for the Screen observer |
| `MIN_BATCH_SIZE` | Minimum observations before processing (default: 5) |
| `MAX_BATCH_SIZE` | Max observations per batch (default: 15) |
| `CALENDAR_ICS` | ICS calendar URL for the Calendar observer |

A `.env` file at the repo root is loaded by `cli.py` via `python-dotenv`. **Never commit real API keys.**

## CLI usage

```bash
# Start listening (runs forever; uses Screen observer)
gum -u "Full Name" -m gpt-4o-mini

# Query propositions (BM25 search)
gum -q "python debugging" -l 10

# List most recent propositions
gum -r -l 5

# Reset the cache (deletes ~/.cache/gum/)
gum --reset-cache
```

## Python API

```python
import asyncio
from gum import gum
from gum.observers import Screen, Calendar

async def main():
    # Listening mode (async context manager)
    async with gum("Alice", "gpt-4o-mini", Screen("gpt-4o-mini")) as g:
        await asyncio.Future()   # run forever

    # Query only (no observers needed)
    g = gum("Alice", "gpt-4o-mini")
    await g.connect_db()
    results = await g.query("email", limit=5)          # BM25 search
    recent  = await g.recent(limit=10)                  # newest propositions
    obs     = await g.recent_observations(limit=10)     # newest raw observations

asyncio.run(main())
```

## Adding a new Observer

1. Subclass `Observer` from `gum/observers/observer.py`
2. Implement `async def _worker(self) -> None` — run forever, use `self._running` as the stop flag
3. Put `Update(content=..., content_type="input_text")` objects onto `self.update_queue`
4. Export from `gum/observers/__init__.py`

## Platform constraints

- **macOS only** for the `Screen` observer (uses `Quartz`, `pyobjc-framework-Quartz`, `mss`, `pynput`)
- Requires Accessibility + Screen Recording permissions in System Settings → Privacy & Security
- Python ≥ 3.6 (repo currently runs 3.13)

## Development setup

```bash
pip install --editable .
# or
pip install -U gum-ai
```

No test suite exists yet. The package is published to PyPI as `gum-ai`.

## Documentation

MkDocs site built from `docs/` using Material theme. Build with `mkdocs build` or serve locally with `mkdocs serve`. Deployed to GitHub Pages.

## Key design decisions to respect

- The LLM client is always an `AsyncOpenAI` instance pointing to any OpenAI-compatible endpoint — do not add provider-specific SDKs.
- Batch processing is event-driven (`asyncio.Event`), not polling — do not add `asyncio.sleep` polling loops.
- Propositions are deleted and replaced (not versioned in-place) during revision — do not add UPDATE statements for proposition text.
- `search_propositions_bm25` uses SQLite FTS5 `bm25()` function; BM25 scores are negative (lower = better) before negation.
- The `revision_group` UUID links propositions that were revised together — preserve this when creating replacement propositions.