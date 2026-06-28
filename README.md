# Nexus Research Engine

**Nexus** is an autonomous research engine that replaces AI chat boxes with a structured visual business dashboard. Give it a topic, and it searches the live web, synthesizes findings, and renders them as tables, charts, and summaries inside persistent local workspace folders.

## Features

- **Autonomous Research**: Start research with one click. Nexus searches the web, synthesizes findings into structured visualizations.
- **Dashboard Workspaces**: Every research result generates a persistent, shareable workspace with multiple data views.
- **RAG Q&A Notebook**: Ask questions about your research findings. Nexus retrieves relevant sources and answers with confidence scoring.
- **Protected by Google OAuth**: Only allowed users can access the engine. Simple email-based allowlist.
- **JSON Contract Architecture**: Backend and frontend are fully decoupled via a strict dashboard_payload.json schema.

---

## Prerequisites

Before getting started, make sure you have:

- **Python 3.11+** — [Install Python](https://www.python.org/downloads/)
- **Node 18+** — [Install Node.js](https://nodejs.org/)
- **Google Cloud Project** — For OAuth integration
- **API Keys**:
  - Tavily API key (web search)
  - Gemini or Groq API key (LLM)
  - Google OAuth Client ID and Secret

---

## Google OAuth App Setup

Follow these steps to create a Google OAuth application:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Go to **APIs & Services** → **OAuth consent screen**
   - Choose "External" user type
   - Fill in app name and your email
4. Go to **APIs & Services** → **Credentials**
   - Click **Create Credentials** → **OAuth Client ID**
   - Application type: **Web application**
   - Add Authorized redirect URIs:
     - `http://localhost:8000/auth/callback` (for local development)
     - `https://your-render-url.onrender.com/auth/callback` (for production)
5. Copy your **Client ID** and **Client Secret**

---

## Quickstart

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/nexus-research-engine.git
cd nexus-research-engine
```

### 2. Install Dependencies

```bash
make install
```

This installs Python dependencies for the backend and npm packages for the frontend.

### 3. Set Up Environment Variables

Copy the example env file:

```bash
cp backend/.env.example backend/.env
```

Fill in your keys in `backend/.env`:

```
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
TAVILY_API_KEY=your_tavily_api_key
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
ALLOWED_GOOGLE_EMAILS=your@gmail.com
SESSION_SECRET_KEY=random_32_char_string
AUTH_SECRET=random_32_char_string_for_nextauth
```

For the frontend, set up `frontend/.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
AUTH_GOOGLE_ID=your_google_client_id
AUTH_GOOGLE_SECRET=your_google_client_secret
AUTH_SECRET=random_32_char_string
```

### 4. Run Development Servers

Start both backend and frontend:

```bash
make dev
```

Or run them separately:

```bash
# Terminal 1
make dev-backend

# Terminal 2
make dev-frontend
```

The app will be available at `http://localhost:3000`.

---

## LLM Router

Nexus uses an intelligent LLM router that tries providers in this order:

1. **Ollama** (local, free if you have Ollama running)
2. **Gemini Flash** (Google, free tier available)
3. **Groq Llama3** (Groq, fast and free)

If all three fail to initialize, the system will raise an error. The router automatically selects the first available provider on startup.

---

## Architecture

### Backend (FastAPI + Python)

- **Orchestrator**: Coordinates the research pipeline
- **Researcher Agent**: Generates sub-queries, searches via Tavily API
- **Synthesizer Agent**: Calls LLM to structure findings into dashboard components
- **Vector Store**: ChromaDB for semantic search (workspace-isolated)
- **Notebook Service**: RAG Q&A with confidence scoring
- **WorkspaceRepository**: All file operations (abstraction for local disk or Cloudflare R2)

### Frontend (Next.js + TypeScript)

- **Dashboard Canvas**: Multi-space visualization (Executive Brief, Data Matrix, Document Library)
- **Blueprint Configurator**: Form to start new research with topic, depth, format
- **Notebook Panel**: RAG Q&A interface with sliding side panel
- **Zustand Store**: Workspace state management

### Database & Storage

- **SQLite**: Job persistence, user tracking
- **ChromaDB**: Vector embeddings per workspace (local `storage/{email_slug}/{workspace_slug}/chroma_db/`)
- **Local Disk**: Dashboard payloads and source documents (swappable to Cloudflare R2)

### Contract

**dashboard_payload.json** — immutable schema contract between backend and frontend:

```json
{
  "topic_metadata": { "topic", "extensiveness", "format_preference", "generated_at", "schema_version": "1.0" },
  "executive_summary": "string",
  "matrix_data": [{ "section_title", "component_type": "table|chart|list", ... }],
  "document_library": [{ "id", "title", "url", "snippet", ... }]
}
```

Frontend checks `schema_version` on load and warns if mismatch.

---

## MVP Features

✅ **Complete**

- Google OAuth with email allowlist
- Research job creation and background execution
- Web search via Tavily API
- LLM-powered synthesis into structured JSON
- Dashboard visualization (tables, charts, lists)
- ChromaDB vector store per workspace
- Notebook Q&A with confidence scoring
- Workspace management (list, view, delete)
- Job polling with auto-redirect
- Empty states and error handling
- Toast notifications

---

## Make Targets

```bash
make install        # Install all dependencies
make dev            # Run both backend and frontend
make dev-backend    # Run backend only (port 8000)
make dev-frontend   # Run frontend only (port 3000)
make test           # Run pytest on backend
make lint           # Lint backend (ruff) and frontend (eslint)
make clean          # Remove __pycache__ and .pyc files
```

---

## Deploy

### Backend → Render

1. Create a new Web Service on [Render](https://render.com/)
2. Connect your GitHub repository
3. Configure environment variables (same as `.env` above)
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`

The Dockerfile in this repo will be automatically detected by Render.

### Frontend → Vercel

1. Create a new project on [Vercel](https://vercel.com/)
2. Connect your GitHub repository (select `frontend/` directory)
3. Configure environment variables:
   - `NEXT_PUBLIC_API_URL`: Your Render backend URL
   - `AUTH_GOOGLE_ID`, `AUTH_GOOGLE_SECRET`, `AUTH_SECRET`
4. Deploy

### Storage → Cloudflare R2

For production, swap local disk storage to Cloudflare R2:

```bash
USE_R2=true R2_ACCOUNT_ID=... R2_ACCESS_KEY_ID=... R2_SECRET_ACCESS_KEY=... make dev
```

This requires setting up an R2 bucket and updating backend env vars. See Task 4.1 for details.

---

## V2 Roadmap

- **Internet Safety Loop**: Notebook can trigger web search if confidence is low
- **Click-to-Verify Citations**: Split-pane source viewer with paragraph highlighting
- **Nexus Map**: NetworkX graph of entities and relationships across workspaces
- **Scheduled Research**: APScheduler for recurring research subscriptions
- **PDF Export**: WeasyPrint for downloadable dashboards
- **Shareable Links**: Public read-only dashboard URLs with UUID tokens

---

## Troubleshooting

### Backend won't start

```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill process if needed
kill -9 <PID>

# Verify all dependencies are installed
cd backend && pip install -r requirements.txt
```

### Frontend build errors

```bash
# Clear next cache
rm -rf frontend/.next

# Reinstall node_modules
cd frontend && rm -rf node_modules && npm install

# Rebuild
npm run build
```

### LLM provider not initializing

- For **Ollama**: Make sure Ollama is running (`ollama serve`)
- For **Gemini**: Verify `GEMINI_API_KEY` is set correctly
- For **Groq**: Verify `GROQ_API_KEY` is set correctly

### ChromaDB errors

- ChromaDB requires `numpy<2.0`. If you see version conflicts, run:
  ```bash
  pip install --upgrade --force-reinstall chromadb
  ```

---

## License

MIT

---

## Support

For issues, questions, or contributions, please open an issue on GitHub.

**Built with ❤️ by the Nexus team.**
