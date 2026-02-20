from __future__ import annotations

import json
import os
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def _get_env_bool(name: str, default: bool = True) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def web_search_enabled(explicit_flag: bool | None = None) -> bool:
    if explicit_flag is not None:
        return explicit_flag
    return _get_env_bool("ENABLE_WEB_SEARCH", default=True)


def _searxng_search(query: str, max_results: int = 5) -> list[dict[str, str]]:
    base_url = os.getenv("SEARXNG_BASE_URL", "http://localhost:8080").rstrip("/")
    timeout = int(os.getenv("WEB_SEARCH_TIMEOUT_SECONDS", "8"))

    params = urlencode(
        {
            "q": query,
            "format": "json",
            "language": "en",
            "safesearch": 1,
        }
    )
    url = f"{base_url}/search?{params}"

    req = Request(url, headers={"User-Agent": "onboard-ai-web-search/1.0"})
    with urlopen(req, timeout=timeout) as response:  # nosec B310 - controlled URL from env
        payload = json.loads(response.read().decode("utf-8"))

    results: list[dict[str, str]] = []
    for item in payload.get("results", [])[:max_results]:
        title = str(item.get("title", "")).strip()
        content = str(item.get("content", "")).strip()
        link = str(item.get("url", "")).strip()
        if not link:
            continue
        results.append({"title": title, "content": content, "url": link})
    return results


def search_web(query: str, max_results: int = 5) -> list[dict[str, str]]:
    provider = os.getenv("WEB_SEARCH_PROVIDER", "searxng").strip().lower()
    if provider != "searxng":
        raise ValueError(
            f"Unsupported WEB_SEARCH_PROVIDER='{provider}'. Supported providers: searxng"
        )
    return _searxng_search(query=query, max_results=max_results)


def format_web_results(results: list[dict[str, str]]) -> str:
    if not results:
        return ""

    lines = ["### Web search context"]
    for r in results:
        title = r.get("title") or "Untitled"
        content = r.get("content") or ""
        snippet = content.replace("\n", " ").strip()
        if len(snippet) > 260:
            snippet = snippet[:257] + "..."
        lines.append(f"- {title}: {snippet} [Web: {r.get('url', '')}]")
    return "\n".join(lines)


def augment_answer_with_web(answer: str, query: str, max_results: int = 5) -> str:
    try:
        results = search_web(query=query, max_results=max_results)
    except Exception as exc:  # noqa: BLE001
        return (
            f"{answer}\n\n"
            f"_Web search fallback unavailable: {exc}. Continuing with local knowledge only._"
        )

    if not results:
        return f"{answer}\n\n_Web search found no additional results._"

    return f"{answer}\n\n{format_web_results(results)}"


def has_any_citation(answer: str) -> bool:
    return "[Data:" in answer or "[Web:" in answer
