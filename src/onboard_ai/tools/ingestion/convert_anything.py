import argparse
import json
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
    ".txt",
    ".md",
    ".log",
    ".py",
    ".js",
    ".ts",
    ".java",
    ".cpp",
    ".h",
}


def _convert_with_docling(file_path: Path, converter: DocumentConverter) -> str:
    result = converter.convert(str(file_path))
    return result.document.export_to_markdown()


def _convert_with_markitdown(file_path: Path, md: MarkItDown) -> str:
    result = md.convert(str(file_path))
    return result.text_content


def _convert_text(file_path: Path) -> str:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def convert_document(file_path: Path, converter: DocumentConverter, md: MarkItDown):
    """Convert document to markdown content and return (content, converter_name)."""
    ext = file_path.suffix.lower()
    print(f"Processing: {file_path}")

    if ext == ".pdf":
        print(" -> Using Docling for PDF conversion...")
        try:
            return _convert_with_docling(file_path, converter), "docling"
        except Exception as e:
            print(f" -> Docling failed ({e}). Falling back to MarkItDown...")
            return _convert_with_markitdown(file_path, md), "markitdown(fallback)"

    if ext in DOC_EXTENSIONS:
        print(f" -> Using MarkItDown for document format ({ext})...")
        return _convert_with_markitdown(file_path, md), "markitdown"

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
    md = MarkItDown()
    converted_count = 0
    skipped_count = 0

    for file in input_path.rglob("*"):
        if file.is_file() and not file.name.startswith("~"):
            try:
                if output_path in file.parents:
                    continue

                markdown_text, converter_name = convert_document(file, converter, md)

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
        f"Done. Converted: {converted_count} | Skipped: {skipped_count} | Metadata: {metadata_path}"
    )


if __name__ == "__main__":
    main()
