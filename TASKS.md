# TASKS.md — Nexus Research Engine
# Every spec is self-contained. No external files needed.
# Status: [ ] todo | [~] incomplete | [x] done | [!] blocked

---

## PHASE 1 — BACKEND

---

### Task 1.1 — Project Skeleton
**Status:** [x] done
**Commit:** `feat(backend): project skeleton and folder structure`

#### Must Implement

Create exact folder structure:
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── schemas.py
│   │   └── exceptions.py
│   ├── repository/
│   │   ├── __init__.py
│   │   └── workspace_repo.py
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── llm_router.py
│   │   └── search_client.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── orchestrator.py
│   │   ├── researcher.py
│   │   ├── synthesizer.py
│   │   ├── graph_engine.py
│   │   └── auditor.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── vector_store.py
│   │   ├── notebook.py
│   │   └── database.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── db_models.py
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── router.py
│   │   └── dependencies.py
│   └── routers/
│       ├── __init__.py
│       ├── research.py
│       ├── workspaces.py
│       └── notebook.py
├── tests/
│   ├── __init__.py
│   └── test_schemas.py
├── storage/
├── requirements.txt
└── pyproject.toml
```

Unimplemented files = stubs with module docstring only.
`storage/` = empty dir, listed in .gitignore.

**requirements.txt:**
```
fastapi==0.115.0
uvicorn[standard]==0.30.0
pydantic==2.7.0
pydantic-settings==2.3.0
httpx==0.27.0
python-dotenv==1.0.1
aiofiles==23.2.1
chromadb==0.5.0
sqlalchemy==2.0.30
aiosqlite==0.20.0
tavily-python==0.3.3
google-generativeai==0.7.0
groq==0.9.0
authlib==1.3.1
itsdangerous==2.2.0
networkx==3.3
pytest==8.2.0
pytest-asyncio==0.23.7
ruff==0.4.0
```

**pyproject.toml:**
```toml
[tool.ruff]
line-length = 88
select = ["E", "F", "I"]

[tool.black]
line-length = 88
```

**app/main.py must:**
- Create FastAPI: title="Nexus Research Engine", version="1.0.0"
- Add SessionMiddleware with SESSION_SECRET_KEY from config
- Add CORSMiddleware: allow_origins from config, methods=["*"],
  headers=["*"], credentials=True
- Mount routers: /auth, /research, /workspaces, /notebook
- Register global exception handlers for NexusBaseError and Exception
- GET /health → returns health status dict (stub for now, full impl in Task 1.7)
- Call llm_router.initialize() in startup event
- Add a startup event handler stub — full DB init and job healing added in Task 1.7
- Note: database and job healing wired in Task 1.7, not here

#### Verification
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --port 8000 &
sleep 3
curl -s http://localhost:8000/health
# Must return JSON with status field

python3 -c "
import os
required = [
    'app/__init__.py','app/main.py',
    'app/core/__init__.py','app/core/config.py',
    'app/core/schemas.py','app/core/exceptions.py',
    'app/repository/__init__.py','app/repository/workspace_repo.py',
    'app/providers/__init__.py','app/providers/llm_router.py',
    'app/providers/search_client.py',
    'app/agents/__init__.py','app/agents/orchestrator.py',
    'app/agents/researcher.py','app/agents/synthesizer.py',
    'app/agents/graph_engine.py','app/agents/auditor.py',
    'app/services/__init__.py','app/services/vector_store.py',
    'app/services/notebook.py','app/services/database.py',
    'app/models/__init__.py','app/models/db_models.py',
    'app/auth/__init__.py','app/auth/router.py','app/auth/dependencies.py',
    'app/routers/__init__.py','app/routers/research.py',
    'app/routers/workspaces.py','app/routers/notebook.py',
    'tests/__init__.py','tests/test_schemas.py',
    'requirements.txt','pyproject.toml'
]
missing = [f for f in required if not os.path.exists(f)]
print('MISSING:', missing) if missing else print('All files present')
"
```

---

### Task 1.2 — Core Schemas
**Status:** [x] done
**Commit:** `feat(backend): core Pydantic V2 schemas — all 16 models`

#### Must Implement

All 16 models in **app/core/schemas.py**.
Every model: class docstring. Every field: description= argument.

**1. ComponentType (str, Enum):** TABLE="table", CHART="chart", LIST="list"
**2. ChartStyle (str, Enum):** BAR="bar", LINE="line", PIE="pie"
**3. ExtensivenesLevel (str, Enum):** QUICK="quick", DEEP="deep"
**4. FormatPreference (str, Enum):** TIMELINE="timeline", SWOT="swot",
   PROS_CONS="pros_cons", COMPARISON="comparison"
**5. JobStatus (str, Enum):** PENDING="pending", RUNNING="running",
   COMPLETE="complete", FAILED="failed"
**6. TopicMetadata:** topic(str), extensiveness(str), format_preference(str),
   generated_at(datetime), schema_version(str, default="1.0")
**7. MatrixComponent:** section_title(str), component_type(ComponentType),
   headers(list[str]|None), rows(list[list[str]]|None),
   chart_style(ChartStyle|None), data(list[dict[str,Any]]|None),
   description(str|None)
**8. DownloadedImage:** alt(str), local_url(str)
**9. DocumentSource:** id(str), title(str), url(str), local_path(str),
   snippet(str), downloaded_images(list[DownloadedImage]=[ ])
**10. DashboardPayload:** topic_metadata(TopicMetadata), executive_summary(str),
    matrix_data(list[MatrixComponent]), document_library(list[DocumentSource])
    Must have: @classmethod get_schema_version(cls) -> str: return "1.0"
**11. ResearchRequest:** topic(str, min_length=3, max_length=500),
    extensiveness(ExtensivenesLevel), format_preference(FormatPreference)
**12. ResearchJobStatus:** job_id(str), status(JobStatus), progress_message(str),
    workspace_slug(str|None), error(str|None), created_at(datetime),
    updated_at(datetime)
**13. NotebookQuery:** workspace_slug(str), question(str, min_length=1)
**14. RetrievedChunk:** content(str), source_id(str), url(str),
    chunk_index(int), distance(float)
**15. NotebookResponse:** answer(str), sources(list[RetrievedChunk]),
    confidence_score(float), needs_web_search(bool)
**16. WorkspaceListItem:** slug(str), topic(str), generated_at(str)

Also define **AuthUser** Pydantic model:
google_id(str), email(str), name(str), avatar_url(str)

**tests/test_schemas.py must test:**
- All 16 models + AuthUser imported in one block
- Complete DashboardPayload round-trips serialize/deserialize
- ComponentType has exactly TABLE, CHART, LIST
- JobStatus has exactly PENDING, RUNNING, COMPLETE, FAILED
- ResearchRequest rejects topic < 3 chars (ValidationError)
- NotebookQuery rejects empty question (ValidationError)
- DashboardPayload.get_schema_version() returns "1.0"

#### Verification
```bash
cd backend
python3 -c "
from app.core.schemas import (
    ComponentType, ChartStyle, ExtensivenesLevel, FormatPreference, JobStatus,
    TopicMetadata, MatrixComponent, DownloadedImage, DocumentSource,
    DashboardPayload, ResearchRequest, ResearchJobStatus,
    NotebookQuery, RetrievedChunk, NotebookResponse, WorkspaceListItem, AuthUser
)
print('All 17 types imported OK')
nq = NotebookQuery(workspace_slug='test', question='hello')
print('NotebookQuery OK:', nq)
rc = RetrievedChunk(content='t', source_id='s1', url='http://x.com', chunk_index=0, distance=0.5)
nr = NotebookResponse(answer='a', sources=[rc], confidence_score=0.8, needs_web_search=False)
print('NotebookResponse OK:', nr)
wl = WorkspaceListItem(slug='test', topic='Test', generated_at='2024-01-01')
print('WorkspaceListItem OK:', wl)
au = AuthUser(google_id='123', email='user@gmail.com', name='User', avatar_url='http://x.com')
print('AuthUser OK:', au)
print('Schema version:', DashboardPayload.get_schema_version())
"
pytest tests/test_schemas.py -v
```

---

### Task 1.3 — Config and LLM Router
**Status:** [x] done
**Commit:** `feat(backend): config settings and LLM context router`

#### Must Implement

**app/core/config.py:**
```python
class Settings(BaseSettings):
    # LLM
    GEMINI_API_KEY: str | None = None
    GROQ_API_KEY: str | None = None
    OLLAMA_HOST: str | None = None
    # Search
    TAVILY_API_KEY: str
    # Auth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    ALLOWED_GOOGLE_EMAILS: str  # comma-separated: "user@gmail.com,other@gmail.com"
    SESSION_SECRET_KEY: str
    # Storage
    STORAGE_ROOT: str = "./storage"
    # Server
    FRONTEND_ORIGIN: str = "http://localhost:3000"
    DATABASE_URL: str = "sqlite+aiosqlite:///./nexus.db"

    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings: ...

def get_storage_path(email_slug: str, slug: str) -> Path:
    """Return Path(STORAGE_ROOT) / email_slug / slug. Never use raw user input."""
    ...

def get_allowed_emails(settings: Settings) -> list[str]:
    """Parse ALLOWED_GOOGLE_EMAILS comma-separated string into list."""
    ...

def email_to_slug(email: str) -> str:
    """Convert email to safe directory name for use as storage path segment.
    Example: user@gmail.com → user_gmail_com
    Defined here (not in auth/) so orchestrator and repository can import it
    without circular dependencies.
    """
    return email.replace("@", "_").replace(".", "_")
```

**app/providers/llm_router.py:**

`BaseLLMProvider` abstract class:
`async def complete(system_prompt: str, user_prompt: str, max_tokens: int = 4096) -> str`

`OllamaProvider(BaseLLMProvider)`:
- POST {OLLAMA_HOST}/api/generate, model="llama3.2", stream=False
- Returns response["response"]

`GeminiProvider(BaseLLMProvider)`:
- google.generativeai, model="gemini-1.5-flash"
- Returns response.text

`GroqProvider(BaseLLMProvider)`:
- groq.AsyncGroq, model="llama-3.1-70b-versatile"
- Returns response.choices[0].message.content

`LLMRouter` class:
- `async initialize()`: check Ollama (2s timeout) → Gemini → Groq → RuntimeError
  Log which provider selected at INFO level
- `async complete(system, user, max_tokens=4096) -> str`:
  Wrap call in `asyncio.timeout(30)` — raise ResearchAgentError on timeout
  Use `with_backoff` (2 retries, 1s base) around provider.complete()
- `get_provider_name() -> str`

Module singleton: `llm_router = LLMRouter(get_settings())`
Dependency: `def get_llm_router() -> LLMRouter: return llm_router`

#### Verification
```bash
cd backend
uvicorn app.main:app --port 8000
# Terminal must log one of:
# INFO: LLM: Using Ollama (local)
# INFO: LLM: Using Gemini Flash
# INFO: LLM: Using Groq Llama3

python3 -c "
from app.providers.llm_router import LLMRouter, OllamaProvider, GeminiProvider, GroqProvider
for cls in [OllamaProvider, GeminiProvider, GroqProvider]:
    assert hasattr(cls, 'complete'), f'{cls.__name__} missing complete'
    print(f'OK: {cls.__name__}')
"
```

---

### Task 1.4 — Search Client and Researcher Agent
**Status:** [x] done
**Commit:** `feat(backend): Tavily search client and researcher agent`

#### Must Implement

**app/core/exceptions.py** — full hierarchy:
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

**app/providers/search_client.py:**

`SearchResult` Pydantic model: url(str), title(str), content(str), score(float)

`TavilySearchClient`:
- `__init__(settings)`: httpx.AsyncClient base_url="https://api.tavily.com" timeout=30.0
- `async search(query, max_results=8) -> list[SearchResult]`:
  POST /search: {api_key, query, max_results, search_depth="advanced",
  include_raw_content=True}
  Parse response["results"]. Raise SearchClientError with context on failure.
- `async close()`, async context manager

**app/agents/researcher.py:**

`ResearchAgent`:
- `__init__(request, workspace_slug, email_slug, llm_router, search_client, settings)`
  Note: email_slug is the directory-safe user id (user@gmail.com → user_gmail_com)
- `async run() -> list[DocumentSource]`:
  1. Create dirs via WorkspaceRepository (not directly)
  2. `await _generate_sub_queries()` → list[str]
  3. Cap concurrency: `asyncio.Semaphore(5)`
     `asyncio.gather(*[bounded(search(q)) for q in queries])`
  4. Flatten, deduplicate by URL (keep highest score)
  5. Save each via WorkspaceRepository.save_source()
  6. Build DocumentSource list, log count with request_id
  7. Return list[DocumentSource]
- `async _generate_sub_queries() -> list[str]`:
  system: "Return ONLY a JSON array of strings. No other text."
  user: "Generate 5 targeted search queries for: {topic} formatted as: {format}"
  Strip fences, json.loads(). Raise ResearchAgentError on parse failure.

#### Verification
```bash
cd backend
python3 -c "
import asyncio
from app.core.config import get_settings
from app.providers.search_client import TavilySearchClient

async def test():
    async with TavilySearchClient(get_settings()) as client:
        results = await client.search('electric vehicles 2024', max_results=3)
        assert len(results) > 0
        assert results[0].url.startswith('http')
        print(f'Search OK: {len(results)} results: {results[0].title[:50]}')

asyncio.run(test())
"
```

---

### Task 1.5 — Synthesizer Agent
**Status:** [x] done
**Commit:** `feat(backend): synthesizer agent with JSON repair retry logic`

#### Must Implement

**app/agents/synthesizer.py:**

`SynthesizerAgent`:
- `__init__(request, workspace_slug, email_slug, llm_router, workspace_repo, settings)`
  Note: email_slug is the directory-safe user id
- `async run(sources: list[DocumentSource]) -> DashboardPayload`:
  1. Build context: `## {title}\nURL: {url}\n\n{snippet[:2000]}\n\n---\n` per source
  2. Token guard: if total context > 80,000 chars, truncate to top-scoring sources
  3. Call `_build_synthesis_prompt(context)` → (system, user)
  4. Call `llm_router.complete(system, user, max_tokens=4096)` wrapped in with_backoff
  5. Call `_parse_llm_response(raw)` → DashboardPayload
  6. Add topic_metadata with generated_at=datetime.utcnow()
  7. Save via workspace_repo.save_payload(email_slug, slug, payload)
  8. Return DashboardPayload

- `_build_synthesis_prompt(context) -> tuple[str, str]`:
  system: "Return ONLY a valid JSON object. No markdown fences. No explanation.
           Raw JSON only. Your entire response must be parseable by json.loads()."
  user includes:
  a) Exact JSON schema shape with all fields
  b) Format instructions:
     COMPARISON → 2 tables + 1 chart + 1 list
     SWOT → 4 lists (Strengths, Weaknesses, Opportunities, Threats)
     TIMELINE → 3 lists with chronological entries
     PROS_CONS → 2 lists (Pros, Cons) + 1 comparison table
  c) Source context
  d) "Return ONLY the JSON. No other text."

- `_parse_llm_response(raw: str) -> DashboardPayload`:
  1. Strip whitespace, remove ```json and ``` fences
  2. json.loads() → on JSONDecodeError call _attempt_json_repair(raw)
  3. json.loads() on repaired → on failure raise SynthesizerError(context={"raw": raw[:500]})
  4. DashboardPayload(**parsed) → on ValidationError raise SynthesizerError
  5. Return validated payload

- `async _attempt_json_repair(broken: str) -> str`:
  Prompt LLM: "Fix this malformed JSON. Return ONLY valid JSON:\n{broken}"

#### Verification
```bash
cd backend
python3 -c "
from app.agents.synthesizer import SynthesizerAgent
for m in ['run','_build_synthesis_prompt','_parse_llm_response','_attempt_json_repair']:
    assert hasattr(SynthesizerAgent, m), f'Missing: {m}'
    print(f'OK: {m}')
"
```

---

### Task 1.6 — Vector Store and Notebook Service
**Status:** [x] done
**Commit:** `feat(backend): ChromaDB vector store with workspace isolation and notebook RAG`

#### Must Implement

**app/services/vector_store.py:**

`VectorStoreService`:
- `__init__(settings)`: stores settings
- `_get_collection(email_slug, workspace_slug)`:
  `chromadb.PersistentClient(path=str(Path(STORAGE_ROOT)/email_slug/slug/"chroma_db"))`
  NEVER use chromadb.Client() — that is the deprecated in-memory version.
  Collection name: f"nexus_{email_slug}_{slug}"
  Each user+workspace gets its own isolated collection. Never share.
- `_chunk_text(text, chunk_size=500, overlap=50) -> list[str]`
- `async ingest(documents, email_slug, workspace_slug) -> int`:
  Wrap ALL chromadb calls in `asyncio.run_in_executor(None, fn)`
  id = f"{doc.id}_chunk_{i}" for each chunk
  metadata = {source_id, url, chunk_index, email_slug}
  Return total chunks ingested
- `async query(question, email_slug, workspace_slug, n_results=5) -> list[RetrievedChunk]`:
  Wrap in run_in_executor. Return sorted by distance ascending.

**app/services/notebook.py:**

`NotebookService`:
- `__init__(llm_router, vector_store)`
- `async answer(query: NotebookQuery, user_email: str) -> NotebookResponse`:
  email_slug = email_to_slug(user_email)  # from app.core.config
  1. vector_store.query(question, email_slug, slug, n_results=5)
  2. Empty → NotebookResponse(needs_web_search=True, confidence_score=0.0,
     answer="No relevant information found.", sources=[])
  3. confidence = avg(1 - chunk.distance/2) for each chunk
  4. system: "Answer ONLY using provided context. If insufficient: INSUFFICIENT_CONTEXT"
  5. user: f"Context:\n{chunks}\n\nQuestion: {question}"
  6. needs_web_search = "INSUFFICIENT_CONTEXT" in response or confidence < 0.3
  7. Return NotebookResponse

#### Verification
```bash
cd backend
python3 -c "
from app.services.vector_store import VectorStoreService
from app.services.notebook import NotebookService
for m in ['_get_collection','_chunk_text','ingest','query']:
    assert hasattr(VectorStoreService, m), f'Missing: {m}'
    print(f'OK: VectorStoreService.{m}')
assert hasattr(NotebookService, 'answer')
print('OK: NotebookService.answer')
vs = VectorStoreService.__new__(VectorStoreService)
chunks = vs._chunk_text('a' * 1200)
assert len(chunks) > 1
print(f'Chunking OK: {len(chunks)} chunks')
"
```

---

### Task 1.7 — SQLite Database + Job Persistence + Orchestrator
**Status:** [x] done
**Commit:** `feat(backend): SQLite persistence, job registry, and orchestrator`

#### Must Implement

**app/models/db_models.py** — SQLAlchemy ORM models:
```python
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    google_id: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]
    avatar_url: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[str] = mapped_column(primary_key=True)  # UUID
    user_email: Mapped[str] = mapped_column(index=True)
    status: Mapped[str]  # pending/running/complete/failed
    progress_message: Mapped[str] = mapped_column(default="")
    workspace_slug: Mapped[str | None]
    error: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow,
                                                  onupdate=datetime.utcnow)
```

**app/services/database.py:**
- Async SQLAlchemy engine: `create_async_engine(DATABASE_URL)`
- `async_session_maker` factory
- `async def create_tables()`: called on startup
- `async def get_db()`: FastAPI dependency yielding AsyncSession
- `async def heal_stale_jobs(db)`: sets all RUNNING/PENDING → FAILED on startup

**app/agents/orchestrator.py:**

`def slugify(topic: str) -> str`:
lowercase, spaces→hyphens, strip non-alphanumeric except hyphens,
collapse hyphens, strip edges, max 60 chars, verify `^[a-z0-9-]+$`.

`def resolve_slug_collision(email_slug: str, slug: str, storage_root: str) -> str`:
If `storage/{email_slug}/{slug}/` exists: try `{slug}-2`, `{slug}-3`, etc.

`ResearchOrchestrator`:
- `__init__(settings, db_session_factory)`: stores both
- `async run_research(request: ResearchRequest, user_email: str, db: AsyncSession) -> str`:
  The router passes current_user.email as user_email — orchestrator never calls get_current_user itself.
  1. job_id = str(uuid4()), request_id = job_id[:8]
  2. email_slug = email_to_slug(user_email)
  3. slug = resolve_slug_collision(email_slug, slugify(request.topic), STORAGE_ROOT)
  4. Insert Job row: status=PENDING, user_email=user_email
  5. Log: f"[{request_id}] Starting: {request.topic}"
  6. Update Job: status=RUNNING, message="Generating search queries..."
  7. async with TavilySearchClient(settings) as client:
       researcher = ResearchAgent(request, slug, email_slug, llm_router, client, settings)
       sources = await researcher.run()
  8. Update: message="Synthesizing findings..."
  9. synthesizer = SynthesizerAgent(request, slug, email_slug, llm_router, workspace_repo, settings)
     payload = await synthesizer.run(sources)
  10. Update: message="Building knowledge base..."
  11. await vector_store.ingest(sources, email_slug, slug)
  12. Update: status=COMPLETE, workspace_slug=slug, message="Research complete."
  13. Return job_id
  On ANY exception: update Job status=FAILED, error=str(e), log ERROR, re-raise

- `async get_job_status(job_id, user_email, db) -> ResearchJobStatus`:
  Query Job by id AND user_email (users can only see their own jobs)
  Raise WorkspaceNotFoundError if not found

Module singleton: `orchestrator = ResearchOrchestrator(get_settings(), async_session_maker)`
Dependency: `def get_orchestrator() -> ResearchOrchestrator: return orchestrator`

**app/routers/research.py:**
- `POST /research/run` (protected):
  Body: ResearchRequest
  Gets current_user via Depends(get_current_user)
  Passes current_user.email to orchestrator.run_research as BackgroundTask
  Returns: {"job_id": id, "message": "Research started"} status 202
- `GET /research/status/{job_id}` (protected):
  Gets current_user via Depends(get_current_user)
  Returns ResearchJobStatus for current_user.email's job only

**Full /health implementation in app/main.py:**
```python
@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    services = {}
    # Check DB
    try:
        await db.execute(text("SELECT 1"))
        services["database"] = "ok"
    except Exception:
        services["database"] = "unavailable"
    # Check LLM
    services["llm"] = "ok" if llm_router._provider else "unavailable"
    # Check storage
    services["storage"] = "ok" if Path(settings.STORAGE_ROOT).exists() else "unavailable"

    status = "degraded" if any(v != "ok" for v in services.values()) else "ok"
    http_status = 503 if services["database"] == "unavailable" else 200
    return JSONResponse(
        status_code=http_status,
        content={"status": status, "version": "1.0.0", "services": services}
    )
```

#### Verification
```bash
cd backend
uvicorn app.main:app --port 8000 &
sleep 3
curl -s http://localhost:8000/health | python3 -m json.tool
# Must show: status, version, services object with database/llm/storage keys

python3 -c "
from app.agents.orchestrator import slugify, resolve_slug_collision
assert slugify('AI in Healthcare!') == 'ai-in-healthcare'
assert slugify('  multiple   spaces  ') == 'multiple-spaces'
print('slugify OK')
"
```

---

### Task 1.8 — WorkspaceRepository
**Status:** [x] done
**Commit:** `feat(backend): WorkspaceRepository — all file operations abstracted`

#### Must Implement

**app/repository/workspace_repo.py** — the ONLY class that touches disk.
All agents and services call this. Nothing else touches files directly.

```python
class WorkspaceRepository:
    """
    Abstracts all workspace file system operations.
    Swap implementation here to move from local disk to Cloudflare R2.
    No other file touches disk directly.
    """

    def __init__(self, settings: Settings): ...

    async def save_payload(self, email_slug: str, slug: str,
                           payload: DashboardPayload) -> None:
        """Serialize DashboardPayload and write to storage/{email_slug}/{slug}/dashboard_payload.json"""

    async def load_payload(self, email_slug: str, slug: str) -> DashboardPayload:
        """Read and parse dashboard_payload.json. Raise WorkspaceNotFoundError if absent."""

    async def save_source(self, email_slug: str, slug: str,
                          filename: str, content: str) -> str:
        """Save raw markdown source. Returns local_path string."""

    async def load_source(self, email_slug: str, slug: str,
                          source_id: str) -> str:
        """Read raw source markdown. Raise WorkspaceNotFoundError if absent."""

    async def list_workspaces(self, email_slug: str) -> list[WorkspaceListItem]:
        """Scan storage/{email_slug}/ for dirs with dashboard_payload.json.
        Return WorkspaceListItem list sorted by generated_at desc."""

    async def delete_workspace(self, email_slug: str, slug: str) -> None:
        """Delete entire storage/{email_slug}/{slug}/ tree. Raise WorkspaceNotFoundError if absent."""

    async def ensure_workspace_dir(self, email_slug: str, slug: str) -> Path:
        """Create storage/{email_slug}/{slug}/raw_sources/ if not exists. Return base path."""
```

Path traversal protection — enforce in every method:
```python
def _safe_path(self, email_slug: str, slug: str) -> Path:
    """Build safe path and verify it is inside STORAGE_ROOT."""
    base = Path(self.settings.STORAGE_ROOT).resolve()
    path = (base / email_slug / slug).resolve()
    if not str(path).startswith(str(base)):
        raise WorkspaceNotFoundError(
            "Path traversal attempt detected",
            context={"email_slug": email_slug, "slug": slug}
        )
    return path
```

Use `aiofiles` for all reads and writes. No synchronous file I/O.

Module singleton: `workspace_repo = WorkspaceRepository(get_settings())`
Dependency: `def get_workspace_repo() -> WorkspaceRepository: return workspace_repo`

**app/routers/workspaces.py** (implement now, uses workspace_repo):
Each route: current_user via Depends(get_current_user), then
email_slug = email_to_slug(current_user.email) before calling workspace_repo.
- `GET /workspaces` (protected): workspace_repo.list_workspaces(email_slug)
- `GET /workspaces/{slug}` (protected): workspace_repo.load_payload(email_slug, slug)
- `DELETE /workspaces/{slug}` (protected): workspace_repo.delete_workspace(email_slug, slug)
- `GET /workspaces/{slug}/sources/{source_id}` (protected): workspace_repo.load_source(email_slug, slug, source_id)

#### Verification
```bash
cd backend
python3 -c "
from app.repository.workspace_repo import WorkspaceRepository
required = ['save_payload','load_payload','save_source','load_source',
            'list_workspaces','delete_workspace','ensure_workspace_dir','_safe_path']
for m in required:
    assert hasattr(WorkspaceRepository, m), f'Missing: {m}'
    print(f'OK: {m}')
print('WorkspaceRepository fully implemented')
"
```

---

### Task 1.9 — Google OAuth
**Status:** [x] done
**Commit:** `feat(backend): Google OAuth with session middleware and email allowlist`

#### Must Implement

**app/auth/router.py:**
```python
from authlib.integrations.starlette_client import OAuth, OAuthError
from starlette.middleware.sessions import SessionMiddleware

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)
```

Routes:
- `GET /auth/login`: redirect to Google OAuth authorization URL
- `GET /auth/callback`: receive Google code, exchange for token,
  extract userinfo from token (contains email, name, picture, sub),
  check email in ALLOWED_GOOGLE_EMAILS list,
  if not allowed: raise AuthError("Access denied", context={"email": email}),
  upsert user in DB (create if first login, update name/avatar if returning),
  store in session: {google_id, email, name, avatar_url},
  redirect to FRONTEND_ORIGIN
- `GET /auth/logout`: clear session, redirect to FRONTEND_ORIGIN/login
- `GET /auth/me`: return current user from session or 401

**app/auth/dependencies.py:**
```python
async def get_current_user(request: Request) -> AuthUser:
    """
    FastAPI dependency. Reads session, returns AuthUser.
    Raises HTTPException 401 if not authenticated.
    Used by Depends() on every protected route.
    """
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return AuthUser(**user)

# email_to_slug is defined in app/core/config.py — import from there
# from app.core.config import email_to_slug
```

Register SessionMiddleware in app/main.py:
```python
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET_KEY,
    https_only=False,  # set True in production
    same_site="lax",
)
```

**Google OAuth App setup (document in README):**
1. Go to console.cloud.google.com
2. Create a new project (or select existing)
3. APIs & Services → OAuth consent screen → External → fill in app name + email
4. APIs & Services → Credentials → Create Credentials → OAuth Client ID
5. Application type: Web application
6. Authorized redirect URIs: http://localhost:8000/auth/callback
7. Copy Client ID and Client Secret to .env

#### Verification
```bash
cd backend
uvicorn app.main:app --port 8000 &
sleep 2

# Test /auth/me without session → must return 401
curl -s http://localhost:8000/auth/me
# Expected: {"detail": "Not authenticated"}

# Test /auth/login → must return redirect to google.com
curl -s -I http://localhost:8000/auth/login | grep -i location
# Expected: Location: https://accounts.google.com/o/oauth2/...

python3 -c "
from app.auth.dependencies import get_current_user
from app.auth.router import oauth
from app.core.config import email_to_slug
print('Auth imports OK')
assert oauth.google is not None
print('Google OAuth client registered OK')
assert email_to_slug('user@gmail.com') == 'user_gmail_com'
print('email_to_slug OK')
"
```

---

### Task 1.10 — All API Routes Protected
**Status:** [ ] todo
**Commit:** `feat(backend): all routes protected, notebook router complete`

#### Must Implement

Every route in research.py, workspaces.py, and notebook.py must have:
```python
current_user: AuthUser = Depends(get_current_user)
```

**app/routers/notebook.py:**
- `POST /notebook/query` (protected):
  Body: NotebookQuery
  Calls notebook_service.answer(query, user_email=current_user.email)
  Returns NotebookResponse
- `POST /notebook/search-and-answer` stub (returns 501 Not Implemented for now)

Verify every endpoint returns 401 without a valid session:
```bash
curl -s http://localhost:8000/workspaces
# Must return 401

curl -s http://localhost:8000/research/status/fake-id
# Must return 401

curl -s -X POST http://localhost:8000/notebook/query \
  -H "Content-Type: application/json" \
  -d '{"workspace_slug":"test","question":"hello"}'
# Must return 401
```

#### Verification
```bash
cd backend
uvicorn app.main:app --port 8000 &
sleep 2

for endpoint in "/workspaces" "/research/status/fake"; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000$endpoint)
  echo "$endpoint → $STATUS (expected 401)"
  [ "$STATUS" = "401" ] || echo "FAIL: expected 401 got $STATUS"
done

STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/notebook/query \
  -H "Content-Type: application/json" -d '{"workspace_slug":"x","question":"y"}')
echo "/notebook/query → $STATUS (expected 401)"
```

---

## PHASE 2 — FRONTEND

---

### Task 2.1 — Next.js Project Setup
**Status:** [ ] todo
**Commit:** `feat(frontend): Next.js setup, auth, types, API client, Zustand store`

#### Must Implement

Initialize (run from repo root):
```bash
npx create-next-app@latest frontend --typescript --tailwind --eslint --app --no-src-dir
cd frontend
npm install zustand recharts lucide-react clsx tailwind-merge next-auth@beta
npx shadcn-ui@latest init
npx shadcn-ui@latest add button card badge dialog scroll-area separator tabs toast progress avatar
```

**auth.ts** (at frontend root):
```typescript
import NextAuth from "next-auth"
import Google from "next-auth/providers/google"

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [Google],
  callbacks: {
    async jwt({ token, account, profile }) {
      if (account) {
        token.email = profile?.email
        token.accessToken = account.access_token
      }
      return token
    },
    async session({ session, token }) {
      session.user.email = token.email as string
      session.accessToken = token.accessToken as string
      return session
    },
  },
  pages: { signIn: "/login" },
})
```

**src/types/next-auth.d.ts** — augment next-auth Session type:
```typescript
import "next-auth"
declare module "next-auth" {
  interface Session {
    accessToken?: string
  }
}
declare module "next-auth/jwt" {
  interface JWT {
    accessToken?: string
  }
}
```
This file must exist or `npm run build` will throw TypeScript errors on `session.accessToken`.

**middleware.ts** (at frontend root):
```typescript
import { auth } from "./auth"
export default auth((req) => {
  const isLoggedIn = !!req.auth
  const isLoginPage = req.nextUrl.pathname.startsWith("/login")
  const isAuthRoute = req.nextUrl.pathname.startsWith("/api/auth")
  if (!isLoggedIn && !isLoginPage && !isAuthRoute) {
    return Response.redirect(new URL("/login", req.nextUrl))
  }
})
export const config = { matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"] }
```

**src/app/api/auth/[...nextauth]/route.ts:**
```typescript
import { handlers } from "@/auth"
export const { GET, POST } = handlers
```

**src/lib/types.ts** — mirrors all backend schemas:
```typescript
export enum ComponentType { TABLE = "table", CHART = "chart", LIST = "list" }
export enum ChartStyle { BAR = "bar", LINE = "line", PIE = "pie" }
export enum ExtensivenesLevel { QUICK = "quick", DEEP = "deep" }
export enum FormatPreference {
  TIMELINE = "timeline", SWOT = "swot",
  PROS_CONS = "pros_cons", COMPARISON = "comparison"
}
export enum JobStatus {
  PENDING = "pending", RUNNING = "running",
  COMPLETE = "complete", FAILED = "failed"
}
export interface TopicMetadata {
  topic: string; extensiveness: string; format_preference: string;
  generated_at: string; schema_version: string;
}
export interface MatrixComponent {
  section_title: string; component_type: ComponentType;
  headers?: string[]; rows?: string[][];
  chart_style?: ChartStyle; data?: Record<string, unknown>[];
  description?: string;
}
export interface DownloadedImage { alt: string; local_url: string; }
export interface DocumentSource {
  id: string; title: string; url: string; local_path: string;
  snippet: string; downloaded_images: DownloadedImage[];
}
export interface DashboardPayload {
  topic_metadata: TopicMetadata;
  executive_summary: string;
  matrix_data: MatrixComponent[];
  document_library: DocumentSource[];
}
export interface ResearchRequest {
  topic: string; extensiveness: ExtensivenesLevel; format_preference: FormatPreference;
}
export interface ResearchJobStatus {
  job_id: string; status: JobStatus; progress_message: string;
  workspace_slug?: string; error?: string;
  created_at: string; updated_at: string;
}
export interface NotebookQuery { workspace_slug: string; question: string; }
export interface RetrievedChunk {
  content: string; source_id: string; url: string;
  chunk_index: number; distance: number;
}
export interface NotebookResponse {
  answer: string; sources: RetrievedChunk[];
  confidence_score: number; needs_web_search: boolean;
}
export interface WorkspaceListItem { slug: string; topic: string; generated_at: string; }
```

**src/lib/api.ts** — typed client, attaches session token to every request:
```typescript
import type { ResearchRequest, ResearchJobStatus, DashboardPayload,
              WorkspaceListItem, NotebookQuery, NotebookResponse } from "@/lib/types"

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message) }
}

async function request<T>(path: string, token?: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { "Authorization": `Bearer ${token}` } : {}),
    },
    ...init,
  })
  if (!res.ok) throw new ApiError(res.status, await res.text())
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const createApi = (token: string) => ({
  runResearch: (body: ResearchRequest) =>
    request<{ job_id: string }>("/research/run", token,
      { method: "POST", body: JSON.stringify(body) }),
  getJobStatus: (jobId: string) =>
    request<ResearchJobStatus>(`/research/status/${jobId}`, token),
  listWorkspaces: () =>
    request<WorkspaceListItem[]>("/workspaces", token),
  getWorkspace: (slug: string) =>
    request<DashboardPayload>(`/workspaces/${slug}`, token),
  deleteWorkspace: (slug: string) =>
    request<void>(`/workspaces/${slug}`, token, { method: "DELETE" }),
  queryNotebook: (body: NotebookQuery) =>
    request<NotebookResponse>("/notebook/query", token,
      { method: "POST", body: JSON.stringify(body) }),
})
```

**src/lib/utils.ts:**
```typescript
import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"
export function cn(...inputs: ClassValue[]) { return twMerge(clsx(inputs)) }
export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short" })
}
export function getDomain(url: string): string {
  try { return new URL(url).hostname.replace("www.", "") } catch { return url }
}
```

**src/store/workspace.ts:**
```typescript
import { create } from "zustand"
import type { WorkspaceListItem } from "@/lib/types"
import { createApi } from "@/lib/api"

interface WorkspaceStore {
  activeSlug: string | null
  workspaces: WorkspaceListItem[]
  isLoading: boolean
  error: string | null
  setActiveSlug: (slug: string | null) => void
  fetchWorkspaces: (token: string) => Promise<void>
  removeWorkspace: (slug: string) => void
}

export const useWorkspaceStore = create<WorkspaceStore>((set) => ({
  activeSlug: null,
  workspaces: [],
  isLoading: false,
  error: null,
  setActiveSlug: (slug) => set({ activeSlug: slug }),
  fetchWorkspaces: async (token) => {
    set({ isLoading: true, error: null })
    try {
      const workspaces = await createApi(token).listWorkspaces()
      set({ workspaces, isLoading: false })
    } catch (e) {
      set({ error: String(e), isLoading: false })
    }
  },
  removeWorkspace: (slug) =>
    set((state) => ({ workspaces: state.workspaces.filter((w) => w.slug !== slug) })),
}))
```

**frontend/.env.local:**
```
NEXT_PUBLIC_API_URL=http://localhost:8000
AUTH_GOOGLE_ID=your_google_client_id
AUTH_GOOGLE_SECRET=your_google_client_secret
AUTH_SECRET=random_32_char_string
```

#### Verification
```bash
cd frontend
npm run build
# Zero TypeScript errors

grep -c "export interface\|export enum" src/lib/types.ts
# Must be 16 or more
```

---

### Task 2.2 — App Shell, Sidebar, Login Page
**Status:** [ ] todo
**Commit:** `feat(frontend): app shell, sidebar, login page, design system`

#### Must Implement

**tailwind.config.ts** — add custom colors:
```typescript
extend: {
  colors: {
    base: "#0a0a0f", surface: "#111118", card: "#13131a",
    border: "#1e1e2e", accent: "#6366f1", muted: "#64748b", primary: "#e2e8f0",
  }
}
```

**src/app/login/page.tsx:**
```typescript
import { signIn } from "@/auth"
export default function LoginPage() {
  return (
    <main className="min-h-screen bg-base flex items-center justify-center">
      <div className="text-center space-y-6">
        <h1 className="text-3xl font-bold text-primary">NEXUS</h1>
        <p className="text-muted">Autonomous Research Engine</p>
        <form action={async () => { "use server"; await signIn("google") }}>
          <button type="submit" className="...">
            Sign in with Google
          </button>
        </form>
      </div>
    </main>
  )
}
```

**src/components/layout/AppShell.tsx:**
```typescript
interface AppShellProps {
  children: React.ReactNode
  showNotebook: boolean
  onToggleNotebook: () => void
}
```
- Layout: `flex h-screen bg-base overflow-hidden`
- Left: Sidebar 240px, bg-surface, border-r border-border
- Center: flex-1 overflow-auto, renders children
- Top header: 56px, bg-surface, border-b border-border
  Left: "NEXUS" in accent color + "Research Engine" subtitle
  Right: MessageSquare icon + "Research Assistant" toggle button
         + user avatar from session + sign out button

**src/components/layout/Sidebar.tsx:**
- Gets session token from `useSession()`, calls fetchWorkspaces(token) on mount
- "New Research" button at top → router.push("/")
- Each workspace: topic truncated to 28 chars, date in muted
  Active: bg-accent/10. Trash icon on hover → deleteWorkspace + removeWorkspace
- Empty: "No workspaces yet. Start your first research."

**src/app/layout.tsx:** wrap children in AppShell with useState showNotebook.
**src/app/page.tsx:** `export default function Home() { return <BlueprintForm /> }`

#### Verification
```bash
cd frontend && npm run dev &
sleep 5
curl -s http://localhost:3000/login | grep -i "nexus"
# Must find NEXUS branding
# Visiting http://localhost:3000 (not login) must redirect to /login
npm run build
```

---

### Task 2.3 — Blueprint Configurator
**Status:** [ ] todo
**Commit:** `feat(frontend): blueprint configurator with job polling and redirect`

#### Must Implement

**src/components/configurator/BlueprintForm.tsx**

State:
```typescript
const [topic, setTopic] = useState("")
const [extensiveness, setExtensiveness] = useState<ExtensivenesLevel>(ExtensivenesLevel.QUICK)
const [formatPref, setFormatPref] = useState<FormatPreference>(FormatPreference.COMPARISON)
const [phase, setPhase] = useState<"idle"|"running"|"complete"|"error">("idle")
const [jobId, setJobId] = useState<string|null>(null)
const [progressMsg, setProgressMsg] = useState("")
const [errorMsg, setErrorMsg] = useState<string|null>(null)
const { data: session } = useSession()
```

On submit:
1. Validate topic.trim().length >= 3 → inline error if not
2. api = createApi(session.accessToken)
3. Call api.runResearch({topic, extensiveness, format_preference: formatPref})
4. Store job_id, set phase="running"
5. Poll every 2000ms: api.getJobStatus(jobId)
   Update progressMsg. On COMPLETE: router.push(`/workspace/${workspace_slug}`)
   On FAILED: phase="error", errorMsg=response.error
6. Clear polling interval in cleanup (useEffect return)

Format cards with lucide-react icons:
- TIMELINE → Clock, "Timeline"
- SWOT → Grid2X2, "SWOT Analysis"
- PROS_CONS → Scale, "Pros & Cons"
- COMPARISON → Table2, "Comparison Matrix"

Layout: centered card max-w-[560px] on dark page.
Not a generic form — feels like a mission briefing panel.

#### Verification (manual)
```
1. http://localhost:3000 shows BlueprintForm (after Google login)
2. Empty submit → inline validation error
3. Real topic → progress messages update → redirects on complete
```

---

### Task 2.4 — Dashboard Canvas
**Status:** [ ] todo
**Commit:** `feat(frontend): dashboard canvas with all three spaces and visualizations`

#### Must Implement

**src/app/workspace/[slug]/page.tsx:**
- Gets session, fetches api.getWorkspace(slug) with token
- Loading: shimmer skeleton for all 3 spaces
- Error: "Workspace not found" with back button (wrap in try/catch)
- schema_version check: if !== "1.0" show warning banner
- Renders: `<DashboardCanvas payload={payload} />`

**src/components/dashboard/DashboardCanvas.tsx:**
- Header: topic + generated_at + schema_version badge
- 3-col grid on lg (25/50/25), 1-col on mobile
- Left: ExecutiveBrief, Center: DataMatrix, Right: DocumentLibrary

**ExecutiveBrief.tsx:**
- border-l-4 border-accent card
- "Executive Brief" label in muted small caps
- Split executive_summary on "\n\n" → each as `<p>`
- Badges for extensiveness and format_preference

**DataMatrix.tsx:**
- "Data Matrix" label
- Each MatrixComponent → TableBlock | ChartBlock | ListBlock
- Wrap each block in React error boundary:
```typescript
class ChartErrorBoundary extends React.Component {
  state = { hasError: false }
  static getDerivedStateFromError() { return { hasError: true } }
  render() {
    if (this.state.hasError)
      return <div className="text-muted p-4">Chart failed to render.</div>
    return this.props.children
  }
}
```

**TableBlock.tsx:** `<table>` with zebra striping, overflow-x-auto
**ChartBlock.tsx:** Recharts BAR/LINE (fallback to BAR), height=280, color=#6366f1
**ListBlock.tsx:** row[0] as title, row[1] as description, dividers

**DocumentLibrary.tsx:**
- "Source Library" + count badge
- Each doc: card with title, getDomain(url) badge, 3-line snippet
- Anchor tag, target="_blank" rel="noopener noreferrer"

#### Verification (manual)
```
1. Complete a research run, navigate to /workspace/[slug]
2. All 3 spaces render with real data
3. At least one chart or table renders
4. No console errors in devtools
5. npm run build passes
```

---

### Task 2.5 — Notebook Panel
**Status:** [ ] todo
**Commit:** `feat(frontend): notebook panel with RAG Q&A and retry alert`

#### Must Implement

**src/components/notebook/NotebookPanel.tsx:**
```typescript
interface NotebookPanelProps { workspaceSlug: string; isOpen: boolean }
interface Message {
  id: string; role: "user"|"assistant"; content: string
  sources?: RetrievedChunk[]; confidence?: number; needsWebSearch?: boolean
}
```
- Fixed right panel, w-[320px], CSS transition translateX
- On submit: add user msg → api.queryNotebook → add assistant msg
  → if needsWebSearch: add RetryAlert message → scroll to bottom
- Gets session token from useSession()

**ChatThread.tsx:**
- User: right-aligned bg-accent bubble
- Assistant: left-aligned bg-card bubble
- Confidence bar: green >0.7, yellow 0.3-0.7, red <0.3
- Empty: BookOpen + "Ask a question about your research"
- Auto-scroll with useEffect + scrollIntoView

**QueryInput.tsx:** Enter submits, Shift+Enter newline, ArrowRight icon, disabled when loading

**RetryAlert.tsx:** inline card (NOT modal), AlertCircle icon
"This answer needs more data. Run a quick web search?"
"Search the web" (accent) + "Dismiss" (ghost) buttons

Wire into workspace page: useState showNotebook, toggle from AppShell.

#### Verification (manual)
```
1. Toggle opens/closes panel with smooth CSS transition
2. Question returns answer with confidence bar
3. needsWebSearch=true shows RetryAlert inline
4. Dismiss removes it
```

---

## PHASE 3 — POLISH AND SHIP

---

### Task 3.1 — End-to-End Integration Test
**Status:** [ ] todo
**Commit:** `fix: integration test fixes and edge case handling`

#### Must Implement

Start both servers. Test every flow. Fix every bug before marking done.

**Happy path:**
1. Visit http://localhost:3000 → redirects to /login
2. Click "Sign in with Google" → Google OAuth → redirects back
3. Enter "Future of electric vehicles in Germany", Deep Dive, Comparison Matrix
4. Click Start Research → progress messages update
5. Redirects to /workspace/[slug]
6. All 3 spaces render with real content
7. Open Notebook → ask a question → answer returns with confidence bar
8. Sign out → redirects to /login

**Edge cases (all must work without crashing):**
- Empty topic submit → validation error, no API call
- Visit /workspace/nonexistent → error state with back button
- Delete workspace from sidebar → disappears immediately
- Refresh workspace page → data reloads correctly
- Unauthenticated API call → 401 returned
- Non-allowed Google email login → access denied message

Create **KNOWN_ISSUES.md** at repo root documenting any limitations.

---

### Task 3.2 — Empty States and Error Handling
**Status:** [ ] todo
**Commit:** `feat: empty states, error handling, and toast notifications`

#### Must Implement

**src/hooks/useToast.ts:**
```typescript
import { toast } from "@/components/ui/use-toast"
export function useToast() {
  return {
    success: (message: string) => toast({ title: message }),
    error: (message: string) => toast({ title: message, variant: "destructive" }),
  }
}
```

Empty states:
1. Sidebar: no workspaces → BookOpen + "No workspaces yet."
2. DataMatrix: no components → "No structured data generated."
3. DocumentLibrary: no sources → "No sources saved."
4. ChatThread: no messages → MessageSquare + "Ask a question..."

Error states:
1. Workspace 404 → AlertCircle + "Workspace not found." + back button
2. Research failed → error message in red in BlueprintForm
3. Backend unreachable → fixed top banner "Cannot connect to backend."

Toasts:
- Research complete → "Research complete! Workspace ready."
- Workspace deleted → "Workspace deleted."
- Research failed → error toast

---

### Task 3.3 — Makefile, README, Dockerfile
**Status:** [ ] todo
**Commit:** `docs: Makefile, README, and Dockerfile`

#### Must Implement

Root **Makefile:**
```makefile
.PHONY: install dev dev-backend dev-frontend test lint clean

install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

dev:
	@echo "Starting Nexus..."
	@(cd backend && uvicorn app.main:app --reload --port 8000 & \
	  cd frontend && npm run dev & \
	  wait)

test:
	cd backend && pytest tests/ -v

lint:
	cd backend && ruff check app/
	cd frontend && npm run lint

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
```

Root **Dockerfile** (for Render deployment):
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
RUN mkdir -p storage
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Root **README.md** sections:
1. What Nexus is (two sentences)
2. Prerequisites: Python 3.11+, Node 18+, Google Cloud Console OAuth App, API keys
3. Google OAuth App setup (step by step)
4. Quickstart: clone → make install → copy .env → fill keys → make dev
5. LLM Router: Ollama → Gemini → Groq fallback
6. Architecture: decoupled, JSON contract, ChromaDB isolation, WorkspaceRepository
7. MVP Features list
8. Deploy: Render (backend) + Vercel (frontend) + Cloudflare R2 (swap Task 4.1)
9. V2 Roadmap

---

## PHASE 4 — DEPLOY (one afternoon, after MVP complete)

---

### Task 4.1 — Swap WorkspaceRepository to Cloudflare R2
**Status:** [ ] todo
**Commit:** `feat(deploy): Cloudflare R2 storage backend`

#### Must Implement

Add to requirements.txt: `boto3==1.34.0`

Add to .env:
```
R2_ACCOUNT_ID=
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_BUCKET_NAME=nexus-workspaces
```

Create `app/repository/r2_workspace_repo.py` implementing
the same WorkspaceRepository interface using boto3 S3 client
pointing at Cloudflare R2 endpoint:
`https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com`

Switch the singleton in workspace_repo.py based on env var:
```python
USE_R2 = os.getenv("USE_R2", "false").lower() == "true"
workspace_repo = R2WorkspaceRepository(settings) if USE_R2 else WorkspaceRepository(settings)
```

No other file changes. Zero agents or services need to know about this swap.

---

### Task 4.2 — Deploy Backend to Render
**Status:** [ ] todo
**Commit:** `feat(deploy): Render deployment configuration`

#### Must Implement

Create `render.yaml` at repo root:
```yaml
services:
  - type: web
    name: nexus-backend
    runtime: docker
    dockerfilePath: ./Dockerfile
    envVars:
      - key: USE_R2
        value: "true"
      - key: GEMINI_API_KEY
        sync: false
      - key: TAVILY_API_KEY
        sync: false
      - key: GOOGLE_CLIENT_ID
        sync: false
      - key: GOOGLE_CLIENT_SECRET
        sync: false
      - key: ALLOWED_GOOGLE_EMAILS
        sync: false
      - key: SESSION_SECRET_KEY
        sync: false
      - key: R2_ACCOUNT_ID
        sync: false
      - key: R2_ACCESS_KEY_ID
        sync: false
      - key: R2_SECRET_ACCESS_KEY
        sync: false
      - key: R2_BUCKET_NAME
        value: nexus-workspaces
      - key: FRONTEND_ORIGIN
        sync: false
```

Update Google OAuth App callback URL to Render backend URL.
Update FRONTEND_ORIGIN to Vercel URL.

---

### Task 4.3 — Deploy Frontend to Vercel
**Status:** [ ] todo
**Commit:** `feat(deploy): Vercel deployment configuration`

#### Must Implement

Create `vercel.json` in frontend/:
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "framework": "nextjs"
}
```

Update frontend/.env.local with production values:
```
NEXT_PUBLIC_API_URL=https://your-render-url.onrender.com
AUTH_GOOGLE_ID=your_google_client_id
AUTH_GOOGLE_SECRET=your_google_client_secret
AUTH_SECRET=your_auth_secret
```

Deploy: `npx vercel --prod` from frontend/ directory.
Set same env vars in Vercel dashboard.

---

## PHASE 5 — V2 FEATURES

---

### Task 5.1 — Internet Safety Loop
**Status:** [ ] todo
**Commit:** `feat(v2): internet safety loop — web search fallback for notebook`

Add to api.ts: `searchAndAnswer` method → POST /notebook/search-and-answer
Backend: run Tavily search on question, re-ingest, re-answer, return NotebookResponse
Frontend: RetryAlert onConfirm calls searchAndAnswer, shows loading, adds new answer

---

### Task 5.2 — Click-to-Verify Citations
**Status:** [ ] todo
**Commit:** `feat(v2): click-to-verify citations with split-pane source viewer`

Backend: add paragraph_hash (SHA256) to ChromaDB metadata on ingest
         GET /workspaces/{slug}/sources/{source_id} → returns raw markdown
Frontend: CitationBadge chip on answers → click opens SourceViewer
          50/50 split: answer right, source left, matched chunk highlighted yellow

---

### Task 5.3 — Nexus Map
**Status:** [ ] todo
**Commit:** `feat(v2): Nexus Map with NetworkX entity extraction and ReactFlow`

Backend: GraphEngine extracts entities per workspace via LLM,
         NetworkX finds overlaps, returns GraphPayload (nodes + edges)
         GET /graph/global → GraphPayload
Frontend: npm install reactflow, /map page, NexusMap + EntityNode components
          "Nexus Map" link in Sidebar

---

### Task 5.4 — Scheduled Research Subscriptions
**Status:** [ ] todo
**Commit:** `feat(v2): scheduled research subscriptions with APScheduler`

Add apscheduler==3.10.4 to requirements.txt
SchedulerService: schedule workspace refresh, save changelog.json
Routes: POST/DELETE /workspaces/{slug}/subscribe, GET /workspaces/{slug}/changelog
Frontend: bell icon → SubscribeDialog, changelog in ExecutiveBrief

---

### Task 5.5 — PDF Export
**Status:** [ ] todo
**Commit:** `feat(v2): PDF export for dashboard workspaces`

Add weasyprint==62.3 to requirements.txt
GET /workspaces/{slug}/export/pdf → render HTML template → WeasyPrint → FileResponse
Frontend: download icon button → fetch → browser download

---

### Task 5.6 — Shareable Dashboard Links
**Status:** [ ] todo
**Commit:** `feat(v2): shareable read-only dashboard links`

Backend: POST /workspaces/{slug}/share → UUID token → share.json
         GET /share/{token} → DashboardPayload (no auth required)
Frontend: share icon → copy URL → toast
          /shared/[token]/page.tsx → read-only DashboardCanvas, no sidebar/notebook
          "Built with Nexus" footer
