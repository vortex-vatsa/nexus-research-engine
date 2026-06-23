# FRONTEND_VERIFICATION.md — Complete Frontend Health Check
# Read this file completely before running anything.
# Run after EVERY frontend task completes — not just at the end.
# Do not proceed to the next task until current task passes all checks.

---

## How to Use This File

After every task (2.4, 2.5, 3.1, 3.2, 3.3):
1. Run the task-specific checks in Section A
2. Run the universal checks in Section B after every task
3. Fix all failures before proceeding
4. Generate the summary report and stop for user confirmation

---

## Prerequisites — Both Servers Must Be Running

**Terminal 1 — Backend:**
```bash
cd /Users/aaryanvatsa/Documents/projects/NEXUS_RESEARCH_ENGINE
source venv/bin/activate
cd backend
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd /Users/aaryanvatsa/Documents/projects/NEXUS_RESEARCH_ENGINE/frontend
npm run dev
```

Verify both are up before running any checks:
```bash
curl -s http://localhost:8000/health | python3 -m json.tool
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
# Backend must return JSON with status ok
# Frontend must return 200
```

---

## Section A — Task-Specific Checks

---

### Task 2.4 — Dashboard Canvas

#### Build Check
```bash
cd frontend && npm run build 2>&1 | grep -E "✓|Error|error" | head -20
# Must show zero TypeScript errors
```

#### File Existence Check
```bash
cd frontend && python3 -c "
import os
required = [
    'src/app/workspace/[slug]/page.tsx',
    'src/components/dashboard/DashboardCanvas.tsx',
    'src/components/dashboard/ExecutiveBrief.tsx',
    'src/components/dashboard/DataMatrix.tsx',
    'src/components/dashboard/DocumentLibrary.tsx',
    'src/components/dashboard/matrix-blocks/TableBlock.tsx',
    'src/components/dashboard/matrix-blocks/ChartBlock.tsx',
    'src/components/dashboard/matrix-blocks/ListBlock.tsx',
]
missing = [f for f in required if not os.path.exists(f)]
print('MISSING:', missing) if missing else print('All dashboard files present')
"
```

#### Manual Visual Checks (must do in browser)
```
Prerequisites: Complete a research run first if no workspace exists.
If no workspace exists yet, run one now:
  1. Go to http://localhost:3000
  2. Enter topic: "Benefits of renewable energy"
  3. Select Quick + Comparison Matrix
  4. Click Start Research
  5. Wait for completion (60-90 seconds)
  6. Should redirect to /workspace/[slug]

Visual checks on the workspace page:
  [ ] Page loads without white screen or blank content
  [ ] Header shows topic name and generated date
  [ ] schema_version badge visible (should show 1.0)
  [ ] Left space (25%): Executive Brief visible with text content
  [ ] Center space (50%): Data Matrix shows at least one component
  [ ] Right space (25%): Document Library shows source cards
  [ ] At least one TABLE or CHART renders with real data
  [ ] Document cards show title, domain badge, snippet
  [ ] Document cards are clickable links (open in new tab)
  [ ] No console errors in browser devtools (F12)
  [ ] Layout is 3-column on desktop
  [ ] No TypeScript errors in terminal
```

#### Error Boundary Check
```
  [ ] Open browser devtools console
  [ ] Navigate to workspace page
  [ ] Console must show zero red errors
  [ ] If chart data is malformed, ChartErrorBoundary must show
      "Chart failed to render" instead of crashing the page
```

#### API Integration Check
```bash
# Get the slug from the workspace URL and test the API
SLUG="benefits-of-renewable-energy"  # replace with actual slug
curl -s http://localhost:8000/workspaces/$SLUG \
  -H "Authorization: Bearer YOUR_TOKEN" | python3 -m json.tool | head -30
# Must return valid DashboardPayload JSON
# If 401: JWT token issue — fix auth before continuing
```

---

### Task 2.5 — Notebook Panel

#### Build Check
```bash
cd frontend && npm run build 2>&1 | grep -E "✓|Error|error" | head -20
```

#### File Existence Check
```bash
cd frontend && python3 -c "
import os
required = [
    'src/components/notebook/NotebookPanel.tsx',
    'src/components/notebook/ChatThread.tsx',
    'src/components/notebook/QueryInput.tsx',
    'src/components/notebook/RetryAlert.tsx',
]
missing = [f for f in required if not os.path.exists(f)]
print('MISSING:', missing) if missing else print('All notebook files present')
"
```

#### Manual Visual Checks
```
On the workspace page (/workspace/[slug]):

Panel toggle:
  [ ] "Research Assistant" button visible in header
  [ ] Clicking it opens the notebook panel from the right
  [ ] Panel slides in with smooth CSS transition
  [ ] Clicking again closes the panel
  [ ] Panel width is approximately 320px
  [ ] Panel background is dark (surface color)

Empty state:
  [ ] Before first message: shows BookOpen icon
  [ ] Shows "Ask a question about your research" text

Asking a question:
  [ ] Type a question in the input area
  [ ] Press Enter to submit (Shift+Enter adds newline)
  [ ] Send button shows loading spinner while waiting
  [ ] User message appears right-aligned in accent color
  [ ] Assistant message appears left-aligned in card color
  [ ] Confidence bar appears below assistant message
  [ ] Confidence bar color: green >0.7, yellow 0.3-0.7, red <0.3
  [ ] Sources are listed below the answer

RetryAlert:
  [ ] If needs_web_search=true: RetryAlert appears inline
  [ ] "Search the web" button is visible
  [ ] "Dismiss" button removes the alert
  [ ] RetryAlert is inline card NOT a modal popup

Auto-scroll:
  [ ] After each message the thread scrolls to bottom automatically

API check:
  [ ] No 401 errors in browser network tab when submitting question
  [ ] POST /notebook/query returns 200 with answer and sources
```

#### Notebook API Direct Test
```bash
# Test notebook endpoint directly (replace TOKEN and SLUG)
curl -s -X POST http://localhost:8000/notebook/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_NEXUS_TOKEN" \
  -d '{"workspace_slug":"benefits-of-renewable-energy","question":"What are the main benefits?"}' \
  | python3 -m json.tool
# Must return: answer, sources array, confidence_score, needs_web_search
# Must NOT return 401 or 422
```

---

### Task 3.1 — End-to-End Integration Test

#### Full Happy Path Test
```
Run this complete flow without errors:

1. Open incognito window → http://localhost:3000
   [ ] Redirects to /login

2. Click Sign in with Google
   [ ] Goes to accounts.google.com
   [ ] Returns to app after login
   [ ] User avatar visible in header

3. Enter topic: "Future of electric vehicles in Germany"
   Select: Deep Dive + Comparison Matrix
   Click: Start Research
   [ ] Progress messages update every few seconds
   [ ] No 401 errors in console
   [ ] Redirects to /workspace/[slug] after 60-90 seconds

4. On workspace page:
   [ ] Executive Brief has meaningful text
   [ ] Data Matrix has at least 2 components
   [ ] Document Library has at least 3 sources
   [ ] Schema version badge shows 1.0

5. Open Notebook:
   [ ] Panel opens smoothly
   [ ] Ask: "What is the main challenge for EVs in Germany?"
   [ ] Answer returns within 10 seconds
   [ ] Confidence score visible
   [ ] Sources listed

6. Sign out:
   [ ] Click Sign out button
   [ ] Redirects to /login
   [ ] Accessing / redirects to /login (session cleared)
```

#### Edge Cases
```
Test each — all must work without crashing:

  [ ] Submit empty topic → inline validation error shown, no API call
  [ ] Submit topic < 3 chars → validation error
  [ ] Navigate to /workspace/nonexistent-slug → error state with back button
  [ ] Delete workspace from sidebar → disappears immediately, toast shown
  [ ] Refresh workspace page → data reloads correctly
  [ ] Non-allowed Google email login → access denied message shown
  [ ] Backend down → "Cannot connect to backend" banner shown
```

---

### Task 3.2 — Empty States and Error Handling

#### Visual Checks
```
Empty states (verify each exists):
  [ ] Sidebar with no workspaces: BookOpen icon + helpful message
  [ ] DataMatrix with no components: "No structured data generated"
  [ ] DocumentLibrary with no sources: "No sources saved"
  [ ] ChatThread before messages: MessageSquare icon + prompt text

Error states:
  [ ] /workspace/nonexistent → AlertCircle + message + back button
  [ ] Research failed → error shown in red in BlueprintForm
  [ ] Backend unreachable → fixed banner at top of page

Toast notifications:
  [ ] Complete research run → success toast appears
  [ ] Delete workspace → success toast appears
  [ ] Research fails → error toast appears
  [ ] Toasts auto-dismiss after a few seconds
```

---

### Task 3.3 — Makefile and README

#### Makefile Check
```bash
cd /Users/aaryanvatsa/Documents/projects/NEXUS_RESEARCH_ENGINE

# Verify Makefile exists
ls Makefile && echo "✓ Makefile exists" || echo "✗ Missing"

# Verify all targets exist
for target in install dev dev-backend dev-frontend test lint clean; do
  grep -q "^$target:" Makefile && echo "✓ $target" || echo "✗ Missing: $target"
done
```

#### README Check
```bash
ls README.md && echo "✓ README exists" || echo "✗ Missing"
# Open README.md and verify these sections exist:
# [ ] Project description
# [ ] Prerequisites
# [ ] Google OAuth App setup steps
# [ ] Quickstart (make install → .env → make dev)
# [ ] Architecture overview
# [ ] MVP features list
# [ ] V2 roadmap
```

#### Dockerfile Check
```bash
ls Dockerfile && echo "✓ Dockerfile exists" || echo "✗ Missing"
# Verify it builds without errors:
docker build -t nexus-test . 2>&1 | tail -5
# Expected: Successfully built
```

---

## Section B — Universal Checks (Run After Every Task)

Run these after every single task before marking it done.

### B1 — TypeScript Build
```bash
cd frontend && npm run build 2>&1 | grep -E "error|Error|✓" | head -20
# Expected: zero errors, shows ✓ Compiled successfully
```

### B2 — ESLint
```bash
cd frontend && npm run lint 2>&1 | tail -10
# Expected: no errors (warnings acceptable)
```

### B3 — Backend Still Starts
```bash
curl -s http://localhost:8000/health | python3 -m json.tool
# Expected: status ok, all services ok
```

### B4 — Auth Still Works
```bash
# Must return 401 (not 500 or connection refused)
CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/workspaces)
echo "Unauth check: $CODE (must be 401)"
```

### B5 — No Console Errors
```
Open browser devtools (F12) → Console tab
Navigate through the app
Expected: zero red errors
Yellow warnings are acceptable
```

### B6 — Key Files Not Accidentally Deleted
```bash
cd frontend && python3 -c "
import os
critical = [
    'src/lib/types.ts',
    'src/lib/api.ts',
    'src/lib/utils.ts',
    'src/store/workspace.ts',
    'src/auth.ts',
    'src/types/next-auth.d.ts',
]
missing = [f for f in critical if not os.path.exists(f)]
print('MISSING CRITICAL FILES:', missing) if missing else print('All critical files present')
"
```

### B7 — Git Status Clean
```bash
cd /Users/aaryanvatsa/Documents/projects/NEXUS_RESEARCH_ENGINE
git status
git diff --stat
# Only files from the current task should appear
# No untracked files in wrong directories
```

---

## Section C — Full Integration API Test

Run this after Task 3.1 to verify the complete system works end to end.

```bash
cd /Users/aaryanvatsa/Documents/projects/NEXUS_RESEARCH_ENGINE/backend
source ../venv/bin/activate

python3 -c "
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
    print(f'LLM: {llm_router.get_provider_name()}')

    request = ResearchRequest(
        topic='Impact of AI on software development',
        extensiveness=ExtensivenesLevel.QUICK,
        format_preference=FormatPreference.COMPARISON
    )
    email_slug_val = email_to_slug('test@nexus.local')
    slug = 'impact-of-ai-on-software-development'
    workspace_repo = WorkspaceRepository(settings)
    vector_store = VectorStoreService(settings)

    print('Running researcher...')
    async with TavilySearchClient(settings) as client:
        sources = await ResearchAgent(
            request, slug, email_slug_val, llm_router, client, settings
        ).run()
    print(f'PASS: {len(sources)} sources')

    print('Running synthesizer...')
    payload = await SynthesizerAgent(
        request, slug, email_slug_val, llm_router, workspace_repo, settings
    ).run(sources)
    print(f'PASS: {len(payload.matrix_data)} matrix components')
    print(f'PASS: schema_version={payload.topic_metadata.schema_version}')

    print('Ingesting into ChromaDB...')
    count = await vector_store.ingest(sources, email_slug_val, slug)
    print(f'PASS: {count} chunks ingested')

    print('Querying ChromaDB...')
    chunks = await vector_store.query(
        'how is AI changing software development',
        email_slug_val, slug, n_results=3
    )
    print(f'PASS: {len(chunks)} chunks retrieved')

    payload_path = Path(settings.STORAGE_ROOT) / email_slug_val / slug / 'dashboard_payload.json'
    assert payload_path.exists(), 'FAIL: payload not saved'
    print(f'PASS: payload saved to disk')

    print()
    print('ALL INTEGRATION TESTS PASSED')
    print(f'  LLM Provider:      {llm_router.get_provider_name()}')
    print(f'  Sources:           {len(sources)}')
    print(f'  Matrix components: {len(payload.matrix_data)}')
    print(f'  ChromaDB chunks:   {count}')

asyncio.run(test())
"
```

---

## Summary Report Template

After completing all checks for a task, generate this report:

```
NEXUS FRONTEND TASK VERIFICATION REPORT
=========================================
Task: [Task number and name]
Date: [today]
Build: PASS/FAIL
Lint: PASS/FAIL
File existence: PASS/FAIL
Visual checks: [n]/[total] passed
API checks: PASS/FAIL
Console errors: NONE/[list them]
Universal checks (B1-B7): PASS/FAIL

Issues found: [list any]
Issues fixed: [list fixes applied]

Task Status: READY TO COMMIT / NEEDS FIXES

Next task: [next task number and name]
```

Stop after generating this report. Do not start the next task until user confirms.

---

## Handoff Message for New Claude Code Session

If session is interrupted, paste this to resume:

```
Read CLAUDE.md and TASKS.md. Run git log --oneline -5.

Environment:
- Python 3.11 venv at repo root: source venv/bin/activate
- Backend runs from backend/ directory
- Frontend files all in src/ directory
- JWT auth: frontend sends Authorization: Bearer <nexusToken>
- ChromaDB 0.5.23, numpy<2.0, greenlet installed
- google.genai (NOT google.generativeai which is deprecated)

Before starting any task:
1. source venv/bin/activate
2. cd backend && uvicorn app.main:app --reload --port 8000
3. cd frontend && npm run dev
4. Verify http://localhost:8000/health returns status ok
5. Verify http://localhost:3000 redirects to /login

After completing each task:
1. Run all checks in FRONTEND_VERIFICATION.md for that task
2. Run universal checks Section B
3. Fix all failures
4. Generate summary report
5. Stop and wait for user confirmation before next task
```
