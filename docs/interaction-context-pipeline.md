# How GUM Takes Interaction Context to Be Analyzed

There are **five distinct stages** where context is collected, shaped, and fed to an LLM. Each stage adds a layer on top of the previous one.

---

## Stage 1 — Screen capture: building a "before/after" frame pair

`screen.py:416-427` runs a tight loop at **10 FPS** (`_CAPTURE_FPS = 10`). On every tick it calls `mss.sct.grab(monitor)` — wrapped in `asyncio.to_thread` to avoid blocking the event loop — and stores the raw pixel buffer in `self._frames[monitor_index]`. These are the **"before" frames**: a continuously-refreshed snapshot of what the screen looks like *right now*.

In parallel, `pynput.mouse.Listener` watches for **mouse move, click, and scroll** events. Because pynput is synchronous and runs in its own thread, events are bridged into the asyncio event loop via `asyncio.run_coroutine_threadsafe` (`screen.py:351-352`).

When the first event arrives (`screen.py:400-406`):
- The monitor index is resolved from the mouse coordinates via `_mon_for`
- The **currently-buffered "before" frame** for that monitor is latched into `self._pending_event`
- A **2-second debounce timer** is started (`DEBOUNCE_SEC = 2`)

Each subsequent event resets the timer (`screen.py:408-411`). After 2 seconds of silence, `flush()` fires:
1. Grabs a fresh **"after"** frame at that moment (`screen.py:371`)
2. Saves both to JPEG at `~/.cache/gum/screenshots/{timestamp}_before.jpg` / `_after.jpg`
3. Calls `_process_and_emit(before_path, after_path)`

The debounce design means: one burst of mouse activity → one capture pair, not one per event.

---

## Stage 2 — Two sequential GPT Vision calls: transcription then summary

`_process_and_emit` (`screen.py:286-311`) makes **two separate vision API calls** with different images and prompts. Both use the same `AsyncOpenAI` client that can point to any OpenAI-compatible endpoint.

### Call 1 — Transcription (`screen.py:299`)

Images sent: `[before_path, after_path]` — only the two frames from the current interaction.

Prompt (`prompts/screen.py:1-6`):
> "Transcribe in markdown ALL the content from the screenshots of the user's screen. NEVER SUMMARIZE ANYTHING. You must transcribe everything EXACTLY, word for word... ALWAYS include all the application names, file paths, and website URLs."

The output is a verbatim markdown dump of everything visible — file names, code lines, webpage text, UI labels, URLs. This is the **factual substrate**.

### Call 2 — Summary (`screen.py:305-308`)

Images sent: the rolling **history deque** (`self._history`, capped at `history_k=10` frames) plus the current before and after — potentially up to **12 images in sequence**.

The history is populated *before* the transcription call (`screen.py:293-295`), so it reflects the last 10 distinct interactions. This gives the summary model a **temporal sequence** of where the user has been.

Prompt (`prompts/screen.py:9-15`):
> "Provide a detailed description of the actions occurring across the provided images. The images are in the order they were taken... reference *specific* actions the user is taking... the content on the screen is what the user is viewing. It may not be what the user is actively doing."

Output: bullet-point narrative of what changed across the sequence — which window appeared, what was typed, what was clicked.

**Final content** = `transcription + summary` concatenated into one string, then placed as `Update(content=txt, content_type="input_text")` onto `self.update_queue`.

---

## Stage 3 — Calendar observer: structured event diffs

The `Calendar` observer (`observers/calendar.py`) runs a separate poll every 60 seconds. It fetches the ICS URL via `aiohttp`, parses events with the `ics` library, and diffs the last 7 days against a JSON cache at `~/.cache/gum/calendar/calendar_cache.json`.

Changes (added / modified / deleted events) are formatted as structured text:

```
Current Time: 2026-05-21 10:30 PDT
NEW calendar event:
  Title      : Team Standup
  When       : 2026-05-21 11:00 → 2026-05-21 11:30
  Location   : Zoom
  Starts In  : 0d 0h 30m
```

Every 24 hours it also emits a **weekly snapshot** of all upcoming events. Both go onto the same `update_queue` as `Update(content=..., content_type="input_text")`.

---

## Stage 4 — Batching: accumulating context across observers

`gum._update_loop` (`gum.py:195-216`) waits on *all* observers simultaneously with `asyncio.wait(..., return_when=FIRST_COMPLETED)`. When any observer emits an `Update`, it immediately calls `_default_handler`, which pushes the observation to `ObservationBatcher.push()` (`gum.py:578-583`).

`ObservationBatcher` (`batcher.py`) is backed by `persist-queue` — a SQLite-backed queue under `~/.cache/gum/batches/queue/`. Each item is stored as:

```python
{
  'id': uuid,
  'observer_name': "Screen",   # or "Calendar"
  'content': "<full transcription+summary>",
  'content_type': "input_text",
  'timestamp': "2026-05-21T10:31:00+00:00"
}
```

When queue size reaches `min_batch_size` (default 5), `_batch_ready_event` is set. `_batch_processing_loop` wakes, acquires a lock, and pops up to `max_batch_size` (15) items.

In `_process_batch` (`gum.py:230-285`), all items in the batch are **concatenated with their observer name as a prefix**:

```
[Screen] ## File: gum.py
\`\`\`python
async def _update_loop...
...
[Calendar] Current Time: 2026-05-21 10:30
NEW calendar event: ...
```

This single combined string becomes the `{inputs}` placeholder in the PROPOSE_PROMPT. Screen observations and calendar events therefore **inform the same proposition batch together**.

---

## Stage 5 — Three LLM calls: propose → classify → revise

### LLM Call A — PROPOSE (`gum.py:287-308`, `prompts/gum.py:36-106`)

The combined content is substituted into `PROPOSE_PROMPT`:
- `{user_name}` → the user's name
- `{inputs}` → the full concatenated observation batch

The prompt instructs the model to generate **at least 5 propositions**, each with:
- `proposition`: a concrete claim about the user
- `reasoning`: specific named entities from the transcript as evidence
- `confidence`: 1–10 (only high if the user is clearly *actively* engaging, not just glancing)
- `decay`: 1–10 (how long this will stay relevant)

Response is validated against `PropositionSchema` (Pydantic) via `response_format=get_schema(...)` — OpenAI's structured output mode.

**BM25 retrieval** (`gum.py:424-461`): For each draft proposition, `search_propositions_bm25` is called with `"{draft.text}\n{draft.reasoning}"` as the query. This searches the `propositions_fts` FTS5 virtual table for existing stored propositions. The result is a **candidate pool** of existing propositions that might be related. New drafts and these existing hits are combined into one pool — so the next step sees both fresh inferences and accumulated history.

### LLM Call B — SIMILAR (`gum.py:327-378`, `prompts/gum.py:186-210`)

The entire pool (new drafts + historical hits) is formatted as:

```
[id=42] Omar is working on gum.py
    Reasoning: Terminal shows active editing...

[id=7] Omar prefers async patterns
    Reasoning: Observer pattern, asyncio.Queue...
```

The model labels every pair as `IDENTICAL` / `SIMILAR` / `UNRELATED` and returns a `RelationSchema`. The pool is split into three lists.

### LLM Call C — REVISE (`gum.py:401-422`, `prompts/gum.py:108-184`) — similar cluster only

Before calling the LLM, GUM fetches the **supporting observations** for all similar propositions from the DB (`get_related_observations`), plus the current batch's observations. The revision prompt receives:
- All similar proposition texts + their reasoning
- All their supporting observations (raw screen transcriptions etc.)

The model is asked to merge, split, edit, or add propositions — and to **preserve named entities** for BM25 retrieval quality. Old similar propositions are deleted; the new revised set replaces them, linked to all the collected observations.

---

## Summary of context layers

| Layer | Where | What's included |
|---|---|---|
| Raw pixels | `Screen._frames` | 10-FPS rolling buffer per monitor |
| Before/after pair | `_pending_event` + `flush()` | Frames bracketing a debounced mouse burst |
| Temporal history | `Screen._history` | Last 10 interaction frames (sent to summary call) |
| Transcription | TRANSCRIPTION_PROMPT | Verbatim text of both frames |
| Action summary | SUMMARY_PROMPT | Temporal narrative across up to 12 frames |
| Calendar diff | `Calendar._poll_once` | Structured event changes vs. 7-day JSON cache |
| Batch aggregation | `ObservationBatcher` | Up to 15 observations, mixed observers, prefixed by name |
| Prior knowledge | `search_propositions_bm25` | BM25-matched existing propositions from the DB |
| Revision context | `_handle_similar` | All observations ever linked to similar propositions |

The core design principle is that **no single LLM call sees raw pixels**. By the time an observation reaches the PROPOSE_PROMPT, it has already been pre-processed by two vision calls into named-entity-rich text. And by the time propositions are revised, they are grounded in both the current batch and the full historical evidence stored in the DB.