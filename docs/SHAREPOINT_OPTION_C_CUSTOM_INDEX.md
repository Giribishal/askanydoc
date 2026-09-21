# Future option C — permission-aware custom SharePoint index

**Recorded:** 2026-09-21
**Current decision:** Defer. AskAnyDoc uses Option B—delegated Microsoft Graph Search with bounded on-demand extraction—as the selected SharePoint path for the current test environment. Copilot Retrieval remains implemented but commercially blocked in this tenant.
**Purpose:** Preserve the custom-index option for a future scale or cost decision without confusing it with the current implementation.

> Current execution order and approval rules are defined in `SHAREPOINT_RETRIEVAL_SOURCE_OF_TRUTH.md`. This file cannot authorize Option C implementation.

## Simple answer

Option C can produce the same **effective authorization outcome**—a user retrieves only documents they are allowed to read—but it does not receive that protection automatically.

- Copilot Retrieval checks the user's live Microsoft 365 permissions inside Microsoft's retrieval service.
- A custom index must copy each document's permission information, keep it synchronized, and filter every search using the authenticated user's identity and group memberships **before** any text is sent to the answer model.

If any part of that permission pipeline is stale or incorrect, Option C can disclose information that SharePoint would have denied. Therefore it is an enterprise platform, not merely a vector database.

## Required architecture

```text
SharePoint documents and permissions
        ↓
Graph ingestion + incremental change detection
        ↓
parse → chunk → embed
        ↓
index every chunk with document ID, source URL, version, and ACL identities
        ↓
signed-in user token → user ID and group memberships
        ↓
mandatory ACL filter before retrieval results leave the index
        ↓
optional live Graph recheck for sensitive/top-ranked documents
        ↓
Claude receives only authorized evidence
        ↓
application-controlled citations and audit record
```

## Controls required for permission equivalence

1. Use validated Entra identity; never trust user IDs supplied by the browser.
2. Store allowed user and group object IDs with every indexed document/chunk.
3. Apply authorization filters inside the retrieval query, before ranking results are returned to the application or model.
4. Track document additions, modifications, deletions, moves, sharing changes, and permission inheritance changes.
5. Fail closed when permission metadata is missing, stale, or synchronization is unhealthy.
6. Do not share retrieval or answer caches across users unless the cache key includes the complete authorization scope.
7. Revalidate sensitive candidates against live SharePoint permissions when the business risk requires it.
8. Test revocation: removing a user's SharePoint access must remove retrieval access within the accepted security window.
9. Preserve document version, page/chunk provenance, source URL, and the authorization decision in audit records.
10. Monitor synchronization delay, denied-result counts, permission mismatches, stale documents, and deletion failures.

## When option C becomes useful

Consider it only when measured evidence shows several of these conditions:

- retrieval volume makes managed per-call cost materially higher than the full custom-platform cost;
- the organization has thousands or millions of documents and requires predictable low latency;
- content is sufficiently stable for indexed copies, and the organization permits that data duplication;
- custom parsing, OCR, page citations, ranking, or cross-system retrieval is strategically important;
- an engineering/security team can own ingestion, ACL synchronization, operations, incident response, and audits;
- the organization cannot accept the managed provider's licensing, preview/SLA posture, limits, or vendor dependency.

## When not to choose it

Do not choose option C merely to avoid an API charge. It is usually the wrong first choice when:

- permissions change frequently or use complex item-level sharing;
- the organization has no dedicated search/platform/security ownership;
- the source must remain exclusively inside Microsoft 365;
- query volume is low or uncertain;
- a permission-sync delay could create unacceptable exposure;
- the custom platform has not passed identity-isolated authorization, revocation, deletion, and audit tests.

## Future decision gate

Before replacing Copilot Retrieval, collect at least 30 days of real or representative measurements:

- users and retrieval calls per month;
- managed retrieval cost and model cost;
- corpus size and monthly change rate;
- permission-change and revocation frequency;
- latency and answer-quality targets;
- estimated custom infrastructure, engineering, security, and operational cost;
- acceptable permission-staleness window and required SLA.

Then compare total cost of ownership, not API price alone. Option C is approved only if it meets the same permission matrix as SharePoint, passes revocation and deletion tests, improves a measured cost/latency/quality constraint, and has an assigned operational owner.

## Official references checked

- Microsoft Graph DriveItem delta and permission-change tracking: https://learn.microsoft.com/en-us/graph/api/driveitem-delta?view=graph-rest-1.0
- Azure AI Search document-level access control patterns: https://learn.microsoft.com/en-us/azure/search/search-document-level-access-overview
- Query-time ACL enforcement and SharePoint group resolution: https://learn.microsoft.com/en-us/azure/search/search-query-access-control-rbac-enforcement
- Microsoft secure multitenant RAG guidance: https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/secure-multitenant-rag

Some automatic SharePoint ACL ingestion and query-time enforcement features in Azure AI Search are currently preview. They are useful reference patterns but must not be presented as a production guarantee until their status and limitations are rechecked.
