import argparse
import statistics
import time
from pathlib import Path

from graphrag.cli.query import run_global_search, run_local_search


def index_ready(root_dir: Path) -> bool:
    output_dir = root_dir / "data" / "output"
    if not output_dir.exists():
        return False
    if (output_dir / "lancedb").exists():
        return True
    if list(output_dir.rglob("*.parquet")):
        return True
    return False


def read_eval_cases(file_path: Path) -> list[dict]:
    cases: list[dict] = []
    for raw in file_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        parts = [p.strip() for p in line.split("\t")]
        if len(parts) != 2:
            raise ValueError(
                f"Invalid line in {file_path}: '{line}'. Expected '<Audience>\\t<Question>'"
            )

        audience, question = parts
        cases.append({"audience": audience, "question": question})

    return cases


def audience_instruction(audience: str) -> str:
    audience_map = {
        "General": "Use plain language and explain product terms briefly.",
        "Developer": "Focus on architecture, APIs, dependencies, and implementation detail.",
        "QA": "Focus on test scenarios, edge cases, validations, and release risk.",
        "Manager": "Focus on outcomes, timelines, risks, ownership, and business impact.",
    }
    return audience_map.get(audience, audience_map["General"])


def contains_citation(text: str) -> bool:
    return "[Data:" in text


def is_uncertain(text: str) -> bool:
    lowered = text.lower()
    triggers = [
        "i don't know",
        "i do not know",
        "not enough information",
        "insufficient information",
        "cannot determine",
        "can't determine",
        "not found in the provided",
    ]
    return any(t in lowered for t in triggers)


def run_query(
    *,
    root_dir: Path,
    query: str,
    mode: str,
    response_type: str,
    community: int,
) -> tuple[str, float]:
    start = time.perf_counter()
    if mode == "local":
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

    return result, time.perf_counter() - start


def main() -> int:
    parser = argparse.ArgumentParser(description="Local quality gate for onboarding chatbot.")
    parser.add_argument("--root", default=".", help="GraphRAG root directory (default: .)")
    parser.add_argument(
        "--cases",
        default="assets/prompts/onboarding_eval_queries.tsv",
        help="TSV file with '<Audience>\\t<Question>' per line.",
    )
    parser.add_argument("--mode", choices=["local", "global"], default="local")
    parser.add_argument("--response-type", default="single paragraph")
    parser.add_argument("--community", type=int, default=0)
    parser.add_argument("--repeat", type=int, default=1)

    parser.add_argument("--min-citation-rate", type=float, default=0.90)
    parser.add_argument("--max-uncertain-rate", type=float, default=0.25)
    parser.add_argument("--max-p95-latency", type=float, default=12.0)
    args = parser.parse_args()

    root_dir = Path(args.root)
    if not index_ready(root_dir):
        print("FAIL: index not ready. Add docs and run indexing, then run local quality gate.")
        return 2

    case_file = Path(args.cases)
    if not case_file.exists():
        print(f"FAIL: case file not found: {case_file}")
        return 2

    cases = read_eval_cases(case_file)
    if not cases:
        print("FAIL: no evaluation cases found.")
        return 2

    results = []
    print(f"Running local quality gate with {len(cases)} case(s), repeat={args.repeat}, mode={args.mode}")

    for case in cases:
        audience = case["audience"]
        question = case["question"]
        query = f"{question}\n\nAudience guidance: {audience_instruction(audience)}"

        for run in range(args.repeat):
            answer, latency = run_query(
                root_dir=root_dir,
                query=query,
                mode=args.mode,
                response_type=args.response_type,
                community=args.community,
            )
            cited = contains_citation(answer)
            uncertain = is_uncertain(answer)
            results.append(
                {
                    "audience": audience,
                    "question": question,
                    "latency": latency,
                    "cited": cited,
                    "uncertain": uncertain,
                }
            )
            print(
                f"- {audience:<9} | run={run + 1} | latency={latency:.2f}s | "
                f"citation={'Y' if cited else 'N'} | uncertain={'Y' if uncertain else 'N'}"
            )

    total = len(results)
    citation_rate = sum(1 for r in results if r["cited"]) / total
    uncertain_rate = sum(1 for r in results if r["uncertain"]) / total
    latencies = sorted(r["latency"] for r in results)
    p95_index = max(0, min(total - 1, int(round(0.95 * (total - 1)))))
    p95_latency = latencies[p95_index]
    mean_latency = statistics.mean(latencies)

    pass_citation = citation_rate >= args.min_citation_rate
    pass_uncertain = uncertain_rate <= args.max_uncertain_rate
    pass_latency = p95_latency <= args.max_p95_latency

    print("\nGate Summary")
    print(f"citation_rate={citation_rate:.2%} (target >= {args.min_citation_rate:.2%})")
    print(f"uncertain_rate={uncertain_rate:.2%} (target <= {args.max_uncertain_rate:.2%})")
    print(f"latency_mean={mean_latency:.2f}s")
    print(f"latency_p95={p95_latency:.2f}s (target <= {args.max_p95_latency:.2f}s)")

    if pass_citation and pass_uncertain and pass_latency:
        print("PASS: local quality gate passed.")
        return 0

    print("FAIL: local quality gate did not pass thresholds.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
