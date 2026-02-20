# Contributing to Onboard AI

Thank you for your interest in contributing! This document provides guidelines to ensure the project remains clean, consistent, and easy to understand for both humans and AI agents.

## Development Setup

1. **Prerequisites**:
    - Python 3.12+
    - Ollama (for local LLMs)
    - LiteLLM Proxy (recommended for AutoGen)

2. **Environment**:

    ```bash
    python -m venv .venv
    source .venv/bin/activate  # or .venv\Scripts\Activate on Windows
    pip install -e .[dev]
    pre-commit install
    ```

## Coding Standards

### Python

- **Style**: We use `ruff` for linting and formatting. configuration is in `pyproject.toml`.
- **Type Hints**: Strictly encouraged. Use `typing` module or modern syntax (`list[str]`, `dict[str, Any]`).
- **Docstrings**: Use Google-style docstrings for functions and classes.

    ```python
    def my_function(param: str) -> bool:
        """
        Does something important.

        Args:
            param: A description of the parameter.

        Returns:
            True if successful, False otherwise.
        """
        ...
    ```

### Imports

- Group imports: Standard library first, then third-party, then local application imports.
- Use absolute imports for local modules (e.g., `from onboard_ai.settings import ...` instead of `from .settings import ...`).

## Testing

Run tests before submitting changes:

```bash
pytest
```

Ensure new features have corresponding unit tests in `tests/`.

## Project Structure

Refer to `CONTEXT.md` for a detailed map of the project architecture and file responsibilities.

## Git Workflow

1. Create a feature branch (`feature/new-agent`, `fix/graph-query`).
2. Commit with clear, descriptive messages.
3. Open a Pull Request describing the changes and linking to any relevant issues.
