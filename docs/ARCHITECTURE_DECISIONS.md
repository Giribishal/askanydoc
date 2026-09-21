# AskAnyDoc architecture decision record

> **Current authority:** Before using these historical ADRs, read `SHAREPOINT_RETRIEVAL_SOURCE_OF_TRUTH.md`. ADR-008 selects Option B for the current test environment after the Copilot commercial gate failed; the source-of-truth document governs current steps and approval boundaries.

This is the append-only record of architecture evolution. Each decision states the previous position, the new position, the evidence, the consequences, and whether a later decision supersedes it. Do not rewrite old decisions to make the history look cleaner; append a superseding decision instead.

## ADR-001 — 2026-09-21 — Preserve the custom AWS RAG baseline and add source adapters

**Status:** accepted for implementation; no AWS-path replacement is authorised.

### Before

AskAnyDoc had a working custom AWS path: S3 ingestion, format-specific extraction, provenance-preserving chunks, Titan Text Embeddings V2, Aurora PostgreSQL/pgvector retrieval, and Claude answers with application-built citations. SharePoint work then introduced identity, routing, provider, API, and frontend changes around that baseline.

### Decision

- Preserve the existing AWS ingestion, embedding, Aurora storage, retrieval, provenance, and deployed resources as the understandable custom baseline.
- Add external systems behind narrow source adapters. The current adapters are AWS organisation sources and Microsoft SharePoint; Snowflake remains later work.
- Keep source authorization inside every adapter. Tool selection never grants access.
- Do not copy SharePoint content into the shared Aurora index for the permission-aware slice. Retrieve it in the signed-in user's delegated context and return normalized evidence with source provenance.
- Keep citations application-controlled: models may select evidence, but cannot invent source metadata.
- Split the orchestrator into more services only when measured scaling, isolation, ownership, or deployment evidence justifies it. A microservice rewrite is not the default.

### Why

This preserves the learning value and proven behavior of the AWS vertical slice while creating a durable boundary for additional sources. It avoids a second complete application and prevents a SharePoint experiment from silently replacing working AWS infrastructure.

### Consequences and risks

- Shared orchestration must support different authorization models without confusing routing with permission.
- Cross-source answers must retain per-item provenance and must fail closed when user identity is missing.
- Any edit to shared AWS-path code or infrastructure still requires an explicit impact review and Bishal's approval immediately before the change.

## ADR-002 — 2026-09-21 — Microsoft access uses SPA sign-in, protected API, and delegated on-behalf-of retrieval

**Status:** accepted target; implementation exists but the two-user permission matrix is not yet verified.

### Before

The public website called an unauthenticated Lambda Function URL. That boundary cannot safely carry a trusted Microsoft user identity for permission-aware SharePoint retrieval.

### Decision

Use this flow for Microsoft-backed requests:

```text
React/MSAL sign-in
→ API Gateway HTTPS endpoint with Microsoft Entra JWT validation
→ answer/orchestrator Lambda
→ OAuth 2.0 on-behalf-of token exchange
→ Microsoft retrieval API in the signed-in user's context
→ normalized, provenance-bearing evidence
→ Claude answer with application-built citations
```

The existing Function URL may remain temporarily for AWS-only regression and migration safety, but it must not be treated as an authenticated SharePoint boundary.

### Evidence

- Microsoft documents the on-behalf-of flow for a web API calling a downstream API in the user's context.
- Microsoft Search and Microsoft 365 Copilot Retrieval apply the signed-in user's accessible Microsoft 365 content boundary.
- AWS's serverless web guidance uses CloudFront/private S3 for the web tier and API Gateway/Lambda for the API tier; this matches the target boundary without replacing the AWS RAG core.

### Consequences and risks

- The backend must validate the API audience/issuer before exchanging a token.
- Tokens, client secrets, raw document text, and private questions must not be logged.
- Direct Function URL requests must never be allowed to assert SharePoint identity through client-supplied fields.
- The public Function URL should be retired only after protected-API AWS and SharePoint regression tests pass; removal is a separate approved change.

## ADR-003 — 2026-09-21 — Retrieval provider strategy and site scoping

**Status:** Superseded by ADR-006. This records the temporary Graph-first position for history.

### Decision

- Use Microsoft Graph Search first to prove delegated on-behalf-of identity, general-site access, restricted-site denial, citations, and failure handling.
- Treat Microsoft 365 Copilot Retrieval as an optional managed semantic/hybrid provider. Enable it only after tenant entitlement, preview/SLA status, request limits, regional/tenant behavior, and any pay-as-you-go cost are explicitly accepted.
- Scope both providers to the two approved SharePoint site paths in the server-side query. Retain URL allowlist filtering after retrieval as defense in depth.
- Do not hard-code an experimental provider as the production default.

### Why

The existing implementation filtered tenant-wide results only after retrieval. That can omit relevant allowed-site evidence when higher-ranked results come from elsewhere, wastes result capacity, and makes the restriction less explicit. Query-time path scoping plus post-filtering is the safer and more predictable design.

### Current official constraints to recheck before deployment

- Copilot Retrieval uses `POST /v1.0/copilot/retrieval`, supports SharePoint, delegated permissions, KQL filtering, a maximum of 25 results, a 1,500-character query, and service-specific throttling.
- Copilot Retrieval licensing/pay-as-you-go and preview/SLA conditions can change and must be verified from current Microsoft documentation at the deployment gate.

## ADR-004 — 2026-09-21 — Production-hardening changes are staged, not bundled

**Status:** proposed; each stateful or AWS-impacting item needs a separate plan and approval.

### Staged items

1. Prove the Adele/Alex site-access matrix directly in SharePoint.
2. Prove the protected API and delegated Graph Search path without Claude.
3. Run AWS-only regression tests through the preserved path.
4. Run the full general/restricted/missing/citation/failure matrix.
5. Only then decide whether to enable Copilot Retrieval.
6. Separately plan remote Terraform state/locking, deletion protection/final snapshots, alarms, throttling/WAF, secret rotation, and Function URL retirement.

### Approval boundary

Documentation, tests, and isolated Microsoft adapter changes are authorised by the current request. Changes to shared AWS orchestration, Lambda environment/configuration, API routing, IAM, Terraform-managed AWS resources, state migration, or deployment require an exact impact summary and Bishal's explicit approval immediately before execution.

## Official references used for the 2026-09-21 decisions

- Microsoft 365 Copilot Retrieval API overview: https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/api/ai-services/retrieval/overview
- Microsoft identity platform — web API calls another web API / on-behalf-of: https://learn.microsoft.com/en-us/entra/identity-platform/scenario-web-api-call-api-overview
- Microsoft Search API overview: https://learn.microsoft.com/en-us/graph/api/resources/search-api-overview?view=graph-rest-1.0
- AWS Well-Architected Serverless Applications Lens — web application: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/web-application.html

## ADR-005 — 2026-09-21 — Authorisation-filtered, bounded source routing

**Status:** accepted and implemented locally; not deployed.

### Decision

- Authentication and routing remain separate: identity determines which tools may be exposed; the model chooses only among those authorised tools.
- Unauthenticated requests receive only `search_aws_documents`. SharePoint is exposed only when the feature is enabled and validated user, tenant, and bearer-token context are present.
- Tool responsibilities are non-overlapping: AWS means documents uploaded/indexed by AskAnyDoc; SharePoint means live Microsoft 365 content visible to the signed-in user.
- Use explicit user source requests first. Otherwise choose one likely source. Search both only for an explicit comparison or a question that clearly needs both. After an empty/insufficient result, permit at most one different-source fallback within the existing bounded tool loop.
- Do not add a separate model call solely for routing at the current scale. Bedrock Converse tool selection performs routing in the first assistant call; the application executes the tool and returns evidence for finalization.
- Future sources join through the same capability-filtered adapter catalogue. Do not introduce multi-agent orchestration until evaluation proves that the single orchestrator cannot route accurately enough.

### Implementation evidence

- Renamed the AWS tool from the ambiguous `search_organisation_sources` to `search_aws_documents` and clarified both tool descriptions.
- Added per-request tool configuration and routing instructions to the existing orchestrator.
- Reconciled Terraform source to explicit SharePoint variables with safe activation defaults: disabled and `copilot_retrieval`; Graph Search remains explicit fallback-only.
- Backend verification: 35 tests plus 6 subtests passed in 1.60 seconds.

### Risks and deployment gate

- Renaming the internal tool can affect routing behavior, so the AWS-only, SharePoint-only, no-tool, fallback, and cross-source evaluation cases must pass before deployment.
- Safe Terraform defaults intentionally differ from the applied-state feature flag. The ignored environment tfvars must explicitly set the approved test values before planning. No Terraform apply is authorised by this ADR.

## ADR-006 — 2026-09-21 — Copilot Retrieval is the selected SharePoint provider

**Status:** accepted and implemented locally; supersedes the provider-ordering portions of ADR-003 and ADR-004. Not deployed.

### Decision

- Microsoft 365 Copilot Retrieval is the intended SharePoint grounding provider for AskAnyDoc.
- Graph Search remains available only as an explicit diagnostic or entitlement fallback. It is not a prerequisite baseline and must not become the default silently.
- Keep the independent activation gate: `SHAREPOINT_ENABLED=false` by default while `SHAREPOINT_PROVIDER=copilot_retrieval` expresses the target architecture.
- Continue delegated OBO identity, query-time `path:` filtering to the two approved sites, post-response URL allowlisting, permission-trimmed evidence, bounded result count, and application-built citations.
- Do not copy SharePoint documents into the AWS Aurora/vector corpus for this slice. The AWS RAG path remains unchanged.

### Current Microsoft constraints verified at this decision

- The supported endpoint is `POST https://graph.microsoft.com/v1.0/copilot/retrieval` with `dataSource: sharePoint`.
- SharePoint retrieval requires delegated `Files.Read.All` and `Sites.Read.All`; application permission is not supported.
- Queries are limited to 1,500 characters, results to 25, and requests to 200 per user per hour.
- For users without a Microsoft 365 Copilot add-on license, pay-as-you-go is preview, requires at least one Copilot license in the tenant plus an Azure subscription/resource group, has no SLA, and is currently documented at USD $0.10 per API call.
- Microsoft warns that invalid KQL can execute unscoped, so post-response URL allowlisting remains mandatory defense in depth.

### Verification and activation gate

- Local automated verification passes: **39 tests plus 6 subtests**.
- A focused provider test proves the OBO token is used, the v1.0 endpoint and scoped payload are produced, extracts are normalized, and extract relevance scores are parsed correctly.
- Response allowlisting now requires an exact HTTPS host and exact site-path boundary, preventing lookalike hosts or sibling paths from passing a simple string-prefix check.
- Live activation still requires Bishal's explicit approval after tenant entitlement/licensing or pay-as-you-go billing, delegated admin consent, Adele/Alex permission tests, Terraform validation and plan review, rollback, cost exposure, and AWS regression are shown.

## ADR-007 — 2026-09-21 — Preserve, but defer, a permission-aware custom SharePoint index

**Status:** future option; not selected, designed, or implemented.

- Option C can achieve the same effective user-authorization outcome as Copilot Retrieval only when document ACLs, group membership, changes, deletions, and revocations are synchronized and enforced before retrieval evidence reaches Claude.
- It becomes a candidate when measured managed-retrieval cost, latency, scale, custom parsing, SLA, or cross-system requirements justify owning a search and security platform.
- It must not be introduced merely to avoid per-call pricing, and it must remain separate from the protected AWS document corpus unless a future design explicitly proves tenant/document isolation and receives approval.
- The future decision criteria and required controls are recorded in `SHAREPOINT_OPTION_C_CUSTOM_INDEX.md`.

## ADR-008 — 2026-09-21 — Select Graph Search with bounded extraction for the current test environment

**Status:** accepted, deployed, and live-proven for Bishal; Adele/Alex permission proof remains incomplete.

### Before

Option A, Microsoft 365 Copilot Retrieval, was the preferred target. Option B remained an explicit fallback pending commercial and tenant evidence.

### Evidence

- The tenant license inventory contains Microsoft 365 E5 Developer SKU V2 but no Microsoft 365 Copilot add-on.
- Copilot Billing & usage shows no connected Retrieval PAYG policy or enabled Retrieval API service.
- Current Microsoft prerequisites require at least one tenant Copilot license plus eligible Azure billing for nonlicensed-user PAYG Retrieval.
- The local Option B adapter already uses OBO delegated identity, permission-trimmed Graph Search, approved-site query and response filtering, bounded PDF download/extraction, and application-controlled citations.
- SharePoint effective permissions are proven: Adele = General Edit / Restricted None; Alex = Edit on both.

### Decision

- Select `graph_search` for the current test environment.
- Keep SharePoint disabled by default in checked-in source and enable it only through reviewed environment-specific inputs.
- Retain Copilot Retrieval code as a future eligible-environment option; do not invoke it automatically.
- Preserve the AWS ingestion, embeddings, Aurora/pgvector retrieval, permissions, data, and deployed resources unchanged.

### Consequences

- AskAnyDoc owns bounded PDF parsing/ranking and must measure latency, Graph throttling, extraction quality, and Lambda resource use.
- Graph Search is not represented as equivalent to Copilot semantic/hybrid retrieval.
- Live Lambda/configuration deployment and any Entra consent change remain separately approval-controlled.

## ADR-009 — 2026-09-21 — Defer a dedicated SharePoint retrieval Lambda until measured need

**Status:** deferred future option; documentation only; not approved or implemented.

- Keep one answer/orchestration Lambda so source routing, Bedrock finalization, evidence normalization, and citations have one owner.
- Move only OBO, Graph Search, SharePoint download, and bounded extraction into a dedicated Lambda with a least-privilege role and independent metrics/concurrency controls.
- Do not copy the full AWS answer Lambda and do not create a second complete application.
- The design reduces deployment and dependency blast radius and allows measured concurrency isolation. It adds a small invocation charge and overlapping billed duration for synchronous calls.
- Complete the current permission/latency baseline before migration. Any new Lambda, IAM, invocation permission, routing change, or deployment requires a fresh exact Terraform plan and explicit approval.
- Detailed gates and rollback are in `SHAREPOINT_LAMBDA_SEPARATION_PLAN.md`.
- For the current volume, retain the single Lambda because it is simpler and avoids the extra synchronous invocation and overlapping billed duration. Reopen separation only for measured concurrency contention, blast-radius incidents, independent release ownership, package/cold-start pressure, least-privilege audit requirements, or unmet latency/SLA targets.
