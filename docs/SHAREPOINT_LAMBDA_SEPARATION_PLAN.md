# SharePoint Lambda separation — retained architecture option

**Status:** deferred; not approved or implemented

**Recorded:** 2026-09-21

**Current authority:** [`SHAREPOINT_RETRIEVAL_SOURCE_OF_TRUTH.md`](SHAREPOINT_RETRIEVAL_SOURCE_OF_TRUTH.md)

**Risks, triggers, planned infrastructure, gates, cost, and rollback:** [`MODERNIZATION_RISK_AND_CHANGE_REGISTER.md`](MODERNIZATION_RISK_AND_CHANGE_REGISTER.md), especially `R-003`, `R-007`, `R-013`, `R-021`, and planned-change order 10.

## Retained target shape

If measured scale, reliability, security, least privilege, or release evidence justifies isolation, add one dedicated `askanydoc-sharepoint-retrieval` Lambda. Do not copy the complete answer application.

```text
React + MSAL
  -> API Gateway JWT authorizer
  -> answer/orchestration Lambda
       -> existing AWS retrieval code (unchanged)
       -> synchronous IAM-authorized invocation
          -> SharePoint retrieval Lambda
               -> OBO delegated Graph token
               -> Graph Search
               -> bounded download/extraction
               -> normalized evidence only
  -> model finalization and application-built citations
```

The answer/orchestration Lambda remains the single owner of routing, Bedrock interaction, answer validation, and citation assembly. The SharePoint Lambda receives only the permissions and configuration required for OBO, allowlisted Microsoft retrieval, bounded extraction, and evidence normalization. It receives no Aurora, AWS document-corpus, ingestion, or unrelated-secret access.

## Non-negotiable migration rules

1. Preserve the deployed in-process adapter as rollback until the complete AWS, SharePoint, permission, and cross-source matrix passes.
2. Use a versioned request/evidence contract; the retrieval Lambda never produces a competing final answer.
3. Do not add SQS to the interactive delegated-token path merely for separation.
4. Do not introduce Step Functions, provisioned concurrency, reserved concurrency, or a second application without a measured requirement.
5. Prepare the exact Terraform/IAM/topology plan and obtain fresh approval immediately before any change.

All open triggers, tradeoffs, acceptance evidence, official references, and implementation order are deliberately maintained only in the modernization register to prevent this option from drifting into a second risk or roadmap list.
