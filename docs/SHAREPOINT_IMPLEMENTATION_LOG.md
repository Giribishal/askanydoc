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
