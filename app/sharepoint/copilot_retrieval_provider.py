"""Permission-aware SharePoint grounding through Microsoft 365 Copilot Retrieval."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from .microsoft_identity import acquire_graph_token
from .sharepoint_config import SharePointConfig
from .sharepoint_source import SharePointError, match_allowed_site


def _quote_kql_value(value: str) -> str:
    """Quote a trusted configuration value for a KQL property restriction."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _allowed_site_filter(config: SharePointConfig) -> str:
    """Restrict Copilot Retrieval to the approved SharePoint site paths."""
    paths = (
        config.general_site.url.rstrip("/"),
        config.restricted_site.url.rstrip("/"),
    )
    # Microsoft documents the SharePoint property as lowercase ``path``.
    # KQL is generally case-insensitive, but keeping the documented spelling
    # avoids silent unscoped retrieval if the parser becomes stricter.
    return " OR ".join(f'path:"{_quote_kql_value(path)}"' for path in paths)


class CopilotRetrievalProvider:
    """Call Microsoft's managed, permission-trimmed grounding API."""

    def __init__(self, config: SharePointConfig):
        self.config = config

    def search(self, query: str, user_context: dict[str, str], max_results: int) -> list[dict[str, Any]]:
        if len(query) > 1500:
            raise SharePointError(
                "invalid_request",
                "Microsoft 365 Copilot Retrieval queries are limited to 1,500 characters",
            )
        token = acquire_graph_token(user_context["access_token"], self.config.timeout_seconds)
        payload = {
            "queryString": query,
            "dataSource": "sharePoint",
            "filterExpression": _allowed_site_filter(self.config),
            "resourceMetadata": ["title"],
            "maximumNumberOfResults": min(max_results, 25),
        }
        request = urllib.request.Request(
            "https://graph.microsoft.com/v1.0/copilot/retrieval",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                result = json.loads(response.read())
        except urllib.error.HTTPError as error:
            code = {401: "sharepoint_unauthorized", 403: "sharepoint_forbidden", 429: "sharepoint_throttled"}.get(error.code, "sharepoint_upstream_error")
            raise SharePointError(code, "Microsoft 365 Copilot Retrieval failed", retryable=error.code >= 500 or error.code == 429) from error
        except urllib.error.URLError as error:
            reason = getattr(error, "reason", None)
            if isinstance(reason, TimeoutError):
                raise SharePointError("sharepoint_timeout", "Microsoft 365 Copilot Retrieval timed out", retryable=True) from error
            raise SharePointError("sharepoint_upstream_error", "Microsoft 365 Copilot Retrieval was unavailable", retryable=True) from error
        except TimeoutError as error:
            raise SharePointError("sharepoint_timeout", "Microsoft 365 Copilot Retrieval timed out", retryable=True) from error
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise SharePointError("malformed_response", "Microsoft 365 Copilot Retrieval returned invalid JSON") from error

        if not isinstance(result, dict) or not isinstance(result.get("retrievalHits", []), list):
            raise SharePointError("malformed_response", "Microsoft 365 Copilot Retrieval returned an invalid response")

        evidence: list[dict[str, Any]] = []
        for hit in result.get("retrievalHits", []):
            web_url = hit.get("webUrl")
            if not isinstance(web_url, str):
                continue
            site = match_allowed_site(web_url, self.config)
            if site is None:
                continue
            extract_items = hit.get("extracts", [])
            extracts = [e.get("text", "").strip() for e in extract_items if isinstance(e, dict) and isinstance(e.get("text"), str) and e.get("text", "").strip()]
            if not extracts:
                continue
            metadata = hit.get("resourceMetadata") or {}
            scores = [e.get("relevanceScore") for e in extract_items if isinstance(e, dict) and isinstance(e.get("relevanceScore"), (int, float))]
            evidence.append({
                "text": " ".join(extracts),
                "name": metadata.get("title") or "SharePoint document",
                "web_url": web_url,
                "site": site.name,
                "classification": site.classification,
                "relevance_score": max(scores) if scores else None,
            })
        return evidence[:max_results]
