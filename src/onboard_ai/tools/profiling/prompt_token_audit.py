"""Prompt token auditor — measures and ranks optimisation headroom.

Reads prompt file paths from ``settings.yaml``, counts tokens (current vs.
git HEAD), estimates a lean-but-equivalent version, and produces Markdown +
JSON reports under ``assets/prompts/proofing/``.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

import tiktoken

PROMPT_KEY_PATTERN = re.compile(r"\b(?:\w+_)?prompt\s*:\s*[\"'](assets/prompts/[^\"']+)[\"']")


@dataclass
class PromptAuditRow:
    path: str
    before_tokens: int | None
    after_tokens: int
    delta_tokens: int | None
    delta_pct: float | None
    est_min_tokens: int
    headroom_tokens: int
    headroom_pct: float


def read_text(path: Path) -> str:
    """Read and return the UTF-8 text content of ``path``."""
    return path.read_text(encoding="utf-8")


def prompt_paths_from_settings(settings_path: Path) -> list[Path]:
    """Extract prompt file paths referenced in ``settings.yaml``."""
    text = read_text(settings_path)
    matches = PROMPT_KEY_PATTERN.findall(text)
    unique = sorted(set(matches))
    return [settings_path.parent / m for m in unique]


def token_count(text: str, encoding_name: str) -> int:
    """Count the number of tokens in ``text`` using the named tiktoken encoding."""
    enc = tiktoken.get_encoding(encoding_name)
    return len(enc.encode(text))


def git_show_head(repo_root: Path, relative_file: Path) -> str | None:
    """Return the file content at ``HEAD`` via ``git show``, or None on failure."""
    try:
        proc = subprocess.run(
            ["git", "show", f"HEAD:{relative_file.as_posix()}"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None

    if proc.returncode != 0:
        return None
    return proc.stdout


def estimate_minimal_prompt_text(text: str) -> str:
    """Estimate a lean-but-equivalent prompt by removing common verbose boilerplate."""
    keep: list[str] = []

    skip_patterns = [
        r"^\s*For example:\s*$",
        r'^\s*"This is an example sentence supported by',
        r"^\s*where\s+\d+.*represent the id",
        r"^\s*Add sections and commentary to the response as appropriate for the length and format\.?\s*$",
        r"^\s*Style the response in markdown\.?\s*$",
    ]
    skip_regexes = [re.compile(p, re.IGNORECASE) for p in skip_patterns]

    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        if any(r.search(line) for r in skip_regexes):
            continue
        keep.append(line)

    # Collapse repeated separator lines and duplicate consecutive lines.
    deduped: list[str] = []
    for line in keep:
        if deduped and line == deduped[-1]:
            continue
        if line.strip() in {"---", "#######"} and deduped and deduped[-1].strip() == line.strip():
            continue
        deduped.append(line)

    return "\n".join(deduped) + "\n"


def audit_prompt(repo_root: Path, prompt_path: Path, encoding_name: str) -> PromptAuditRow:
    """Audit a single prompt file: count tokens, compute delta vs HEAD, estimate headroom."""
    rel = prompt_path.relative_to(repo_root)
    after_text = read_text(prompt_path)
    before_text = git_show_head(repo_root, rel)

    before_tokens = token_count(before_text, encoding_name) if before_text is not None else None
    after_tokens = token_count(after_text, encoding_name)

    delta_tokens = (after_tokens - before_tokens) if before_tokens is not None else None
    delta_pct = (
        (delta_tokens / before_tokens) * 100.0
        if before_tokens and delta_tokens is not None
        else None
    )

    est_min_text = estimate_minimal_prompt_text(after_text)
    est_min_tokens = token_count(est_min_text, encoding_name)
    headroom_tokens = max(0, after_tokens - est_min_tokens)
    headroom_pct = (headroom_tokens / after_tokens * 100.0) if after_tokens else 0.0

    return PromptAuditRow(
        path=rel.as_posix(),
        before_tokens=before_tokens,
        after_tokens=after_tokens,
        delta_tokens=delta_tokens,
        delta_pct=delta_pct,
        est_min_tokens=est_min_tokens,
        headroom_tokens=headroom_tokens,
        headroom_pct=headroom_pct,
    )


def render_markdown(rows: list[PromptAuditRow], encoding_name: str) -> str:
    """Render a Markdown report from audit rows."""
    total_before = sum(r.before_tokens for r in rows if r.before_tokens is not None)
    total_after = sum(r.after_tokens for r in rows)
    comparable = [r for r in rows if r.before_tokens is not None]
    total_delta = sum(r.delta_tokens for r in comparable if r.delta_tokens is not None)
    top = sorted(rows, key=lambda r: r.headroom_tokens, reverse=True)

    lines = [
        "# Prompt token audit",
        "",
        f"- tokenizer: `{encoding_name}`",
        f"- prompts audited: {len(rows)}",
        f"- total after tokens: {total_after}",
    ]

    if comparable:
        pct = (total_delta / total_before * 100.0) if total_before else 0.0
        lines.append(f"- total before tokens (git HEAD): {total_before}")
        lines.append(f"- total delta: {total_delta:+d} ({pct:+.2f}%)")
    else:
        lines.append("- total before tokens (git HEAD): not available")

    lines.extend(
        [
            "",
            "## Per prompt",
            "",
            "| Prompt | Before | After | Delta | Est. minimal | Headroom |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )

    for r in rows:
        before = str(r.before_tokens) if r.before_tokens is not None else "n/a"
        delta = f"{r.delta_tokens:+d}" if r.delta_tokens is not None else "n/a"
        lines.append(
            f"| `{r.path}` | {before} | {r.after_tokens} | {delta} | {r.est_min_tokens} | {r.headroom_tokens} ({r.headroom_pct:.1f}%) |"
        )

    lines.extend(["", "## Optimization headroom ranking", ""])
    for i, r in enumerate(top, 1):
        lines.append(f"{i}. `{r.path}` — {r.headroom_tokens} tokens ({r.headroom_pct:.1f}%)")

    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- `Before` comes from `git show HEAD:<path>` when available.")
    lines.append("- `Est. minimal` is a heuristic lower bound, not a semantic rewrite.")
    lines.append("- Use ranking to prioritize proofing work on highest-headroom prompts.")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit prompt token usage (before/after) and rank optimization headroom."
    )
    parser.add_argument("--root", default=".", help="Repository root directory")
    parser.add_argument("--settings", default="settings.yaml", help="Path to settings yaml")
    parser.add_argument("--encoding", default="cl100k_base", help="tiktoken encoding name")
    parser.add_argument(
        "--output-md",
        default="assets/prompts/proofing/prompt_token_audit.md",
        help="Markdown report output path",
    )
    parser.add_argument(
        "--output-json",
        default="assets/prompts/proofing/prompt_token_audit.json",
        help="JSON report output path",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    settings_path = (root / args.settings).resolve()
    if not settings_path.exists():
        print(f"Settings file not found: {settings_path}")
        return 2

    prompt_paths = [p.resolve() for p in prompt_paths_from_settings(settings_path) if p.exists()]
    if not prompt_paths:
        print("No prompt files found from settings.")
        return 2

    rows = [audit_prompt(root, p, args.encoding) for p in prompt_paths]
    rows = sorted(rows, key=lambda r: r.path)

    md = render_markdown(rows, args.encoding)
    out_md = (root / args.output_md).resolve()
    out_json = (root / args.output_json).resolve()
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(md, encoding="utf-8")
    out_json.write_text(
        json.dumps(
            {
                "encoding": args.encoding,
                "rows": [asdict(r) for r in rows],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Wrote markdown report: {out_md}")
    print(f"Wrote json report: {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
