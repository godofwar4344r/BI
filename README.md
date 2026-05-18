# BI - Billionaire Intelligence

BI is a production-ready MVP for evidence-grounded decision intelligence. It retrieves structured founder/investor decision cases, ranks trait patterns, and returns a concise answer with recommendation, reasoning, trade-offs, risks, next step, and supporting cases.

This is not a rich-lifestyle mimic. BI treats wealth as a noisy signal and focuses on decision patterns: capital allocation, leverage, compounding, risk management, execution speed, hiring, market sensing, narrative building, and long-term thinking.

## Architecture

- `frontend/`: Next.js chat UI with structured answer rendering and supporting evidence cards.
- `backend/`: FastAPI API, Pydantic models, SQLAlchemy repository, ingestion, retrieval, synthesis, guardrails, tests, and evals.
- `data/sample_decision_cases.jsonl`: Seed corpus of structured decision cases with trait scores and source references.
- `docker-compose.yml`: Optional Postgres and Qdrant services for production-like local runs.

Default local mode uses SQLite plus deterministic hash embeddings and an in-process vector store, so the MVP runs without external keys. The code keeps the LLM and embedding layers mockable and replaceable.

## Data Model

Each decision case includes:

- `person`
- `domain`
- `context`
- `decision`
- `reasoning`
- `traits` with 1-5 scores and confidence weights
- `tradeoffs`
- `outcome`
- `lesson`
- `confidence`
- `source_type`
- `source_reference`
- optional `timestamp`

## Backend Setup

```powershell
cd "D:\waah folder (work)\web site\BI ai"
Copy-Item .env.example .env
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The backend seeds the demo dataset automatically on startup.

Useful endpoints:

- `GET /health`
- `GET /cases`
- `POST /chat`
- `POST /ingest/demo`
- `POST /ingest/cases`

Example chat request:

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://localhost:8000/chat `
  -ContentType "application/json" `
  -Body '{"query":"Should I bootstrap longer or raise a seed round now?"}'
```

## Frontend Setup

```powershell
cd "D:\waah folder (work)\web site\BI ai\frontend"
npm install
npm run dev
```

Open `http://localhost:3000`.

## Optional Postgres + Qdrant

```powershell
cd "D:\waah folder (work)\web site\BI ai"
docker compose up -d postgres qdrant
```

Then set these in `.env`:

```dotenv
BI_DATABASE_URL=postgresql+psycopg://bi:bi@localhost:5432/bi
BI_VECTOR_STORE=qdrant
BI_QDRANT_URL=http://localhost:6333
```

## Tests

```powershell
cd "D:\waah folder (work)\web site\BI ai\backend"
.\.venv\Scripts\Activate.ps1
pytest
```

Frontend checks:

```powershell
cd "D:\waah folder (work)\web site\BI ai\frontend"
npm run lint
npm run build
npm audit --audit-level=moderate
```

## Evaluation

```powershell
cd "D:\waah folder (work)\web site\BI ai"
python backend/scripts/evaluate.py
```

The harness covers:

- bootstrap vs raise
- hire vs automate
- spend vs conserve
- build vs buy
- expand vs consolidate
- acquire vs grow organically

It scores clarity, leverage, realism, risk awareness, usefulness, and decision quality using lightweight deterministic checks.

## Retrieval Flow

1. Classify intent and domain from the query.
2. Detect trait signals such as risk tolerance, speed, discipline, leverage, and long-term thinking.
3. Retrieve semantically relevant cases from the vector store.
4. Add trait-matched cases from the repository.
5. Re-rank by vector score, trait fit, domain match, and confidence.
6. Synthesize an answer using only retrieved supporting cases.
7. Return supporting cases with confidence, source reference, and trait scores.

## Guardrails

BI refuses to assist with fraud, manipulation, deception, bribery, evasion, or illegal conduct. It redirects those queries toward lawful strategy, risk management, transparency, and durable advantage.

## Next Improvements

- Add real embedding providers behind the `EmbeddingProvider` protocol.
- Add a hosted LLM synthesizer behind `AnswerSynthesizer` while keeping the current deterministic synthesizer for tests.
- Add Alembic migrations and Postgres JSON indexes.
- Add document upload with source metadata and review workflow.
- Add human approval for newly ingested cases before indexing.
- Add richer evaluator rubrics with human-labeled expected outputs.
- Add source confidence tiers and citation links for each case.
