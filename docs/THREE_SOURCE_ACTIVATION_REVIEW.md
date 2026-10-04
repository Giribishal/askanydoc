# Three-source activation review — 4 October 2026

**Current checkpoint, 4 October 2026:** Bishal approved the exact protected-path impact. Three-source AWS + SharePoint + Salesforce synthesis is now deployed and visibly tested, including all three citation groups and bounded CRM coverage. AWS-only, SharePoint-only, AWS+SharePoint and Salesforce-only regressions passed; a mixed missing-CRM test disclosed no_match and cited only found AWS evidence. Existing grants, IAM, data and original retrieval implementations were preserved. The sections describing pending activation below are historical. Exact actions, hashes, safe request IDs, tests and rollback are in [the integration ledger](SALESFORCE_MCP_INTEGRATION_PLAN.md) and [existing one-pass guide, Stage 6B](SALESFORCE_MCP_ONE_PASS_INTEGRATION.md#stage-6b--add-shared-aws-sharepoint-and-salesforce-answers). Source remains uncommitted; Terraform reconciliation, two-user permissions, refresh/revoke and reliability gates remain open.


## Ready locally; not activated or live-proven

New `app/api/shared_source_controller.py` implements a small adapter registry, focused per-source query planning, bounded retrieval, shared evidence/citation synthesis and deterministic partial-coverage disclosure. The controller accepts explicitly requested registered sources, including a test adapter representing a future connector. Today's transport opt-in is explicit Salesforce plus existing AWS/SharePoint source cues; automatic inference for all future systems is not claimed.

New `app/salesforce/evidence_endpoint.py` retrieves evidence using the validated Entra owner's existing Salesforce grant and the unchanged typed CRM compiler. No client-supplied identity or raw SOQL is accepted. Salesforce credentials remain in the dedicated Lambda. The async worker forwards only the existing caller's Entra token to a configured HTTPS API Gateway endpoint; redirects are disabled. The route revalidates JWT signature, audience, issuer, expiry and `access_as_user` through the existing authorizer. Expired/disconnected/failed sources yield a partial answer with a coverage warning, never a weaker identity fallback.

The six-existing-file activation diff is `SHARED_SOURCE_ACTIVATION.patch`. Its candidate files are under ignored `tmp/three-source-activation/`. The protected worker, existing frontend and Terraform files have not received this patch. New local modules are uncommitted. The existing Salesforce/frontend changes from the earlier deployed slice also remain uncommitted; this activation must not overwrite them.

## Exact proposed impact

- `app/api/answer_job_worker.py`: dispatch only mixed Salesforce/document questions to the new controller. Ordinary document jobs still call the current `answer_question`. Database resume exceptions still reach the existing bounded retry logic; queue/result/lease handling is unchanged.
- `app/salesforce/web_handler.py`: dispatch new `POST /salesforce/evidence` to the evidence-only helper. Existing connection, disconnect, refresh and `/ask` routes remain.
- `frontend/src/App.jsx`: send mixed Salesforce/document questions through existing `/jobs`; retain Salesforce-only `/ask`; show every cited source in the badge. A disconnected Salesforce source may produce a useful explicitly partial document answer.
- `infra/build_salesforce_web.ps1`, `infra/salesforce_web.tf`, `infra/answer_jobs.tf`: include the new modules in build/hash lists, declare the JWT/scoped evidence route and worker `SALESFORCE_EVIDENCE_URL` configuration.
- Targeted live changes after approval: code for `askanydoc-answer-job-worker` and `askanydoc-salesforce-web-dev`; one worker environment key; one existing-API route using existing Salesforce integration and Entra JWT authorizer; private frontend JS/index upload and CloudFront invalidation. No IAM change, database/schema/data change, new store/queue/service, vendor consent, billing activation or dependency update. Direct targeted deployment would add Terraform drift; any later Terraform apply requires its own exact reviewed plan. The shared archive definition can affect the job API in a full Terraform plan, so do not deploy that API merely to activate the targeted worker.

## Verification already completed

- 65 API tests passed, including ten new contract tests: independent three-source queries/citations; invalid plan and decline execute no reads; disconnected source; invalid source evidence; retained database-resume recovery; generic registered adapter; no redirect/token forwarding to a new host; no-match/truncation; invented citations rejected; validated owner-bound evidence endpoint.
- Staged worker passes the five existing job tests plus a separate dispatch probe proving a mixed question takes the new controller and does not call the old answer path.
- Staged Salesforce handler passes all 26 existing CRM/OAuth tests.
- Staged frontend Vite 8.1.5 build and ESLint pass. Existing approximately 603 kB chunk warning remains.
- Actual deployed model read-back: `au.anthropic.claude-haiku-4-5-20251001-v1:0`. A real Bedrock planning call returned independent AWS disaster-recovery, SharePoint hybrid-cloud and Salesforce Rivergum VPN Case queries. This was synthetic query planning only, not three-source live retrieval. Planner usage: 495 input/59 output tokens.
- Candidate Terraform formatting ran; configuration directory access warning occurred. No Terraform validation or saved live plan is claimed. Git whitespace check passed before this document was added.

No three-source application answer has been tested because the protected activation is pending. Prior fresh AWS-only, SharePoint-only and AWS+SharePoint live regression evidence is in the integration ledger. Current permission-isolation, refresh/concurrency and intermittent MCP reliability gates remain open.

## Cost and failure exposure

Only selected sources run. Maximum three source adapters; existing AWS retrieval, bounded SharePoint primary/fallback and at most three CRM object reads plus one Account resolution. A mixed request adds one CRM planning call and its existing hosted MCP requests to the document work; all use existing usage-based services. No price/SLO guarantee is inferred. Source latency, token expiry and intermittent MCP failures may reduce coverage. The same customer name across sources does not establish a shared identity or a recorded technical implementation; synthesis must distinguish facts and inference.

## Exact rollback preparation and sequence

Immediately before deployment, save both actual deployed Lambda ZIPs and code hashes, the complete worker configuration privately, and actual frontend index plus asset references into ignored `tmp/three-source-before-20261004/`. Preserve dependencies byte-for-byte when updating packages. Record the actual evidence route ID after creation; keep old frontend assets.

1. Restore the saved frontend index to `s3://askanydoc-site-prod-apse2/index.html` with `text/html` and `no-cache`, then invalidate `/` and `/index.html` on `E302MAX0PA60NZ`.
2. Restore only the saved `askanydoc-answer-job-worker` ZIP and exact saved environment; wait for Successful update status. Existing jobs then use their previous controller again.
3. Remove only the newly recorded evidence route, then restore the saved dedicated Salesforce ZIP. Preserve user grants and existing routes.
4. Reverse only the activation patch after reviewing any subsequent user edits. Keep append-only evidence; leave original AWS retrieval, SharePoint provider, permissions, records, data and infrastructure intact.

Exact CLI values and saved package hashes must be recorded at deployment, not invented here. Approval does not authorize unrelated Terraform drift reconciliation or permission changes.

## Required approval and live acceptance

Workspace `AGENTS.md`, AWS Path Change Control: “If the architecture genuinely requires an AWS-path change, explain the exact impact and obtain Bishal's explicit approval immediately before making it.” This opt-in changes the shared answer worker and its deployed package, so that requirement applies. SharePoint source-of-truth sections 11/15 also require exact deployment scope and approval; the full document was read for this work. These are project requirements, not an automatic approval-review rejection.

After approval, apply only the reviewed patch, validate/build the final files, deploy only the targets above with backups and safe revision checks, and visibly test: AWS-only; SharePoint-only; AWS+SharePoint; Salesforce-only; all three together; mixed request with unavailable/no-match CRM evidence. The all-three question must return record and document citation groups and no invented entity join. Record safe job/request IDs, latency, source outcomes, failures and rollback identity. Do not commit; Bishal owns commits.
