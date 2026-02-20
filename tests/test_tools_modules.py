from __future__ import annotations

import importlib
from pathlib import Path


def test_read_eval_cases_parses_tsv(tmp_path: Path) -> None:
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
    profiler = importlib.import_module("onboard_ai.tools.profiling.profile_queries")

    assert profiler.percentile([], 95) == 0.0
    assert profiler.percentile([1.0, 2.0, 3.0, 4.0], 50) == 3.0
