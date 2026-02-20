import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import uvicorn

from onboard_ai.graphrag_service import index_ready


REQUIRED_OLLAMA_MODELS = ("mistral-nemo", "nomic-embed-text", "llama3")


def _run_step(command: list[str], *, cwd: Path, label: str) -> None:
    print(f"[onboard-ai] {label}: {' '.join(command)}")
    subprocess.run(command, cwd=str(cwd), check=True)


def _assert_ollama_installed() -> None:
    if shutil.which("ollama") is None:
        raise SystemExit(
            "Ollama is not installed or not on PATH. Install Ollama first, then retry."
        )


def _assert_chainlit_installed() -> None:
    if shutil.which("chainlit") is None:
        raise SystemExit(
            "Chainlit command not found. Install project dependencies with 'pip install -e .[dev]'."
        )


def bootstrap() -> None:
    parser = argparse.ArgumentParser(
        description="Bootstrap Onboard AI: pull models, convert docs, and build GraphRAG index."
    )
    parser.add_argument("--root", default=".", help="Project root directory (default: .)")
    parser.add_argument(
        "--input-dir",
        default="data/input",
        help="Source documents directory (default: data/input)",
    )
    parser.add_argument(
        "--output-dir",
        default="data/input/markdown",
        help="Converted markdown output directory (default: data/input/markdown)",
    )
    parser.add_argument(
        "--skip-model-pull",
        action="store_true",
        help="Skip 'ollama pull' for required models.",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    input_dir = (root / args.input_dir).resolve()

    if not input_dir.exists():
        raise SystemExit(f"Input directory not found: {input_dir}")

    _assert_ollama_installed()

    if not args.skip_model_pull:
        for model in REQUIRED_OLLAMA_MODELS:
            _run_step(["ollama", "pull", model], cwd=root, label=f"Pull model '{model}'")

    _run_step(
        [
            sys.executable,
            "-m",
            "onboard_ai.tools.ingestion.convert_anything",
            args.input_dir,
            args.output_dir,
        ],
        cwd=root,
        label="Convert source docs to markdown",
    )

    _run_step(
        [sys.executable, "-m", "graphrag.index", "--root", str(root)],
        cwd=root,
        label="Build GraphRAG index",
    )

    if not index_ready(root):
        raise SystemExit(
            "Bootstrap finished but GraphRAG index artifacts were not detected in data/output."
        )

    print("[onboard-ai] Bootstrap complete. Next: run 'onboard-ai-ui' or 'onboard-ai-api'.")


def run_ui() -> None:
    _assert_chainlit_installed()
    subprocess.run(["chainlit", "run", "src/onboard_ai/chainlit_app.py"], check=True)


def run_api() -> None:
    uvicorn.run("onboard_ai.api.main:app", host="0.0.0.0", port=8000, reload=True)
