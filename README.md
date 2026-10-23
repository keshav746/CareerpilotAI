# CareerPilot AI
### Agentic AI-Based Job Search, Resume Analysis and Career Recommendation System

An educational full-stack career platform implementing **22 planned modules** through integrated screens, API routes, deterministic multi-tool agent execution, local retrieval, role-based access, and tests. This is a working **prototype**, not a production-ready hiring platform.

## Quick start (VS Code)
1. Install Python 3.11+ and open this folder in VS Code.
2. Open Terminal → New Terminal.
3. Create environment: `python -m venv .venv`
4. Activate it: Windows PowerShell `.venv\Scripts\Activate.ps1`; macOS/Linux `source .venv/bin/activate`.
5. Install: `pip install -r requirements.txt`
6. Run: `uvicorn app.main:app --reload`
7. Visit **http://127.0.0.1:8000**. Register a student account.
8. API documentation: **http://127.0.0.1:8000/docs**.
9. Run tests: `pytest -q`.

## Live demo
Register → Career Profile (enter `python, sql, git`) → Resume Intelligence → Job Discovery → Agent Workspace (run a goal) → RAG Knowledge Base → Skill Roadmap → Applications → Analytics → Safety & Evaluation.

## Features and honesty about implementation
- 22 module areas: auth, profile, resume analysis, job discovery, matching, career guidance, skill gaps, roadmaps, resume text optimization guidance, interview coaching, multi-agent execution, applications, saved search alerts, analytics, recruiter listings, market stats, admin audit API, evaluation, RAG, execution trace, prompt templates, and safety controls.
- **Agent behavior:** a planner coordinates eight specialized deterministic tool workflows, returning a visible execution trace. This is genuine multi-step orchestration but **not an LLM-driven autonomous planning system**. LangGraph and an LLM are proposed upgrades, not falsely claimed dependencies.
- **RAG:** local lexical similarity retrieval over curated sample career documents. There is **no vector database, embeddings or generative grounded synthesis** in this prototype; these are next steps.
- **Jobs:** six illustrative sample jobs (fictional companies), plus recruiter-posted local listings. **No live job API** is connected; sample jobs must not be presented as genuine vacancies.
- **Resume scoring:** heuristic completeness score, not a certified ATS score. Resume parsing works for text-based PDFs, DOCX and TXT; scanned PDFs require OCR not included.
- **Interview:** text-based heuristic feedback, not a live LLM interview.
- **Alerts:** saved searches; background scheduling and email notifications are not yet implemented.
- **Safety:** PBKDF2 password hashing, bearer session tokens, access checks, file size limit, human approval stub, audit logs. No real external applications are submitted. Local SQLite is not a production security design.
- **Frontend:** responsive HTML/CSS/JavaScript SPA; no React build tooling required. FastAPI serves the static UI.

## Directory
- `app/main.py` API endpoints
- `app/engine.py` career intelligence, agents, retrieval, storage
- `app/static/` responsive UI
- `tests/` automated test suite
- `docs/` report, rubric mapping, architecture, test cases, presentation outline

## Security & privacy
Use only synthetic resumes in a classroom demonstration. The local database may contain uploaded resume text and should not be committed. Do not upload personal resumes to a public repository. No built-in admin account is provisioned. For deployment add secure HTTPS cookies, rate limiting, CSRF controls where relevant, user deletion, encrypted storage, and external provider consent.

## Production roadmap
LangGraph dynamic tool calling, pgvector + embeddings, licensed live job feeds, genuine LLM interview and resume rewriting, scheduler/notifications, secure admin provisioning, CI/CD, and richer automated evaluation.

## Updated evaluator build
- Student portal: overview, profile, resume, jobs, careers, roadmap, agent workspace, RAG, interview coach, applications, market intelligence.
- Recruiter portal: recruiter listing publication only. Backend student endpoints reject recruiter tokens (HTTP 403).
- Removed modules and dedicated APIs: Prompt Engineering, Job Alerts, Analytics, Safety & Evaluation (feedback endpoint). Internal approval safeguards are retained for agent behavior.
- Interview Coach: five questions per session, sequential submissions, feedback after each, saved session and answers in SQLite, and an overall summary. Feedback is heuristic, not an LLM evaluation.
- Existing SQLite data is retained; the new interview tables are created automatically on startup.

## Real LLM + semantic RAG upgrade (v2)

Two NEW student pages are included: **LLM Agent Planner** and **LLM + Semantic RAG**. The existing deterministic Agent Workspace and local RAG page are retained as baselines for comparison. The new pages **make actual external model API calls**; they never pretend a response came from an LLM when no provider is configured.

### Set up your own working provider credentials

1. Install dependencies: `pip install -r requirements.txt`.
2. Copy `.env.example` to `.env` in the `careerpilot_Final` folder.
3. Put your **real** API key in `LLM_API_KEY`. The default OpenAI-compatible configuration uses `LLM_BASE_URL=https://api.openai.com/v1`, `LLM_MODEL=gpt-4.1-mini`, and `EMBEDDING_MODEL=text-embedding-3-small`. These require a provider account with API access and potentially paid credits. The model names must exist for your chosen provider. Other OpenAI-compatible providers can work if they implement both `/chat/completions` and `/embeddings` in the same base URL.
4. Run `uvicorn app.main:app --reload` and sign in as a student. Visit **LLM + Semantic RAG** and **LLM Agent Planner**. Errors from missing credentials, unsupported models or unavailable APIs are shown instead of fake results.
5. Add career knowledge to `app/knowledge/*.md`. Markdown paragraphs become cited retrievable passages. The supplied files are authored career-guidance content, **not verified live labor-market sources**. For a real deployment, add attributed, reviewed, regularly updated source documents.
6. Run `python -m pytest -q` to run automated tests.

### How the advanced AI actually works

- `app/llm_service.py` defines **versioned prompts**: `planner_v2` (JSON tool plan with a strict allowlist), `rag_v2` (source-only answers with numbered citations and explicit insufficient-evidence handling), and `synthesis_v2` (summary constrained to actual tool results). Prompts explicitly separate untrusted user/source content from instructions.
- Semantic RAG calls a real **embeddings endpoint**, computes cosine similarity over document passages, applies `RAG_MIN_SIMILARITY`, then sends numbered evidence to a real chat-completions endpoint. If no passage passes the threshold, it returns an honest insufficient-evidence response without fabricating an LLM answer.
- The LLM planner chooses which tools to call using a strict JSON schema and allowlist. Python validates the plan and executes actual existing career matching, job ranking, roadmap, and semantic retrieval functions. A separate model call summarizes the real tool results. There is **no arbitrary code execution**, no external job application, and no live-job guarantee.
- A valid API key is necessary for live AI features. Automated tests mock the external provider; passing tests does **not** establish that your real provider credentials or internet connection work. Validate them on your computer before evaluation.

### Security and scope

The `.env` file is ignored by Git and should never be shared. The new AI endpoints require a logged-in **student** account; recruiter accounts cannot access them. Prompt engineering is implemented in backend code, **not restored as a student-facing Prompt Engineering page**. Removed Job Alerts, Analytics, and Safety & Evaluation pages remain removed. Internal safeguards are retained.
