from __future__ import annotations

from types import SimpleNamespace

from onboard_ai import cli


def test_ollama_model_available_returns_true(monkeypatch) -> None:
    def _run(*_args, **_kwargs):
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(cli.subprocess, "run", _run)
    assert cli._ollama_model_available("deepseek-r1:8b") is True


def test_ollama_model_available_returns_false_on_nonzero(monkeypatch) -> None:
    def _run(*_args, **_kwargs):
        return SimpleNamespace(returncode=1)

    monkeypatch.setattr(cli.subprocess, "run", _run)
    assert cli._ollama_model_available("deepseek-r1:8b") is False


def test_ollama_model_available_returns_false_on_exception(monkeypatch) -> None:
    def _run(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(cli.subprocess, "run", _run)
    assert cli._ollama_model_available("deepseek-r1:8b") is False
