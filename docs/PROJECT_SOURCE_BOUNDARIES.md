# Project source boundaries

> Current SharePoint provider choices and execution steps are governed by `SHAREPOINT_RETRIEVAL_SOURCE_OF_TRUTH.md`; this file defines ownership boundaries only.

## AWS side

The AWS side owns S3 ingestion, PDF extraction, Titan embeddings, Aurora/pgvector retrieval, Bedrock answer generation, AWS IAM, Lambda, ECR, and Terraform resources.

## SharePoint side

The SharePoint side owns Microsoft identity context, SharePoint/Graph or Copilot Retrieval providers, SharePoint site allowlists, permission-aware evidence, Microsoft source URLs, and SharePoint-specific retry/error categories.

## Salesforce side

`app/salesforce/` owns the existing user-bound OAuth grant, Hosted MCP client, allowlisted CRM query compiler and evidence endpoint. Only the dedicated Salesforce Lambda resolves Salesforce credentials; the worker forwards the validated caller token to the fixed protected evidence route. CRM evidence includes application-built record URLs, with bounded sample disclosure.

## Shared answer boundary

`app/api/shared_source_controller.py` adds a small registered adapter loop for explicitly mixed Salesforce/document requests. It reuses existing AWS/SharePoint execution and finalization helpers; ordinary document requests and Salesforce-only requests keep their current paths. A new connector needs verified capabilities, scoped authorization, bounded retrieval/provenance and tests before registration. Shared answers do not merge stores, identities or permissions. Commit `e303b98`, 4 October 2026.

## Boundary rule

The sources communicate only through source-neutral evidence and a source plan. SharePoint code must not copy AWS vector-store logic, and AWS retrieval must not contain SharePoint permission assumptions. This keeps the Visual Studio Code project readable and allows either source to be disabled independently.
