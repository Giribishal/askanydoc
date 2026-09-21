# AskAnyDoc SharePoint retrieval — current source of truth

**Effective date:** 2026-09-21
**Document version:** 1.5
**Authority:** This document is the authoritative current execution plan for the SharePoint retrieval slice.
**Historical records:** Older chats, trackers, ADRs, and implementation logs remain valuable history. If their current recommendation conflicts with this document, follow this document and record any future correction append-only.

## 0. Small-model execution contract — read this first

This block is intentionally short and repetitive. A small or low-cost model must be able to determine the current state without interpreting the full history.

```yaml
project: AskAnyDoc
feature: Permission-aware SharePoint retrieval
selected_provider: graph_search
selected_option: B
option_a: retained_but_commercially_blocked_in_current_tenant
option_b: selected_graph_on_demand_extraction_for_current_test_environment
option_c: document_only_deferred_custom_acl_index
sharepoint_source_default_enabled: false
local_source_provider_default: graph_search
last_applied_provider_from_local_state: graph_search
last_applied_sharepoint_enabled_from_local_state: true
copilot_live_proven: false
copilot_commercial_gate: blocked_no_copilot_addon_and_no_retrieval_payg_policy
sharepoint_effective_permission_matrix_proven: true
direct_user_session_permission_matrix_proven: false
adele_alex_retrieval_matrix_proven: false
aws_retrieval_path_may_be_changed_without_explicit_approval: false
terraform_apply_authorized: true
deployment_authorized: true
deployment_approval_recorded_at: 2026-09-21T17:39:49+10:00
deployment_status: deployed_option_b_to_askanydoc_api
deployed_at: 2026-09-21T17:41:27+10:00
deployed_commit: 39f2474
deployed_lambda_code_sha256: T51h5B4tXxhOFCriUnlNTdf4BQ8OEGpwc1PhFxPEjgg=
next_action: Run direct authenticated Graph extraction and the Adele/Alex end-to-end permission matrix, then record latency and failure evidence
last_automated_verification: 43 Python tests plus 6 subtests passed
frontend_current_lint_build: passed_with_existing_589_kb_bundle_warning
terraform_current_validation: passed_with_terraform_1_16_3
terraform_plan_status: applied_successfully_lambda_in_place_update_only_plus_local_build_trigger_replacement
```

### Mandatory interpretation rules

1. **Current choice:** Option B is selected for this test environment. Do not switch providers again unless Bishal explicitly reopens and records the decision.
2. **Option A:** Keep the implementation, but do not deploy it in this tenant while the commercial gate is blocked.
3. **Option C:** Do not implement it now. It is a future architecture triggered only by measured scale, cost, latency, SLA, or cross-system requirements.
4. **Current live truth:** local source targets Copilot but is disabled by default; inspected applied state still records enabled Graph Search. Do not describe Copilot as deployed or working live.
5. **AWS protection:** do not modify AWS ingestion, S3, Titan, Aurora, pgvector, AWS retrieval, IAM, state, or data without the exact warning and Bishal's explicit approval immediately before the action.
6. **Next action only:** the reviewed Option B plan is deployed. Run authenticated retrieval and the Adele/Alex permission matrix. Do not grant consent, change topology, or modify the protected AWS path without a new exact warning and approval.
7. **Historical text:** statements such as “Graph first” in older logs are history, not current instructions.
8. **Uncertainty:** when permission, billing, tenant, plan, or blast radius is uncertain, stop before mutation and report the missing evidence.
9. **Recording:** append evidence to the implementation log and root history; update the current-state sections here only when a verified superseding decision occurs.
10. **Completion:** passing unit tests does not prove live Copilot entitlement, user isolation, or production readiness.

### Minimum read set before acting

A future agent must read these sections before any SharePoint action:

- Section 0 — small-model contract;
- Section 2 — non-negotiable requirements;
- Section 3 — current verified state;
- Section 9 — code/file ownership;
- Section 11 — execution gates;
- Section 15 — approval boundaries;
- Section 16 — exact next actions.

Do not treat a chat summary, browser tab, historical ADR, Terraform default, or local state file alone as authority.

## 1. Executive decision

AskAnyDoc will support three SharePoint retrieval architectures behind one permission-aware provider boundary:

| Option | Role | Current status |
|---|---|---|
| **A — Microsoft 365 Copilot Retrieval** | Managed, permission-trimmed semantic/hybrid SharePoint grounding | **Retained; commercially blocked in this tenant** |
| **B — Microsoft Graph search + bounded on-demand file extraction** | Lower-cost delegated retrieval when Copilot entitlement/PAYG is unavailable or deliberately avoided | **Selected for the current test environment** |
| **C — custom permission-aware SharePoint index** | Future high-scale, low-latency, or cost/SLA alternative | **Documented and deferred until measurements justify it** |

The selected current-environment path is Option B. Option A remains implemented for a future eligible environment. Option C is a future platform decision, not current implementation work.

The existing AWS RAG path remains protected and independent:

```text
AWS-owned documents
→ S3 ingestion
→ extraction and chunking
→ Titan embeddings
→ Aurora PostgreSQL/pgvector
→ search_aws_documents
```

SharePoint documents must not be silently copied into that corpus. A future custom SharePoint index requires a separate approved permission and isolation design.

### Project goal

AskAnyDoc is a career-aligned learning and evidence project for building one understandable hybrid AI assistant that can answer from application-owned AWS documents and live external systems while preserving identity, permissions, provenance, cost controls, and explainability.

The immediate feature goal is not to claim a finished enterprise product. It is to prove one secure, permission-aware SharePoint vertical slice that a medium organization could evaluate and extend. The design should scale conceptually, but every production or enterprise claim must be supported by tests, operations, governance, and measured evidence.

### Current non-goals

- Do not rebuild or replace the working AWS custom RAG core.
- Do not create a second complete application for SharePoint.
- Do not implement Option C now.
- Do not buy licenses, enable billing, or grant broad permissions merely to make a demo pass.
- Do not expose unauthenticated SharePoint retrieval or public document upload.
- Do not claim that a visible filename proves grounded content retrieval.
- Do not treat the current developer/test tenant or 12-document corpus as representative production scale.

## 2. Non-negotiable requirements

Every SharePoint provider must satisfy all of the following:

1. A user receives evidence only from documents that the user is permitted to read in SharePoint.
2. Identity comes from a validated Entra token. The browser cannot assert its own user ID, tenant ID, groups, role, or classification.
3. The protected API validates audience, issuer, tenant, and required application scope before SharePoint retrieval is exposed.
4. Downstream Microsoft calls use OAuth 2.0 on-behalf-of (OBO) delegated identity unless a future architecture explicitly documents and approves a different model.
5. Authorization is applied before document text is sent to Claude or returned to the caller.
6. Retrieval text is untrusted data. Instructions inside documents are never executed as system or tool instructions.
7. Citations come from application-controlled provenance, not filenames, URLs, or page numbers invented by the model.
8. Missing or insufficient evidence produces an explicit insufficient-evidence answer, not a guess presented as company information.
9. Site/path allowlisting is applied at query time where supported and again after results return.
10. Authentication and routing remain separate: identity decides which tools are available; the model selects only among authorized tools.
11. No SharePoint secret, bearer token, authorization code, raw private question, or private document body is logged.
12. Any fallback must preserve or strengthen the same permission boundary. Cost or availability never justifies weaker authorization.

## 3. Current verified project state

### 3.1 Local working source

- Graph Search is the selected default provider in local application configuration.
- Terraform source defaults `SHAREPOINT_ENABLED=false` and `SHAREPOINT_PROVIDER=graph_search`.
- Site URLs default to non-routable placeholders until the target environment supplies approved values.
- Copilot Retrieval remains an explicit provider value for a future eligible environment.
- The SharePoint tool is offered to Claude only when SharePoint is enabled and validated `user_id`, `tenant_id`, and `access_token` context exists.
- AWS and SharePoint are separate tools: `search_aws_documents` and `search_sharepoint`.
- Both Microsoft providers apply query-time site scoping and post-response URL validation.
- Post-response validation requires an exact HTTPS host and an exact configured site-path boundary.
- The Copilot adapter uses `POST https://graph.microsoft.com/v1.0/copilot/retrieval`, `dataSource: sharePoint`, a two-site `path:` filter, title metadata, and bounded results.
- Automated verification currently passes: **43 Python tests plus 6 subtests**. The new tests cover Copilot's 1,500-character query limit, malformed JSON, invalid response shape, and retryable network failure mapping.
- The local frontend dependency installation was restored without downloading or replacing tracked source. Frontend lint and the production build pass. The existing approximately 589 kB JavaScript bundle warning remains a performance follow-up, not a correctness failure.

### 3.2 Applied/deployed evidence

- Local Terraform state serial 236 records SharePoint enabled with `graph_search` in the previously applied Lambda environment.
- Therefore local source and applied state intentionally disagree.
- The deployed Graph path found an exact PDF filename, proving sign-in/OBO/search metadata retrieval, but it did not answer a semantic question from that PDF's body.
- Copilot Retrieval has not been proven live in this tenant.
- Read-only Microsoft 365 admin inspection on 2026-09-21 found only **Microsoft 365 E5 Developer SKU V2** in the license inventory; no Microsoft 365 Copilot add-on license was present.
- The Copilot Billing & usage page showed no connected billing policy for its listed pay-as-you-go services and did not list Microsoft 365 Copilot Retrieval API as an enabled service.
- Current Microsoft documentation requires at least one tenant Microsoft 365 Copilot license plus eligible Azure billing for nonlicensed-user Retrieval PAYG. Therefore Option A is commercially blocked in this tenant until eligibility is deliberately obtained or Microsoft changes the requirements.
- Entra delegated permission/admin-consent status is not live-verified because the Entra portal requested a separate interactive authentication step. Local state confirms a JWT-protected `POST /chat` route with `access_as_user` and configured tenant/client/secret references, but local state is not proof of current Entra consent.
- No current record proves the Adele/Alex retrieval permission matrix end to end.
- Terraform 1.16.3 is checksum-verified in the ignored project `tmp` directory; formatting and validation pass.
- No Terraform apply, Lambda deployment, billing enablement, Entra permission grant, state migration, IAM change, database change, or AWS-path change is authorized by this document.

### 3.2.1 Current Option B plan evidence

- The saved Option B plan proposes only an in-place update of `aws_lambda_function.lambda_function` (`askanydoc-api`) plus replacement of the local `null_resource.install_deps` packaging trigger and a reread of the local ZIP data source.
- Planned environment remains `SHAREPOINT_ENABLED=true`, `SHAREPOINT_PROVIDER=graph_search`, the two verified site URLs, and `SHAREPOINT_MAX_RESULTS=10`.
- The plan contains no create/delete/replacement for S3, Aurora, pgvector, IAM, API Gateway, CloudFront, the Function URL, ingestion Lambda, queues, secrets, or databases.
- Bishal gave explicit Gate 6 approval at 2026-09-21 17:39:49 +10:00 after reviewing the shared-Lambda blast radius, failure modes, cost exposure, rollback, and verification plan. Commit `39f2474` was created immediately before apply.
- The reviewed plan applied successfully. Lambda `askanydoc-api` was updated in place at 2026-09-21 07:41:27 UTC with code SHA-256 `T51h5B4tXxhOFCriUnlNTdf4BQ8OEGpwc1PhFxPEjgg=`. AWS reports `Active` and `LastUpdateStatus=Successful`.
- Live configuration reports SharePoint enabled, provider `graph_search`, the exact General and Restricted site allowlist, and 10 maximum results.
- A live known AWS-corpus question passed with the expected `17-lambda-sqs-partial-batch-responses.pdf`, page 5 citation. The protected `/chat` endpoint returned HTTP 401 without a token. This proves the AWS smoke path and unauthenticated denial after deployment; it does not prove the Adele/Alex SharePoint matrix.

### 3.3 SharePoint test corpus and identities

- General site: `https://y4m7.sharepoint.com/sites/AskAnyDoc-General-Documents`
- Restricted site: `https://y4m7.sharepoint.com/sites/AskAnyDoc-Restricted-Senior-Documents`
- General corpus: 8 PDFs verified in the site UI.
- Restricted corpus: 4 PDFs verified in the site UI.
- Adele is intended to read general content and be denied restricted content.
- Alex is intended to read both general and restricted content.
- Bishal is the administrative test identity and cannot substitute for the Adele/Alex isolation tests.
- SharePoint's read-only **Check Permissions** tool now proves the effective site-level matrix: Adele has **Edit** on General and **None** on Restricted; Alex has **Edit** on both General and Restricted.
- This proves the configured SharePoint permission boundary, but not yet isolated browser sign-in or end-to-end retrieval. Adele/Alex direct-session and AskAnyDoc retrieval tests remain required.

### 3.4 Decision and implementation evolution

This timeline explains why older files contain apparently conflicting statements:

1. AskAnyDoc first established the custom AWS S3/Titan/Aurora RAG path and citation controls.
2. The assistant architecture was generalized so Claude could choose controlled source tools rather than relying on phrase lists.
3. SharePoint was added as a thin external adapter using Entra sign-in, a protected API, OBO delegated identity, and two permission-separated sites.
4. Earlier project conversations selected Copilot Retrieval as the preferred Microsoft grounding path and Graph Search as fallback/comparison.
5. A later risk-control pass temporarily described Graph Search as the verification baseline because Copilot entitlement, PAYG, and preview/SLA status were unknown.
6. The deployed Graph test proved identity and exact-filename metadata lookup but did not return sufficient PDF body evidence for a semantic answer.
7. Bishal clarified that Copilot Retrieval was the intended path. Local defaults and current records were reconciled; no deployment occurred.
8. Options B and C were retained deliberately so future organizations can choose based on measured permission complexity, scale, cost, latency, SLA, and operational capability.
9. This document now supersedes conflicting current recommendations while the append-only files preserve the complete history.

### 3.5 Evidence vocabulary

Use these words precisely:

- **Implemented locally:** source files exist in the working tree.
- **Unit-tested:** automated local tests passed with mocks/local logic.
- **Applied state records:** the inspected local Terraform state reports a prior deployment value; this is not a live cloud inventory.
- **Deployed:** a reviewed package/configuration was applied to the target environment.
- **Live-proven:** a real authenticated request produced the expected result and evidence.
- **Permission-proven:** the authorized and unauthorized identity matrix passed end to end.
- **Production-ready:** security, reliability, monitoring, cost, recovery, governance, and operational ownership all meet an agreed production standard.

Never substitute one level of evidence for another.

## 4. Shared request architecture

```text
React frontend + MSAL
        ↓ API access token
CloudFront/private S3 frontend
        ↓ HTTPS
API Gateway Entra JWT authorizer
        ↓ validated claims
answer/orchestration Lambda
        ↓ request-specific authorized tool catalogue
Claude chooses AWS or SharePoint tool
        ↓
SharePoint adapter
        ↓ OBO exchange using the original user's delegated identity
selected provider A, B, or future C
        ↓
normalized evidence with source name, URI, site/classification, and page where available
        ↓
Claude answer from evidence
        ↓
application validates evidence references and builds citations
```

Routing rules:

1. Follow an explicit user source request first.
2. Otherwise select one likely primary source.
3. Search both AWS and SharePoint only for an actual comparison or cross-source question.
4. Permit at most one different-source fallback after empty or insufficient evidence.
5. Never invoke an unavailable SharePoint tool for an unauthenticated request.
6. Do not add a separate model solely for routing until evaluation proves the existing Bedrock tool selection is inadequate.

## 5. Option A — Microsoft 365 Copilot Retrieval

### 5.1 What it does

Copilot Retrieval searches Microsoft 365's managed semantic/hybrid index and returns relevant SharePoint text extracts. Microsoft applies the signed-in user's permissions and keeps indexing, parsing, freshness, and security trimming within the managed retrieval service.

### 5.2 Permission mechanism

```text
validated AskAnyDoc API token
→ OBO delegated Graph token
→ Copilot Retrieval in the user's context
→ Microsoft security trimming
→ only accessible extracts returned
```

The application still performs defense-in-depth site allowlisting and citation validation.

### 5.3 Current licensing and service facts to recheck at deployment

- Licensed Microsoft 365 Copilot users can call Retrieval without an additional Retrieval API charge.
- Non-Copilot users can currently use tenant-level SharePoint retrieval through PAYG preview.
- PAYG currently requires an Azure subscription/resource group, Microsoft 365 admin access, and at least one Microsoft 365 Copilot license in the tenant.
- The currently documented PAYG price is USD $0.10 per API call.
- PAYG preview currently has no SLA.
- A single tenant Copilot license satisfies the stated PAYG prerequisite; it does not make other users' calls free.
- Nonlicensed users must be covered by the configured PAYG policy.
- A single assistant question can cost more than one retrieval call if orchestration is not bounded. AskAnyDoc should normally allow one SharePoint retrieval call and explicitly meter exceptions.

These facts are version-sensitive. Recheck Microsoft documentation immediately before any commercial or production decision.

### 5.4 Current technical limits to recheck

- Delegated `Files.Read.All` and `Sites.Read.All` are required for SharePoint Retrieval.
- Application-only access is not supported for this SharePoint Retrieval flow.
- Query string maximum: 1,500 characters.
- Maximum results: 25.
- Current documented throttling: up to 200 requests per user per hour.
- Semantic/hybrid retrieval supports selected file formats including PDF, Word, PowerPoint, SharePoint pages, and OneNote.
- Nontextual content such as diagrams and images is not semantically interpreted merely because it appears in a PDF.
- Invalid KQL can execute without intended scoping; post-response allowlisting is therefore mandatory.

### 5.5 When to choose A

Choose A when permissions are complex or change frequently, SharePoint freshness matters, the organization lacks a dedicated search/security platform team, usage cost is acceptable, and managed-service terms meet the workload's SLA and compliance needs.

### 5.6 Current AskAnyDoc status

Retained and locally contract-tested, but commercially blocked in this tenant and not selected for deployment.

## 6. Option B — Graph Search plus bounded on-demand extraction

### 6.1 What it means

Option B does not mean that employees manually download and re-upload every SharePoint document. The application performs the work:

```text
user question
→ delegated Graph Search scoped to approved sites
→ select a small number of candidate files the user can access
→ download those files using the same user's delegated identity
→ extract text/pages in bounded memory
→ rank relevant passages
→ send only authorized evidence to Claude
→ build page/source citations
→ discard temporary bytes
```

If a user manually uploads a document into AskAnyDoc, that is the existing AWS-owned document workflow, not Option B.

### 6.2 Permission mechanism

Graph Search and file download run using the signed-in user's delegated token. A user who cannot open or download a SharePoint file must not be able to retrieve its body through AskAnyDoc.

Required defenses:

- OBO identity and delegated permissions;
- query-time approved-site restrictions;
- exact post-response host/path allowlisting;
- bounded downloads and HTTPS-only preauthenticated URLs;
- no bearer-token forwarding to the storage download host;
- no persistent cross-user content cache unless authorization scope is part of the cache key;
- no model call until authorized evidence exists;
- explicit denial/insufficient-evidence handling.

### 6.3 Current bounds

Local configuration currently limits Option B to:

- up to 2 hydrated files;
- 10 MB per file;
- 150 pages inspected per document;
- 3 evidence pages;
- 3,500 excerpt characters;
- an 8-second Microsoft timeout;
- 2 configured retries.

These are experimental safety limits, not proven enterprise settings.

### 6.4 Advantages

- Avoids Copilot Retrieval licensing/PAYG dependency.
- Uses official Graph APIs and live delegated file access.
- Supports custom parsing, ranking, page citations, and refusal thresholds.
- Does not require a persistent duplicate SharePoint index.
- Useful as a diagnostic and a small/low-volume production pattern where latency is acceptable.

### 6.5 Limitations

- Graph Search candidate discovery is not equivalent to Copilot semantic/hybrid retrieval.
- Search summaries can be empty; the application must download and parse files.
- Repeated download/extraction increases latency and compute usage.
- Large PDFs, OCR, tables, diagrams, and unusual formats need additional parsers.
- High concurrency increases Graph throttling and Lambda duration risk.
- It does not scale efficiently to continuously parse many files per question.

### 6.6 When to choose B

Choose B when Copilot Retrieval is commercially or technically unavailable, query volume is low or moderate, the number of files downloaded per question stays very small, the organization accepts latency, and measured quality meets the required evaluation set.

Do not select B merely because its API has no explicit Retrieval charge. Compare Graph throttling, compute, model tokens, parsing maintenance, latency, failures, and engineering ownership.

### 6.7 Current AskAnyDoc status

Implemented locally as `graph_search`, previously deployed, metadata lookup proven, semantic body-answer quality not proven. Retain as an explicit configured provider, not an automatic silent fallback from A.

## 7. Option C — custom permission-aware SharePoint index

### 7.1 What it means

```text
SharePoint documents + permissions
→ Graph ingestion and incremental synchronization
→ parse, chunk, and embed
→ separate SharePoint search index with document/chunk ACL metadata
→ authenticated user/group authorization filter inside every query
→ optional live Graph recheck for sensitive candidates
→ Claude receives only authorized evidence
```

### 7.2 Can it match Copilot permissions?

It can produce the same effective result—users retrieve only documents they may read—but not automatically. The organization owns correctness and freshness for ACLs, permission inheritance, group membership, sharing changes, moves, deletions, and revocations.

Required controls:

1. Validated Entra identity only.
2. User/group ACL metadata on every indexed document or chunk.
3. Authorization filtering inside retrieval before evidence leaves the index.
4. Incremental content and permission synchronization.
5. Fail-closed behavior when synchronization or ACL metadata is unhealthy.
6. Revocation and deletion service-level objectives.
7. No cross-user cache leakage.
8. Live revalidation for high-risk content where required.
9. Audit records for source version, authorization decision, retrieved chunks, and citations.
10. Dedicated operational and security ownership.

### 7.3 When to choose C

Consider C only when measurements show that high sustained volume, large corpus size, latency, custom parsing/ranking, cross-system retrieval, SLA, or vendor dependency justifies the complete custom-platform cost.

Before selecting C, collect at least 30 days of representative usage and compare:

- managed retrieval calls and cost;
- model and application cost;
- corpus size and change rate;
- permission-change and revocation frequency;
- required latency and availability;
- custom infrastructure cost;
- engineering, security, audit, and operational cost;
- acceptable permission-staleness window.

### 7.4 Current AskAnyDoc status

Documented future option only. Do not implement or mix it into Aurora as part of the current SharePoint slice. Detailed future controls are also recorded in `SHAREPOINT_OPTION_C_CUSTOM_INDEX.md`.

## 8. Provider-selection policy

Use this decision order:

1. If live SharePoint permission trimming, managed semantic retrieval, and service terms are acceptable, use A.
2. If A is unavailable or deliberately declined and bounded on-demand extraction meets measured volume/latency/quality needs, use B.
3. If A's total cost/SLA/limits are unacceptable and B cannot meet measured scale or latency, evaluate C as a separately funded platform.
4. Never move from A to B or C automatically after an authorization error. Fail closed and surface the error.
5. Never choose a provider based only on API price.

Indicative PAYG formula for non-Copilot users:

```text
monthly Retrieval API cost
= nonlicensed-user retrieval calls × current price per call
```

Example at the current documented USD $0.10 rate, assuming one retrieval call per SharePoint question and 22 working days:

| Employees | Questions each/day | Calls/month | Retrieval cost/month |
|---:|---:|---:|---:|
| 20 | 5 | 2,200 | $220 |
| 50 | 5 | 5,500 | $550 |
| 100 | 5 | 11,000 | $1,100 |
| 200 | 5 | 22,000 | $2,200 |

These examples exclude Copilot licensing, Claude/model calls, AWS, Azure, monitoring, support, and engineering. They are decision examples, not a budget commitment.

## 9. Code and file ownership map

### Microsoft adapter code

| File | Responsibility |
|---|---|
| `app/sharepoint/sharepoint_config.py` | Provider choice, activation flag, approved sites, timeouts, retries, and Option B extraction limits |
| `app/sharepoint/microsoft_identity.py` | Confidential-client secret retrieval and OBO token exchange |
| `app/sharepoint/sharepoint_source.py` | Provider-neutral evidence contract, retries, normalization, and exact site allowlisting |
| `app/sharepoint/copilot_retrieval_provider.py` | Option A request, filtering, extracts, metadata, and error mapping |
| `app/sharepoint/graph_search_provider.py` | Option B candidate search, delegated download, extraction, and provenance |
| `app/sharepoint/pdf_grounding.py` | Bounded in-memory PDF page extraction/ranking used only by Option B |
| `app/sharepoint/test_sharepoint_source.py` | Provider, routing, security-boundary, PDF, and contract tests |

### Shared assistant/API code

| File | Responsibility |
|---|---|
| `app/api/organisation_tools.py` | Authorized tool catalogue, provider selection, evidence normalization, and AWS/SharePoint separation |
| `app/api/assistant_orchestrator.py` | Bedrock Converse tool-routing policy and bounded tool loop |
| `app/api/answer_lambda_handler.py` | HTTP validation, authenticated context, history validation, and orchestration entry point |
| `app/api/retrieval.py` | Existing protected AWS retrieval only; do not place SharePoint provider logic here |

### Frontend and infrastructure

| File | Responsibility |
|---|---|
| `frontend/src/authConfig.js` | MSAL tenant/client/API scope configuration |
| `frontend/src/App.jsx` | Sign-in, protected API token, bounded history, answer/citation UI |
| `infra/sharepoint_auth.tf` | Entra/API Gateway/CloudFront boundary and SharePoint provider variables |
| `infra/answer_lambda.tf` | Lambda package/runtime environment wiring |
| `infra/sharepoint_auth.auto.tfvars.example` | Nonsecret environment-value example; never store real secrets here |
| `infra/terraform.tfstate` | Historical applied-state evidence; never hand-edit |

### Decision and evidence records

| File | Responsibility |
|---|---|
| `docs/SHAREPOINT_RETRIEVAL_SOURCE_OF_TRUTH.md` | This authoritative current execution plan |
| `docs/ARCHITECTURE_DECISIONS.md` | ADR history and approved architecture decisions |
| `docs/SHAREPOINT_IMPLEMENTATION_LOG.md` | Append-only implementation/evidence evolution |
| `docs/SHAREPOINT_REFERENCE_TEST_MATRIX.md` | Core retrieval and permission evaluation cases |
| `docs/SHAREPOINT_OPTION_C_CUSTOM_INDEX.md` | Detailed future Option C gate |
| `PROJECT_HANDOFF.md` | Cross-session current handoff and approval boundaries |
| `PROGRESS_TRACKER.md` | Current project status and next micro-win |
| `SOURCE_OF_TRUTH.md` | Immutable append-only project history |

## 10. Configuration contract

| Setting | Current source default | Meaning |
|---|---|---|
| `SHAREPOINT_ENABLED` | `false` | Independent live activation gate |
| `SHAREPOINT_PROVIDER` | `graph_search` | `graph_search` for selected B; `copilot_retrieval` for future A |
| `SHAREPOINT_GENERAL_SITE_URL` | non-routable placeholder | Exact approved general site path |
| `SHAREPOINT_RESTRICTED_SITE_URL` | non-routable placeholder | Exact approved restricted site path |
| `SHAREPOINT_MAX_RESULTS` | `10` | Bounded evidence/results request, maximum 25 |
| `SHAREPOINT_TIMEOUT_SECONDS` | `8` | Microsoft request timeout |
| `SHAREPOINT_MAX_RETRIES` | `2` | Retry cap for retryable provider failures |
| `ENTRA_TENANT_ID` | required environment value | Expected tenant for OBO |
| `ENTRA_API_CLIENT_ID` | required environment value | Confidential API app client ID |
| `ENTRA_CREDENTIAL_SECRET_ID` | Terraform-managed reference | AWS Secrets Manager location for client credential |

Real secrets and tokens must never enter Terraform variables, example tfvars, source control, test fixtures, logs, or tracker documents.

## 11. Step-by-step execution plan

### Gate 0 — freeze architecture and preserve AWS

- Treat this document as the current SharePoint plan.
- Do not modify AWS ingestion, Titan embeddings, Aurora, pgvector, AWS retrieval, or their permissions.
- Do not delete Options B or C documentation.
- Do not deploy merely to reconcile source with applied state.

**Exit evidence:** current file/status review and no unreviewed shared-path change.

### Gate 1 — verify Microsoft commercial eligibility read-only

Determine and record:

- whether Bishal, Adele, or Alex has a Microsoft 365 Copilot add-on license;
- whether the tenant has at least one qualifying Copilot license;
- whether Retrieval PAYG is already enabled;
- which users/groups would be covered;
- linked Azure subscription/resource group, if any;
- current pricing, preview status, SLA, propagation behavior, quotas, and terms.

Do not create billing, enable PAYG, assign licenses, or accept terms during this read-only gate.

**Exit evidence:** dated tenant/licensing note with official source links and no assumed entitlement.

**Result on 2026-09-21:** gate completed with a blocker. The tenant has no Microsoft 365 Copilot add-on and no connected Retrieval PAYG policy/service. Do not proceed with Option A deployment unless eligibility is deliberately obtained and separately approved.

### Gate 2 — verify Entra applications and consent read-only

Confirm:

- single-tenant frontend and protected API registrations;
- frontend redirect URI matches deployed HTTPS URL;
- frontend requests only the AskAnyDoc API delegated scope;
- API exposes `access_as_user`;
- API registration has delegated `Files.Read.All` and `Sites.Read.All` for Option A;
- admin consent status;
- client secret is stored only in AWS Secrets Manager;
- API Gateway JWT authorizer audience, issuer, and scope match the registrations.

Do not grant new tenant-wide permission without a separate warning and approval.

**Exit evidence:** redacted configuration table and screenshots/IDs sufficient to reproduce configuration without revealing secrets.

### Gate 3 — verify exact SharePoint paths and direct access

- Copy exact site/folder paths from SharePoint Details, not browser sharing links.
- Verify Adele can open general content and cannot open restricted content.
- Verify Alex can open both.
- Record identity, timestamp, path, result, and screenshot/evidence.

**Exit evidence:** direct SharePoint permission truth table passes before AI retrieval testing.

### Gate 4 — finish local provider verification

- Run all Python tests.
- Add/retain tests for Copilot request payload, OBO token use, query limits, error mapping, extract parsing, relevance score, empty response, malformed response, retries, and allowlisting.
- Add identity-isolated provider mocks for general/restricted evidence.
- Verify no AWS retrieval modules changed unexpectedly.
- Run frontend lint/build if frontend/auth files changed.
- Install/use Terraform only through the approved project workflow; run format and validation when available.

**Exit evidence:** passing test log, clean diff check, and documented unavailable tools.

### Gate 5 — prepare environment values and Terraform plan

Prepare noncommitted environment values for:

- real tenant/client/API scope IDs;
- `sharepoint_enabled=true`;
- `sharepoint_provider=graph_search`;
- exact approved general and restricted site paths;
- bounded result count.

Create a Terraform plan only. Review all changes, including Lambda code hash/environment, API Gateway, IAM, Secrets Manager, CloudFront/S3, provider replacements, deletions, and unrelated drift.

**Exit evidence:** saved/redacted plan summary with no unexpected replacement, deletion, AWS-path, database, IAM, or public-access change.

### Gate 6 — explicit deployment approval

Immediately before any apply or deployment, present Bishal with:

- exact files and AWS/Microsoft resources affected;
- current versus proposed values;
- expected behavior change;
- Microsoft cost/licensing exposure;
- preview/SLA implications;
- security risks and mitigations;
- downtime/failure scenarios;
- rollback commands/values;
- confirmation that the AWS retrieval path is unchanged.

Do not rely on earlier general approval. Obtain explicit approval for this exact plan.

### Gate 7 — controlled Option B deployment

After approval only:

- ensure required delegated Graph consent is complete;
- deploy the reviewed Lambda package and environment/provider values;
- do not modify AWS ingestion, Aurora, or vector data;
- retain Copilot provider code but do not invoke it automatically.

**Exit evidence:** deployed version/config identity and timestamps.

### Gate 8 — direct Graph retrieval and extraction smoke test

Before involving Claude answer generation, inspect retrieval behavior using focused questions:

- exact-title question;
- semantic content question;
- no-match question;
- approved-site scoping;
- empty results;
- unauthorized/consent failure;
- timeout/throttling response.

Do not log bearer tokens or unrestricted document text.

**Exit evidence:** permission-trimmed PDF page evidence with correct URL/title/page provenance.

### Gate 9 — full identity and answer matrix

Run at minimum:

| User | General question | Restricted question | Expected |
|---|---|---|---|
| Adele | yes | yes | general grounded; restricted denied/no evidence |
| Alex | yes | yes | both grounded with correct citations |
| Bishal | administration only | administration only | not a substitute for user isolation |
| unauthenticated | SharePoint request | any | SharePoint tool absent/denied |

Also test missing evidence, citation URL correctness, malicious instructions inside documents, source-routing behavior, retry limits, and error messages.

**Exit evidence:** completed `SHAREPOINT_REFERENCE_TEST_MATRIX.md` with timestamps and outcomes.

### Gate 10 — regress the protected AWS path

- Ask known AWS-corpus questions and verify semantic retrieval and citations.
- Ask an unrelated question and verify grounded refusal/general handling.
- Confirm SharePoint changes did not modify AWS embeddings, chunks, Aurora schema/data, IAM, or citations.
- Test an explicit cross-source comparison only after both individual sources pass.

**Exit evidence:** AWS regression results identical or acceptably explained.

### Gate 11 — observe cost, latency, quality, and failures

Record per provider:

- retrieval calls per question;
- retrieval/provider latency;
- answer latency;
- result/extract count;
- answer and citation correctness;
- authorization outcome;
- throttling/timeouts;
- model tokens/cost;
- Microsoft retrieval cost where applicable.

Do not enable automatic retries that can multiply PAYG costs without a bounded policy.

### Gate 12 — reconsider Option A only if eligibility changes

If the tenant later becomes eligible, run the same golden questions through `copilot_retrieval` in a separate explicit evaluation configuration. Compare quality, latency, failure rate, permissions, and total cost. Do not switch automatically.

### Gate 13 — evaluate Option C only after scale evidence

Use `SHAREPOINT_OPTION_C_CUSTOM_INDEX.md`. Require an architecture/security review, separate index boundary, permission model, synchronization/revocation SLO, cost model, test plan, operational owner, and explicit approval before implementation.

## 12. Definition of done for the current SharePoint slice

The current slice is complete only when:

- Option A is commercially and technically verified for the test users, or a clearly recorded blocker selects Option B for the environment;
- Adele and Alex permission tests pass both directly in SharePoint and through AskAnyDoc;
- semantic questions return sufficient text extracts/evidence, not filename-only metadata;
- restricted text, title, URL, and citation never appear for an unauthorized user;
- answers use only returned evidence and cite real SharePoint sources;
- missing evidence produces an honest refusal;
- AWS-only and cross-source regression tests pass;
- cost, latency, call count, and errors are observable;
- deployment and rollback are documented;
- trackers and append-only history contain the final evidence;
- no production-ready or enterprise-ready claim exceeds the evidence.

## 13. Failure modes and required response

| Failure | Required behavior |
|---|---|
| Missing/expired user token | Do not expose or execute SharePoint tool; require sign-in |
| OBO consent/credential failure | Fail closed; do not fall back to app-only or client-supplied identity |
| Copilot entitlement/billing failure | Surface controlled availability error; no automatic B fallback |
| Invalid KQL/path uncertainty | Reject or return no evidence; post-filter every result |
| Result outside approved site | Drop result and record safe diagnostic metadata only |
| Empty extracts | State insufficient SharePoint evidence |
| Graph file too large | Skip/fail with bounded error; never exceed memory limit |
| Microsoft throttling | Bounded retry/backoff; respect service guidance and prevent cost loops |
| Permission changed mid-session | Re-query under current user context; do not rely on stale answer cache |
| Provider returns malformed data | Reject evidence; do not send it to Claude |
| Document prompt injection | Treat as quoted evidence, never as executable instruction |
| Terraform plan includes replacement/deletion/unrelated AWS change | Stop and request review/approval |

## 14. Rollback plan

Preferred rollback order after an Option B deployment problem:

1. Set `SHAREPOINT_ENABLED=false` through a reviewed environment/Terraform change.
2. Redeploy the previously known Lambda package/configuration if code, not provider availability, caused the problem.
3. Keep AWS-only answering available if its regression tests pass and its boundary remains independent.
4. Redeploy the previously known package/configuration if the bounded Graph adapter caused the failure.
5. Do not switch to Copilot Retrieval as an emergency fallback while its commercial gate remains blocked.

Rollback must not delete SharePoint sites, documents, groups, AWS data, Terraform state, or secrets.

## 15. Approval boundaries

### Allowed without additional infrastructure approval

- read-only inspection;
- current official-source research;
- local documentation;
- isolated Microsoft adapter code/tests;
- mocked provider tests;
- local lint/build/tests;
- read-only Terraform state/plan inspection when tooling and credentials permit.

### Requires explicit warning and approval immediately before action

- enabling PAYG, linking Azure billing, assigning/purchasing licenses, or accepting preview terms;
- granting or changing Entra delegated/application permissions or admin consent;
- rotating or changing the confidential-client credential;
- changing live Lambda code/environment/provider flags;
- Terraform apply, import, state migration, destroy, replacement, or resource move;
- changing API Gateway/CloudFront/Function URL/IAM/public access;
- changing AWS ingestion, S3 layout, embeddings, Aurora, pgvector, retrieval, or data;
- implementing Option C or copying SharePoint documents into a persistent external index;
- removing the Graph fallback or retiring the Function URL.

Every approval request must state blast radius, failure modes, cost exposure, rollback, and verification.

## 16. Exact next actions

Resume in this order:

1. Read this document and the latest `PROJECT_HANDOFF.md` checkpoint.
2. Treat Bishal's explicit 2026-09-21 selection of Option B as complete and recorded in ADR-008.
3. Complete Gate 2 read-only Entra permission/admin-consent inspection after Bishal completes the portal's interactive authentication step.
4. Complete direct sign-in checks as Adele and Alex. The admin-side effective permission matrix is proven, but isolated user sessions are not.
5. Keep the verified exact site paths unchanged unless SharePoint Details produces a different canonical path.
6. Preserve the current green local baseline: 43 Python tests plus 6 subtests, frontend lint, and frontend production build.
7. Preserve deployment identity: commit `39f2474`, Lambda code SHA-256 `T51h5B4tXxhOFCriUnlNTdf4BQ8OEGpwc1PhFxPEjgg=`, applied 2026-09-21 17:41 AEST.
8. Run direct authenticated Graph retrieval and bounded PDF extraction before relying on Claude's answer.
9. Run the isolated Adele/Alex General/Restricted/no-match/citation matrix and record timestamps and outcomes.
10. Preserve the completed AWS regression evidence and add cross-source testing only after both sources independently pass.
11. Record latency, throttling, timeout, extraction-limit, token, and error evidence.
12. Compare the other provider only as an explicit evaluation after the selected path has evidence.
13. Design reliability/decoupling separately using current official AWS and Microsoft guidance and measured failure/latency data. Do not alter the protected AWS path under the completed deployment approval.
14. Keep Option C deferred until representative scale measurements justify a separate platform project.

## 17. Official references to recheck

- Copilot Retrieval overview: https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/api/ai-services/retrieval/overview
- Copilot Retrieval request/reference: https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/api/ai-services/retrieval/copilotroot-retrieval
- Copilot Retrieval PAYG: https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/api/ai-services/retrieval/paygo-retrieval
- Microsoft identity OBO: https://learn.microsoft.com/en-us/entra/identity-platform/scenario-web-api-call-api-overview
- Microsoft Search API: https://learn.microsoft.com/en-us/graph/api/resources/search-api-overview?view=graph-rest-1.0
- Search SharePoint/OneDrive files: https://learn.microsoft.com/en-us/graph/search-concept-files
- Download DriveItem content: https://learn.microsoft.com/en-us/graph/api/driveitem-get-content?view=graph-rest-1.0
- DriveItem delta/change tracking: https://learn.microsoft.com/en-us/graph/api/driveitem-delta?view=graph-rest-1.0
- Document-level access control: https://learn.microsoft.com/en-us/azure/search/search-document-level-access-overview
- Secure multitenant RAG: https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/secure-multitenant-rag
- Bedrock tool use: https://docs.aws.amazon.com/bedrock/latest/userguide/tool-use.html

All licensing, prices, preview/GA status, permissions, quotas, supported formats, and service limits are version-sensitive and must be rechecked from current official sources at the relevant gate.
