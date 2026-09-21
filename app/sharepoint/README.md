# SharePoint adapter boundary

This folder contains only the Microsoft SharePoint side of AskAnyDoc:

- `sharepoint_config.py` — SharePoint-only feature flags, site allowlist, limits, and timeout settings.
- `sharepoint_source.py` — provider-neutral permission-aware retrieval boundary and provenance normalisation.
- `copilot_retrieval_provider.py` — the intended Microsoft 365 semantic/hybrid grounding provider.
- `graph_search_provider.py` — an explicit diagnostic/entitlement fallback, not the target architecture.
- `source_router.py` — an isolated deterministic routing experiment retained for tests; it is not the runtime router. Runtime routing uses the capability-filtered Bedrock tool catalogue in `app/api/organisation_tools.py` and `app/api/assistant_orchestrator.py`.
- `test_sharepoint_source.py` — mocked SharePoint tests that do not call Microsoft or AWS.

The existing AWS ingestion, Aurora/vector retrieval, Bedrock orchestration, and infrastructure remain under their existing AWS/application paths. No SharePoint SDK, token, or site-specific permission logic belongs in the AWS retrieval modules.
