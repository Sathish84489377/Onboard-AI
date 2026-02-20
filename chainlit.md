# Onboard AI — Chainlit UI Guide

This repository now uses a clean-break modern structure. Chainlit handlers live in:

- `src/onboard_ai/chainlit_app.py`

## What the Chainlit UI provides

- Local and global GraphRAG search modes
- Audience-aware responses (`General`, `Developer`, `QA`, `Manager`)
- Optional specialist multi-agent routing toggle
- Web search fallback toggle (SearXNG), ON by default
- Citation visibility check in answers
- Graceful "index not ready" feedback before GraphRAG artifacts exist

Web search fallback is only used when local GraphRAG quality is weak (for example, missing `[Data: ...]` citations) or when the index is not ready.

## Run Chainlit

```bash
chainlit run src/onboard_ai/chainlit_app.py
```

## Related modules

- `src/onboard_ai/agent_factory.py`
- `src/onboard_ai/graphrag_service.py`
- `src/onboard_ai/settings.py`

For full setup and indexing/profiling commands, see `README.md`.

Runtime web fallback defaults come from `.env`; GraphRAG internals come from `settings.yaml`.
