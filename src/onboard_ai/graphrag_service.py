from pathlib import Path

from graphrag.cli.query import run_global_search, run_local_search


def index_ready(root_dir: Path) -> bool:
    output_dir = root_dir / "data" / "output"
    if not output_dir.exists():
        return False

    known_artifacts = [
        output_dir / "lancedb",
        output_dir / "create_final_nodes.parquet",
        output_dir / "create_final_entities.parquet",
        output_dir / "create_final_community_reports.parquet",
    ]
    if any(path.exists() for path in known_artifacts):
        return True

    return bool(list(output_dir.rglob("*.parquet")))


def index_not_ready_message() -> str:
    return (
        "GraphRAG index is not ready yet.\\n\\n"
        "Next steps:\\n"
        "1) Add source files to the data/input folder.\\n"
        "2) Run GraphRAG indexing after all config changes are complete.\\n"
        "3) Retry your question once indexing finishes."
    )


def has_data_citation(answer: str) -> bool:
    return "[Data:" in answer


def query_graphrag(
    *,
    root_dir: Path,
    local_search: bool,
    community_level: int,
    response_type: str,
    query: str,
) -> str:
    if local_search:
        result, _ = run_local_search(
            data_dir=None,
            root_dir=root_dir,
            community_level=community_level,
            response_type=response_type,
            streaming=False,
            query=query,
            verbose=False,
        )
    else:
        result, _ = run_global_search(
            data_dir=None,
            root_dir=root_dir,
            community_level=community_level,
            dynamic_community_selection=False,
            response_type=response_type,
            streaming=False,
            query=query,
            verbose=False,
        )
    return result
