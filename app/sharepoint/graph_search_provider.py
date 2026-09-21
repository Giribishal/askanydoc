"""Permission-aware SharePoint retrieval through Microsoft Graph Search."""

from __future__ import annotations

import html
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from .microsoft_identity import acquire_graph_token
from .pdf_grounding import extract_relevant_pdf_pages
from .sharepoint_config import SharePointConfig
from .sharepoint_source import SharePointError, match_allowed_site


_HTML_TAG = re.compile(r"<[^>]+>")


def _quote_kql_value(value: str) -> str:
    """Quote a trusted configuration value for a KQL property restriction."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _allowed_site_filter(config: SharePointConfig) -> str:
    """Restrict Graph Search to the approved SharePoint site paths."""
    paths = (
        config.general_site.url.rstrip("/"),
        config.restricted_site.url.rstrip("/"),
    )
    return " OR ".join(f'Path:"{_quote_kql_value(path)}"' for path in paths)


def _scoped_query(query: str, config: SharePointConfig) -> str:
    # Parentheses ensure user-supplied KQL operators cannot remove the mandatory
    # site boundary. URL post-filtering below remains a second control.
    return f"({query}) AND ({_allowed_site_filter(config)})"


def _error_from_http(error: urllib.error.HTTPError, action: str) -> SharePointError:
    code = {
        401: "sharepoint_unauthorized",
        403: "sharepoint_forbidden",
        404: "sharepoint_not_found",
        429: "sharepoint_throttled",
    }.get(error.code, "sharepoint_upstream_error")
    return SharePointError(
        code,
        f"Microsoft Graph {action} failed",
        retryable=error.code >= 500 or error.code == 429,
    )


def _download_drive_item(
    graph_token: str,
    drive_id: str,
    item_id: str,
    maximum_bytes: int,
    timeout_seconds: float,
) -> bytes:
    """Resolve Graph's short-lived download URL, then fetch it without a bearer token."""
    quoted_drive = urllib.parse.quote(drive_id, safe="")
    quoted_item = urllib.parse.quote(item_id, safe="")
    select = urllib.parse.urlencode({"$select": "id,name,size,file,@microsoft.graph.downloadUrl"})
    metadata_request = urllib.request.Request(
        f"https://graph.microsoft.com/v1.0/drives/{quoted_drive}/items/{quoted_item}?{select}",
        headers={"Authorization": f"Bearer {graph_token}"},
    )
    try:
        with urllib.request.urlopen(metadata_request, timeout=timeout_seconds) as response:
            metadata = json.loads(response.read())
    except urllib.error.HTTPError as error:
        raise _error_from_http(error, "file metadata request") from error
    except TimeoutError as error:
        raise SharePointError("sharepoint_timeout", "Microsoft Graph file metadata timed out", retryable=True) from error

    size = metadata.get("size")
    if isinstance(size, int) and size > maximum_bytes:
        raise SharePointError("document_too_large", "The SharePoint file exceeds the byte limit")
    download_url = metadata.get("@microsoft.graph.downloadUrl")
    if not isinstance(download_url, str) or urllib.parse.urlparse(download_url).scheme != "https":
        raise SharePointError("malformed_response", "Microsoft Graph omitted a valid download URL")

    # The short-lived URL is preauthenticated. Never forward the Graph bearer token
    # to the storage host returned in the redirect.
    try:
        with urllib.request.urlopen(download_url, timeout=timeout_seconds) as response:
            file_bytes = response.read(maximum_bytes + 1)
    except urllib.error.HTTPError as error:
        raise _error_from_http(error, "file download") from error
    except TimeoutError as error:
        raise SharePointError("sharepoint_timeout", "Microsoft Graph file download timed out", retryable=True) from error
    if len(file_bytes) > maximum_bytes:
        raise SharePointError("document_too_large", "The SharePoint file exceeds the byte limit")
    return file_bytes


class GraphSearchProvider:
    def __init__(self, config: SharePointConfig):
        self.config = config

    def search(
        self,
        query: str,
        user_context: dict[str, str],
        max_results: int,
    ) -> list[dict[str, Any]]:
        graph_token = acquire_graph_token(
            user_context["access_token"],
            self.config.timeout_seconds,
        )
        payload = {
            "requests": [{
                "entityTypes": ["driveItem"],
                "query": {"queryString": _scoped_query(query, self.config)},
                "from": 0,
                "size": min(max_results, 25),
                "fields": [
                    "id", "name", "webUrl", "lastModifiedDateTime",
                    "parentReference", "size", "file",
                ],
            }]
        }
        request = urllib.request.Request(
            "https://graph.microsoft.com/v1.0/search/query",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {graph_token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                result = json.loads(response.read())
        except urllib.error.HTTPError as error:
            raise _error_from_http(error, "search") from error
        except TimeoutError as error:
            raise SharePointError("sharepoint_timeout", "Microsoft Graph search timed out", retryable=True) from error

        hits: list[dict[str, Any]] = []
        for response_set in result.get("value", []):
            for container in response_set.get("hitsContainers", []):
                hits.extend(container.get("hits", []))

        evidence = []
        hydrated_files = 0
        for hit in hits:
            resource = hit.get("resource", {})
            web_url = resource.get("webUrl")
            if not isinstance(web_url, str):
                continue
            matching_site = match_allowed_site(web_url, self.config)
            if matching_site is None:
                continue
            summary = html.unescape(_HTML_TAG.sub(" ", hit.get("summary", "")))
            summary = " ".join(summary.split())
            name = resource.get("name") or "SharePoint document"
            parent = resource.get("parentReference") or {}
            drive_id = parent.get("driveId")
            item_id = resource.get("id") or hit.get("hitId")
            is_pdf = isinstance(name, str) and name.lower().endswith(".pdf")

            if (
                is_pdf
                and hydrated_files < self.config.max_hydrated_files
                and isinstance(drive_id, str)
                and isinstance(item_id, str)
            ):
                pdf_bytes = _download_drive_item(
                    graph_token,
                    drive_id,
                    item_id,
                    self.config.max_file_bytes,
                    self.config.timeout_seconds,
                )
                pages = extract_relevant_pdf_pages(
                    pdf_bytes,
                    query,
                    max_document_pages=self.config.max_document_pages,
                    max_evidence_pages=self.config.max_evidence_pages,
                    max_excerpt_characters=self.config.max_excerpt_characters,
                )
                hydrated_files += 1
                for page in pages:
                    evidence.append({
                        "text": page["text"],
                        "name": name,
                        "web_url": web_url,
                        "site": matching_site.name,
                        "classification": matching_site.classification,
                        "modified_at": resource.get("lastModifiedDateTime"),
                        "page_number": page["page_number"],
                    })
                    if len(evidence) >= max_results:
                        return evidence
                if pages:
                    continue

            if summary:
                evidence.append({
                    "text": summary,
                    "name": name,
                    "web_url": web_url,
                    "site": matching_site.name,
                    "classification": matching_site.classification,
                    "modified_at": resource.get("lastModifiedDateTime"),
                })
        return evidence[:max_results]
