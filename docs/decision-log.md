# Decision Log

Design decisions for Sarkari Sahayak, newest first. Each entry records what was decided, why, and what it affects. Add a new entry whenever a design choice is made; don't rewrite old ones. If a decision is reversed, add a new entry that points back to the old one.

---

## 2026-11-16 — Multilingual defaults: 9 languages, no keypad menu

**Decision:** The first multilingual version supports the 9 languages that Sarvam's `bulbul:v4-flash` has voices for: Hindi, English, Bengali, Gujarati, Kannada, Marathi, Punjabi, Tamil and Telugu. The keypad language menu is removed. The bot greets callers in Hindi and English, then follows whatever language they speak.

**Why:** These were the recommended defaults; no other choice was given. `saaras:v4` can understand 23 languages, but the bot can only answer aloud in languages Bulbul v4 has voices for. Removing the keypad menu shortens the start of every call by 6–12 seconds.

**Affects:** `voice/core/languages.py`, `voice/core/language_router.py` (replaces `voice/core/ivr.py`), `voice/core/pipeline.py`.

**Known gaps:** Bulbul v4 has no Malayalam or Odia voices yet, so those callers are answered in Hindi or English. Tamil has no conversational-style voice, so it uses a narration voice. All voices need a listening check.

---

## 2026-11-16 — `check_*` lookups fetch by filter instead of searching

**Decision:** The five functions `check_eligibility`, `check_documents`, `check_benefits`, `check_application_process` and `check_scheme_details` in `voice/retrieval/retriever.py` become five one-line wrappers around one shared helper, `_check_section()`.
- The helper fetches the scheme's section from Weaviate by filter (`scheme_id` + `section`) instead of running a hybrid search.
- It runs the reranker only when more than one chunk comes back.

**Why:** 16,770 of the 16,780 `(scheme_id, section)` pairs in the data are a single chunk, so the old functions did work that decided nothing:
- **Wasted calls:** every follow-up question made a Cloudflare embedding call, a vector search plus a BM25 search, and a reranker run, all of which ended at the same single chunk.
- **Latency:** those steps added delay to every follow-up answer.
- **Fragility:** follow-up answers failed whenever Cloudflare was unavailable or over its rate limit, even though they're plain lookups.
- **Duplication:** the same ~30 lines existed five times, so any change, including the multilingual one, had to be made in five places.

**Kept the same:** the five function names, their arguments and return values (so `voice/core/tool.py` and the eval script don't change), the filters including `government_level`, the chunk returned for single-chunk sections, and the "No information was found" reply when nothing matches.

**Affects:** `voice/retrieval/retriever.py`. These lookups no longer depend on the caller's language, so they work unchanged in the multilingual design.
