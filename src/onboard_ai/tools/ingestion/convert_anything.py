import argparse
import json
import os
from pathlib import Path

from docling.document_converter import DocumentConverter
from markitdown import MarkItDown

DOC_EXTENSIONS = {
    ".pdf",
    ".pptx",
    ".docx",
    ".xlsx",
    ".html",
    ".htm",
    ".csv",
    ".json",
    ".xml",
}

TEXT_EXTENSIONS = {
    ".txt",  # Plain notes / lightweight docs
    ".md",  # Primary authored knowledge docs
    ".log",  # Operational notes when intentionally included
    # Code extensions intentionally excluded for now to reduce ingestion noise:
    # .py, .js, .ts, .java, .cpp, .h
}


def _convert_with_docling(file_path: Path, converter) -> str:
    result = converter.convert(str(file_path))
    return result.document.export_to_markdown()


def _convert_with_markitdown(file_path: Path, md: MarkItDown) -> str:
    result = md.convert(str(file_path))
    return result.text_content


def _convert_text(file_path: Path) -> str:
    with open(file_path, encoding="utf-8", errors="ignore") as f:
        return f.read()


def _get_pdf_page_count(file_path: Path) -> int | None:
    try:
        import pypdfium2 as pdfium

        pdf = pdfium.PdfDocument(str(file_path))
        return len(pdf)
    except Exception:
        return None


def _prefer_markitdown_for_pdf(
    *,
    file_path: Path,
    pdf_engine: str,
    pdf_docling_max_mb: int,
    pdf_docling_max_pages: int,
    md: MarkItDown | None,
) -> bool:
    if file_path.suffix.lower() != ".pdf" or md is None:
        return False

    if pdf_engine == "markitdown":
        return True

    if pdf_engine == "docling":
        return False

    # auto mode: avoid Docling for large PDFs where preprocess can hit std::bad_alloc
    file_size_mb = file_path.stat().st_size / (1024 * 1024)
    if file_size_mb >= pdf_docling_max_mb:
        return True

    if pdf_docling_max_pages > 0:
        page_count = _get_pdf_page_count(file_path)
        if page_count is not None and page_count >= pdf_docling_max_pages:
            return True

    return False


def convert_document(
    file_path: Path,
    converter,
    md: MarkItDown | None,
    fallback_engine: str,
    pdf_engine: str,
    pdf_docling_max_mb: int,
    pdf_docling_max_pages: int,
):
    """Convert document to markdown content and return (content, converter_name)."""
    ext = file_path.suffix.lower()
    print(f"Processing: {file_path}")

    if ext in DOC_EXTENSIONS:
        if _prefer_markitdown_for_pdf(
            file_path=file_path,
            pdf_engine=pdf_engine,
            pdf_docling_max_mb=pdf_docling_max_mb,
            pdf_docling_max_pages=pdf_docling_max_pages,
            md=md,
        ):
            print(" -> Using MarkItDown for PDF (configured strategy)...")
            return _convert_with_markitdown(file_path, md), "markitdown(pdf-strategy)"

        print(f" -> Using Docling for document format ({ext})...")
        try:
            return _convert_with_docling(file_path, converter), "docling"
        except Exception as e:
            if fallback_engine == "markitdown" and md is not None:
                print(f" -> Docling failed ({e}). Falling back to MarkItDown...")
                return _convert_with_markitdown(file_path, md), "markitdown(fallback)"
            print(f" -> Docling failed ({e}). Fallback disabled; skipping.")
            return None, "docling(failed-no-fallback)"

    if ext in TEXT_EXTENSIONS:
        print(" -> Reading text file directly...")
        return _convert_text(file_path), "text-reader"

    print(f" -> Warning: Unsupported format {ext}. Skipping.")
    return None, "unsupported"


def _build_markdown_payload(markdown_text: str, source_file: Path, converter_name: str) -> str:
    header = [
        "---",
        f"source_path: {source_file.as_posix()}",
        f"converter: {converter_name}",
        "---",
        "",
    ]
    return "\n".join(header) + markdown_text


def main():
    parser = argparse.ArgumentParser(
        description="Universal document converter for GraphRAG ingestion"
    )
    parser.add_argument(
        "input_dir",
        nargs="?",
        default="data/input",
        help="Directory containing source documents (default: data/input)",
    )
    parser.add_argument(
        "output_dir",
        nargs="?",
        default="data/input/markdown",
        help="Directory to save converted markdown files (default: data/input/markdown)",
    )
    parser.add_argument(
        "--metadata-file",
        default="data/input/markdown/_sources.jsonl",
        help="Path to JSONL metadata output file (default: data/input/markdown/_sources.jsonl)",
    )
    parser.add_argument(
        "--fallback-engine",
        choices=["markitdown", "off"],
        default=os.getenv("FALLBACK_ENGINE", "markitdown"),
        help="Fallback engine when Docling fails: markitdown|off (default: env FALLBACK_ENGINE or markitdown)",
    )
    parser.add_argument(
        "--pdf-engine",
        choices=["auto", "docling", "markitdown"],
        default=os.getenv("PDF_ENGINE", "docling"),
        help=(
            "PDF conversion strategy: auto|docling|markitdown (default: env PDF_ENGINE or docling)."
        ),
    )
    parser.add_argument(
        "--pdf-docling-max-mb",
        type=int,
        default=int(os.getenv("PDF_DOCLING_MAX_MB", "25")),
        help=(
            "In --pdf-engine auto mode, PDFs at or above this size use MarkItDown "
            "to reduce Docling memory pressure (default: env PDF_DOCLING_MAX_MB or 25)."
        ),
    )
    parser.add_argument(
        "--pdf-docling-max-pages",
        type=int,
        default=int(os.getenv("PDF_DOCLING_MAX_PAGES", "0")),
        help=(
            "In --pdf-engine auto mode, PDFs at or above this page count use MarkItDown "
            "to avoid Docling OCR memory spikes (default: env PDF_DOCLING_MAX_PAGES or 0=disabled)."
        ),
    )
    args = parser.parse_args()

    input_path = Path(args.input_dir)
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    metadata_path = Path(args.metadata_file)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        print(f"Error: Input directory '{input_path}' not found.")
        return

    converter = DocumentConverter()
    md = MarkItDown() if args.fallback_engine == "markitdown" else None
    converted_count = 0
    skipped_count = 0

    for file in input_path.rglob("*"):
        if file.is_file() and not file.name.startswith("~"):
            try:
                if output_path in file.parents:
                    continue

                markdown_text, converter_name = convert_document(
                    file,
                    converter,
                    md,
                    args.fallback_engine,
                    args.pdf_engine,
                    args.pdf_docling_max_mb,
                    args.pdf_docling_max_pages,
                )

                if markdown_text:
                    rel_path = file.relative_to(input_path)
                    output_file = (output_path / rel_path).with_suffix(".md")
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    payload = _build_markdown_payload(markdown_text, file, converter_name)

                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(payload)

                    meta_record = {
                        "source_path": str(file),
                        "output_markdown": str(output_file),
                        "converter": converter_name,
                        "bytes": file.stat().st_size,
                    }
                    with open(metadata_path, "a", encoding="utf-8") as mf:
                        mf.write(json.dumps(meta_record, ensure_ascii=False) + "\n")

                    print(f" -> Saved to: {output_file}")
                    converted_count += 1
                else:
                    skipped_count += 1

            except Exception as e:
                print(f" -> ERROR converting {file.name}: {e}")

    print(
        f"Done. Converted: {converted_count} | Skipped: {skipped_count} | "
        f"Fallback: {args.fallback_engine} | Metadata: {metadata_path}"
    )


if __name__ == "__main__":
    main()
