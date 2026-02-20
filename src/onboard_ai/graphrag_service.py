"""Core GraphRAG service layer.

Provides index-readiness checks, search execution (local/global), and
citation detection. This is the single source of truth for ``index_ready()``
which other modules should import rather than re-implementing.
"""

from pathlib import Path

from graphrag.cli.query import run_global_search, run_local_search


def index_ready(root_dir: Path) -> bool:
    """Check whether the GraphRAG index has been built.

    Looks for known artifact files (lancedb, parquet) under
    ``<root_dir>/data/output``.

    Args:
        root_dir: Project root containing the ``data/`` directory.

    Returns:
        True if at least one index artifact exists.
    """
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
    """Return a user-facing message explaining the index is not built yet."""
    return (
        "GraphRAG index is not ready yet.\n\n"
        "Next steps:\n"
        "1) Add source files to the data/input folder.\n"
        "2) Run GraphRAG indexing after all config changes are complete.\n"
        "3) Retry your question once indexing finishes."
    )


def has_data_citation(answer: str) -> bool:
    """Return True if ``answer`` contains a GraphRAG ``[Data: ...]`` citation."""
    return "[Data:" in answer


def query_graphrag(
    *,
    root_dir: Path,
    local_search: bool,
    community_level: int,
    response_type: str,
    query: str,
) -> str:
    """Execute a GraphRAG local or global search and return the answer text.

    Args:
        root_dir: Project root for GraphRAG data.
        local_search: Use local search when True, global search otherwise.
        community_level: Community hierarchy level for the search.
        response_type: Desired response format (e.g. 'single paragraph').
        query: The natural-language question.

    Returns:
        The answer string produced by GraphRAG.
    """
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
