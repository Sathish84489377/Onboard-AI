import os
import argparse
import traceback
import json
import math

os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
os.environ["IN_STREAMLIT"] = "true"
os.environ["PDFTEXT_CPU_WORKERS"] = "1"

import pypdfium2  # noqa: F401
import torch.multiprocessing as mp
from tqdm import tqdm
from marker.convert import convert_single_pdf  # type: ignore[import-not-found]
from marker.logger import configure_logging  # type: ignore[import-not-found]
from marker.models import load_all_models  # type: ignore[import-not-found]
from marker.output import markdown_exists, save_markdown  # type: ignore[import-not-found]
from marker.pdf.utils import find_filetype  # type: ignore[import-not-found]
from marker.pdf.extract_text import get_length_of_text  # type: ignore[import-not-found]
from marker.settings import settings  # type: ignore[import-not-found]

configure_logging()


def worker_init(shared_model):
    if shared_model is None:
        shared_model = load_all_models()

    global model_refs
    model_refs = shared_model


def worker_exit():
    global model_refs
    del model_refs


def process_single_pdf(args):
    filepath, out_folder, metadata, min_length = args

    fname = os.path.basename(filepath)
    if markdown_exists(out_folder, fname):
        return

    try:
        if min_length:
            filetype = find_filetype(filepath)
            if filetype == "other":
                return 0

            length = get_length_of_text(filepath)
            if length < min_length:
                return

        full_text, images, out_metadata = convert_single_pdf(
            filepath, model_refs, metadata=metadata, batch_multiplier=2
        )
        if len(full_text.strip()) > 0:
            save_markdown(out_folder, fname, full_text, images, out_metadata)
        else:
            print(f"Empty file: {filepath}. Could not convert.")
    except Exception as e:
        print(f"Error converting {filepath}: {e}")
        print(traceback.format_exc())


def multiple(
    in_folder: str,
    out_folder: str,
    workers: int = 10,
    chunk_idx: int = 0,
    num_chunks: int = 1,
    max_files: int | None = None,
    metadata_file: str | None = None,
    min_len: int | None = None,
):
    files = [os.path.join(in_folder, f) for f in os.listdir(in_folder)]
    files = [f for f in files if os.path.isfile(f)]
    os.makedirs(out_folder, exist_ok=True)

    chunk_size = math.ceil(len(files) / num_chunks)
    start_idx = chunk_idx * chunk_size
    end_idx = start_idx + chunk_size
    files_to_convert = files[start_idx:end_idx]

    if max_files:
        files_to_convert = files_to_convert[:max_files]

    metadata = {}
    if metadata_file:
        with open(os.path.abspath(metadata_file), "r", encoding="utf-8") as f:
            metadata = json.load(f)

    total_processes = min(len(files_to_convert), workers)

    if settings.CUDA:
        tasks_per_gpu = settings.INFERENCE_RAM // settings.VRAM_PER_TASK
        total_processes = int(min(tasks_per_gpu, total_processes))

    try:
        mp.set_start_method("spawn")
    except RuntimeError:
        raise RuntimeError(
            "Set start method to spawn twice. This may be temporary. Please run again."
        )

    if settings.TORCH_DEVICE == "mps" or settings.TORCH_DEVICE_MODEL == "mps":
        model_lst = None
    else:
        model_lst = load_all_models()
        for model in model_lst:
            if model is not None:
                model.share_memory()

    print(
        f"Converting {len(files_to_convert)} pdfs in chunk {chunk_idx + 1}/{num_chunks} "
        f"with {total_processes} processes, storing in {out_folder}"
    )
    task_args = [
        (f, out_folder, metadata.get(os.path.basename(f)), min_len) for f in files_to_convert
    ]

    with mp.Pool(processes=total_processes, initializer=worker_init, initargs=(model_lst,)) as pool:
        list(
            tqdm(
                pool.imap(process_single_pdf, task_args),
                total=len(task_args),
                desc="Processing PDFs",
                unit="pdf",
            )
        )
        pool._worker_handler.terminate = worker_exit

    del model_lst


def single(input_pdf: str, output_dir: str = "data/input/markdown"):
    model_lst = load_all_models()
    full_text, images, out_meta = convert_single_pdf(
        input_pdf,
        model_lst,
        max_pages=None,
        langs=None,
        batch_multiplier=2,
        start_page=None,
    )

    fname = os.path.basename(input_pdf)
    subfolder_path = save_markdown(output_dir, fname, full_text, images, out_meta)
    print(f"Saved markdown to {subfolder_path}")


def main():
    parser = argparse.ArgumentParser(description="Convert PDF files to markdown using marker-pdf.")
    parser.add_argument("--mode", choices=["single", "multiple"], default="single")
    parser.add_argument("--input-pdf", default="data/input/sample.pdf")
    parser.add_argument("--input-dir", default="data/input")
    parser.add_argument("--output-dir", default="data/input/markdown")
    parser.add_argument("--workers", type=int, default=10)
    args = parser.parse_args()

    if args.mode == "single":
        single(args.input_pdf, args.output_dir)
    else:
        multiple(args.input_dir, args.output_dir, workers=args.workers)


if __name__ == "__main__":
    main()
