# Project source boundaries

> Current SharePoint provider choices and execution steps are governed by `SHAREPOINT_RETRIEVAL_SOURCE_OF_TRUTH.md`; this file defines ownership boundaries only.

## AWS side

The AWS side owns S3 ingestion, PDF extraction, Titan embeddings, Aurora/pgvector retrieval, Bedrock answer generation, AWS IAM, Lambda, ECR, and Terraform resources.

## SharePoint side

The SharePoint side owns Microsoft identity context, SharePoint/Graph or Copilot Retrieval providers, SharePoint site allowlists, permission-aware evidence, Microsoft source URLs, and SharePoint-specific retry/error categories.

## Boundary rule

The two sides communicate only through source-neutral evidence and a source plan. SharePoint code must not copy AWS vector-store logic, and AWS retrieval must not contain SharePoint permission assumptions. This keeps the Visual Studio Code project readable and allows either source to be disabled independently.
