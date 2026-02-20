# Onboard AI — Project Context for LLMs & Agents

## Overview

**Onboard AI** is a local-first onboarding copilot designed to help product teams quickly understand documentation. It uses a **GraphRAG** (Graph Retrieval-Augmented Generation) approach to index documents and provide answers tailored to specific audiences (General, Developer, QA, Manager).

## Architecture

The system follows a three-layer modular architecture:

1. **Presentation** — user-facing surfaces
   - `chainlit_app.py` — Chainlit chat UI lifecycle (start, settings, message).
   - `api/main.py` — FastAPI REST endpoints (`/health`, `/query`).
   - `cli.py` — CLI entry points mapped to `[project.scripts]` in `pyproject.toml`.

2. **Orchestration** — agent routing and query logic
   - `agent_factory.py` — AutoGen agent creation (Retriever, UserProxy, Specialists).
   - `services/graphrag_query.py` — High-level query orchestrator combining GraphRAG + web-search fallback.
   - `chainlit_agents.py` — Chainlit-aware wrappers around AutoGen agents.

3. **Knowledge** — data retrieval and indexing
   - `graphrag_service.py` — Core RAG service: index readiness checks, search execution, citation detection. **Canonical source for `index_ready()`**.
   - `services/web_search.py` — SearXNG web-search fallback integration.

## Ingestion Pipeline

1. Documents (`.pdf`, `.docx`, `.md`, `.pptx`, `.xlsx`, `.html`) are placed in `data/input/`.
2. `onboard-ai-convert` (using `docling` & `markitdown`) converts them to Markdown.
3. `onboard-ai-bootstrap` runs the GraphRAG indexing process.

## Tech Stack

- **Language**: Python 3.12+
- **Frameworks**:
  - `Chainlit 2.9.2` — Chat UI.
  - `FastAPI` — REST API backend.
  - `GraphRAG 3.0.2` — Microsoft's graph-based RAG library.
  - `AutoGen (pyautogen 0.10)` — Multi-agent orchestration.
  - `LiteLLM` — LLM proxy (standardises API calls to Ollama/OpenAI/etc).
- **Data Processing**:
  - `Docling` / `MarkItDown` — Document conversion.
  - `Pandas` — Data manipulation.
  - `tiktoken` — Token counting for prompt auditing.
- **Dev Tooling**:
  - `Ruff` — Linting + formatting (config in `pyproject.toml`).
  - `Mypy` — Static type checking.
  - `Pytest` — Test runner (tests in `tests/`).
  - `pre-commit` — Git hooks for ruff + mypy (`.pre-commit-config.yaml`).

## Key Directories & Files

| Path | Purpose |
| :--- | :--- |
| `src/onboard_ai/chainlit_app.py` | Chat UI lifecycle handlers (start, settings, message). |
| `src/onboard_ai/graphrag_service.py` | Core RAG logic — index checks, search, citations. Canonical `index_ready()`. |
| `src/onboard_ai/agent_factory.py` | AutoGen agent creation (Retriever, UserProxy, Specialists). |
| `src/onboard_ai/chainlit_agents.py` | Chainlit-aware wrappers for AutoGen agents. |
| `src/onboard_ai/settings.py` | Shared constants: `LLM_CONFIG_AUTOGEN`, `AUDIENCE_INSTRUCTION`, audience map. |
| `src/onboard_ai/config.py` | Singleton `AppConfig` Pydantic model (env-driven). |
| `src/onboard_ai/cli.py` | CLI entry points: `bootstrap`, `run_ui`, `run_api`. |
| `src/onboard_ai/api/` | FastAPI app — endpoints + Pydantic schemas. |
| `src/onboard_ai/services/` | Query orchestration (`graphrag_query.py`) + web search (`web_search.py`). |
| `src/onboard_ai/tools/ingestion/` | Document conversion via `convert_anything.py` (docling + markitdown). |
| `src/onboard_ai/tools/evaluation/` | Quality-gate checks: citation rate, uncertainty, latency. |
| `src/onboard_ai/tools/profiling/` | Query profiler + prompt token auditor. |
| `src/onboard_ai/py.typed` | PEP 561 marker — signals typed package to downstream tools. |
| `settings.yaml` | GraphRAG runtime configuration (models, prompts, chunk sizes). |
| `data/input/` | Raw documents to be indexed. |
| `tests/` | Pytest test suite with shared `conftest.py` fixtures. |
| `.pre-commit-config.yaml` | Git hooks: ruff lint, ruff format, mypy. |
| `.github/copilot-instructions.md` | Agent-specific project context for GitHub Copilot. |
| `CONTEXT.md` | This file — full architecture map for LLMs. |
| `llms.txt` | Concise LLM-oriented project briefing. |

## Canonical Sources (Single Source of Truth)

These items are defined in exactly one place — import them, never re-implement:

| Symbol | Module | Usage |
| :--- | :--- | :--- |
| `index_ready()` | `graphrag_service.py` | Check whether the GraphRAG index is built. |
| `AUDIENCE_INSTRUCTION` | `settings.py` | Audience → system-prompt mapping. |
| `LLM_CONFIG_AUTOGEN` | `settings.py` | AutoGen LLM configuration dict. |

## Coding Standards

- **Type Hinting**: All function signatures use modern Python type hints (`dict[str, str]`, `X | None`).
- **Docstrings**: All public functions/classes use Google-style docstrings.
- **Pathlib**: Use `pathlib.Path` over `os.path` everywhere.
- **Formatting**: Ruff with `line-length = 100`, `target-version = "py312"` (see `pyproject.toml`).
- **Import order**: stdlib → third-party → local (enforced by ruff `I` rules).
- **Async/Await**: The Chainlit app is asynchronous; ensure blocking calls are handled correctly.
- **Tests**: Use `monkeypatch`, stubs, and `tmp_path` — no real network or GPU calls.

## Common Workflows

### 1. Adding a New Feature to the Chat UI

1. Modify `src/onboard_ai/chainlit_app.py` to add new UI elements or logic.
2. Update `on_chat_start` for initialisation.
3. Update `on_message` for handling user input.

### 2. Tuning the RAG Pipeline

1. Edit `settings.yaml` to adjust chunk sizes, LLM parameters, or prompts.
2. Run `onboard-ai-bootstrap` to rebuild the index.

### 3. Adding a New Tool

1. Create the tool logic in `src/onboard_ai/tools/<category>/`.
2. Expose it via the category's `__init__.py`.
3. Add a `[project.scripts]` entry in `pyproject.toml` if it needs a CLI command.
4. Register it with the agent in `agent_factory.py` if needed.

### 4. Before Committing

```bash
ruff check src/ tests/
ruff format --check src/ tests/
pytest
```

Or, with pre-commit hooks installed: `pre-commit run --all-files`.
