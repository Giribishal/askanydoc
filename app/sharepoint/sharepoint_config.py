"""Validated configuration for the permission-aware SharePoint adapter."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class SharePointSite:
    name: str
    url: str
    classification: str


@dataclass(frozen=True)
class SharePointConfig:
    enabled: bool
    provider: str
    general_site: SharePointSite
    restricted_site: SharePointSite
    max_results: int = 10
    timeout_seconds: float = 8.0
    max_retries: int = 2
    max_hydrated_files: int = 2
    max_file_bytes: int = 10_000_000
    max_document_pages: int = 150
    max_evidence_pages: int = 3
    max_excerpt_characters: int = 3_500


def load_sharepoint_config(env: dict[str, str] | None = None) -> SharePointConfig:
    values = env or os.environ
    # Option B is selected for this environment because Copilot Retrieval is
    # commercially unavailable in the tenant. The independent
    # SHAREPOINT_ENABLED gate still prevents accidental activation.
    provider = values.get("SHAREPOINT_PROVIDER", "graph_search")
    if provider not in {"copilot_retrieval", "graph_search", "mock"}:
        raise ValueError("SHAREPOINT_PROVIDER is not supported")
    return SharePointConfig(
        enabled=values.get("SHAREPOINT_ENABLED", "false").lower() == "true",
        provider=provider,
        general_site=SharePointSite(
            "general",
            values.get("SHAREPOINT_GENERAL_SITE_URL", "https://example.invalid/general"),
            "general",
        ),
        restricted_site=SharePointSite(
            "restricted",
            values.get("SHAREPOINT_RESTRICTED_SITE_URL", "https://example.invalid/restricted"),
            "senior_restricted",
        ),
        max_results=int(values.get("SHAREPOINT_MAX_RESULTS", "10")),
        timeout_seconds=float(values.get("SHAREPOINT_TIMEOUT_SECONDS", "8")),
        max_retries=int(values.get("SHAREPOINT_MAX_RETRIES", "2")),
        max_hydrated_files=int(values.get("SHAREPOINT_MAX_HYDRATED_FILES", "2")),
        max_file_bytes=int(values.get("SHAREPOINT_MAX_FILE_BYTES", "10000000")),
        max_document_pages=int(values.get("SHAREPOINT_MAX_DOCUMENT_PAGES", "150")),
        max_evidence_pages=int(values.get("SHAREPOINT_MAX_EVIDENCE_PAGES", "3")),
        max_excerpt_characters=int(values.get("SHAREPOINT_MAX_EXCERPT_CHARACTERS", "3500")),
    )
