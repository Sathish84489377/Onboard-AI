from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path


def _install_graphrag_stub() -> None:
    if "graphrag.cli.query" in sys.modules:
        return

    graphrag_mod = types.ModuleType("graphrag")
    cli_mod = types.ModuleType("graphrag.cli")
    query_mod = types.ModuleType("graphrag.cli.query")

    def _run_local_search(**_: object) -> tuple[str, None]:
        return "", None

    def _run_global_search(**_: object) -> tuple[str, None]:
        return "", None

    query_mod.run_local_search = _run_local_search
    query_mod.run_global_search = _run_global_search

    sys.modules["graphrag"] = graphrag_mod
    sys.modules["graphrag.cli"] = cli_mod
    sys.modules["graphrag.cli.query"] = query_mod


def test_read_eval_cases_parses_tsv(tmp_path: Path) -> None:
    _install_graphrag_stub()
    gate = importlib.import_module("onboard_ai.tools.evaluation.local_quality_gate")

    cases_file = tmp_path / "cases.tsv"
    cases_file.write_text(
        "# comment\nDeveloper\tHow to run tests?\nQA\tWhat are release risks?\n",
        encoding="utf-8",
    )

    cases = gate.read_eval_cases(cases_file)

    assert cases == [
        {"audience": "Developer", "question": "How to run tests?"},
        {"audience": "QA", "question": "What are release risks?"},
    ]


def test_percentile_handles_edge_cases() -> None:
    _install_graphrag_stub()
    profiler = importlib.import_module("onboard_ai.tools.profiling.profile_queries")

    assert profiler.percentile([], 95) == 0.0
    assert profiler.percentile([1.0, 2.0, 3.0, 4.0], 50) == 3.0
