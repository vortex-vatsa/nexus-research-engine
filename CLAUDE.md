# CLAUDE.md — Nexus Research Engine

---

## 1. Project Identity

Nexus is an autonomous research engine that replaces AI chat boxes with a structured
visual business dashboard. A user gives it a topic; it searches the live web, synthesizes
findings, and renders them as tables, charts, and summaries inside persistent local
workspace folders. Protected by Google OAuth — only allowed users can access it.

---

## 2. Architecture Overview

```
Backend:    FastAPI (Python 3.11+)
Database:   SQLite via SQLAlchemy (jobs, sessions, users)
Vector DB:  ChromaDB (persistent local directory per workspace)
Storage:    Local disk (WorkspaceRepository abstraction — swappable to R2)
LLM:        Ollama (local dev) → Gemini Flash → Groq Llama3 (router)
Search:     Tavily API
Auth:       Google OAuth via authlib (backend) + next-auth v5 (frontend)
Frontend:   Next.js 14 App Router + TypeScript + Tailwind + shadcn/ui + Recharts
Deploy:     Vercel (frontend, free) + Render (backend, free)
            Files: Local disk → Cloudflare R2 when deploying (one file swap)
```

Core principle: backend and frontend are fully decoupled via a strict JSON schema
contract (dashboard_payload.json). Backend writes it. Frontend reads it. Nothing
else crosses the boundary as raw data.

All file system operations go through WorkspaceRepository. This is the ONLY class
that touches disk. Swapping local disk to Cloudflare R2 means changing one file.

---

## 3. Folder Structure

```
nexus-research-engine/
├── CLAUDE.md
├── TASKS.md
├── .env.example
├── .gitignore
├── Makefile
├── Dockerfile
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py        → Settings, env vars, get_settings()
│   │   │   ├── schemas.py       → All 16 Pydantic V2 models
│   │   │   └── exceptions.py    → NexusBaseError hierarchy
│   │   ├── repository/
│   │   │   └── workspace_repo.py → ALL file system operations (only class touching disk)
│   │   ├── providers/
│   │   │   ├── llm_router.py    → Ollama → Gemini → Groq abstraction
│   │   │   └── search_client.py → Tavily API wrapper
│   │   ├── agents/
│   │   │   ├── orchestrator.py  → Coordinates full pipeline, job registry
│   │   │   ├── researcher.py    → Sub-query generation + Tavily search
│   │   │   ├── synthesizer.py   → LLM → strict JSON schema
│   │   │   ├── graph_engine.py  → [V2] NetworkX cross-topic mapping
│   │   │   └── auditor.py       → [V2] Citation paragraph hashing
│   │   ├── services/
│   │   │   ├── vector_store.py  → ChromaDB per-workspace isolation
│   │   │   ├── notebook.py      → RAG Q&A with confidence scoring
│   │   │   └── database.py      → SQLAlchemy engine, session factory
│   │   ├── models/
│   │   │   └── db_models.py     → SQLAlchemy ORM models (User, Job, Workspace)
│   │   ├── auth/
│   │   │   ├── router.py        → /auth/login, /auth/callback, /auth/logout, /auth/me
│   │   │   └── dependencies.py  → get_current_user() FastAPI dependency
│   │   └── routers/
│   │       ├── research.py      → POST /research/run, GET /research/status/{id}
│   │       ├── workspaces.py    → CRUD for workspaces
│   │       └── notebook.py      → POST /notebook/query
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_schemas.py
│   ├── storage/                 → Runtime data. NEVER committed to git.
│   ├── requirements.txt
│   └── pyproject.toml
│
└── frontend/
    ├── src/
    │   ├── app/
    │   │   ├── layout.tsx
    │   │   ├── page.tsx                    → Home / Blueprint Configurator
    │   │   ├── workspace/[slug]/page.tsx   → Dashboard canvas
    │   │   ├── login/page.tsx              → Google OAuth login page
    │   │   └── api/auth/[...nextauth]/route.ts → next-auth handler
    │   ├── components/
    │   │   ├── layout/
    │   │   │   ├── AppShell.tsx
    │   │   │   └── Sidebar.tsx
    │   │   ├── auth/
    │   │   │   └── LoginButton.tsx
    │   │   ├── configurator/
    │   │   │   └── BlueprintForm.tsx
    │   │   ├── dashboard/
    │   │   │   ├── DashboardCanvas.tsx
    │   │   │   ├── ExecutiveBrief.tsx
    │   │   │   ├── DataMatrix.tsx
    │   │   │   ├── DocumentLibrary.tsx
    │   │   │   └── matrix-blocks/
    │   │   │       ├── TableBlock.tsx
    │   │   │       ├── ChartBlock.tsx
    │   │   │       └── ListBlock.tsx
    │   │   └── notebook/
    │   │       ├── NotebookPanel.tsx
    │   │       ├── ChatThread.tsx
    │   │       ├── QueryInput.tsx
    │   │       └── RetryAlert.tsx
    │   ├── hooks/
    │   │   ├── useWorkspace.ts
    │   │   ├── useNotebook.ts
    │   │   └── useResearchJob.ts
    │   ├── lib/
    │   │   ├── types.ts       → TypeScript mirror of all 16 backend schemas
    │   │   ├── api.ts         → Typed fetch wrappers for all endpoints
    │   │   └── utils.ts       → cn(), formatDate(), getDomain()
    │   └── store/
    │       └── workspace.ts   → Zustand store
    ├── auth.ts                → next-auth v5 config
    ├── middleware.ts          → Route protection
    └── .env.local
```

Rules:
- WorkspaceRepository is the ONLY class that reads or writes files. No exceptions.
- Routers call services/agents and return HTTP responses. Zero business logic.
- Components call hooks and render. Zero data fetching.
- Never commit backend/storage/. It is runtime data.
- Never commit .env or .env.local. Always commit .env.example.

---

## 4. Auth Architecture

### Backend (authlib + Starlette sessions)
- `authlib.integrations.starlette_client` handles Google OAuth flow
- `starlette.middleware.sessions.SessionMiddleware` stores session in signed cookie
- On callback: verify Google user, check email against ALLOWED_GOOGLE_EMAILS
- If allowed: store {google_id, email, name, avatar_url} in session
- `get_current_user()` FastAPI dependency: reads session, returns user or raises 401
- Every protected router depends on `get_current_user()`
- Workspaces are namespaced per user email prefix: `storage/{email_slug}/{topic-slug}/`
  where email_slug = email address with @ and . replaced by underscores

### Frontend (next-auth v5)
- `auth.ts` at root configures GoogleProvider with client ID and secret
- `middleware.ts` protects all routes except /login and /api/auth/*
- Session passed as JWT, user info available in all server and client components
- Every API call to backend includes the session token in Authorization header
- Backend verifies this token on every request via `get_current_user()`

### Environment variables required for auth
```
GOOGLE_CLIENT_ID=from_google_cloud_console
GOOGLE_CLIENT_SECRET=from_google_cloud_console
ALLOWED_GOOGLE_EMAILS=your@gmail.com,friend@gmail.com
SESSION_SECRET_KEY=random_32_char_string
AUTH_SECRET=random_32_char_string_for_nextauth
```

---

## 5. Coding Standards

### All code
- No magic strings or numbers. Use named constants or enums.
- Every function/method needs a docstring (Python) or JSDoc (TypeScript):
  what it does, parameters, return value, exceptions raised.
- All environment variables added to .env.example immediately when introduced.
- No commented-out code in commits. Delete it or keep it.

### Python / Backend
- Never use bare `except:`. Catch specific exception types always.
- Never use `print()`. Use `logging` at correct level:
  DEBUG=internal state, INFO=milestones, WARNING=retries, ERROR=failures.
- All FastAPI route handlers must be `async def`.
- All outbound HTTP: `httpx.AsyncClient` only. Never `requests`.
- All data shapes crossing boundaries: Pydantic V2 models. No raw dicts.
- ChromaDB is synchronous — always wrap in `asyncio.run_in_executor(None, fn)`.
- File I/O must use `aiofiles` for non-blocking reads and writes.
- All concurrent external calls capped with `asyncio.Semaphore(5)`.
- Import order: stdlib → third-party → local. Enforced by ruff.

### TypeScript / Frontend
- Never use `any`. Use `unknown` and narrow, or correct type from lib/types.ts.
- `const` by default. `let` only when reassignment is genuinely needed.
- All component props: explicit named interface. Never infer from usage.
- All data fetching in hooks/. Components only call hooks and render.
- Tailwind strings over 5 classes use `cn()` from lib/utils.ts.
- Never inline styles. Tailwind only.
- Always handle loading, error, and empty states explicitly.

---

## 6. Schema Contract

`dashboard_payload.json` is the immutable contract between backend and frontend.

- Pydantic V2 model in `backend/app/core/schemas.py`
- TypeScript interfaces in `frontend/src/lib/types.ts`
- Both must always be in sync. Any change updates both in the same commit.
- Contains `schema_version: "1.0"`. Bump on any structural change.
- Frontend checks schema_version on load and warns if mismatch.

---

## 7. Dependency Injection

Never instantiate services inside route handlers or agents.
Use FastAPI `Depends()` for all service injection.

```python
# WRONG — never do this
@router.post("/research/run")
async def run(request: ResearchRequest):
    orchestrator = ResearchOrchestrator(get_settings())

# CORRECT
@router.post("/research/run")
async def run(
    request: ResearchRequest,
    orchestrator: ResearchOrchestrator = Depends(get_orchestrator),
    current_user: AuthUser = Depends(get_current_user),
):
```

---

## 8. Error Handling

### Exception hierarchy (app/core/exceptions.py)
```python
class NexusBaseError(Exception):
    def __init__(self, message: str, context: dict | None = None):
        super().__init__(message)
        self.context = context or {}

class SearchClientError(NexusBaseError): ...
class ResearchAgentError(NexusBaseError): ...
class SynthesizerError(NexusBaseError): ...
class VectorStoreError(NexusBaseError): ...
class NotebookError(NexusBaseError): ...
class WorkspaceNotFoundError(NexusBaseError): ...
class AuthError(NexusBaseError): ...
```

Always raise with context:
```python
raise SearchClientError(
    "Tavily search failed",
    context={"query": query, "status_code": response.status_code}
)
```

### Global handlers (registered in main.py)
```python
@app.exception_handler(NexusBaseError)
async def nexus_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"error": str(exc), "context": exc.context, "type": type(exc).__name__}
    )

@app.exception_handler(Exception)
async def unhandled_error_handler(request, exc):
    logging.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "type": type(exc).__name__}
    )
```

### Retry with exponential backoff
```python
async def with_backoff(fn, retries: int = 2, base_delay: float = 1.0):
    """Retry an async callable with exponential backoff on failure."""
    for attempt in range(retries + 1):
        try:
            return await fn()
        except Exception as e:
            if attempt == retries:
                raise
            delay = base_delay * (2 ** attempt)
            logging.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s.")
            await asyncio.sleep(delay)
```

Use for all LLM calls and Tavily search calls. Never retry immediately.

### LLM call timeout
All LLM provider calls must have a 30 second timeout:
```python
async with asyncio.timeout(30):
    result = await llm_provider.complete(system, user)
```
On timeout: raise ResearchAgentError with context={"timeout_seconds": 30}.

---

## 9. Job Persistence (SQLite)

Jobs are stored in SQLite via SQLAlchemy — not in a dict. Survives restarts.

- `models/db_models.py` defines: User, Job, Workspace ORM models
- Job table: id, user_id, status, progress_message, workspace_slug, error,
  created_at, updated_at
- On every status change: update the DB row immediately
- On FastAPI startup: query all RUNNING or PENDING jobs, set them to FAILED
  with error="Server restarted while job was in progress."
- `services/database.py` provides: engine, get_db() dependency (async session)

---

## 10. Non-Blocking Code

The FastAPI event loop must never be blocked.

ChromaDB (sync client) — always wrap:
```python
collection = await asyncio.run_in_executor(None, self._get_collection, slug)
results = await asyncio.run_in_executor(None, collection.query, ...)
```

File I/O — always use aiofiles:
```python
async with aiofiles.open(path, "w") as f:
    await f.write(content)
```

Parallel external calls — always cap with Semaphore:
```python
_semaphore = asyncio.Semaphore(5)
async def bounded(coro):
    async with _semaphore:
        return await coro
results = await asyncio.gather(*[bounded(search(q)) for q in queries])
```

---

## 11. Request Tracing

Every job carries a request_id through all log messages:
```python
request_id = str(uuid4())[:8]
logger.info(f"[{request_id}] Starting: {topic}")
logger.info(f"[{request_id}] Sub-queries: {len(queries)}")
logger.info(f"[{request_id}] Sources: {len(sources)}")
```

Pass request_id through ResearchAgent, SynthesizerAgent, VectorStoreService.

---

## 12. Input Validation and Security

- Slug sanitisation: lowercase, spaces→hyphens, strip non-alphanumeric,
  max 60 chars. Must pass regex `^[a-z0-9-]+$` before any file path use.
- Path traversal protection: workspace paths must always be constructed as
  `Path(STORAGE_ROOT) / email_slug / slug` — never from raw user input.
  email_slug = email_to_slug(user.email) e.g. user@gmail.com → user_gmail_com
  Verify the resolved path starts with STORAGE_ROOT before any file operation.
- LLM token guard: count approximate tokens before synthesis call.
  If sources exceed 80,000 chars total, truncate to top-scoring sources only.
- Slug collision: if `storage/{user}/{slug}/` already exists, append `-2`, `-3`
  etc. Never silently overwrite an existing workspace.

---

## 13. Health Check

GET /health must verify all dependencies are reachable:
```python
{
  "status": "ok" | "degraded",
  "version": "1.0.0",
  "services": {
    "llm": "ok" | "unavailable",
    "tavily": "ok" | "unavailable",
    "database": "ok" | "unavailable",
    "storage": "ok" | "unavailable"
  }
}
```
Returns 200 even when degraded (so load balancers don't restart unnecessarily).
Returns 503 only if database is unavailable (nothing works without it).

---

## 14. Task Status System

**`[ ] todo`** — Not started. Implement from scratch.

**`[~] incomplete`** — Started but did not finish or pass verification.
Read what exists. Compare against Must Implement. Add missing. Fix broken.
Never rewrite what already works. Then run Verification and Checklist.

**`[x] done`** — Complete, verified, committed, confirmed by user. Never touch.

**`[!] blocked`** — Cannot complete without human input.
Set after exactly two failed attempts. When setting [!]:
1. Change status in TASKS.md to `[!]`
2. Write blocker note on next line:
   `**Blocker:** [exact error and what was tried]`
3. Stop. Report to user. Do not attempt any other task.

---

## 15. Session Workflow

**Step 1** — Run `git status`. Understand current state.

**Step 2** — Scan TASKS.md top to bottom. Find first non-[x] task.
Priority: `[~] incomplete` → `[!] blocked` → `[ ] todo`
If `[!]` found: read blocker note, report word for word, wait for instructions.

**Step 3** — Read the full spec for that task before writing any code.

**Step 4** — Implement everything in Must Implement. Nothing more.
`[ ]`: from scratch. `[~]`: read existing first, add only what is missing.

**Step 5** — Run every Verification command. Fix all failures.
Two failed attempts on same error → go to Step 7b.

**Step 6** — Run every item in Task Completion Checklist (Section 16).
Fix failures. Two failed attempts → go to Step 7b.

**Step 7a — Success:**
Commit with exact message from task. Mark `[x]` in TASKS.md.
Report: "✅ Task [name] complete. Confirm to continue."
Do not proceed until user explicitly confirms.

**Step 7b — Blocked:**
Mark `[!]` in TASKS.md. Write blocker note.
Report: "🚫 Task [name] blocked. Blocker: [exact error]. Please advise."
Do not attempt any other task.

---

## 16. Task Completion Checklist

Runs at Step 6, after Verification, before Commit.
Every item must pass. Fix before continuing.

- [ ] Every Must Implement item exists in the codebase
- [ ] Every new function/class/method has docstring (Python) or JSDoc (TypeScript)
- [ ] No `any` in TypeScript files touched by this task
- [ ] No bare `except:` in Python files touched by this task
- [ ] No `print()` in Python files touched by this task
- [ ] No blocking calls (ChromaDB, file I/O) without run_in_executor or aiofiles
- [ ] Concurrent external calls use asyncio.Semaphore
- [ ] LLM calls have 30 second asyncio.timeout
- [ ] Custom exceptions raised with context dict not bare strings
- [ ] Global exception handlers registered in main.py
- [ ] SQLite job status updated on every state change (Task 1.7+)
- [ ] Input sanitised and path traversal check on all workspace paths (Task 1.8+)
- [ ] All protected routes depend on get_current_user() (Task 1.9+)
- [ ] All Verification commands passed with zero errors
- [ ] `ruff check app/` zero issues (backend tasks)
- [ ] `npm run build` zero TypeScript errors (frontend tasks)
- [ ] `git diff --stat` shows only expected files — nothing extra
- [ ] .env.example updated if any new env var introduced
- [ ] Commit message is exactly as specified — not paraphrased

---

## 17. Scope Boundaries

### MVP — build in this order, nothing skipped
1.1  Project skeleton + folder structure
1.2  Core schemas (16 Pydantic models)
1.3  Config + LLM router (Ollama → Gemini → Groq)
1.4  Search client + researcher agent
1.5  Synthesizer agent
1.6  Vector store + notebook service
1.7  SQLite database + job persistence + orchestrator
1.8  WorkspaceRepository (local disk abstraction)
1.9  Google OAuth (auth router + session middleware)
1.10 All API routes (all protected by get_current_user)
2.1  Next.js setup + types + api client + Zustand store
2.2  App shell + sidebar + login page
2.3  Blueprint configurator
2.4  Dashboard canvas (all three spaces)
2.5  Notebook panel
3.1  End-to-end integration test
3.2  Empty states + error handling + toasts
3.3  Makefile + README + Dockerfile

### Deploy (one afternoon, after MVP complete)
4.1  Swap WorkspaceRepository to Cloudflare R2
4.2  Deploy backend to Render (free tier)
4.3  Deploy frontend to Vercel (free tier)

### V2 — locked until every MVP task is [x] done
5.1  Internet safety retry loop
5.2  Click-to-verify citations (paragraph hashing)
5.3  Nexus Map (NetworkX + ReactFlow)
5.4  Scheduled research subscriptions (APScheduler)
5.5  PDF export (WeasyPrint)
5.6  Shareable read-only dashboard links

If V2 is requested while MVP tasks remain:
"V2 features are locked until all MVP tasks are [x]. Pending: [list them]."
