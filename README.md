# Onboard AI — Local Product Onboarding Assistant

Onboard AI is a local-first onboarding copilot for product teams. It ingests product docs, builds a GraphRAG knowledge index, and serves audience-aware answers through Chainlit UI and FastAPI.

## What you get

- GraphRAG-powered local and global retrieval
- Audience-aware responses (`General`, `Developer`, `QA`, `Manager`)
- Optional specialist routing with AutoGen
- Optional web fallback (SearXNG) when RAG evidence is weak
- Local profiling and quality-gate tooling

## Project structure

- `src/onboard_ai/cli.py` — package CLI commands (`onboard-ai-*`)
- `src/onboard_ai/api/main.py` — FastAPI entrypoint
- `src/onboard_ai/chainlit_app.py` — Chainlit chat app
- `src/onboard_ai/services/` — query orchestration and fallback logic
- `src/onboard_ai/tools/ingestion/` — document conversion pipeline
- `src/onboard_ai/tools/profiling/` — latency/memory profiling
- `src/onboard_ai/tools/evaluation/` — quality gate checks
- `settings.yaml` — GraphRAG config
- `env.sample` — runtime environment template

## Prerequisites

Before setup, ensure:

- Python 3.12+
- Ollama installed and available on PATH
- LiteLLM proxy reachable at `http://0.0.0.0:4000` (required for AutoGen specialist routing)
- Docker (optional, only for SearXNG local web fallback)
- Source docs available in `data/input`

## Installation

1. Create and activate a virtual environment.
2. Install project dependencies.

```bash
pip install -e .[dev]
```

## CLI command reference

- `onboard-ai-bootstrap` — pull models, convert source docs, and build GraphRAG index
- `onboard-ai-ui` — run Chainlit app (`src/onboard_ai/chainlit_app.py`)
- `onboard-ai-api` — run FastAPI service on `http://localhost:8000`
- `onboard-ai-convert <input_dir> <output_dir>` — convert documents to markdown
- `onboard-ai-profile` — profile query latency/memory
- `onboard-ai-gate` — run local/global quality gate checks
- `onboard-ai-prompt-audit` — audit prompt token usage under `assets/prompts`

## Quickstart (recommended)

### 1) Bootstrap RAG pipeline

```bash
onboard-ai-bootstrap
```

This command:

- pulls required Ollama models (`deepseek-r1:8b`, `qwen3-embedding:0.6b`)
- converts source docs to markdown
- builds GraphRAG index artifacts

### 2) Start app UI

```bash
onboard-ai-ui
```

### Fast repeat run

Use this when models are already available:

```bash
onboard-ai-bootstrap --skip-model-pull && onboard-ai-ui
```

API-only run (optional):

```bash
onboard-ai-bootstrap --skip-model-pull && onboard-ai-api
```

## First success check

After quickstart, confirm all three checks:

1. Bootstrap completed without errors and `data/output` contains GraphRAG artifacts (for example, parquet files or `lancedb`).
2. Chainlit UI opens and is reachable at `http://localhost:8000`.
3. Ask a simple onboarding question in UI (for example: `What does this project do?`) and verify you get a non-empty answer.

## Runtime configuration

Copy `env.sample` to `.env` and adjust as needed.

Default AutoGen model calls are routed via LiteLLM proxy (`http://0.0.0.0:4000`) as defined in `src/onboard_ai/settings.py`.

Quality-first ingestion defaults:

```bash
PDF_ENGINE=docling
PDF_DOCLING_MAX_PAGES=0
```

Default runtime web fallback configuration:

```bash
ENABLE_WEB_SEARCH=true
WEB_SEARCH_PROVIDER=searxng
SEARXNG_BASE_URL=http://localhost:8080
WEB_SEARCH_TIMEOUT_SECONDS=8
```

Set `ENABLE_WEB_SEARCH=false` to disable web fallback globally.

## Config ownership

- `settings.yaml`: GraphRAG indexing/query configuration (models, chunking, storage, prompts).
- `.env`: runtime app flags (web fallback, provider endpoint, timeouts).
- Chainlit/API payload flags: per-session or per-request behavior overrides.

## Document ingestion details

Ingestion uses a hybrid pipeline:

- PDFs: `Docling` by default, with `MarkItDown` fallback only if Docling fails
- Office/web formats (`.pptx`, `.docx`, `.xlsx`, `.html`, `.htm`, `.csv`, `.json`, `.xml`): `Docling` first, with optional fallback
- Plain text/code files: direct text reader

Run conversion directly:

```bash
onboard-ai-convert data/input data/input/markdown
```

Conversion metadata is written to `data/input/markdown/_sources.jsonl`.

## Run modes

### Chainlit

```bash
onboard-ai-ui
```

In UI settings, `(Web) Enable SearXNG fallback` is ON by default. It is used only when GraphRAG citations are weak/missing or index is not ready.

### FastAPI

```bash
onboard-ai-api
```

Set `"enable_web_search": false` in JSON request payload to disable fallback for a specific call.

Health check (when FastAPI is running):

```bash
curl http://localhost:8000/health
```

Expected result:

```json
{"status":"ok"}
```

Sample query request:

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What does this project do?",
    "mode": "local",
    "response_type": "single paragraph",
    "community_level": 0,
    "enable_web_search": true
  }'
```

## Optional: run SearXNG locally

```bash
docker run -d --name searxng -p 8080:8080 searxng/searxng:latest
```

Health check:

```bash
curl "http://localhost:8080/search?q=python&format=json"
```

## Evaluation and profiling

```bash
onboard-ai-profile --mode local --repeat 2
onboard-ai-profile --mode global --repeat 2
onboard-ai-gate --mode local --repeat 2
onboard-ai-gate --mode global --repeat 1 --max-p95-latency 20
onboard-ai-prompt-audit
```

## Notes

- Specialist routing is available in Chainlit settings.
- Keep specialist routing OFF while baselining quality and latency.
- Audience policy guidance: `assets/prompts/onboarding_roles.md`.
