# AWS and Microsoft boundaries

> **Execution authority:** This file defines system ownership boundaries. `SHAREPOINT_RETRIEVAL_SOURCE_OF_TRUTH.md` governs the current SharePoint provider, verified state, gates, rollback, and approval rules.

AskAnyDoc keeps the two retrieval paths deliberately separate so they can be learned, tested, and troubleshot independently.

## AWS path

- `app/ingestion/` and `app/shared/askanydoc_rag/` own the AWS-indexed ingestion and retrieval pipeline.
- `app/api/retrieval.py` owns retrieval from the application-managed AWS corpus.
- AWS infrastructure owns the private document bucket, Aurora/pgvector, Bedrock generation, and the existing Lambda path.
- AWS data is application-owned and is not populated from SharePoint automatically.

## Microsoft path

- `app/sharepoint/` owns Microsoft 365 Copilot Retrieval, its explicit Graph Search fallback, and delegated on-behalf-of token exchange.
- `infra/sharepoint_auth.tf` owns the Entra-protected API Gateway, CloudFront frontend, and the Secrets Manager container for the Entra API credential.
- Microsoft access remains permission-trimmed by SharePoint/Graph for the signed-in user; SharePoint remains the source of truth.
- Microsoft documents are not copied into the AWS vector store as part of this integration.

## Neutral application bridge

`app/api/organisation_tools.py` and `app/api/assistant_orchestrator.py` provide the existing document bridge. `app/api/shared_source_controller.py` adds the bounded mixed-source registry, reusing those helpers and the dedicated `/salesforce/evidence` adapter. Salesforce tokens remain inside its dedicated Lambda. Commit `e303b98` preserves the underlying stores and permission models. They expose separate tools (`search_aws_documents` and, only for an authenticated and enabled request, `search_sharepoint`) and normalize evidence/citations without merging the underlying stores or authentication models.

This boundary makes it possible to compare authorization, retrieval, failure handling, cost, and operational evidence for AWS and Microsoft independently.

## Change-control rule

The established AWS path is protected. Microsoft/SharePoint work must be additive and must not alter the AWS retrieval code, stores, permissions, or deployed resources. Any architecture-required AWS change must be described with its impact and approved explicitly before implementation; read-only verification and tests remain allowed.
