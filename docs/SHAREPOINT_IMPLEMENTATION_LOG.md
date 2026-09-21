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
