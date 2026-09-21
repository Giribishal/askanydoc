"""Provider-neutral SharePoint retrieval boundary.

The real Microsoft provider can be added behind this interface without changing
or duplicating the existing S3/Aurora retrieval path.
"""

from __future__ import annotations

import time
import urllib.parse
from dataclasses import dataclass
from typing import Any, Protocol

from .sharepoint_config import SharePointConfig


class SharePointError(Exception):
    """A categorized SharePoint adapter failure."""

    def __init__(self, code: str, message: str, retryable: bool = False):
        super().__init__(message)
        self.code, self.retryable = code, retryable


@dataclass(frozen=True)
class SharePointEvidence:
    text: str
    source_name: str
    source_uri: str
    site: str
    classification: str
    modified_at: str | None = None
    page_number: int | None = None


class SharePointProvider(Protocol):
    def search(
        self,
        query: str,
        user_context: dict[str, str],
        max_results: int,
    ) -> list[dict[str, Any]]: ...


def match_allowed_site(web_url: str, config: SharePointConfig):
    """Return the configured site only for an exact host and path boundary match."""
    candidate = urllib.parse.urlsplit(web_url)
    if candidate.scheme.lower() != "https":
        return None
    candidate_path = urllib.parse.unquote(candidate.path).rstrip("/").casefold()
    for site in (config.general_site, config.restricted_site):
        allowed = urllib.parse.urlsplit(site.url)
        allowed_path = urllib.parse.unquote(allowed.path).rstrip("/").casefold()
        if (
            candidate.scheme.casefold() == allowed.scheme.casefold()
            and candidate.netloc.casefold() == allowed.netloc.casefold()
            and (
                candidate_path == allowed_path
                or candidate_path.startswith(f"{allowed_path}/")
            )
        ):
            return site
    return None


def _normalise(item: dict[str, Any]) -> SharePointEvidence:
    required = ("text", "name", "web_url", "site", "classification")
    if not all(isinstance(item.get(key), str) and item[key].strip() for key in required):
        raise SharePointError("malformed_response", "SharePoint evidence was incomplete")
    return SharePointEvidence(
        text=item["text"], source_name=item["name"], source_uri=item["web_url"],
        site=item["site"], classification=item["classification"],
        modified_at=item.get("modified_at"),
        page_number=(
            item.get("page_number")
            if isinstance(item.get("page_number"), int) else None
        ),
    )


def search_sharepoint(
    provider: SharePointProvider,
    query: str,
    user_context: dict[str, str],
    config: SharePointConfig,
    logger=None,
) -> list[SharePointEvidence]:
    if not config.enabled:
        return []
    if not user_context.get("user_id") or not user_context.get("access_token") or not query.strip():
        raise SharePointError("invalid_request", "authenticated user context and query are required")
    started = time.monotonic()
    attempts = 0
    while True:
        attempts += 1
        try:
            raw = provider.search(query.strip(), user_context, config.max_results)
            evidence = [_normalise(item) for item in raw[: config.max_results]]
            if logger:
                logger("sharepoint_search", {"status": "success", "attempts": attempts, "count": len(evidence), "latency_ms": round((time.monotonic() - started) * 1000)})
            return evidence
        except SharePointError as exc:
            if not exc.retryable or attempts > config.max_retries:
                raise
            time.sleep(min(0.25 * attempts, 1.0))
        except Exception as exc:
            retryable = getattr(exc, "retryable", False)
            if not retryable or attempts > config.max_retries:
                if logger:
                    logger("sharepoint_search", {"status": "failed", "attempts": attempts, "error": "provider_error"})
                raise SharePointError("provider_error", "SharePoint provider failed", retryable=False) from exc
