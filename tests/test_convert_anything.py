from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from onboard_ai.tools.ingestion import convert_anything
from onboard_ai.tools.ingestion.convert_anything import convert_document


class _DoclingResult:
    class document:  # noqa: N801
        @staticmethod
        def export_to_markdown() -> str:
            return "docling-md"


class _DoclingConverterSuccess:
    def convert(self, _: str) -> _DoclingResult:
        return _DoclingResult()


class _DoclingConverterFail:
    def convert(self, _: str) -> _DoclingResult:
        raise RuntimeError("docling boom")


class _DoclingConverterMustNotRun:
    def convert(self, _: str) -> _DoclingResult:
        raise AssertionError("Docling should not be used for this test")


class _MarkItDownResult:
    text_content = "markitdown-md"


class _MarkItDownStub:
    def convert(self, _: str) -> _MarkItDownResult:
        return _MarkItDownResult()


def test_convert_document_docling_success_for_doc_extension(tmp_path: Path) -> None:
    source = tmp_path / "sample.docx"
    source.write_text("x", encoding="utf-8")

    content, converter_name = convert_document(
        source,
        _DoclingConverterSuccess(),
        cast(Any, _MarkItDownStub()),
        "markitdown",
        "auto",
        25,
        180,
    )

    assert content == "docling-md"
    assert converter_name == "docling"


def test_convert_document_falls_back_to_markitdown_when_enabled(tmp_path: Path) -> None:
    source = tmp_path / "sample.pdf"
    source.write_text("x", encoding="utf-8")

    content, converter_name = convert_document(
        source,
        _DoclingConverterFail(),
        cast(Any, _MarkItDownStub()),
        "markitdown",
        "auto",
        25,
        180,
    )

    assert content == "markitdown-md"
    assert converter_name == "markitdown(fallback)"


def test_convert_document_skips_when_fallback_is_off(tmp_path: Path) -> None:
    source = tmp_path / "sample.html"
    source.write_text("<h1>x</h1>", encoding="utf-8")

    content, converter_name = convert_document(
        source,
        _DoclingConverterFail(),
        None,
        "off",
        "auto",
        25,
        180,
    )

    assert content is None
    assert converter_name == "docling(failed-no-fallback)"


def test_convert_document_reads_text_directly(tmp_path: Path) -> None:
    source = tmp_path / "notes.txt"
    source.write_text("hello world", encoding="utf-8")

    content, converter_name = convert_document(
        source,
        _DoclingConverterSuccess(),
        cast(Any, _MarkItDownStub()),
        "markitdown",
        "auto",
        25,
        180,
    )

    assert content == "hello world"
    assert converter_name == "text-reader"


def test_convert_document_uses_markitdown_when_pdf_engine_forces_it(tmp_path: Path) -> None:
    source = tmp_path / "large.pdf"
    source.write_text("x", encoding="utf-8")

    content, converter_name = convert_document(
        source,
        _DoclingConverterMustNotRun(),
        cast(Any, _MarkItDownStub()),
        "markitdown",
        "markitdown",
        25,
        180,
    )

    assert content == "markitdown-md"
    assert converter_name == "markitdown(pdf-strategy)"


def test_convert_document_auto_prefers_markitdown_for_large_pdf(tmp_path: Path) -> None:
    source = tmp_path / "large-auto.pdf"
    source.write_bytes(b"x")

    content, converter_name = convert_document(
        source,
        _DoclingConverterMustNotRun(),
        cast(Any, _MarkItDownStub()),
        "markitdown",
        "auto",
        0,
        180,
    )

    assert content == "markitdown-md"
    assert converter_name == "markitdown(pdf-strategy)"


def test_convert_document_auto_prefers_markitdown_for_high_page_count(
    tmp_path: Path, monkeypatch
) -> None:
    source = tmp_path / "long.pdf"
    source.write_bytes(b"x")
    monkeypatch.setattr(convert_anything, "_get_pdf_page_count", lambda _p: 250)

    content, converter_name = convert_document(
        source,
        _DoclingConverterMustNotRun(),
        cast(Any, _MarkItDownStub()),
        "markitdown",
        "auto",
        999,
        180,
    )

    assert content == "markitdown-md"
    assert converter_name == "markitdown(pdf-strategy)"
