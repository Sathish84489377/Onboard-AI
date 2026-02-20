"""Shared test fixtures for the Onboard AI test suite."""

from __future__ import annotations

import sys
import types

import pytest


@pytest.fixture(autouse=True)
def _graphrag_stub() -> None:
    """Install a lightweight stub for ``graphrag.cli.query`` into ``sys.modules``.

    This prevents tests from requiring the real (heavy) graphrag package and
    its transitive dependencies. The stub provides no-op ``run_local_search``
    and ``run_global_search`` functions that return ``("", None)``.
    """
    if "graphrag.cli.query" in sys.modules:
        return

    graphrag_mod = types.ModuleType("graphrag")
    cli_mod = types.ModuleType("graphrag.cli")
    query_mod = types.ModuleType("graphrag.cli.query")

    def _run_local_search(**_: object) -> tuple[str, None]:
        return "", None

    def _run_global_search(**_: object) -> tuple[str, None]:
        return "", None

    query_mod.run_local_search = _run_local_search  # type: ignore[attr-defined]
    query_mod.run_global_search = _run_global_search  # type: ignore[attr-defined]

    sys.modules["graphrag"] = graphrag_mod
    sys.modules["graphrag.cli"] = cli_mod
    sys.modules["graphrag.cli.query"] = query_mod
