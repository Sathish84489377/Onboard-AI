# Onboard AI — Chainlit UI Guide

Chainlit handlers live in:

- `src/onboard_ai/chainlit_app.py`

Recommended launcher command:

- `onboard-ai-ui`

## What the Chainlit UI provides

- Local and global GraphRAG search modes
- Audience-aware responses (`General`, `Developer`, `QA`, `Manager`)
- Optional specialist multi-agent routing toggle
- Web search fallback toggle (SearXNG), ON by default
- Citation visibility check in answers
- Graceful "index not ready" feedback before GraphRAG artifacts exist

Web search fallback is only used when local GraphRAG quality is weak (for example, missing `[Data: ...]` citations) or when the index is not ready.

## Before you run

1. Install dependencies: `pip install -e .[dev]`
2. Build index artifacts at least once: `onboard-ai-bootstrap`
3. For faster repeat runs: `onboard-ai-bootstrap --skip-model-pull`

## Run Chainlit

Recommended:

```bash
onboard-ai-ui
```

Direct command (equivalent):

```bash
chainlit run src/onboard_ai/chainlit_app.py
```

Default UI URL: `http://localhost:8000`

## Quick UI validation

After launch:

1. Confirm the chat page opens in browser.
2. Ask: `What does this project do?`
3. Verify the answer is non-empty.

If GraphRAG index is not ready, the app shows guidance and can still use optional web fallback.

## Related modules

- `src/onboard_ai/agent_factory.py`
- `src/onboard_ai/graphrag_service.py`
- `src/onboard_ai/services/web_search.py`
- `src/onboard_ai/settings.py`

For full setup and indexing/profiling commands, see `README.md`.

Runtime web fallback defaults come from `.env`; GraphRAG internals come from `settings.yaml`.
