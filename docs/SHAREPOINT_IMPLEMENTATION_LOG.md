# SharePoint integration implementation log

> **Historical evidence log:** Read `SHAREPOINT_RETRIEVAL_SOURCE_OF_TRUTH.md` for the current provider decision, state, next action, and approval rules. Older Graph-first entries below are preserved history and do not override it.

This file records verified implementation evidence for the architecture in `SHAREPOINT_SOURCE_PLAN.md`. It must distinguish inspection, configuration, testing, and deployment; a planned or attempted action is not recorded as complete.

## Phase 1 — permission test environment

### Baseline inspection — 2026-09-20

- Signed into the `y4m7` Microsoft 365 developer tenant as its Global Administrator.
- Microsoft 365 E5 Developer SKU V2 is assigned to 17 users: the administrator plus 16 synthetic sample users.
- Selected existing synthetic identities for the proposed test matrix:
  - employee: Adele Vance (`AdeleV@y4m7.onmicrosoft.com`);
  - senior: Alex Wilber (`AlexW@y4m7.onmicrosoft.com`).
- Existing Microsoft 365 groups are sample groups such as All Company, Mark 8 Project Team, Retail, Sales and Marketing, and U.S. Sales.
- The Security groups tab contains no existing groups.
- Existing SharePoint sites are sample sites. No site named `AskAnyDoc-General` or `AskAnyDoc-Restricted` exists.
- No group, membership, site, library, document, or permission was changed during this inspection.

### Controlled change completed — 2026-09-20

1. Created security group `AskAnyDoc-General-Readers` (object ID `945eb7f1-380b-41fb-8e9b-82d181c56514`).
2. Added Adele Vance (`AdeleV@y4m7.onmicrosoft.com`) and Alex Wilber (`AlexW@y4m7.onmicrosoft.com`) to that group.
3. Created security group `AskAnyDoc-Senior-Readers` (object ID `6ee55ab2-ae38-41fe-96d2-89a04384c7bc`).
4. Added Alex Wilber (`AlexW@y4m7.onmicrosoft.com`) only to that group.
5. Verified the memberships in the Microsoft 365 admin center: general group has two members; senior group has one member.
6. Created the SharePoint team site `AskAnyDoc-General-Documents` at `https://y4m7.sharepoint.com/sites/AskAnyDoc-General-Documents` with Bishal Giri as owner.
7. Created the SharePoint team site `AskAnyDoc-Restricted-Senior-Documents` at `https://y4m7.sharepoint.com/sites/AskAnyDoc-Restricted-Senior-Documents` with Bishal Giri as owner.
8. Verified both sites appeared in SharePoint admin center Active sites as Team sites connected to Microsoft 365 groups.
9. Tried to add the security groups during each site-creation wizard. SharePoint's directory picker did not resolve them at that point, so the assignments were completed afterward from each site's classic permissions page once directory search resolved the groups.
10. Granted `AskAnyDoc-General-Readers` access to `AskAnyDoc-General-Documents` through the Share dialog. The picker resolved the tenant group with object ID `945eb7f1-380b-41fb-8e9b-82d181c56514`; the page then displayed `Shared with: AskAnyDoc-General-Readers`.
11. Granted `AskAnyDoc-Senior-Readers` access to `AskAnyDoc-Restricted-Senior-Documents` through the Share dialog. The picker resolved the tenant group with object ID `6ee55ab2-ae38-41fe-96d2-89a04384c7bc`; the page then displayed `Shared with: AskAnyDoc-Senior-Readers`.

### Next controlled change

1. Upload small, clearly labelled test documents to each site's Documents library.
2. Verify source visibility and access boundaries with the general and senior synthetic identities.

Status: Phase 1 identity boundary, both test sites, and both group-to-site assignments are configured and verified. The approved Microsoft 365 automation corpus and validation matrix are recorded in `SHAREPOINT_AUTOMATION_CORPUS_PLAN.md`; document creation/upload and retrieval/access-boundary tests remain pending.

The official-reference stage is now recorded in `MICROSOFT_AUTOMATION_REFERENCE_INDEX.md`. The index separates general guidance from senior-restricted governance/ALM material and records the rule to store Learn pages as links and upload only permitted official PDFs.

The validation stage is prepared in `SHAREPOINT_REFERENCE_TEST_MATRIX.md`. It defines ten questions covering single-source answers, multi-source answers, missing evidence, restricted access, citation correctness, and operational evidence. Actual SharePoint upload and identity-isolated retrieval results remain the next external steps.

The code boundary is now explicit: SharePoint adapter code lives under `app/sharepoint/`, while existing AWS ingestion/retrieval/orchestration remains in its existing paths. See `PROJECT_SOURCE_BOUNDARIES.md`. The bundled project Python runtime successfully completed `compileall` for the SharePoint package. Full pytest execution remains pending because pytest is not installed in that bundled runtime; the AWS virtual environment was not changed.

Infrastructure preparation items 1–9 are implemented: SharePoint configuration/site allowlist, provider-neutral adapter, user-context parameter, source routing, provenance normalization, categorized failures, bounded retry boundary, disabled-by-default feature flag, and isolated mocked tests. Terraform now exposes the SharePoint flags and site URLs while keeping the feature disabled until Entra delegated retrieval is configured.

## Official reference preparation — 2026-09-20

- Created `MICROSOFT_AUTOMATION_REFERENCE_INDEX.md` with Microsoft Learn and architecture references, separated into general and senior-restricted topics.
- Created `UPLOAD_MANIFEST.md` for the official PDF batch.
- Downloaded official Microsoft PDFs into `projects/askanydoc/official_references/`:
  - general: Microsoft 365 enterprise architecture;
  - general: Microsoft 365 Teams logical architecture;
  - senior-restricted: SharePoint sites for highly regulated data.
- Uploaded `MICROSOFT_AUTOMATION_REFERENCE_INDEX.md` to the general SharePoint Documents library and verified it appeared in the library.
- The two general PDFs and the senior-restricted PDF have not yet been uploaded; Bishal will upload them later.

## Entra preparation — 2026-09-20

- Added `app/sharepoint/entra_config.example.json` with placeholders for tenant ID, client ID, HTTPS redirect URI, and delegated scopes.
- Added `ENTRA_SHAREPOINT_SETUP_CHECKLIST.md`.
- No client secret, token, OTP, or password was collected or stored.
- `SHAREPOINT_ENABLED` remains `false` in Terraform until delegated retrieval and permission tests are complete.

## Current blockers and next actions

1. Upload the three downloaded official PDFs to their assigned SharePoint libraries.
2. Register the Entra application using the final HTTPS redirect URI and grant only the required delegated consent.
3. Install pytest into the project-managed test environment and run the isolated SharePoint tests.
4. Implement the real Microsoft provider behind the adapter boundary.
5. Run the general/restricted, missing-answer, citation, latency, and failure matrix.

## Superseding implementation checkpoint — 2026-09-21

This section supersedes the earlier "Next controlled change," upload status, feature-flag statement, and blockers where they conflict. Earlier text remains unchanged as the historical record of what was true at that time.

### Yesterday's position and completed changes

- The controlled permission world was created and verified: Adele and Alex are general readers; Alex alone is a senior reader; both SharePoint sites exist and the matching security groups are assigned.
- Bishal subsequently reported uploading **8 documents to the general site and 4 documents to the restricted senior site**. This is current user-reported evidence; the file inventory and contents still need direct verification through the two identities.
- Entra application/authentication work, the protected API boundary, frontend sign-in integration, on-behalf-of token exchange, Graph Search provider, Copilot Retrieval provider, source routing, and Terraform wiring now exist in the working tree.
- Local Terraform state shows the CloudFront/private-S3 frontend and API Gateway/Entra JWT boundary were applied. It also records SharePoint as enabled with `graph_search` at the last applied checkpoint.
- The current uncommitted Terraform working copy instead selects `copilot_retrieval`. That provider switch is **not treated as approved or deployed** and must not be applied until entitlement, cost/preview status, and the permission matrix are verified.
- Before the architecture correction, all Python tests passed (28 tests plus 6 subtests). After adding query-time site scoping and restoring Graph Search as the safe default, all Python tests pass again: **31 tests plus 6 subtests in 1.36 seconds**. Frontend lint and production build passed before this backend-only change. Terraform validation was not rerun because Terraform was unavailable in the current shell.

### Architecture correction now adopted

- The AWS ingestion/retrieval stores and data flow remain the protected working baseline. No SharePoint document is copied into Aurora for this slice.
- The Microsoft path uses the signed-in Entra identity, API Gateway JWT validation, on-behalf-of token exchange, and permission-trimmed Microsoft retrieval.
- Both Microsoft providers must scope the server-side request to the two approved SharePoint paths and must also retain post-response URL allowlist filtering.
- Implemented that correction in both providers: Graph Search now combines the user query with mandatory KQL `Path` restrictions; Copilot Retrieval sends the same allowlist through `filterExpression`. Both retain response URL filtering. Copilot Retrieval also rejects queries above its documented 1,500-character limit, and provider configuration now defaults to Graph Search.
- Graph Search is the initial verification provider. Copilot Retrieval remains conditional and is not the default until its tenant entitlement, limits, preview/SLA posture, and cost are accepted.
- Full rationale, official references, consequences, and approval boundaries are in `ARCHITECTURE_DECISIONS.md`.

### Current inconsistencies and risk controls

1. The applied-state provider (`graph_search`) and current Terraform source (`copilot_retrieval`) disagree. Do not apply Terraform until reconciled.
2. The feature is enabled in applied state even though the earlier checklist said to keep it disabled. Treat the environment as potentially live and test it cautiously; do not assume the old document is a safety control.
3. The public Function URL still exists. It is not an acceptable identity boundary for SharePoint and must remain AWS-only during migration.
4. Direct live AWS verification is pending because this session has no usable AWS CLI credentials/region context. Local state is evidence of an apply, not a substitute for a live inventory.
5. The two-user Adele/Alex permission and retrieval matrix is still unproven. No production-ready claim is allowed before it passes.

### Next evidence gates, in order

1. Verify Adele can open general documents and cannot open the restricted site; verify Alex can open both.
2. Test direct on-behalf-of Graph retrieval through the protected API without Claude, including query-time site scoping.
3. Regress the preserved AWS-only retrieval and answer path.
4. Run general, restricted, missing-answer, citation, throttling/timeout, and identity-failure cases for both users.
5. Reconcile the Terraform provider/feature flags, review a plan, and obtain explicit approval before applying any AWS/shared-path change.
6. Consider Copilot Retrieval only after the Graph baseline is proven and its commercial/service conditions are accepted.

## Source-routing implementation — 2026-09-21

This section supersedes the provider/source mismatch described in the earlier checkpoint. The earlier wording is retained as the pre-reconciliation history.

- Replaced the ambiguous AWS tool name `search_organisation_sources` with `search_aws_documents`; the implementation still calls the unchanged AWS retrieval function and does not modify the AWS ingestion, embedding, Aurora, or provenance path.
- Requests now receive a capability-filtered tool catalogue. AWS search is always available to the current assistant; SharePoint search is advertised only when the feature is enabled and validated `user_id`, `tenant_id`, and bearer-token context are present.
- The prompt now prefers an explicit user source, otherwise one primary source, permits both only for a real comparison/cross-source need, and permits one different-source fallback rather than searching every source by default.
- Terraform source now uses explicit variables. Safe defaults are `sharepoint_enabled = false` and `sharepoint_provider = "graph_search"`; URLs default to non-routable placeholders and must be deliberately supplied for the target environment.
- Verification: **35 Python tests plus 6 subtests passed in 1.60 seconds**. Terraform formatting/validation remains unverified because the Terraform executable is unavailable in the current shell.
- No package, AWS resource, Terraform state, secret, or live deployment was changed.

## Copilot Retrieval local application — 2026-09-21

- Applied the Copilot Retrieval adapter locally and aligned its KQL spelling with Microsoft's documented `path:` property.
- Hardened response handling to match the documented shape: extracts carry `relevanceScore`; the adapter now preserves the strongest extract score while returning bounded text and provenance.
- Verification: **30 Python tests passed in 1.23 seconds** for the SharePoint/API slice.
- This is still a local, un-deployed provider experiment. The applied AWS environment remains unchanged and still uses the previously applied Graph Search configuration.
- Official current reference: Microsoft documents `POST /v1.0/copilot/retrieval`, SharePoint `dataSource`, delegated `Files.Read.All` + `Sites.Read.All`, 1,500-character queries, maximum 25 results, and permission-trimmed extracts. Pay-as-you-go for non-Copilot users remains preview and requires tenant acceptance.

## Provider-direction reconciliation — 2026-09-21

- Bishal confirmed that Copilot Retrieval was always the intended SharePoint path. The temporary records describing Graph Search as a required baseline did not reflect that decision.
- Changed local application and Terraform provider defaults to `copilot_retrieval` while keeping `SHAREPOINT_ENABLED=false`; Graph Search remains available only as an explicit diagnostic/entitlement fallback.
- Updated current handoff, tracker, source-plan, checklist, README, boundaries, delivery criteria, and architecture decision records. Historical entries remain intact and are superseded rather than erased.
- Added a focused Copilot provider contract test covering the OBO bearer token, v1.0 endpoint, `sharePoint` payload, two-site `path:` filter, extract normalization, and extract-level relevance scores.
- Replaced permissive URL-prefix checks with exact HTTPS host and site-path-boundary matching for both providers.
- Verification: **39 Python tests plus 6 subtests passed in 1.46 seconds**.
- No AWS resource, Lambda configuration, Terraform state, Entra permission, billing policy, secret, or live provider was changed.

## Gate 1 and permission evidence — 2026-09-21

- Restored the existing local frontend dependency installation after the interrupted package-manager check. Frontend lint and production build now pass; the known approximately 589 kB bundle warning remains.
- Current Microsoft official guidance was rechecked. Retrieval for non-Copilot users remains PAYG preview at USD $0.10 per API call, with no SLA, and requires eligible Azure billing plus at least one Microsoft 365 Copilot license in the tenant.
- Read-only tenant inspection found only Microsoft 365 E5 Developer SKU V2 and no Microsoft 365 Copilot add-on. Copilot Billing & usage showed no connected PAYG policy and no enabled Retrieval API service. Option A is therefore commercially blocked in this tenant at this gate.
- SharePoint Check Permissions proved the effective site matrix without changing access: Adele = General Edit / Restricted None; Alex = General Edit / Restricted Edit. Direct sign-in and end-to-end retrieval isolation remain pending.
- Hardened the local Copilot adapter so network failures, invalid JSON, and invalid response shapes fail with controlled categorized errors. Added tests for those cases and the 1,500-character limit. Verification: **43 tests plus 6 subtests passed in 1.42 seconds**.
- Entra live consent inspection remains incomplete because the Entra portal requested a separate interactive authentication step. Terraform remains unavailable. No AWS resource, Lambda environment, Terraform state, Microsoft permission, billing policy, license, secret, or live provider changed.

## Option B selection and reviewed plan — 2026-09-21

- Bishal explicitly selected Option B, Graph Search plus bounded on-demand extraction, for the current test environment after reviewing its Microsoft identity and permission architecture.
- Reconciled local application and Terraform provider defaults to `graph_search`; the checked-in activation default remains `false`. Added a Git-ignored, nonsecret environment input file with SharePoint enabled, the two verified site URLs, and a 10-result cap for planning.
- Added ADR-008. Copilot Retrieval remains implemented but commercially blocked and is not an automatic fallback.
- Installed official Terraform 1.16.3 into the ignored project `tmp` directory and verified its published SHA-256 checksum. Formatting and validation pass.
- The saved plan proposes only an in-place update of `askanydoc-api`, replacement of the local dependency-build trigger, and rereading the local Lambda ZIP data source. It proposes no protected AWS retrieval, S3, Aurora, IAM, API Gateway, CloudFront, Function URL, ingestion, queue, secret, or database change.
- Planned SharePoint values are enabled, `graph_search`, the verified General/Restricted site URLs, and 10 maximum results. The plan remains unapplied pending the exact Gate 6 warning and approval.
## 2026-09-21 17:39 AEST — Option B deployment approved

- Bishal explicitly approved applying the reviewed saved Option B Terraform plan.
- The approved blast radius is limited to an in-place update of the shared `askanydoc-api` Lambda, its environment values, and the local packaging trigger. The plan does not change AWS ingestion, S3, Aurora, pgvector, IAM, API Gateway, CloudFront, the Function URL, secrets, queues, or stored data.
- Bishal requested a Git checkpoint before deployment so the reviewed source can be recovered.
- The reliability and decoupling concern is recorded as a separate follow-up architecture phase. It must use current AWS and Microsoft guidance, measured evidence, and a separately reviewed plan; it does not broaden this deployment approval or authorize changes to the protected AWS retrieval path.
- Immediate sequence: checkpoint, apply the exact saved plan, capture deployed identity/timestamp, test SharePoint permission boundaries and citations, then regress the existing AWS path.

## 2026-09-21 17:41 AEST — Option B deployed and initial regression passed

- Created recovery checkpoint commit `39f2474` before deployment.
- Applied only the reviewed saved Terraform plan. Terraform reported one local packaging-trigger replacement and one in-place update of `aws_lambda_function.lambda_function`; no protected AWS-path or other cloud resource was changed.
- AWS reports `askanydoc-api` active with successful last update, Python 3.13, 60-second timeout, 512 MB memory, and code SHA-256 `T51h5B4tXxhOFCriUnlNTdf4BQ8OEGpwc1PhFxPEjgg=`.
- Verified live SharePoint environment values: enabled, provider `graph_search`, exact General/Restricted site URLs, and 10 maximum results.
- Live AWS regression passed for “What problem does SQS partial batch response solve?” with a grounded answer citing `17-lambda-sqs-partial-batch-responses.pdf`, page 5.
- The protected endpoint returned HTTP 401 without a bearer token, confirming that SharePoint retrieval is not exposed anonymously through that route.
- Remaining evidence: direct authenticated Graph extraction; isolated Adele General/Restricted tests; isolated Alex General/Restricted tests; SharePoint citations, no-match, throttling/timeout, and latency observations.
- Reliability/decoupling remains a separately scoped design follow-up. The deployed shared Lambda is not being described as the final large-enterprise topology.
## 2026-09-21 17:50 AEST — First authenticated Option B test exposed download fallback gap

- Bishal's authenticated session successfully reached the protected API, OBO exchange, delegated Graph Search, and a permitted PDF candidate.
- The request then failed closed before document content or an answer was returned because the drive-item metadata response omitted `@microsoft.graph.downloadUrl`.
- CloudWatch recorded `SharePointError: Microsoft Graph omitted a valid download URL`; no token or document body was logged.
- Added a local fallback to Microsoft's documented `GET /drives/{drive-id}/items/{item-id}/content` contract. The code deliberately intercepts the 302 and downloads the preauthenticated HTTPS URL without forwarding the Graph bearer token to the storage host.
- Added a regression test for the omitted-annotation path while retaining the existing bearer-token boundary test.
- Verification: **86 tests passed, 10 skipped, plus 6 subtests passed**. No live code or configuration change has yet been made for this fix.
## 2026-09-21 17:54–18:00 AEST — Download fallback deployed and live grounding proven

- Bishal explicitly approved the narrow saved plan for commit `4645279`; it updated only the shared `askanydoc-api` package in place plus the local packaging trigger.
- AWS reports active/successful with code SHA-256 `ZfmED9FKHsVh7dTKhu6NjgW5m66chLiRoNUziDNW+LQ=`. No configuration, IAM, API Gateway, S3, Aurora, ingestion, frontend, or stored-data resource changed.
- Bishal's authenticated semantic question succeeded after the fix. Graph Search selected permitted General-site content, the Lambda downloaded and extracted PDF pages, and the answer cited pages 1–3 of `microsoft-cloud-hybrid-architecture.pdf`.
- SharePoint Lambda duration was 13.4 seconds, 6,204 input tokens, 319 output tokens, three citations, 170 MB maximum memory in a 512 MB function.
- The known AWS SQS question passed again with the expected `17-lambda-sqs-partial-batch-responses.pdf`, page 5 citation; client latency was 33.7 seconds.
- This proves Bishal's authenticated Option B vertical slice and AWS coexistence. It does not prove Adele/Alex isolation.
- Recorded the recommended next architecture direction in `SHAREPOINT_LAMBDA_SEPARATION_PLAN.md`: one answer/orchestrator plus a dedicated least-privilege SharePoint retrieval Lambda. The proposal is not approval to change IAM, routing, concurrency, or live infrastructure.
## 2026-09-21 — Single Lambda retained; separation deferred

- Bishal chose the current single answer/orchestration Lambda for the present workload and cost profile.
- The dedicated SharePoint retrieval Lambda is retained as a future option only, with measurable triggers recorded in `SHAREPOINT_LAMBDA_SEPARATION_PLAN.md`.
- Current code-level controls remain: authenticated tool exposure, OBO delegation, exact site allowlisting, bounded results/files/bytes/pages/excerpts, bounded retries/timeouts, fail-closed provider errors, and source-specific evidence/citations.
- No live AWS, Microsoft, IAM, routing, state, code, configuration, or data change occurred for this decision.

## 2026-09-21 18:32–18:56 AEST — Adele/Alex end-to-end retrieval matrix passed

- Verified the identity displayed by AskAnyDoc before each isolated test session: Alex was `AlexW@y4m7.onmicrosoft.com`; Adele was `AdeleV@y4m7.onmicrosoft.com`.
- Used the same controlled General question for both users. Both received grounded answers with three citations to `microsoft-cloud-hybrid-architecture.pdf` pages 2, 1, and 3 under the General site.
- Used the same controlled Restricted question for both users. Alex received the Restricted document answer with one citation to `sharepoint-sites-highly-regulated-data.pdf` page 1. Adele received `organisation_not_found`, zero citations, no Restricted URL, and no Restricted document-derived protection list.
- CloudWatch completion evidence: Alex General 11.18 s (6,204 input / 315 output tokens); Alex Restricted 28.08 s (8,029 / 604); Adele General 17.08 s (6,204 / 335); Adele Restricted denial 13.58 s (7,310 / 616). All four requests completed successfully at the Lambda boundary.
- An earlier Alex filename-heavy query returned no match in 8.68 s. It is recorded as query-sensitivity evidence, not a permission failure.
- This proves the core end-to-end AskAnyDoc permission matrix for the tested corpus and questions. It does not prove production readiness, the remaining operational/failure cases, or direct site navigation under each isolated identity.
- No permissions, Entra consent, AWS resource, Lambda code/configuration, Terraform state, billing, IAM, routing, document, or protected AWS retrieval component changed during this test.

## 2026-09-22 — Read-only Entra audit and remaining boundary checks

- Direct Adele navigation proved General allowed and Restricted denied by SharePoint itself. Bishal accepted the existing Alex permission/retrieval evidence without another redundant direct login.
- Live Entra inspection proved the single-tenant API exposes enabled `access_as_user`; delegated Microsoft Graph `Files.Read.All`, `Sites.Read.All`, and `User.Read` each show `Granted for y4m7`. The single-tenant frontend has the exact CloudFront SPA redirect and requests `access_as_user` plus `User.Read`. No permission or consent changed.
- A live generic SharePoint no-match returned the controlled no-match mode with no citations.
- Added test-only coverage for malicious-document isolation, Graph metadata timeout mapping, bounded throttling retries, and the configured file-byte limit. The current source-tree suite passed 48 tests plus 6 subtests in 1.63 seconds.
- The explicit AWS-versus-SharePoint comparison failed twice: first `Service Unavailable`, then the controlled generic answer failure. This is retained as measured evidence and is the next defect to diagnose; it was not retried further or misreported as a pass.
- No production code, AWS resource, Lambda configuration, Terraform state, Entra permission, consent, SharePoint permission, billing policy, IAM, routing, document, or protected AWS retrieval component changed.

## 2026-09-22 — Read-only cross-source failure diagnosis

- CloudWatch question hashes matched both explicit AWS-versus-SharePoint prompts to their exact Lambda invocations.
- The first request, `1e3327cd-715f-4aaa-a0c3-ee87cbaea03a`, completed successfully inside Lambda with `source_mode=organisation_sources`, five citations, and a 34,219.76 ms duration. The protected endpoint is an API Gateway HTTP API whose integration timeout is capped at 30 seconds, explaining the client-visible `Service Unavailable` even though Lambda later logged completion.
- The bounded retry, `69dfd28c-a14f-4632-9e5f-f3dc8a40aa7c`, failed after 6,908.22 ms in `_final_payload`. Its model result contained valid evidence citation numbers while declaring a non-`organisation_sources` source mode, triggering `ValueError: Only organisation-sourced answers may include citations.` The Lambda handler then returned the observed controlled generic failure.
- These are two distinct defects: a synchronous transport-duration mismatch and an uncaught final structured-output consistency error. The comparison remains failed until a reviewed remediation is approved and one bounded live retest passes.
- This diagnosis was read-only. No production code, AWS resource, Lambda/API configuration, Terraform state, Entra permission, consent, SharePoint permission, billing policy, IAM, routing, document, or protected AWS retrieval component changed.

## 2026-09-22 — Test-first narrow source-attribution recovery

- Bishal chose to retain the first request's 30-second HTTP API timeout as an honest, documented boundary rather than changing topology merely to eliminate every failure.
- Added a regression test that first reproduced the retry's exact semantic failure: retrieved citation numbers paired with a non-organisation source mode escaped as an uncaught `ValueError`.
- Changed only the final-response validation path. A source-mode/citation inconsistency after a real organisation search now receives the existing single, tool-disabled finalization attempt with explicit consistency instructions. A failed correction still raises `forced_finalization_failed`.
- Added a separate fail-closed test proving that an organisation attribution mismatch without an actual search is not retried. Existing invented-citation and unsupported no-search organisation-claim boundaries remain unchanged.
- Verification: **50 Python tests plus 6 subtests passed in 1.35 seconds**; `compileall` passed for `app/api`; `git diff --check` reported no patch errors.
- This fix is local only. No Lambda deployment, API Gateway/Lambda configuration change, Terraform action, permission/consent change, billing change, document change, or live retest occurred.

## 2026-09-25 — Root source-classification fix supersedes retry-only proposal

- Bishal correctly challenged the earlier bounded retry as an outer-layer safeguard rather than the root fix. The confirmed contract flaw was that the model selected both citation numbers and the global source label even though the application alone owns and validates the evidence boundary. Partial cross-source evidence could therefore contain a valid citation while using `organisation_not_found` for the missing side of the comparison.
- Replaced the undeployed source-label retry with deterministic application classification. After a real organisation search, one or more validated citation numbers produce `organisation_sources`; a completed search with no cited evidence produces `organisation_not_found`. The model still writes the answer and selects supporting evidence numbers, but it no longer has final authority over the organisation badge.
- Added a test-first partial AWS-plus-SharePoint case: AWS evidence is present, SharePoint is no-match, and the model proposes `organisation_not_found` with the AWS citation. The application now returns the partial answer as organisation-sourced with the valid citation and no extra Bedrock call.
- Added a test proving that a completed search without cited evidence is classified as `organisation_not_found`. The existing no-search organisation-claim test still fails closed, and invented or out-of-range citation numbers remain rejected.
- Verification: **51 Python tests plus 6 subtests passed in 2.72 seconds**; the API-only suite passed 22 tests; `compileall` passed for `app/api`; `git diff --check` reported no patch errors.
- This root fix is local only and supersedes the undeployed retry-only proposal above. No Lambda deployment, API Gateway/Lambda configuration change, Terraform action, permission/consent change, billing change, document change, or live retest occurred.

## 2026-09-25 — Reviewed production deployment and AWS regression

- Bishal approved the exact saved production plan after review. Terraform replaced only the local packaging trigger, rebuilt/read the archive, and updated the existing `askanydoc-api` Lambda in place. It did not change IAM, API Gateway, S3, ingestion, Aurora configuration/data, Entra, SharePoint, or billing resources.
- The Lambda update completed successfully at 2026-09-25 09:57:55 AEST with code SHA-256 `LcHPpnPfDjL7yM7yXKi68t2YqlSZaNLsHXI+/MbyR4A=`.
- The first AWS SQS regression request, `3397dcf3-51b6-476c-affe-a25fe2724a3a`, returned the controlled 503 after 43.38 client seconds. Its exact CloudWatch trace proves `DatabaseResumingException` while the zero-ACU Aurora writer resumed; Lambda duration was 40,095.76 ms. No speculative code change was made.
- After the database resumed, the single justified retry passed in 31.35 client seconds with `organisation_sources`, a grounded answer, and the expected `17-lambda-sqs-partial-batch-responses.pdf` page 5 citation.
- The Aurora first-request behavior is now `R-001` in `MODERNIZATION_RISK_AND_CHANGE_REGISTER.md`. The authenticated SharePoint General and explicit cross-source post-deployment checks remain pending until Adele's interactive Microsoft sign-in is completed.

## 2026-09-25 — Authenticated production proof of the root fix

- Adele signed in to the production CloudFront client as `AdeleV@y4m7.onmicrosoft.com`.
- A broad General semantic question completed as a safe no-match: request `8ea8b1dc-ea29-4359-9e18-95491a545581`, `organisation_not_found`, zero citations, 20.02 s Lambda duration. This is retained as query-sensitivity evidence.
- One targeted request then returned HTTP 401 before Lambda while the UI still showed Adele signed in. Browser diagnostics showed the expected tenant issuer, API audience, delegated scope, and token version. Reloading the page/session cleared the condition; no identity or permission setting was changed. The root is unproven and tracked as modernization risk `R-026`.
- The isolated targeted General retry passed: request `8b9d8629-9a67-464b-9b68-08ffc27d2f59`, `organisation_sources`, three citations to `microsoft-cloud-hybrid-architecture.pdf` pages 4, 1, and 2, 13.94 s Lambda duration, 6,325 input / 451 output tokens.
- The one explicit AWS-versus-SharePoint comparison returned `Service Unavailable` to the browser but completed successfully inside Lambda: request `f3fb33c0-d173-443d-bf20-6d448f7f2271`, 38.78 s, `organisation_sources`, five citations, 7,556 input / 552 output tokens. The deterministic source-classification defect did not recur; the known 30-second transport boundary remains separate and intentionally unfixed.
- This completes the bounded production proof requested for the root change. Observability and alert design are next; no additional production mutation is authorized.

## 2026-09-26 — Asynchronous answer contract approved and locally verified

- A fresh cold comparison, request `5fbe7886-113e-44f6-acba-fc702aa03972`, failed after 42.77 seconds with `DatabaseResumingException`. The immediate warmed repeat, request `67423134-94a0-4539-bb94-ed0a6e44cd1c`, completed correctly in 43.55 seconds with `organisation_sources` and five citations, while the browser again received `Service Unavailable`.
- This confirms two independent reliability boundaries: Aurora scale-to-zero resume latency and the API Gateway HTTP API's fixed 30-second integration ceiling. It is not an Adele permission failure and does not require changing SharePoint consent or site access.
- Bishal approved the official AWS asynchronous request-reply approach: authenticated job creation/status routes, a KMS-encrypted SQS queue and DLQ, a dedicated bounded-concurrency worker, and a KMS-encrypted owner-bound DynamoDB result with one-hour application-enforced expiry and TTL cleanup. The existing answer/retrieval core, S3 ingestion, Titan embeddings, Aurora data, pgvector schema/data, OBO flow, and SharePoint permissions remain unchanged.
- The worker alone receives a 45-second bounded Aurora resume-retry budget. The current synchronous Lambda keeps the existing 14-second default. The frontend polls for up to three minutes and tolerates temporary status `429`/`5xx` responses.
- Local verification passed: 11 focused asynchronous/retry tests, 55 complete API/SharePoint tests, frontend lint, frontend production build, Terraform formatting/validation, and `git diff --check`. The existing approximately 590 kB bundle warning remains.
- The final saved Terraform plan is `23 to add, 3 to change, 2 to destroy`. The destroys are the replaced local packaging trigger and the obsolete hashed frontend JavaScript object; no database, document, queue data, SharePoint permission, Entra consent, ingestion resource, S3 document object, Aurora resource, or pgvector data is deleted or replaced.
- The saved plan is not yet applied. Fresh explicit approval is still required immediately before the production apply. Alerts remain the next package after the client-visible comparison proof.

## 2026-09-26 — First asynchronous apply stopped at account concurrency guardrail

- The exact approved plan partially applied, then AWS rejected `reserved_concurrent_executions = 2` on the new worker because this account must retain at least 10 unreserved Lambda executions. AWS returned `InvalidParameterValueException`; Terraform exited nonzero and did not create the SQS event source mapping.
- Read-only verification found both new Lambdas active and successful with no reserved concurrency. The API routes, frontend, encrypted queues, DynamoDB table, KMS key, IAM, and log groups were created; the queue had no consumer yet, so the asynchronous path was not declared operational.
- AWS's current Lambda documentation supports SQS event-source maximum concurrency independently of function reserved concurrency, with a minimum value of 2. The narrow recovery changes the control location: remove function reserved concurrency and set the SQS event source mapping `maximum_concurrency = 2`. This preserves the intended worker cap without consuming the account's protected unreserved pool.
- A refreshed Terraform plan and fresh approval are required before applying this recovery. No concurrency quota increase, database change, permission change, or rollback was attempted.

## 2026-09-27 — Recovery deployed; transport passed and cold-answer gate failed

- Bishal approved the narrow recovery plan. Terraform applied exactly `2 added, 0 changed, 1 destroyed`: it replaced the newly tainted worker without function reserved concurrency and added the SQS event source mapping with maximum concurrency two.
- Read-only verification found both Lambdas active and successful, the worker at 180 seconds/512 MB with no reserved concurrency, an enabled batch-size-one event source mapping, KMS-encrypted SQS/DLQ and DynamoDB resources, and a post-apply Terraform plan reporting no changes.
- Bishal approved one production comparison through Adele's authenticated session. Job `8710fbc1-c644-44bd-9d0d-b40b966e9b46` was created in 235.76 ms and the browser polled beyond 30 seconds for about 90 seconds, proving the asynchronous transport removed the former client-wait boundary.
- Worker request `73e1a631-0248-5a48-9a92-c5037e1e54a2` ended after 88.40356 seconds with `DatabaseResumingException`. The job reached a controlled `failed` state and the browser displayed the request ID, but no answer or citations were returned.
- Aurora capacity moved from 0 to 0.5 ACU during the request. The worker's current 45-second per-call resume budget was insufficient for this cold start; this is an R-001 reliability failure, not a SharePoint permission or asynchronous-transport failure.
- The source queue and DLQ were empty afterward, showing controlled terminal handling rather than a stranded or poison message.
- Bishal's standing instruction now requires explicit permission before every future change. No further code, infrastructure, production test, or documentation change is authorized by this record.

## 2026-09-28 — Bounded cross-invocation Aurora recovery verified locally

- Bishal explicitly approved the researched recommendation to preserve the working evidence-combination architecture and fix only the remaining `DatabaseResumingException` boundary. No separate answer merger, Step Functions workflow, persistent SharePoint evidence store, database configuration change, or new service was added.
- Added tests first. The original worker failed the new contract because it had no SQS retry client, no failed-item response, and treated every answer exception as terminal.
- The worker now claims and records an attempt number, retries only `DatabaseResumingException`, returns only that message through `ReportBatchItemFailures`, releases its DynamoDB lease to `pending`, and changes the message visibility for a bounded 15-second then 30-second delay. Three total attempts are allowed; unrelated failures remain terminal. Completed and failed jobs remove stale retry metadata.
- Terraform source reduces the worker's in-process database wait from 45 to 15 seconds, adds the queue URL and attempt/delay settings, grants only `sqs:ChangeMessageVisibility` on the answer queue, enables partial-batch reporting, and changes DLQ `maxReceiveCount` from 2 to AWS's currently recommended minimum of 5. The application-level three-attempt cap remains authoritative for this specific recovery.
- Verification passed: 5 focused worker tests, 35 complete API tests, 22 complete SharePoint tests, Python compilation, Terraform format check, and Terraform validation. The temporary Windows test dependencies live only under ignored `tmp/windows-test-deps` because the historical virtual environments point to a removed Python installation.
- A read-only targeted Terraform preview reported `1 to add, 5 to change, 1 to destroy`; the add/destroy pair is the local packaging-trigger replacement. Cloud changes are in-place updates to the encrypted answer queue, worker IAM policy, event-source mapping, job API Lambda, and worker Lambda. The job API code is unchanged but shares the rebuilt ZIP. No Aurora configuration/data, AWS ingestion, S3 document, pgvector, SharePoint permission, Entra, API Gateway, CloudFront, frontend, or billing resource is changed.
- The preview was not saved or applied. No production test ran. Fresh explicit approval remains required before a saved plan/apply, followed by one varied cold cross-source question and inspection of answer, citations, attempts, latency, tokens, and cost.

## 2026-09-28 — Bounded Aurora recovery deployed; cold cross-source answer passed

- Bishal explicitly approved the exact targeted deployment and one varied production comparison. A fresh saved Terraform plan matched the reviewed scope: one local packaging-trigger replacement and five in-place cloud updates to the answer queue, worker IAM policy, SQS event-source mapping, shared-package job API Lambda, and worker Lambda.
- Terraform applied successfully. Both Lambdas are active with code SHA-256 `31EBxNTHee98Nyhb+Ikv/6pFMvWf4jplV12uYwAeti4=`. The worker exposes the reviewed 15-second in-process wait, three-attempt cap, and 15-second base retry delay; the mapping reports `ReportBatchItemFailures`; queue visibility remains 1,080 seconds; DLQ `maxReceiveCount` is five; and IAM adds only queue-scoped `sqs:ChangeMessageVisibility`.
- No Aurora configuration/data, ingestion, S3 document, pgvector, SharePoint permission, Entra, API Gateway, CloudFront, frontend, or billing resource changed.
- The varied question compared disaster-recovery guidance for AWS workloads with Microsoft hybrid-cloud architecture without naming the storage locations. Job `274b655d-f13d-4219-83b2-96f60d8ed3b9`, worker request `c0fc002f-3934-58f2-a30b-631cf07b4976`, returned a browser-visible `organisation_sources` answer with five citations to `13-disaster-recovery-workloads-on-aws.pdf` and three citations to `microsoft-cloud-hybrid-architecture.pdf`.
- CloudWatch capacity data proves Aurora was at 0 ACU before the request and resumed during the test. The job completed on attempt one in 47 wall-clock seconds. The worker ran for 44.43388 seconds, billed 47.021 seconds, used at most 170 MB, and recorded 7,723 input / 741 output tokens. Because resume succeeded within the first attempt, the slower 15/30-second cross-invocation branch was not needed live; its success and terminal-cap behavior remain covered by the five focused worker tests.
- At the current published AU Claude Haiku 4.5 rates, the answer tokens cost about USD $0.01257; Sydney Lambda worker compute was about $0.00039. The measured major subtotal is therefore about $0.013, before negligible embedding, SQS, DynamoDB, KMS, logging, Graph, and short Aurora-capacity charges.
- The answer gate passed. Work now stops for Bishal's review. Observability and alerts are the next planned package, but require a separate scope, exact plan, cost/rollback review, and fresh explicit approval.

## 2026-09-28 — Multi-tool planning regression diagnosed and fixed locally

- A clean AWS-only production question passed with the expected SQS partial-batch-response citations, and a clean targeted SharePoint-only question passed with citations to `microsoft-cloud-hybrid-architecture.pdf`. Two later combined jobs failed quickly: requests `ec4479fb-7749-5275-8800-1ac89fd09c10` and `c57f6851-eee4-5e64-bf85-0b62062d2001` logged `planned_source_tool_missing`.
- A direct, read-only Bedrock planning diagnostic reproduced the model contract: one valid `tool_use` response contained both `search_aws_documents` and `search_sharepoint`. The recent controller incorrectly assumed a forced tool must be the only returned tool even though both tools were still exposed.
- The local controller now exposes only authorized planned tools, accepts one or both planned tool calls in the first combined response, executes each source at most once, and makes one bounded forced call only for a missing planned source. Unplanned tools, invalid responses, and no-progress loops fail closed. Final synthesis remains tool-disabled and citations remain application-validated.
- Test-first verification passed: the production-shaped two-tool regression, single-source tool exposure, duplicate suppression, authorization-limited routing, and missing-source fallback; the complete result is 41 API tests and 22 SharePoint tests. Python compilation, Terraform validation, `git diff --check`, and a real Bedrock planning-only contract check also passed.
- Saved plan `infra/adaptive-source-controller.tfplan` has SHA-256 `98D85DF78BA0040C2B3E558728C5E9FBF880E42F5DB9CC7E1CD6799BB07AD3B8`. It reports two local packaging-trigger replacements and three in-place Lambda code updates only. No IAM, API Gateway, queues, tables, database, ingestion, stored document, pgvector, SharePoint/Entra permission, CloudFront, frontend, or data resource changes are present.
- This fix is local only. No Terraform apply or production retest has occurred. A fresh explicit deployment approval is required, followed by isolated AWS-only, SharePoint-only, and combined UI tests before alerts.

## 2026-09-28 — Adaptive controller deployed; query-relevance gate remains

- Bishal explicitly approved the hash-verified saved plan after reviewing the active-request retry risk. Terraform applied exactly `2 added, 3 changed, 2 destroyed`: the add/destroy pairs replaced two local dependency-packaging triggers and the three changes updated `askanydoc-api`, `askanydoc-answer-job-api`, and `askanydoc-answer-job-worker` in place.
- AWS reports all three Lambdas `Active` with `LastUpdateStatus=Successful`. Code SHA-256 is `gS5PgQjv/3gZTwoU6F83h0H1+8U2sCxCLPembsZdH1Q=` for `askanydoc-api` and `HsKOeHYUNket7A9h8pYYLaT4qtLdahDDJdI0+nkAfo4=` for both answer-job Lambdas. A post-apply Terraform plan reported no changes.
- AWS-only UI test `How should failed messages be handled in a Lambda queue batch?` passed: job `1c20c069-427b-4b3e-aa84-2a16c5251ff3`, worker request `83dfaccf-6077-5bb9-8702-cffc8ddd94b1`, five evidence items, three citations, `organisation_sources`, 41.39-second worker duration.
- SharePoint-only UI test `How does the hybrid cloud architecture connect on-premises systems?` passed: job `1c2e9185-b3dd-4489-aa7f-632fb2cb952d`, worker request `a1ce4962-832e-51e2-890b-2a516d35c82b`, three evidence items, three citations, `organisation_sources`, 21.90-second worker duration.
- Three comparison formulations no longer raised `planned_source_tool_missing`. Structured logs prove both sources were planned. The first two completed in one planning call; the controlled final test completed in two bounded planning calls. Every comparison returned five AWS evidence items but zero SharePoint evidence items, so the UI could not produce a grounded two-source comparison.
- This separates the defects: the adaptive controller fixed multi-tool execution, and isolated SharePoint permission/retrieval remains healthy; the remaining issue is the model-generated SharePoint query for a combined request. No new fix was attempted. Alerts remain paused until a separately approved per-source query-decomposition change passes locally and in the UI.

## 2026-09-28 — Structured per-source query contract verified locally; apply pending

- Bishal approved local implementation and testing of the narrow query-decomposition recommendation. The retrieval adapters, AWS ingestion/retrieval path, SharePoint OBO/Graph permissions, evidence contract, citation validation, queues, stores, and infrastructure topology remain unchanged.
- The planned-source path now uses one Bedrock structured-output call with an application-owned JSON schema. It requires exactly one bounded query field for every authorized planned source, rejects missing/extra/empty/oversized fields, executes each source once, and then uses the existing tool-disabled grounded synthesis. Deterministic source cues keep the two clauses separated; raw query text is not added to structured production logs.
- The complete local verification passed: 43 API tests, 23 SharePoint tests, Python compilation, Terraform validation, and `git diff --check`. The tests cover one query per source, invalid-plan fail-closed behavior, authorization-limited routing, one execution per source, isolated AWS and SharePoint routing, and the existing no-match/safety/retrieval regressions.
- One read-only real Bedrock planning check for a varied two-clause comparison returned exactly `aws: disaster recovery strategies protect workloads` and `sharepoint: hybrid cloud connect on-premises systems`, using 386 input and 32 output tokens. This corrected the earlier prompt-only experiment, which had produced duplicate/cross-contaminated tool calls and was not deployed.
- Saved plan `infra/source-query-decomposition.tfplan` has SHA-256 `C7755EDB6C8DDC06DDF79ECD8A9D4604F43D2879C4657EEAD635FB21DE9A9AF4`. It contains only two local packaging-trigger replacements and in-place code-package updates to `askanydoc-api`, `askanydoc-answer-job-api`, and `askanydoc-answer-job-worker`. It contains no IAM, API Gateway, queue, table, database, ingestion, document, pgvector, SharePoint/Entra permission, CloudFront, frontend, or data change.
- The plan is not applied and no production UI result is claimed. Fresh explicit approval is required immediately before apply. Afterward the required UI gate is one AWS-only question, one SharePoint-only question, and two varied combined questions with validated citations from both sources; alerts remain paused until that evidence is recorded.

## 2026-09-28 — Structured query contract deployed; supported UI gate passed

- Bishal explicitly approved the exact saved plan after reviewing its hash, blast radius, active-request retry risk, cost, rollback, and verification steps. The SHA-256 was rechecked immediately before apply as `C7755EDB6C8DDC06DDF79ECD8A9D4604F43D2879C4657EEAD635FB21DE9A9AF4`.
- Terraform applied exactly `2 added, 3 changed, 2 destroyed`. The add/destroy pairs replaced only the two local dependency-packaging triggers; the three changes updated the code packages of `askanydoc-api`, `askanydoc-answer-job-api`, and `askanydoc-answer-job-worker` in place. No IAM, API Gateway, queue, table, database, ingestion, document, pgvector, SharePoint/Entra permission, CloudFront, frontend, or data resource changed. A post-apply plan reported no changes.
- All three Lambdas are `Active` with `LastUpdateStatus=Successful`. Code SHA-256 is `q2Eznl692p9TmaDpJIJP0hNPTYnKUfc77MqWDtoZ7eY=` for `askanydoc-api` and `MnpTOLfC26Ar53bJElfydDog4jQAdFgGCvApi/fxi1A=` for both answer-job Lambdas.
- AWS-only UI pass: `Why should an SQS batch report only failed messages?` returned three citations to `17-lambda-sqs-partial-batch-responses.pdf`; job `95052ec2-924d-4f58-a1e1-88098e54f2f8`, request `4c9fe9b1-5aeb-57b5-b559-8a82ae30c519`, five evidence items, 29.51-second worker duration.
- SharePoint-only UI pass: `How does hybrid cloud connect on-premises systems?` returned three citations to `microsoft-cloud-hybrid-architecture.pdf`; job `e37db34e-9e9e-479b-83e9-25bf8b6c93dd`, request `19db330b-f6c6-5646-8757-503803e884ea`, three evidence items, 13.10-second worker duration.
- First combined UI pass: the disaster-recovery versus hybrid-cloud question returned the label `AWS document library + SharePoint`, five citations to `13-disaster-recovery-workloads-on-aws.pdf`, three citations to `microsoft-cloud-hybrid-architecture.pdf`, and a grounded comparison; job `40e02a78-6ef2-4d8a-b658-c2e370263fdd`, request `0d2cabed-9aab-5d81-9de5-c8de6ffec7b1`, eight evidence items, 13.03-second worker duration.
- Second combined UI pass: the SQS failed-message versus hybrid-cloud on-premises question returned the same dual-source label, three citations to the SQS PDF and three citations to the hybrid-cloud PDF; job `e7c82aac-8d48-407f-a364-25f2ca6fe8c4`, request `37ab65a4-2cd0-5df8-911d-0697daf2911e`, eight evidence items, 12.01-second worker duration. The answer correctly stated that the retrieved documents did not directly compare their reliability goals instead of inventing that relationship.
- One intentionally retained no-match exposed a separate corpus-coverage gap. The planner produced clean independent queries for SQS and `Power Automate approval flow creation how to`, but the combined request found AWS evidence only. The same approval question in a clean SharePoint-only session returned `organisation_not_found`, zero citations, and zero evidence (job `d388e615-fe71-46a4-a56b-f959b73f23ab`, request `3e015b80-6d4d-576e-8104-38b398f7cd5e`). This is not a permission, decomposition, or multi-source execution failure; it is recorded as an intended-corpus availability/coverage issue and was not hidden or patched with general knowledge.
- The supported-source acceptance gate is complete. Work stops for Bishal's review before alerts; alert design remains a separate approval-controlled package.

## 2026-09-28 — Narrow responsive sidebar refinement deployed

- Bishal approved the exact saved frontend plan after its SHA-256 was explained and rechecked as `09D351C89E8EB1DA7F815038AAF90A442B6EF8E1C36DD964C0F1AB7962B6D1A6` immediately before apply.
- The sidebar now enters a dedicated compact desktop state below 200 pixels. New chat uses smaller single-line typography, and the account card, name, status, avatar, and Sign out control scale together without wrapping or overflowing. Wider, fully collapsed, and mobile layouts remain separate states.
- Frontend lint and the production build passed. A browser layout check at 160 pixels, 240 pixels, and fully collapsed width found every tested control inside the sidebar with fitting content; the existing approximately 597 kB JavaScript bundle-size warning remains non-blocking.
- Terraform applied exactly `2 added, 1 changed, 2 destroyed`: two new content-hashed frontend assets replaced their obsolete hashed versions, and `index.html` updated in place. No Lambda, API, IAM, queue, table, database, ingestion, document, pgvector, SharePoint/Entra permission, CloudFront distribution, or billing resource changed.
- A post-apply Terraform plan reported no changes. The live signed-in client exposes New chat and Sign out as single controls at the 160-pixel minimum and reports the resize separator at 160.

## 2026-09-28 — Continuous-session source regression recorded

- Bishal requested a production sequence without refreshing because normal users will continue within one browser session. The existing signed-in Bish All chat was deliberately preserved, including the earlier comparison message.
- `How should Lambda handle failed messages in an SQS batch?` passed in that same session with the UI label `Source: AWS document library`. Worker request `edeea481-10ce-5b7d-b7b1-c7b51611ad14` routed only AWS, retrieved five evidence items, returned four citations, and recorded two history messages.
- `How does Microsoft hybrid cloud connect on-premises systems?` then passed without refresh with the UI label `Source: SharePoint`. Worker request `94376aae-a9cf-5d0b-b481-099aaf37075c` routed only SharePoint, retrieved three evidence items, returned three citations, and recorded four history messages.
- Repeating `Compare AWS disaster-recovery strategies with SharePoint guidance for protecting highly regulated sites.` as the third continuous turn failed the grounded-source gate. Worker request `a51b3508-16b8-52ca-925b-563c11a9e4a3` correctly routed both sources and retrieved five AWS plus one SharePoint evidence item, but final synthesis returned zero citation numbers with six history messages. The application correctly derived `organisation_not_found` and exposed no citations rather than claiming unsupported grounding.
- The same question had passed in a clean session immediately before this sequence with six validated citations. The new evidence therefore isolates history-sensitive final synthesis/query quality; it is not a Bish All group membership, SharePoint permission, routing, or source-adapter failure. No code, permission, or infrastructure change was made. The required remediation is tracked under R-023 and needs a separately approved design and implementation.

## 2026-09-28 — Bounded conversation grounding verified locally; apply pending

- The root cause was confirmed in the shared answer orchestrator: the frontend's bounded transcript was passed verbatim into both source-query planning and final grounded synthesis. A standalone combined question could therefore be changed by unrelated earlier turns even after both source adapters returned valid evidence.
- The narrow local change keeps complete questions independent of earlier chat, supplies only the latest user/assistant exchange to explicit or very short follow-ups, and tells final synthesis that conversation history is context only—not organisation evidence. Retrieval adapters, permissions, evidence validation, storage, queues, databases, API routes, and frontend history remain unchanged.
- Tests were added before implementation and reproduced the old behavior. The final suite passed 48 API tests and 23 SharePoint tests, including complete-question isolation, bounded referential follow-ups, short follow-ups, internal-pronoun handling, and the existing malicious-document/no-match/retrieval regressions. Python compilation, Terraform validation, and `git diff --check` passed.
- The current source was compared with both deployed packaging directories. Their only delta is the bounded-history helper, its regular-expression classifier, the two-message limit, and the explicit history-is-not-evidence instruction.
- Saved plan `infra/conversation-grounding.tfplan` has SHA-256 `2B0F2918E102FBB98D17057FC6D308CB7DDC166B423B648ACBF88C74B3335B7A`. It proposes two local packaging-trigger replacements and in-place code-package updates to `askanydoc-api`, `askanydoc-answer-job-api`, and `askanydoc-answer-job-worker`. The archive data sources are read during packaging. No IAM, API Gateway, queue, table, database, ingestion, stored document, pgvector, SharePoint/Entra permission, CloudFront, frontend, or data resource change is present.
- No apply or production pass is claimed. Fresh explicit approval is required immediately before applying this exact plan. The post-apply gate is a continuous no-refresh AWS-only, SharePoint-only, and combined sequence plus short and referential follow-ups, with citations and correlated logs inspected.

## 2026-09-28 — Bounded conversation grounding deployed; explicit-source gate passed

- Bishal approved the exact saved plan after reviewing the distinction between the permanent grounding boundary and the future long-conversation memory design. Its SHA-256 was rechecked immediately before apply as `2B0F2918E102FBB98D17057FC6D308CB7DDC166B423B648ACBF88C74B3335B7A`.
- Terraform applied exactly `2 added, 3 changed, 2 destroyed`: the add/destroy pairs replaced only local dependency-packaging triggers, and the three updates changed the code packages of `askanydoc-api`, `askanydoc-answer-job-api`, and `askanydoc-answer-job-worker`. No IAM, API, queue, table, database, ingestion, document, pgvector, SharePoint/Entra permission, CloudFront, frontend, or data resource changed. The post-apply plan reported no changes.
- AWS reports all three Lambdas `Active` with `LastUpdateStatus=Successful`. Code SHA-256 is `/pNJTHSPldTpzIUXJZYsx8ghvdeLeG4rLpqhEGG3y9E=` for `askanydoc-api` and `2SePvjmKFkerJ4K/2GGKZI/d4td+Nxq5f/uUNF4/SPc=` for both answer-job Lambdas.
- The controlled AWS question passed in the existing unrefreshed session with ten history messages: job `c8b9b578-d6e2-4a76-938e-733d2afecfb5`, request `e13b2637-0acd-591d-b11a-4503060e7d36`, five validated citations to `17-lambda-sqs-partial-batch-responses.pdf`.
- The controlled SharePoint question passed in the same session at the 12-message client limit: job `812932db-2380-4fdd-885c-7b2ebd349fac`, request `f7444b79-188b-5c17-91bd-284d147446bf`, three validated citations to `microsoft-365-information-protection-compliance.pdf`.
- The previously failing explicit comparison then passed without a refresh and with 12 history messages: job `47771fa8-44ab-433e-84c9-1d3f2a53c444`, request `f2f28289-1429-5c25-b91b-e1bd190fb80e`, six validated citations from both `13-disaster-recovery-workloads-on-aws.pdf` and `sharepoint-sites-highly-regulated-data.pdf`. The UI displayed `Sources: AWS document library + SharePoint`.
- A short AWS follow-up also retained its context and returned five organisation citations. A deeper SharePoint referential follow-up returned a controlled no-source result. Bishal explicitly deferred broader follow-up logic. A varied question that did not name AWS was answered as general knowledge; Bishal likewise deferred implicit source selection and approved explicit AWS/SharePoint wording for the current gate.
- The production gate for explicit AWS-only, explicit SharePoint-only, and explicit combined retrieval is complete. Persistent employee chat storage, older-turn summarization, self-contained follow-up rewriting, and implicit source inference remain separately scoped future work; the deployed history-is-not-evidence boundary remains the foundation for that work.

## 2026-09-28 — Answer-details and narrow account layout refinement deployed

- The frontend now keeps `Sources & answer details` and `Tokens` as two separate collapsed disclosures. Input and output token counts appear only after opening `Tokens`; the source disclosure retains citations and the AWS semantic score when available.
- Answer and disclosure typography was reduced slightly to improve information density without changing message content, source labels, retrieval, or answer behavior. The account card now places Sign out on its own centered row so the control remains contained at the 160-pixel desktop sidebar minimum; mobile and fully collapsed states keep their dedicated layouts.
- Frontend lint and the production build passed. The existing approximately 597 kB JavaScript bundle-size warning remains a non-blocking performance follow-up. Terraform validation passed; the unrelated local `sharepoint_auth.auto.tfvars` format warning was intentionally left untouched.
- Bishal approved saved plan `infra/frontend-answer-details.tfplan`, whose SHA-256 was rechecked immediately before apply as `661C008E968DD923F6DFE447BB0B26A55F8D5D3397398F8F2D8A29EB3ADC30EE`.
- Terraform applied exactly `2 added, 1 changed, 2 destroyed`: two new content-hashed frontend assets replaced their obsolete hashed versions and `index.html` updated in place. No Lambda, API, IAM, queue, table, database, ingestion, document, pgvector, SharePoint/Entra permission, CloudFront distribution, or billing resource changed. A post-apply plan reported no changes.
- Live verification at the 160-pixel sidebar minimum showed New chat and Sign out fully contained. A minimal signed-in `Hi` test rendered the smaller answer card, separate collapsed source and token disclosures, and an expanded Tokens view containing `Input: 1581` and `Output: 71`.

## 2026-10-02 - Approved planner/synthesis hardening deployed and live-tested

- Approval: Bishal requested an efficient safe fix, approved the proposed application patch and code-package deployment with `proceed and test`, then explicitly requested questions using both libraries. No AWS retrieval/ingestion, permissions, provider, data, database settings or frontend changes were approved or made.
- Added explicit planner search/decline disposition. Decline returns application-owned safe wording with no retrieval/citations. Search still rejects empty, extra, malformed or oversized fields. Stop reasons are checked; truncation receives one bounded retry (up to 4096 tokens) with combined usage accounting. Refusal/filtering is handled without parsing unsafe/non-schema output. Comparison instructions allow supported synthesis and preserve citations for supported parts when others lack evidence.
- Local result: 52 API tests and 23 SharePoint tests passed; Git diff --check passed. Direct live-model planning reproduced the original empty-query failure before the patch, then explicit decline after it.
- Intermediate live gates honestly retained: first patch safely declined the two adversarial attempts (d0ba971e-0f5f-5294-ad77-f42730063b4d, 8fc6e1b5-ff83-5e58-913c-828cc0ffdb55), but comparison b6028566-de9d-5d28-8a1d-e65fe10fc825 had zero SharePoint evidence and dropped AWS citations. Refined core-topic fallback/partial-evidence wording. Next comparison 58a652db-d6f2-5ad3-b179-31e2967f6a5e passed with eight citations, follow-up 2f7e4503-7b00-56d1-b041-263a3bb7d765 passed, and partial evidence a511dfc4-708b-5643-8cf0-bcfd3044eaee passed. Legitimate unusual-policy question 5e961fe8-713d-51a6-968f-7cd131d49d0b falsely declined; clarified that an implausible premise is not a prohibited action, then directly verified the model returns a search plan.
- A transient pinned-dependency install failure interrupted the third rebuild. Apply was stopped; both previously deployed packages remained Active/Successful with prior hashes. Restored local builds from saved pre-patch rollback packages and overlaid the approved orchestrator. Byte comparison confirms that only assistant_orchestrator.py differs from the pre-patch packages, with all pinned runtime dependencies and protected retrieval code unchanged. Temporary offline packaging helper is ignored under tmp; tracked Terraform/provisioners were not changed. A future build should explicitly fail immediately on pip failure; this build-hardening follow-up is not claimed implemented.
- Saved plans applied within the same approval scope: initial F9D0647ADE40DF98FB941380C69CE009FE2466AB72337C0F18D14C855ED6512B; comparison refinement FB439449167AF89FF7D3BF18AEC4EA95BF32182F71CF25FCC2479FCD1CBF15A6; interrupted BC6682B21D9025B53ABA94087B801AFCF72D3AF46C84FDE1E4E52D49D9C340C7; final recovery 7F8A9EC790F63375E34059BBE3BE5F596DE474C25AD8D135F80B32A04355E89D. Every review showed cloud changes limited to Lambda source_code_hash/last_modified; local dependency-build trigger replacements only. Final recovery apply: one added, three changed, one destroyed (the add/destroy pair is local null_resource).
- Final worker/job-API code SHA-256 qbElBsCo5kE4tO/nNY+D7Hc0oQBZDGbgolmzsNdHU18=; legacy API KxiRPRYxr0K2EpYmLvYm4jktSbwPS44TsAncGi2HASA=. Final worker and legacy API are Active/Successful; post-apply plan reports no changes. Rollback ZIPs remain ignored under tmp/pre-safe-decline-api.zip and tmp/pre-safe-decline-jobs.zip.
- Final-version live requests (all in the same 12-message browser-history session): c8cc4051-325c-5ca1-b074-236870367eec no-match (real search, zero citations); d9c01a32-3239-5808-9342-790b70bd9a45 safe decline (no source execution, zero citations); 40c52022-080b-55e9-8e8d-431b4aba57a4 arithmetic408; 8fa8ad10-5d78-5121-85d0-ce291fa1438c AWS SQS four citations; dc3af604-f554-5350-aca0-953db7be0a18 DR/hybrid comparison seven citations (four AWS/three SharePoint) and 14.10s worker; 80975b31-c1a7-571c-b71c-380882b724ce SQS/hybrid seven citations and 14.82s worker; 2052d127-6ec2-5cbc-b2de-b21e2dff2231 SharePoint-only response passes in UI. No generic answer failure appeared on these final-version checks.
- These are bounded synthetic regression checks, not exhaustive evaluation or fresh denied-user testing. Permission contracts remain covered by the 23-test SharePoint suite and unchanged provider/IAM code. Broader golden-set quality, implicit routing, model safety robustness and production readiness remain open. Aurora zero-ACU wake-up latency remains the existing intentional cost trade-off.

### Additional approved security test evidence

Bishal requested vulnerability/prompt-injection checks after the final deployment. Three unauthenticated API probes returned401. Five UI probes covered admin/permission spoofing, secret disclosure, quoted system-role attack, HTML rendering and forged tool/citation evidence. Two direct live-model probes inserted malicious instructions into synthetic evidence without changing a stored document. No tested attack achieved a bypass, exposed credentials, accepted invented evidence or executed HTML. Benign quoted-attack summarisation and HTML echo were refused: containment passed but over-refusal remains a product-quality issue. Full matrix records the distinction and test boundaries. No additional code/cloud mutation occurred.


### 2026-10-04 05:25–05:28 UTC — Fresh source regressions and extensible-source direction

Bishal requested a permanent post-change gate covering AWS, SharePoint, combined answers and future connectors. Tests ran visibly in AskAnyDoc as Bish All, each from New chat (worker history_messages=0); no code, configuration, source content or permissions changed during these tests.

- AWS: “According to the AWS document library, how should Lambda handle failed messages in an SQS batch?” Passed: partial batch response answer, Source AWS document library, five citations to 17-lambda-sqs-partial-batch-responses.pdf pages 5/5/7/8/7; AWS similarity 0.6445. Job 9ec9d186-14d5-41ed-a090-76001b56a3ac; worker request 5ba07812-892e-56c1-90b2-1b296cade2ab; 32.84267 seconds plus 2.60089-second cold init. Async result delivered to browser; no timeout or error shown.
- SharePoint: “According to the Microsoft cloud hybrid architecture document in SharePoint, how does hybrid cloud connect on-premises systems with Microsoft cloud services?” Passed: document-grounded connectivity/identity/application summary, Source SharePoint, three citations to microsoft-cloud-hybrid-architecture.pdf pages 2/3/5 on General site. Job 620f94cf-e298-4130-a0a7-506b04123f70; request 5c5e6d35-2135-520f-ab09-0e0ec4ea75a9; 20.25424 seconds plus 2.58257-second init. Planner returned six evidence items using the bounded SharePoint fallback; three selected citations. The document contains historical platform names; this is a corpus answer, not a fresh Microsoft deployment recommendation.
- Combined: “Using both the AWS document library and SharePoint, compare how AWS disaster recovery strategies protect workloads with how Microsoft hybrid cloud architecture connects on-premises systems. Cite evidence from both sources and distinguish the two purposes.” Passed: one comparison distinguishes disaster recovery from hybrid connectivity. Expanded sources show five AWS citations to 13-disaster-recovery-workloads-on-aws.pdf pages 16/18/19/35/10 and three SharePoint citations to the hybrid PDF pages 1/2/3. Source label AWS document library + SharePoint, similarity 0.8625. Job 08551202-8c2d-4fd2-bd3e-e44f9dfbca34; request 065ec55c-6f74-5f31-845b-a66789613897; 18.37110 seconds. Plan evidence counts AWS 5, SharePoint 6; final citations 8. Browser left on this result with source details expanded.

The earlier Salesforce deployed tests remain the CRM regression evidence: eight bounded standard types, original Case route, company/contact relationship, missing fields and no-match. These fresh document tests pass after that Salesforce deployment. They do not replace two-user authorization, full claim-by-claim evaluation, reliability, refresh/revoke or existing SharePoint attribution gates. Duplicate AWS document/page citations represent multiple chunks and are a presentation follow-up; no unrelated deduplication patch was applied.

Architectural direction recorded in SHARED_SOURCE_ANSWER_DIRECTION.md: one controller, request-authorized adapter registry, bounded source-specific plans, common evidence/citations and honest partial failures, future connectors without duplicating the application. Three-source AWS+SharePoint+Salesforce synthesis is not deployed. Snowflake and HubSpot are examples, not verified connected capabilities. Shared controller changes require exact protected-path impact and Bishal's immediate explicit approval before mutation. Read the complete SharePoint source of truth before further architecture work; this session did so. Primary Bedrock tool-use, MCP 2025-11-25 tools, Graph search and Salesforce best-practice references were rechecked on 4 October 2026 and recorded in the direction document.

Commit review: git diff --check passes. Existing 26 Salesforce tests and frontend lint/build passed after the last code change; this checkpoint adds documentation only. No shared AWS/SharePoint code changed. Source remains unstaged and uncommitted for Bishal; proposed message: Extend bounded Salesforce CRM reads and record shared-source regression gates. Direct-deployment Terraform drift reconciliation and ignored local rollback archives remain documented open operational items. Documentation rollback removes the new direction document/brief paragraph after review; retain this append-only evidence. Applied code rollback remains the exact preceding ledger procedure.


### 2026-10-04 — Approved three-source activation deployed and tested

Bishal approved exact shared-path impact; targeted CLI deployment added mixed-question worker dispatch, owner-bound Salesforce evidence route, one worker URL setting and frontend jobs routing. Existing AWS/SharePoint retrieval code, IAM, data and grants preserved. Final worker hNjM2dh6IPI78hCGNXlcjSBQsULPCoXbDo0acKCEAZ0=; dedicated Salesforce IvcDopA7b92kp/QyUJyJ564PUYEj3xAT5/LSatXc100=. Visible Salesforce-only, AWS-only, SharePoint-only, AWS+SharePoint, all-three and missing-CRM mixed tests passed. Final all-three job90592259-7800-47ec-9965-866cf2d2c7b3: correct New/High VPNCase, eleven evidence items, eight citations across all three, bounded CRM note;21.78217s. Missing-CRM jobbf4905ea-7530-4a0e-8a04-f4ae9e618c7a disclosed no_match and cited only AWS. 65API/26Salesforce tests, frontend build/lint and Terraform validate passed; exact actions/rollback and quality limitations in SALESFORCE_MCP_INTEGRATION_PLAN.md. Existing step-by-step guide updated at SALESFORCE_MCP_ONE_PASS_INTEGRATION.md Stage6B. No duplicate recipe or commit. Terraform drift reconciliation, two-user permissions, grant refresh/revocation/concurrency, MCP reliability and SharePoint relevance/attribution gates remain open. Future connectors require verified thin adapters and tests. Approval consumed; no new deployment or access expansion authorized.

### 2026-10-04 — Commit and documentation state reconciliation

Bishal committed the three-source slice and prior test evidence as e303b98 at 17:20 Brisbane. Repository clean before this documentation-only update. Option B graph_search remains selected; no SharePoint/AWS runtime, data, access or provider changed. Current source of truth, test matrix, architecture/ADR, risk gates, guides and trackers reconciled. Exact full commit/read-back and doc rollback recorded in SALESFORCE_MCP_INTEGRATION_PLAN.md. Existing functional tests are not a fresh cross-user/production reliability proof. Documentation changes remain uncommitted for Bishal; push unverified.
