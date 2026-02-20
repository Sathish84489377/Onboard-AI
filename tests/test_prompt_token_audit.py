from pathlib import Path

from onboard_ai.tools.profiling.prompt_token_audit import (
    estimate_minimal_prompt_text,
    prompt_paths_from_settings,
)


def test_prompt_paths_from_settings_extracts_prompt_keys(tmp_path: Path) -> None:
    settings = tmp_path / "settings.yaml"
    settings.write_text(
        '\n'.join(
            [
                'local_search:',
                '  prompt: "assets/prompts/local_search_system_prompt.txt"',
                'global_search:',
                '  map_prompt: "assets/prompts/global_search_map_system_prompt.txt"',
                '  reduce_prompt: "assets/prompts/global_search_reduce_system_prompt.txt"',
                '  knowledge_prompt: "assets/prompts/global_search_knowledge_system_prompt.txt"',
            ]
        ),
        encoding="utf-8",
    )

    paths = prompt_paths_from_settings(settings)
    rel = [p.relative_to(tmp_path).as_posix() for p in paths]

    assert rel == [
        "assets/prompts/global_search_knowledge_system_prompt.txt",
        "assets/prompts/global_search_map_system_prompt.txt",
        "assets/prompts/global_search_reduce_system_prompt.txt",
        "assets/prompts/local_search_system_prompt.txt",
    ]


def test_estimate_minimal_prompt_text_removes_verbose_boilerplate() -> None:
    raw = """
---Goal---

Do the task.

For example:
"This is an example sentence supported by multiple data references [Data: Sources (record ids)]."

Add sections and commentary to the response as appropriate for the length and format.
Style the response in markdown.
"""

    minimized = estimate_minimal_prompt_text(raw)

    assert "For example:" not in minimized
    assert "This is an example sentence" not in minimized
    assert "Add sections and commentary" not in minimized
    assert "Style the response in markdown" not in minimized
    assert "Do the task." in minimized
