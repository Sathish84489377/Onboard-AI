# Copilot Instructions — Onboard AI

## Project overview
Onboard AI is a local-first GraphRAG onboarding assistant built with **Chainlit** (UI), **FastAPI** (API), and **GraphRAG** (knowledge retrieval). See `CONTEXT.md` for the full architecture map.

## Architecture (3-layer)
1. **Presentation** — `chainlit_app.py` (chat UI) + `api/main.py` (REST)
2. **Orchestration** — `agent_factory.py` (AutoGen agents) + `services/graphrag_query.py`
3. **Knowledge** — `graphrag_service.py` (index checks, search) + `services/web_search.py` (SearXNG fallback)

## Coding standards
- **Python 3.12+** — use modern type hints (`dict[str, str]`, `list[int]`, `X | None`).
- **Pathlib** over `os.path` everywhere.
- **Google-style docstrings** for all public functions and classes.
- **Ruff** for linting and formatting (`ruff check src/ tests/` / `ruff format src/ tests/`).
- **Type hints** on all function signatures.
- Import order: stdlib → third-party → local (enforced by ruff `I` rules).

## Before committing
```bash
ruff check src/ tests/
ruff format --check src/ tests/
pytest
```

## Key conventions
- `index_ready()` lives in `graphrag_service.py` — import it, do not re-implement.
- `AUDIENCE_INSTRUCTION` lives in `settings.py` — use it as the single source of truth.
- Entry points are defined in `pyproject.toml [project.scripts]`.
- Config is loaded from environment variables (`.env`) and `settings.yaml`.
- Tests use `monkeypatch`, stubs, and `tmp_path` — no real network or GPU calls.

## File map (key modules)
| File | Purpose |
|---|---|
| `src/onboard_ai/chainlit_app.py` | Chainlit chat UI lifecycle handlers |
| `src/onboard_ai/graphrag_service.py` | Core RAG: index checks + search execution |
| `src/onboard_ai/agent_factory.py` | AutoGen agent creation |
| `src/onboard_ai/cli.py` | CLI entry points (bootstrap, ui, api) |
| `src/onboard_ai/api/main.py` | FastAPI REST endpoints |
| `src/onboard_ai/services/web_search.py` | SearXNG web-search fallback |
| `settings.yaml` | GraphRAG runtime configuration |
