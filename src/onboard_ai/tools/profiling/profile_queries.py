"""Latency and memory profiler for GraphRAG queries.

Runs a set of queries (from file or built-in defaults) against the index and
reports mean/p50/p95 latency plus RSS memory deltas.
"""

import argparse
import statistics
import time
from collections.abc import Iterable
from pathlib import Path

import psutil
from graphrag.cli.query import run_global_search, run_local_search

from onboard_ai.graphrag_service import index_ready


def read_queries(query_file: Path | None) -> list[str]:
    """Read queries from a file or return built-in defaults if ``query_file`` is None."""
    if query_file is None:
        return [
            "What is this product and who should use it?",
            "Summarize onboarding steps for a new developer.",
            "List quality risks and test recommendations for QA.",
            "Provide a manager-level summary with milestones and blockers.",
        ]

    queries = []
    for line in query_file.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        queries.append(text)
    return queries


def run_once(
    *,
    root_dir: Path,
    query: str,
    local: bool,
    response_type: str,
    community: int,
) -> tuple[float, float, int]:
    """Run a single query and return (latency_secs, rss_delta_mb, answer_len)."""
    proc = psutil.Process()
    rss_before = proc.memory_info().rss
    start = time.perf_counter()

    if local:
        result, _ = run_local_search(
            data_dir=None,
            root_dir=root_dir,
            community_level=community,
            response_type=response_type,
            streaming=False,
            query=query,
            verbose=False,
        )
    else:
        result, _ = run_global_search(
            data_dir=None,
            root_dir=root_dir,
            community_level=community,
            dynamic_community_selection=False,
            response_type=response_type,
            streaming=False,
            query=query,
            verbose=False,
        )

    elapsed = time.perf_counter() - start
    rss_after = proc.memory_info().rss
    delta_mb = (rss_after - rss_before) / (1024 * 1024)
    return elapsed, delta_mb, len(result)


def percentile(values: Iterable[float], p: float) -> float:
    """Compute the ``p``-th percentile from ``values`` using nearest-rank."""
    seq = sorted(values)
    if not seq:
        return 0.0
    k = max(0, min(len(seq) - 1, int(round((p / 100) * (len(seq) - 1)))))
    return seq[k]


def main() -> None:
    """CLI entry point for the query profiler."""
    parser = argparse.ArgumentParser(description="Profile GraphRAG query latency and memory.")
    parser.add_argument("--root", default=".", help="GraphRAG root directory (default: .)")
    parser.add_argument(
        "--query-file",
        default=None,
        help="Optional text file with one query per line.",
    )
    parser.add_argument(
        "--mode",
        choices=["local", "global"],
        default="local",
        help="Search mode to benchmark.",
    )
    parser.add_argument(
        "--response-type",
        default="single paragraph",
        help="GraphRAG response type.",
    )
    parser.add_argument("--community", type=int, default=0, help="Community level.")
    parser.add_argument("--repeat", type=int, default=1, help="Repeat each query N times.")
    args = parser.parse_args()

    root_dir = Path(args.root)
    if not index_ready(root_dir):
        print("Index not ready. Add docs and run indexing later, then re-run this profiler.")
        return

    query_file = Path(args.query_file) if args.query_file else None
    queries = read_queries(query_file)
    if not queries:
        print("No queries found. Provide a non-empty query file.")
        return

    latencies = []
    mem_deltas = []
    lengths = []

    print(f"Profiling {len(queries)} query(ies), repeat={args.repeat}, mode={args.mode}...")
    for query in queries:
        for i in range(args.repeat):
            elapsed, delta_mb, length = run_once(
                root_dir=root_dir,
                query=query,
                local=args.mode == "local",
                response_type=args.response_type,
                community=args.community,
            )
            latencies.append(elapsed)
            mem_deltas.append(delta_mb)
            lengths.append(length)
            print(
                f"- {query[:60]}{'...' if len(query) > 60 else ''} | run={i + 1} "
                f"| latency={elapsed:.2f}s | rss_delta={delta_mb:.2f}MB | chars={length}"
            )

    print("\nSummary")
    print(f"count={len(latencies)}")
    print(f"latency mean={statistics.mean(latencies):.2f}s")
    print(f"latency p50={percentile(latencies, 50):.2f}s")
    print(f"latency p95={percentile(latencies, 95):.2f}s")
    print(f"rss delta mean={statistics.mean(mem_deltas):.2f}MB")
    print(f"rss delta p95={percentile(mem_deltas, 95):.2f}MB")
    print(f"response chars mean={statistics.mean(lengths):.1f}")


if __name__ == "__main__":
    main()
