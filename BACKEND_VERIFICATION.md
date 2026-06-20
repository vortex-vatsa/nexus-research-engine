# BACKEND_VERIFICATION.md — Phase 1 Backend Health Check
# Read this file completely before running anything.
# Run every step in order. Fix failures before proceeding to next step.
# Do not start Task 2.1 (frontend) until all 12 steps pass.
# After all steps pass, generate the summary report at the bottom.

---

## Instructions

1. Read this entire file first
2. Run each step from inside the `backend/` directory
3. After each step: report PASS or FAIL with the exact output
4. On any FAIL: diagnose and fix before continuing
5. After all 12 steps pass: generate the Summary Report
6. Stop and wait for user confirmation before touching any frontend task

---

## Step 1 — All Imports Resolve

```bash
cd backend && python3 -c "
from app.core.schemas import (
    ComponentType, ChartStyle, ExtensivenesLevel, FormatPreference, JobStatus,
    TopicMetadata, MatrixComponent, DownloadedImage, DocumentSource,
    DashboardPayload, ResearchRequest, ResearchJobStatus,
    NotebookQuery, RetrievedChunk, NotebookResponse, WorkspaceListItem, AuthUser
)
from app.core.config import get_settings, email_to_slug
from app.core.exceptions import (
    NexusBaseError, SearchClientError, ResearchAgentError, SynthesizerError,
    VectorStoreError, NotebookError, WorkspaceNotFoundError, AuthError
)
from app.providers.llm_router import LLMRouter, GeminiProvider, GroqProvider
from app.providers.search_client import TavilySearchClient
from app.agents.orchestrator import slugify, resolve_slug_collision
from app.agents.researcher import ResearchAgent
from app.agents.synthesizer import SynthesizerAgent
from app.services.vector_store import VectorStoreService
from app.services.notebook import NotebookService
from app.repository.workspace_repo import WorkspaceRepository
from app.auth.dependencies import get_current_user
from app.models.db_models import User, Job
print('ALL IMPORTS OK')
"
```

**Expected:** `ALL IMPORTS OK`

---

## Step 2 — Schema Tests Pass

```bash
cd backend && pytest tests/test_schemas.py -v
```

**Expected:** All tests pass, zero failures

---

## Step 3 — Ruff Lint Clean

```bash
cd backend && ruff check app/
```

**Expected:** No output (zero issues)

---

## Step 4 — Server Starts and Health Check Passes

```bash
cd backend
uvicorn app.main:app --port 8000 &
sleep 4
curl -s http://localhost:8000/health | python3 -m json.tool
```

**Expected:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "services": {
    "database": "ok",
    "llm": "ok",
    "storage": "ok"
  }
}
```
Database must be "ok". LLM must be "ok". Status must not be "degraded".

---

## Step 5 — Auth Endpoints Respond Correctly

```bash
cd backend

echo "Test 1: /auth/me without session must return 401"
CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/auth/me)
echo "/auth/me → $CODE (expected 401)"

echo "Test 2: /auth/login must redirect to Google"
curl -s -I http://localhost:8000/auth/login | grep -i location
```

**Expected:**
- `/auth/me` returns `401`
- Location header contains `accounts.google.com`

---

## Step 6 — All Protected Routes Return 401

```bash
cd backend

for endpoint in "/workspaces" "/research/status/fake-id"; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000$endpoint)
  echo "$endpoint → $CODE (expected 401)"
done

CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/notebook/query \
  -H "Content-Type: application/json" -d '{"workspace_slug":"x","question":"y"}')
echo "/notebook/query → $CODE (expected 401)"
```

**Expected:** All three endpoints return `401`

---

## Step 7 — Slugify Logic Correct

```bash
cd backend && python3 -c "
from app.agents.orchestrator import slugify

tests = [
    ('AI in Healthcare!', 'ai-in-healthcare'),
    ('  multiple   spaces  ', 'multiple-spaces'),
    ('Special @#\$% Characters', 'special-characters'),
    ('a' * 100, 'a' * 60),
]
all_passed = True
for input_val, expected in tests:
    result = slugify(input_val)
    if result == expected:
        print(f'PASS: slugify({input_val[:30]!r}) = {result!r}')
    else:
        print(f'FAIL: slugify({input_val[:30]!r}) = {result!r}, expected {expected!r}')
        all_passed = False
print('ALL SLUGIFY TESTS PASSED' if all_passed else 'SLUGIFY TESTS FAILED')
"
```

**Expected:** All 4 tests PASS

---

## Step 8 — email_to_slug Logic Correct

```bash
cd backend && python3 -c "
from app.core.config import email_to_slug

tests = [
    ('user@gmail.com', 'user_gmail_com'),
    ('aaryan.vatsa13@gmail.com', 'aaryan_vatsa13_gmail_com'),
    ('test.user@company.org', 'test_user_company_org'),
]
all_passed = True
for email, expected in tests:
    result = email_to_slug(email)
    if result == expected:
        print(f'PASS: email_to_slug({email!r}) = {result!r}')
    else:
        print(f'FAIL: email_to_slug({email!r}) = {result!r}, expected {expected!r}')
        all_passed = False
print('ALL EMAIL_TO_SLUG TESTS PASSED' if all_passed else 'EMAIL_TO_SLUG TESTS FAILED')
"
```

**Expected:** All 3 tests PASS

---

## Step 9 — Path Traversal Protection Works

```bash
cd backend && python3 -c "
from app.repository.workspace_repo import WorkspaceRepository
from app.core.config import get_settings
from app.core.exceptions import WorkspaceNotFoundError

repo = WorkspaceRepository(get_settings())

traversal_attempts = [
    ('../../etc', 'passwd'),
    ('../../../root', 'secret'),
    ('valid_user', '../other_user'),
]

all_passed = True
for user, slug in traversal_attempts:
    try:
        repo._safe_path(user, slug)
        print(f'FAIL: traversal not blocked for ({user!r}, {slug!r})')
        all_passed = False
    except WorkspaceNotFoundError:
        print(f'PASS: traversal blocked for ({user!r}, {slug!r})')
    except Exception as e:
        print(f'FAIL: wrong exception {type(e).__name__}: {e}')
        all_passed = False

print('ALL TRAVERSAL TESTS PASSED' if all_passed else 'TRAVERSAL TESTS FAILED')
"
```

**Expected:** All 3 traversal attempts blocked

---

## Step 10 — Live Tavily Search Works

```bash
cd backend && python3 -c "
import asyncio
from app.core.config import get_settings
from app.providers.search_client import TavilySearchClient

async def test():
    async with TavilySearchClient(get_settings()) as client:
        results = await client.search('solar energy trends 2024', max_results=3)
        assert len(results) > 0, 'No results returned'
        assert results[0].url.startswith('http'), 'Invalid URL format'
        assert results[0].title, 'Empty title'
        assert results[0].content, 'Empty content'
        print(f'PASS: {len(results)} results returned')
        print(f'  First: {results[0].title[:70]}')
        print(f'  URL:   {results[0].url}')
        print(f'  Score: {results[0].score:.3f}')

asyncio.run(test())
"
```

**Expected:** 3 results with titles, URLs, and scores

---

## Step 11 — Live LLM Call Works

```bash
cd backend && python3 -c "
import asyncio
from app.providers.llm_router import llm_router

async def test():
    await llm_router.initialize()
    provider = llm_router.get_provider_name()
    print(f'Active provider: {provider}')

    response = await llm_router.complete(
        system_prompt='You are a helpful assistant. Reply in one sentence only.',
        user_prompt='What is the capital of France?',
        max_tokens=50
    )
    assert len(response) > 0, 'Empty response'
    assert 'Paris' in response, f'Unexpected: {response}'
    print(f'PASS: LLM responded correctly')
    print(f'  Response: {response.strip()}')

asyncio.run(test())
"
```

**Expected:** Provider name logged, "Paris" in response

---

## Step 12 — Full End-to-End Pipeline Test

This step takes 60-90 seconds. It runs the complete research pipeline.

```bash
cd backend && python3 -c "
import asyncio, json
from pathlib import Path
from app.core.config import get_settings, email_to_slug
from app.core.schemas import ResearchRequest, ExtensivenesLevel, FormatPreference
from app.providers.llm_router import llm_router
from app.providers.search_client import TavilySearchClient
from app.agents.researcher import ResearchAgent
from app.agents.synthesizer import SynthesizerAgent
from app.services.vector_store import VectorStoreService
from app.repository.workspace_repo import WorkspaceRepository

async def test():
    settings = get_settings()
    await llm_router.initialize()
    print(f'LLM Provider: {llm_router.get_provider_name()}')

    request = ResearchRequest(
        topic='Benefits of solar energy',
        extensiveness=ExtensivenesLevel.QUICK,
        format_preference=FormatPreference.PROS_CONS
    )

    test_email = 'test@nexus.local'
    email_slug_val = email_to_slug(test_email)
    slug = 'benefits-of-solar-energy'
    workspace_repo = WorkspaceRepository(settings)
    vector_store = VectorStoreService(settings)

    print()
    print('--- Step A: Researcher Agent ---')
    async with TavilySearchClient(settings) as client:
        researcher = ResearchAgent(
            request, slug, email_slug_val, llm_router, client, settings
        )
        sources = await researcher.run()
    assert len(sources) > 0, 'FAIL: No sources found'
    print(f'PASS: {len(sources)} sources found')

    print()
    print('--- Step B: Synthesizer Agent ---')
    synthesizer = SynthesizerAgent(
        request, slug, email_slug_val, llm_router, workspace_repo, settings
    )
    payload = await synthesizer.run(sources)
    assert payload.executive_summary, 'FAIL: Empty executive summary'
    assert len(payload.matrix_data) > 0, 'FAIL: No matrix components'
    assert payload.topic_metadata.schema_version == '1.0', 'FAIL: Wrong schema version'
    print(f'PASS: Dashboard payload created')
    print(f'  Executive summary length: {len(payload.executive_summary)} chars')
    print(f'  Matrix components: {len(payload.matrix_data)}')
    print(f'  Document library: {len(payload.document_library)} sources')
    print(f'  Schema version: {payload.topic_metadata.schema_version}')

    print()
    print('--- Step C: ChromaDB Ingest ---')
    count = await vector_store.ingest(sources, email_slug_val, slug)
    assert count > 0, 'FAIL: No chunks ingested'
    print(f'PASS: {count} chunks ingested into ChromaDB')

    print()
    print('--- Step D: ChromaDB Query ---')
    chunks = await vector_store.query(
        'what are the main benefits of solar energy',
        email_slug_val, slug, n_results=3
    )
    assert len(chunks) > 0, 'FAIL: No chunks retrieved'
    print(f'PASS: {len(chunks)} chunks retrieved')
    print(f'  Top chunk distance: {chunks[0].distance:.4f}')
    print(f'  Top chunk preview: {chunks[0].content[:80]}...')

    print()
    print('--- Step E: Payload on Disk ---')
    payload_path = (
        Path(settings.STORAGE_ROOT) / email_slug_val / slug / 'dashboard_payload.json'
    )
    assert payload_path.exists(), f'FAIL: Payload not at {payload_path}'
    saved = json.loads(payload_path.read_text())
    assert saved['topic_metadata']['schema_version'] == '1.0'
    assert saved['executive_summary'], 'FAIL: Empty summary in saved file'
    print(f'PASS: Payload saved to {payload_path}')
    print(f'  Schema version on disk: {saved[\"topic_metadata\"][\"schema_version\"]}')

    print()
    print('--- Step F: WorkspaceRepository List ---')
    workspaces = await workspace_repo.list_workspaces(email_slug_val)
    assert any(w.slug == slug for w in workspaces), 'FAIL: Workspace not in list'
    print(f'PASS: Workspace appears in list ({len(workspaces)} total)')

    print()
    print('============================================')
    print('  ALL PIPELINE STEPS PASSED')
    print('============================================')
    print(f'  LLM Provider:       {llm_router.get_provider_name()}')
    print(f'  Sources found:      {len(sources)}')
    print(f'  Matrix components:  {len(payload.matrix_data)}')
    print(f'  ChromaDB chunks:    {count}')
    print(f'  Retrieved chunks:   {len(chunks)}')
    print(f'  Workspace saved:    {payload_path}')

asyncio.run(test())
"
```

**Expected:** All 6 sub-steps (A through F) pass with real data

---

## Summary Report

After all 12 steps pass, generate this report:

```
NEXUS BACKEND VERIFICATION REPORT
===================================
Date: [today]
Total steps: 12
Passed: [n]
Failed: [n]

Step Results:
  Step 1  — Imports:           PASS/FAIL
  Step 2  — Schema tests:      PASS/FAIL
  Step 3  — Ruff lint:         PASS/FAIL
  Step 4  — Health check:      PASS/FAIL
  Step 5  — Auth endpoints:    PASS/FAIL
  Step 6  — Route protection:  PASS/FAIL
  Step 7  — Slugify logic:     PASS/FAIL
  Step 8  — Email slug:        PASS/FAIL
  Step 9  — Path traversal:    PASS/FAIL
  Step 10 — Tavily search:     PASS/FAIL
  Step 11 — LLM call:          PASS/FAIL
  Step 12 — Full pipeline:     PASS/FAIL

Pipeline Details:
  Active LLM provider:    [name]
  Sources found:          [n]
  Matrix components:      [n]
  ChromaDB chunks:        [n]
  Payload saved at:       [path]
  Schema version:         1.0

Backend Status: READY FOR FRONTEND / NOT READY
```

Stop here. Do not start Task 2.1 until the user confirms.
