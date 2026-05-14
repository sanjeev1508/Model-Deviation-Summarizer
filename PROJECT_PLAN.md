# Model Deviation Summarizer — Roadmap & Change Plan

This plan responds to a product/engineering review: **security (API keys)**, **reliability (embeddings / memory)**, **correctness (domains, dual entrypoints)**, and **differentiation (live drift vs post-hoc report)**.

**Already delivered in this pass (baseline fixes):**

- **Legal & engineering personas** added to `DOMAIN_PERSONAS` in `reconstruction_service.py` (no more silent fallback to education tone).
- **Appwrite entrypoint** (`main_appwrite.py`) rewritten to use the **same pipeline** as FastAPI `/analyze` (`analyze_conversation` → `extract_keyword_constraint_analysis` → `build_master_payload` → `generate_master_report`), with `api_key` / `model` passed through `runtime_config`.
- **Shared payload assembly** in `pipeline_core.py` so FastAPI and Appwrite cannot drift silently.
- **Default embeddings via Groq** (`nomic-embed-text-v1.5` HTTP API): no PyTorch on the server by default; optional `EMBEDDING_PROVIDER=local` + `requirements-local-embed.txt` for offline dev.
- **Tighter CORS** (`chrome-extension://…`, localhost, Render host) instead of `*`.
- **Extension sends Groq key in `Authorization: Bearer`** for `/analyze` and `/test-groq` (not in JSON body); FastAPI merges into `ChatRequest.api_key` for downstream Groq SDK calls.

---

## Phase 0 — Principles (unchanged architecture)

- Keep **FastAPI + streaming NDJSON + MV3 extension** as the core stack.
- Prefer **small, testable steps**; ship security and correctness before large UX bets.

---

## Phase 1 — Critical: API key exposure (trust)

### Problem

The extension sends the user’s **Groq API key** to the publisher backend on every analyze request. The server can use it honestly today, but users cannot verify that; any breach, log misconfiguration, or insider risk **burns trust**.

### Direction (pick one primary strategy; document clearly in UI + privacy policy)

| Strategy | Pros | Cons |
|----------|------|------|
| **A. Client-side Groq only** | Key never hits your server | All LLM calls from extension (CORS, rate limits, larger extension logic); embeddings must also be client-side or via a keyless embed API you pay for |
| **B. Short-lived server token** | UX similar to today | Still need bootstrap trust; server issues JWT/session after user proves key once — key still transits at least once unless OAuth with Groq exists |
| **C. Publisher-provisioned API** | Best UX; no user key on wire | You pay Groq/OpenAI; billing + abuse prevention; changes business model |
| **D. User self-host only** | Zero key to publisher | Smallest addressable market unless one-click deploy improves |

**Recommended near-term:** hybrid **A for key + C for optional “cloud mode”**:  

1. **Default path:** extension **service worker** (or offscreen document) holds key, calls **Groq** directly for both LLM steps; optionally calls **Groq/OpenAI embeddings HTTP API** from the same context. Backend used only for **non-secret** assets or omitted.  
2. **Optional “hosted analysis”:** explicit opt-in with clear disclosure if you still offer Render-backed mode.

### Engineering tasks

1. Audit every log line / exception handler on the server for accidental `api_key` logging.  
2. Add automated test or lint rule: **no `api_key` in `print`/`logger` arguments**.  
3. If server path remains: **TLS only**, **no persistence** of key, **minimal retention** for request bodies, document in privacy policy.  
4. Extension: migrate sensitive calls to **service worker** (`background.js` MV3) so the key is not exposed to arbitrary content scripts.

**Exit criteria:** User can use the product with **no Groq secret sent to publisher infrastructure** (unless they explicitly opt into a labeled “cloud” mode).

---

## Phase 2 — Critical: One pipeline, two hosts (done + upkeep)

- **Done:** `main_appwrite.py` aligned with `/analyze`; `pipeline_core.build_master_payload` shared.  
- **Ongoing:** Any new stage in `main.py` must be reflected in `main_appwrite.py` **or** moved into a single `run_analysis_sync()` / `run_analysis_stream()` module to avoid regressions.

**Exit criteria:** CI check or checklist item on every PR touching analysis: “Appwrite path updated?”

---

## Phase 3 — Critical: Domain correctness (done)

- **Done:** `legal` and `engineering` entries in `DOMAIN_PERSONAS`.  
- **Optional:** align `config.py` comments / defaults with all five domains; add unit test asserting every `domain` value from the extension exists in `DOMAIN_PERSONAS`.

---

## Phase 4 — High impact: API-based embeddings (replace SentenceTransformers on server)

### Problem

PyTorch + `sentence-transformers` drives **cold start**, **RAM pressure** on Render free tier, and slow first request while models download.

### Direction

- Add an **`EmbeddingProvider`** abstraction: `embed_texts(texts) -> list[vectors]` implemented by:
  - **Groq** (if/when embedding endpoint fits your account), or  
  - **OpenAI** `text-embedding-3-small` (or similar), or  
  - **Other** hosted embed API.

- **Request shape:** batch user+assistant pairs (or full batch) per analyze call to minimize round-trips.  
- **Config:** `EMBEDDING_PROVIDER=groq|openai|local`, API keys via **server env only** for hosted embeds you pay for, or **extension-only** keys if you move embed calls client-side (Phase 1).

### Tasks

1. Introduce `embedding_provider.py` (protocol + factory).  
2. Migrate `deviation_service.analyze_conversation` to call provider instead of `embedding_service` directly.  
3. Keep **local** implementation behind flag for dev/air-gapped.  
4. Update `requirements.txt`: make `sentence-transformers` / `torch` **optional** extra, e.g. `pip install -r requirements.txt` vs `requirements-gpu.txt`.  
5. Re-benchmark **cosine similarity** parity on a small golden set of conversations.

**Exit criteria:** Production deploy fits **Render memory** without OOM; cold start **&lt; few seconds** after idle.

---

## Phase 5 — Differentiation: Live “during chat” drift (moat)

### Insight

Post-hoc reports are **occasional audits**. **Per-turn drift badges while the user chats** are habit-forming and hard to copy.

### Concept

- **Content script** (persistent on supported origins) observes **new messages** in the DOM (MutationObserver).  
- After each assistant reply (or each pair), run a **lightweight** score:  
  - ideally **incremental** embed on last user + last assistant only (cheap API call), or  
  - keyword-only fast path + periodic full embed sync.  
- Render a **small UI affordance** on/near each turn: score + color (green / amber / red). Click → mini panel with one-line “why” + link to full analyze in popup.

### Phasing

1. **MVP:** manual “Score last turn” button in popup (reuses current backend with last two messages only) — validates latency and cost.  
2. **V1 live:** observer + debounced batch; cap API calls (e.g. max 1 per N seconds).  
3. **V2:** optional streaming update to badge; settings for aggressiveness.

**Exit criteria:** User sees **at least one live badge** update without opening the popup on a supported site.

---

## Phase 6 — Hardening & growth

- Rate limiting / abuse controls on public backend if any anonymous path exists.  
- Tighten CORS if non-extension clients are not required.  
- Telemetry (opt-in): latency, error codes, **never** conversation text or keys.  
- Golden tests for scrapers (fixture HTML snapshots).

---

## Suggested priority order

1. **Phase 1** (API key architecture) — highest trust leverage.  
2. **Phase 4** (API embeddings) — operational reliability on small hosts.  
3. **Phase 5** (live badges) — differentiation and retention.  
4. **Phases 2–3** — maintain what is already fixed; automate drift checks.  
5. **Phase 6** — as traffic grows.

---

## Risks & dependencies

- **Groq client in browser:** confirm CORS policy for Groq HTTP API from extension origins; if blocked, use **minimal** same-origin proxy that forwards requests with **Authorization** header and **never logs** body headers.  
- **Live mode cost:** per-turn embeds scale with messages; product needs **budget slider** in settings.  
- **DOM churn:** live mode multiplies scraper maintenance; invest in **detector tests** per host.

---

*Update this document when phases complete or priorities shift.*
