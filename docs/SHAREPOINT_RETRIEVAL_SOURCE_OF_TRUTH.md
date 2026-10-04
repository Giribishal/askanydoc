# AskAnyDoc SharePoint retrieval — current source of truth

**Verified commit checkpoint — 4 October 2026, 17:20 Brisbane:** Bishal committed the implementation, tests and existing deployment/rollback evidence as `e303b98a02fafaf10cef0b0fa1848b70eea098d1` (`Add shared answers across AWS, SharePoint and Salesforce`). The repository was clean when inspected after the commit. This follow-up changes documentation only and remains uncommitted for Bishal. Previously deployed packages were not redeployed by Git commit; live three-source evidence remains the recorded 4 October tests. Remote push status has not been checked. Terraform drift, two-user Salesforce permissions, grant refresh/revoke/concurrency, MCP reliability and broader answer-quality gates remain open.

**4 October 2026 shared-source checkpoint:** Explicit mixed Salesforce/document questions now use shared_source_controller.py through the existing worker. Option B graph_search remains selected and all existing AWS/SharePoint retrieval implementation, permissions and data are preserved. Bishal approved the exact protected-path update; approval is consumed. Final worker hash hNjM2dh6IPI78hCGNXlcjSBQsULPCoXbDo0acKCEAZ0= supersedes only the worker hash in the historical 2 October contract below; legacy/job API packages unchanged. Visible SharePoint-only, AWS-only, both documents and all-three checks passed; missing CRM gave honest partial coverage. [Exact deployment/test ledger](SALESFORCE_MCP_INTEGRATION_PLAN.md), [existing ordered guide and rollback](SALESFORCE_MCP_ONE_PASS_INTEGRATION.md#stage-6b--add-shared-aws-sharepoint-and-salesforce-answers). No new provider/index/permissions. Existing attribution, employee-isolation and operational gates remain; Terraform CLI drift not reconciled.

**Effective date:** 2026-10-04
**Document version:** 1.26
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
direct_user_session_permission_matrix_proven: true
direct_sharepoint_site_access_matrix_proven: partial_adele_direct_allow_deny_plus_existing_alex_evidence_accepted_without_repeat
adele_alex_retrieval_matrix_proven: true
bishal_authenticated_graph_search_and_pdf_grounding_proven: true
entra_live_permission_and_consent_audit_proven: true
generic_live_no_match_proven: true
malicious_timeout_throttling_extraction_contract_tests_proven: true
live_cross_source_comparison_status: structured_per_source_query_contract_deployed; two_varied_supported_comparisons_returned_AWS_and_SharePoint_citations
async_answer_architecture_approved: true
async_answer_local_implementation_status: bounded_database_resume_recovery_deployed_and_cold_cross_source_answer_verified
aws_retrieval_path_may_be_changed_without_explicit_approval: false
explicit_permission_required_before_every_change: true
terraform_apply_authorized: false
deployment_authorized: false
last_deployment_approval_recorded_at: 2026-10-02
last_deployment_approval_consumed: true
deployment_status: explicit_search_or_decline_planner_and_supported_comparison_synthesis_deployed; final_no_match_AWS_SharePoint_and_two_combined_checks_passed
deployed_at: 2026-10-02
deployed_commit: uncommitted_reviewed_source_tree
deployed_lambda_code_sha256: askanydoc_api_KxiRPRYxr0K2EpYmLvYm4jktSbwPS44TsAncGi2HASA=_answer_jobs_qbElBsCo5kE4tO/nNY+D7Hc0oQBZDGbgolmzsNdHU18=
next_action: Stop for Bishal review; implicit source inference and deeper follow-up logic are deferred; if no changes are requested, design the separate alerts package with expected-no-match exclusions, cost, ownership, rollback, exact Terraform plan, and fresh approval
last_automated_verification: 52_API_tests_and_23_SharePoint_tests_passed; final_live_no_match_safe_decline_general_AWS_and_SharePoint_passed; two_combined_questions_returned_7_citations_each_at_12_message_history_limit; post_apply_Terraform_no_changes
frontend_current_lint_build: passed_with_existing_590_kb_bundle_warning
terraform_current_validation: validate_passed_with_terraform_1_16_3; fmt_check_flags_ignored_live_auth_tfvars_style_only
terraform_plan_status: conversation_grounding_plan_sha256_2B0F2918E102FBB98D17057FC6D308CB7DDC166B423B648ACBF88C74B3335B7A_applied_exactly_2_local_trigger_replacements_3_lambda_code_updates; post_apply_plan_no_changes
```

### Mandatory interpretation rules

1. **Current choice:** Option B is selected for this test environment. Do not switch providers again unless Bishal explicitly reopens and records the decision.
2. **Option A:** Keep the implementation, but do not deploy it in this tenant while the commercial gate is blocked.
3. **Option C:** Do not implement it now. It is a future architecture triggered only by measured scale, cost, latency, SLA, or cross-system requirements.
4. **Current live truth:** Option B is deployed with Graph Search enabled. Bishal's authenticated session proved search, bounded PDF extraction, grounded answering, and SharePoint page citations. Isolated AskAnyDoc sessions now prove Adele can retrieve General but not Restricted evidence, while Alex can retrieve both with correct citations. Copilot Retrieval is not deployed or live-proven.
5. **AWS protection:** do not modify AWS ingestion, S3, Titan, Aurora, pgvector, AWS retrieval, IAM, state, or data without the exact warning and Bishal's explicit approval immediately before the action.
6. **Next action only:** the bounded conversation-grounding mitigation is deployed and the no-refresh explicit AWS-only, SharePoint-only, and combined gate passed at the 12-message client limit. Bishal deferred implicit source inference and deeper follow-up logic; keep those under R-030 and R-023 without expanding this package. Keep the approval-flow no-match as a separate corpus-coverage issue. Stop for review; alerts remain the next separately scoped and approval-controlled package if no changes are requested.
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
- The deployed planned-source path uses one schema-constrained planning response: exactly one bounded query per authorized source, one execution per source, then the existing tool-disabled synthesis and application-validated citations. Missing, extra, empty, or oversized query fields fail closed. This supersedes the earlier adaptive tool-call controller while preserving its authorization and bounded-execution guarantees.
- Both Microsoft providers apply query-time site scoping and post-response URL validation.
- Post-response validation requires an exact HTTPS host and an exact configured site-path boundary.
- The Copilot adapter uses `POST https://graph.microsoft.com/v1.0/copilot/retrieval`, `dataSource: sharePoint`, a two-site `path:` filter, title metadata, and bounded results.
- Automated verification after the Graph download fallback passed: **86 Python tests, 10 intentional skips, plus 6 subtests**. On 2026-09-25, the current source-tree suite passed **51 Python tests plus 6 subtests** after adding focused timeout, throttling-cap, extraction-size, malicious-document isolation, deterministic source classification, partial cross-source evidence, and no-search fail-closed tests.
- The local frontend dependency installation was restored without downloading or replacing tracked source. Frontend lint and the production build pass. The existing approximately 589 kB JavaScript bundle warning remains a performance follow-up, not a correctness failure.

### 3.2 Applied/deployed evidence

- Local Terraform state serial 236 records SharePoint enabled with `graph_search` in the previously applied Lambda environment.
- Therefore local source and applied state intentionally disagree.
- The deployed Graph path found an exact PDF filename, proving sign-in/OBO/search metadata retrieval, but it did not answer a semantic question from that PDF's body.
- Copilot Retrieval has not been proven live in this tenant.
- Read-only Microsoft 365 admin inspection on 2026-09-21 found only **Microsoft 365 E5 Developer SKU V2** in the license inventory; no Microsoft 365 Copilot add-on license was present.
- The Copilot Billing & usage page showed no connected billing policy for its listed pay-as-you-go services and did not list Microsoft 365 Copilot Retrieval API as an enabled service.
- Current Microsoft documentation requires at least one tenant Microsoft 365 Copilot license plus eligible Azure billing for nonlicensed-user Retrieval PAYG. Therefore Option A is commercially blocked in this tenant until eligibility is deliberately obtained or Microsoft changes the requirements.
- Entra delegated permission/admin-consent status was live-verified read-only on 2026-09-22 under the `y4m7` tenant administrator. The single-tenant API registration exposes the enabled `access_as_user` scope. Its delegated Microsoft Graph permissions are `Files.Read.All`, `Sites.Read.All`, and `User.Read`, each showing **Granted for y4m7**. The single-tenant frontend registration has the exact CloudFront SPA redirect URI, requests the API's delegated `access_as_user` scope plus `User.Read`, and has no client credential. No permission or consent was changed.
- The isolated Adele/Alex AskAnyDoc retrieval matrix passed on 2026-09-21. Alex retrieved both General and Restricted evidence with the expected citations. Adele retrieved the General evidence but received `organisation_not_found`, zero citations, and no Restricted URL or document-derived protection list for the identical Restricted query.
- Terraform 1.16.3 is checksum-verified in the ignored project `tmp` directory; formatting and validation pass.
- The recorded deployment approval was consumed by the completed reviewed apply. No further Terraform apply, Lambda deployment, billing enablement, Entra permission grant, state migration, IAM change, database change, or AWS-path change is authorized by this document.
- Production requests `ec4479fb-7749-5275-8800-1ac89fd09c10` and `c57f6851-eee4-5e64-bf85-0b62062d2001` failed with `planned_source_tool_missing`. A direct Bedrock planning diagnostic returned both `search_aws_documents` and `search_sharepoint` in one valid `tool_use` response, proving the exact-one-tool assumption was the defect. Before deployment, the adaptive fix passed 41 API tests, 22 SharePoint tests, Python compilation, Terraform validation, and the direct planning contract check.
- Bishal approved and applied the exact saved adaptive-controller plan. Terraform completed `2 added, 3 changed, 2 destroyed`; the add/destroy pairs were the two local packaging triggers and the three changes were in-place Lambda package updates. All three Lambdas are active with successful update status, and a post-apply Terraform plan reports no changes.
- Post-deployment UI proof: AWS-only request `83dfaccf-6077-5bb9-8702-cffc8ddd94b1` returned three validated citations; SharePoint-only request `a1ce4962-832e-51e2-890b-2a516d35c82b` returned three validated citations. Combined requests planned both sources without the former orchestration error, but returned five AWS evidence items and zero SharePoint evidence items. The remaining gate is per-source query relevance, not permission health or multi-tool execution.
- The local structured per-source query change passed 43 API tests, 23 SharePoint tests, Python compilation, Terraform validation, and `git diff --check`. One real Bedrock planning call returned exactly the focused AWS query `disaster recovery strategies protect workloads` and focused SharePoint query `hybrid cloud connect on-premises systems`; the earlier prompt-only experiment that produced duplicate/cross-contaminated tool calls was rejected and not deployed.
- Bishal explicitly approved and Terraform applied saved plan `infra/source-query-decomposition.tfplan`, SHA-256 `C7755EDB6C8DDC06DDF79ECD8A9D4604F43D2879C4657EEAD635FB21DE9A9AF4`. It completed exactly two local packaging-trigger replacements and in-place package updates for `askanydoc-api`, `askanydoc-answer-job-api`, and `askanydoc-answer-job-worker`. It contained no IAM, API Gateway, queues, tables, database, ingestion, stored documents, pgvector, SharePoint/Entra permissions, CloudFront, frontend, or data change. All three Lambdas are active/successful and a post-apply plan reports no changes.
- Post-deployment supported-source proof passed. AWS-only job `95052ec2-924d-4f58-a1e1-88098e54f2f8` returned three SQS citations; SharePoint-only job `e37db34e-9e9e-479b-83e9-25bf8b6c93dd` returned three hybrid-cloud citations. Combined job `40e02a78-6ef2-4d8a-b658-c2e370263fdd` returned five AWS plus three SharePoint citations, and combined job `e7c82aac-8d48-407f-a364-25f2ca6fe8c4` returned three AWS plus three SharePoint citations. Both displayed `AWS document library + SharePoint`.
- A Power Automate approval question produced a clean focused SharePoint query but returned no evidence both inside a comparison and as an isolated SharePoint question. The isolated job `d388e615-fe71-46a4-a56b-f959b73f23ab` returned `organisation_not_found` with zero citations. This is tracked as corpus coverage `R-029`, not a permission or query-decomposition failure.

### 3.2.1 Current Option B plan evidence

- The saved Option B plan proposes only an in-place update of `aws_lambda_function.lambda_function` (`askanydoc-api`) plus replacement of the local `null_resource.install_deps` packaging trigger and a reread of the local ZIP data source.
- Planned environment remains `SHAREPOINT_ENABLED=true`, `SHAREPOINT_PROVIDER=graph_search`, the two verified site URLs, and `SHAREPOINT_MAX_RESULTS=10`.
- The plan contains no create/delete/replacement for S3, Aurora, pgvector, IAM, API Gateway, CloudFront, the Function URL, ingestion Lambda, queues, secrets, or databases.
- Bishal gave explicit Gate 6 approval at 2026-09-21 17:39:49 +10:00 after reviewing the shared-Lambda blast radius, failure modes, cost exposure, rollback, and verification plan. Commit `39f2474` was created immediately before apply.
- The reviewed plan applied successfully. Lambda `askanydoc-api` was updated in place at 2026-09-21 07:41:27 UTC with code SHA-256 `T51h5B4tXxhOFCriUnlNTdf4BQ8OEGpwc1PhFxPEjgg=`. AWS reports `Active` and `LastUpdateStatus=Successful`.
- Live configuration reports SharePoint enabled, provider `graph_search`, the exact General and Restricted site allowlist, and 10 maximum results.
- A live known AWS-corpus question passed with the expected `17-lambda-sqs-partial-batch-responses.pdf`, page 5 citation. The protected `/chat` endpoint returned HTTP 401 without a token. This proves the AWS smoke path and unauthenticated denial after deployment; it does not prove the Adele/Alex SharePoint matrix.
- The first authenticated SharePoint request found a permitted PDF but failed closed because Graph omitted the optional download annotation. Commit `4645279` added the official `/content` redirect fallback without forwarding the bearer token to storage; 86 tests, 10 intentional skips, and 6 subtests passed.
- The approved fix deployed successfully at 2026-09-21 07:54:44 UTC with code SHA-256 `ZfmED9FKHsVh7dTKhu6NjgW5m66chLiRoNUziDNW+LQ=`.
- Bishal's authenticated retest completed in 13.4 seconds of Lambda duration, returned a grounded architecture answer, and cited pages 1, 2, and 3 of `microsoft-cloud-hybrid-architecture.pdf` from the General site. A subsequent AWS regression again returned the expected SQS PDF/page citation in 33.7 seconds.
- On 2026-09-25, Bishal approved the exact deterministic source-classification deployment after reviewing a refreshed plan. Terraform changed only the local packaging trigger and updated `askanydoc-api` in place. The deployed code SHA-256 is `LcHPpnPfDjL7yM7yXKi68t2YqlSZaNLsHXI+/MbyR4A=` and AWS reports `Active` / `LastUpdateStatus=Successful`.
- The first post-deployment AWS request failed while the zero-ACU Aurora writer resumed (`DatabaseResumingException`, request `3397dcf3-51b6-476c-affe-a25fe2724a3a`, 40.10 s Lambda duration). The one justified retry after resume passed in 31.35 client seconds with the expected SQS page-5 citation. This database-availability risk is tracked as `R-001` in the modernization register; it is not attributed to the source-classification change.
- Adele's first broad General question completed in 20.02 s as a safe no-match with zero citations. A targeted isolated query for `microsoft-cloud-hybrid-architecture.pdf` then completed in 13.94 s with `organisation_sources`, three citations to pages 4, 1, and 2, and no Restricted evidence.
- One intermediate protected request returned HTTP 401 before Lambda despite the browser still showing Adele signed in and safe diagnostics showing the expected tenant issuer, API audience, scope, and token version. A page/session refresh cleared it; the next protected request passed. The unproven authorizer/session cause is tracked as `R-026`, to be diagnosed through access logging rather than a speculative identity change.
- The bounded explicit AWS-versus-SharePoint request `f3fb33c0-d173-443d-bf20-6d448f7f2271` completed successfully inside Lambda in 38.78 s with `organisation_sources`, five citations, 7,556 input tokens, and 552 output tokens. The browser received `Service Unavailable` because the result exceeded the HTTP API boundary. This proves the source-classification root fix in production while preserving the separate transport limitation as `R-002`.
- This proves the Option B vertical slice and user isolation for the tested AskAnyDoc questions. On 2026-09-22, Adele directly opened the General site and received SharePoint Access Denied for the Restricted site. Bishal accepted the existing Alex evidence without repeating another direct-site login. This does not yet prove every remaining operational case.
- Keep the current single-Lambda architecture for the present test volume because it is simpler and avoids an extra synchronous invocation and overlapping billed duration. A dedicated SharePoint retrieval Lambda is documented in `SHAREPOINT_LAMBDA_SEPARATION_PLAN.md` as a deferred scale/reliability option, not the next mandatory migration. Reopen it only when measured triggers justify the extra topology and IAM.
- On 2026-09-28, Bishal approved and Terraform applied the bounded recovery plan: one local packaging-trigger replacement and five in-place cloud updates to the encrypted answer queue, worker IAM policy, event-source mapping, shared-package job API Lambda, and worker Lambda. Both Lambdas are active with code SHA-256 `31EBxNTHee98Nyhb+Ikv/6pFMvWf4jplV12uYwAeti4=`; the event-source mapping reports `ReportBatchItemFailures`; queue visibility remains 1,080 seconds; DLQ `maxReceiveCount` is five; and the worker has only the queue-scoped `sqs:ChangeMessageVisibility` addition. No Aurora configuration/data, ingestion, S3 document, pgvector, SharePoint permission, Entra, API Gateway, CloudFront, or frontend resource changed.
- The approved varied production comparison ran as Adele without naming the storage locations. Job `274b655d-f13d-4219-83b2-96f60d8ed3b9`, worker request `c0fc002f-3934-58f2-a30b-631cf07b4976`, returned a browser-visible `organisation_sources` answer comparing disaster recovery on AWS with Microsoft hybrid-cloud architecture. It cited five pages from `13-disaster-recovery-workloads-on-aws.pdf` and three pages from `microsoft-cloud-hybrid-architecture.pdf`. Aurora was at 0 ACU before the request and resumed during the test. The job completed on attempt one in 47 wall-clock seconds; Lambda duration was 44.43388 seconds, billed duration 47.021 seconds, maximum memory 170 MB, with 7,723 input and 741 output tokens. The slower cross-invocation branch was not needed live and remains locally test-proven. Estimated Claude Haiku 4.5 plus worker compute cost was about USD $0.013, before negligible embedding, queue, table, KMS, logging, Graph, and short Aurora-capacity charges.

### 3.3 SharePoint test corpus and identities

- General site: `https://y4m7.sharepoint.com/sites/AskAnyDoc-General-Documents`
- Restricted site: `https://y4m7.sharepoint.com/sites/AskAnyDoc-Restricted-Senior-Documents`
- General corpus: 8 PDFs verified in the site UI.
- Restricted corpus: 4 PDFs verified in the site UI.
- Adele is intended to read general content and be denied restricted content.
- Alex is intended to read both general and restricted content.
- Bishal is the administrative test identity and cannot substitute for the Adele/Alex isolation tests.
- SharePoint's read-only **Check Permissions** tool now proves the effective site-level matrix: Adele has **Edit** on General and **None** on Restricted; Alex has **Edit** on both General and Restricted.
- Isolated AskAnyDoc browser sessions now prove the end-to-end retrieval boundary: Adele can retrieve General evidence and is denied Restricted evidence; Alex can retrieve both. Direct SharePoint site navigation under each isolated identity remains a separate Gate 3 evidence item because a prior direct-site attempt retained Bishal's SharePoint cookie and was discarded as invalid evidence.

### 3.3.1 Live Adele/Alex retrieval matrix — 2026-09-21

| Identity | Question scope | Result | Evidence |
|---|---|---|---|
| Alex | General | Pass | 3 General-site citations to `microsoft-cloud-hybrid-architecture.pdf` pages 2, 1, and 3; Lambda 11.18 s |
| Alex | Restricted | Pass | 1 Restricted-site citation to `sharepoint-sites-highly-regulated-data.pdf` page 1; Lambda 28.08 s |
| Adele | General | Pass | 3 General-site citations to `microsoft-cloud-hybrid-architecture.pdf` pages 2, 1, and 3; Lambda 17.08 s |
| Adele | Restricted | Pass (denied/no evidence) | `organisation_not_found`, 0 citations, no Restricted URL, and no Restricted document-derived protection list; Lambda 13.58 s |

The first Alex filename-heavy query returned no match and is retained as query-sensitivity evidence, not as a permission failure. The controlled General and Restricted questions above were then held constant across identities.

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

### 3.6 Superseding live hardening evidence - 2026-10-02

Bishal approved the application-only planner/refusal/comparison patch and code-package deployment, then requested an additional two-source test. The planner now has explicit search/decline outcomes; declined plans execute no retrieval and produce no citations. Empty search queries and malformed plans still fail closed. Bedrock completion reasons are checked, with one bounded token-limit retry. Supported comparisons may synthesise separate sources; partial answers retain citations for supported parts and identify missing evidence. A harmless unusual policy query remains a search/no-match, not a fabrication refusal.

Final deployed worker/API-job package SHA-256: `qbElBsCo5kE4tO/nNY+D7Hc0oQBZDGbgolmzsNdHU18=`; legacy answer package: `KxiRPRYxr0K2EpYmLvYm4jktSbwPS44TsAncGi2HASA=`. Final recovery plan SHA-256: `7F8A9EC790F63375E34059BBE3BE5F596DE474C25AD8D135F80B32A04355E89D`. Apply completed with one local build-trigger replacement and three in-place code updates. Final package inspection proves only `assistant_orchestrator.py` differs from verified pre-patch packages; protected retrieval code and pinned dependencies are identical. Post-apply Terraform plan reports no changes.

Final live checks: no-match `c8cc4051-325c-5ca1-b074-236870367eec`; safe decline `d9c01a32-3239-5808-9342-790b70bd9a45`; general knowledge `40c52022-080b-55e9-8e8d-431b4aba57a4`; AWS `8fa8ad10-5d78-5121-85d0-ce291fa1438c`; DR/hybrid comparison `dc3af604-f554-5350-aca0-953db7be0a18`; SQS/hybrid question `80975b31-c1a7-571c-b71c-380882b724ce`; SharePoint-only `2052d127-6ec2-5cbc-b2de-b21e2dff2231`. The two combined questions each returned seven citations across both libraries in one continuous 12-message session. Intermediate retest failures and build recovery remain recorded in the implementation log and modernization register. This section supersedes older current-code hashes and next-action wording; earlier deployment records remain historical.

No permission, provider, database-capacity, AWS ingestion/retrieval, document, IAM, queue, table, or frontend configuration changed. Alerts remain design-only; future unrelated changes still require their own scope and approval. Model routing remains probabilistic and requires broader evaluation; these live checks do not prove production readiness.

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

Implemented and deployed as `graph_search`. Semantic PDF-body answers, page citations, AWS coexistence, and the controlled Adele/Alex permission matrix are live-proven for the tested corpus. Retain as the explicit selected provider for this environment, not an automatic silent fallback from A.

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
| `docs/MODERNIZATION_RISK_AND_CHANGE_REGISTER.md` | Single current register for risks, known issues, official-architecture gaps, and planned changes |
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
3. Preserve the completed read-only Entra audit: the API Graph permissions show tenant consent, `access_as_user` is enabled, and frontend registration values match the deployed CloudFront client. Do not grant or change consent.
4. Preserve the completed Adele/Alex AskAnyDoc matrix and Adele's direct General-allow/Restricted-deny evidence. Bishal accepted the existing Alex evidence without another redundant direct-site login.
5. Preserve the current green source baseline: 43 API tests and 23 SharePoint tests pass after the structured per-source query change; Python compilation, Terraform validation, `git diff --check`, and the real Bedrock structured planning check also pass. Frontend lint/build remain green with the existing bundle warning.
6. Treat the deterministic application-owned classification fix as deployed and live-proven at the Lambda boundary. Retain requests `1e3327cd-715f-4aaa-a0c3-ee87cbaea03a` and `f3fb33c0-d173-443d-bf20-6d448f7f2271` as evidence of the separate 30-second client boundary; do not redesign topology solely to make every long request succeed. Validated citations must continue to determine grounded organisation status; a completed search without cited evidence must determine no-match status; invented citations and organisation claims without a real search must continue to fail closed.
7. Preserve the successful generic no-match result and local malicious-content, timeout, throttling-cap, and extraction-limit contract tests. Obtain live fault/limit evidence only where it is safe and does not require mutating tenant content or production configuration.
8. Preserve the completed adaptive-controller deployment and its proof: exact plan SHA-256 `98D85DF78BA0040C2B3E558728C5E9FBF880E42F5DB9CC7E1CD6799BB07AD3B8`; three in-place Lambda package updates; post-apply plan no changes; no IAM, topology, database, data, permission, frontend, or retrieval-adapter change.
9. Treat the supported-source UI gate as complete: isolated AWS and SharePoint questions passed, and two varied comparisons returned validated citations from both sources. Preserve the exact job/request evidence in the implementation log and test matrix.
10. Keep the approval-flow result as an honest no-match under `R-029`. Before changing code or content, verify whether the intended SharePoint corpus actually contains an approved approval-flow document and whether the reference-matrix expectation should remain. Do not disguise missing organisation evidence with a general-knowledge organisation label.
11. Preserve current deployed identity: `askanydoc-api` code SHA-256 `gS5PgQjv/3gZTwoU6F83h0H1+8U2sCxCLPembsZdH1Q=` and both answer-job Lambdas `HsKOeHYUNket7A9h8pYYLaT4qtLdahDDJdI0+nkAfo4=`. Commit `4645279` remains an older rollback checkpoint.
12. Compare the other provider only as an explicit evaluation after the selected path has evidence.
13. Keep the single Lambda while the current bounds and tests meet the workload. Reopen separation only for measured triggers. Do not alter the protected AWS path under the completed deployment approval.
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
- API Gateway HTTP API quotas (30-second maximum integration timeout): https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-quotas.html

All licensing, prices, preview/GA status, permissions, quotas, supported formats, and service limits are version-sensitive and must be rechecked from current official sources at the relevant gate.
