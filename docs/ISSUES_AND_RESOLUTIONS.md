# AskAnyDoc issues and resolutions

This is the append-only operational history of problems we actually observed, their causes, changes, and verification. The single current list of open risks, known limitations, and planned changes is [`MODERNIZATION_RISK_AND_CHANGE_REGISTER.md`](MODERNIZATION_RISK_AND_CHANGE_REGISTER.md). Do not maintain a second priority list here.

## Current register pointer

Current priorities and acceptance gates are maintained once in the modernization register: token/evidence cost (`R-015`), document/version identity (`R-016`), embedding throughput (`R-017`), ingestion alert/replay operations (`R-018`), and answer-path observability (`R-005`).

## Incident 2026-09-19 — intermittent answer failures

### What users observed

Five of fifteen repeat-run questions returned the generic frontend failure even though relevant PDFs had been indexed.

### What the improved logs proved

Four requests reached the configured two-round organisation-search limit and the model still requested another search. One request returned Bedrock `end_turn` with no usable content block after evidence retrieval.

### Resolution

The answer orchestrator now performs one bounded, tools-disabled finalization using the evidence already retrieved. It removes raw tool-protocol blocks, supplies numbered evidence as untrusted data, requires a final structured answer, and revalidates citations. It does not rerun retrieval tools or broadly retry permission, database, throttling, or infrastructure failures.

### Implementation problem caught before acceptance

The first deployment passed historical `toolUse` and `toolResult` blocks into a tools-disabled Bedrock request. Bedrock correctly rejected that request because tool protocol blocks require `toolConfig`. The implementation was corrected to build a clean text-and-evidence finalization conversation.

### Verification

- 16 API tests passed.
- The corrected Lambda deployment completed successfully.
- The same five previously failing frontend questions completed successfully in fresh sessions.
- CloudWatch recorded five recoveries, five completed answers, and zero answer failures in the verification window.
- Citation counts were 6, 7, 6, 6, and 14.

### Still unresolved

The measured 26,226-input-token case, missing recovery/validation alerts, and long-conversation behavior are tracked without duplication as `R-015`, `R-005`, and `R-023` in the modernization register.

Detailed run evidence is in `../evals/F5_LIVE_CORPUS_EVALUATION_2026-09-19.md`.

## Cost-control decision — 2026-09-20

Use one monthly Amazon Bedrock cost budget with a USD 25 limit and actual-cost notifications at USD 10, 15, 20, and 25. These alerts are an early-warning control, not a real-time hard cap, because AWS billing data and Budget evaluation can be delayed. A future enforced stop should be implemented at the AskAnyDoc application boundary using authenticated-user quotas and a measured monthly/daily usage ledger; any AWS Budgets deny action must be separately reviewed so it cannot disable unrelated Bedrock workloads or prevent recovery.

Live status: created successfully in AWS on 2026-09-20 as `askanydoc-bedrock-monthly`. It is a recurring USD 25 monthly cost budget scoped to both `Amazon Bedrock` and `Claude Haiku 4.5 (Amazon Bedrock Edition)`, with actual-cost email alerts at USD 10, 15, 20, and 25. No automatic deny or shutdown action is attached.

The weekly AWS Budgets Report `askanydoc-bedrock-weekly` was also created successfully. It includes only the new Bedrock budget, runs weekly on Sunday, and has one confirmed owner recipient. AWS charges USD 0.01 per delivered report, so it costs roughly USD 0.04–0.05 per month. This complements threshold alerts; it does not enforce a spending stop.

The matching Terraform budget definition is in `../infra/cost_budget.tf`. The live-budget import and console-created Budget Report ownership are part of the infrastructure-state/change-control work tracked by the modernization register; neither is authorized by this historical record.

## Observation 2026-09-25 — transient protected-request 401

One production request was rejected by API Gateway before Lambda while the frontend still showed Adele signed in. Safe browser diagnostics showed the expected issuer, API audience, delegated scope, and token version. A page/session refresh cleared the condition and the next SharePoint request passed. The root is unproven because API access/authorizer outcome logs are not configured. Current risk, evidence needs, and acceptance criteria are maintained as `R-026` in `MODERNIZATION_RISK_AND_CHANGE_REGISTER.md`; no speculative identity or permission change was made.

## Observation 2026-09-28 — continuous-session grounding regression

A no-refresh production sequence proved that isolated source access remains healthy inside a continuing session: the AWS-only turn returned four validated citations and the SharePoint-only turn returned three. The next combined turn correctly routed both sources and retrieved five AWS plus one SharePoint evidence item, but final synthesis returned no citation numbers once six history messages were present. The application failed closed as `organisation_not_found`; it did not fabricate an organisation source.

The same combined question had returned six validated citations in a clean session. This isolated history-sensitive synthesis/query quality rather than group membership, SharePoint permission, routing, or adapter availability.

The deployed correction now treats complete questions independently of unrelated earlier chat, supplies only the latest exchange to explicit or short follow-ups, and marks conversation history as context rather than organisation evidence. In an unrefreshed session at the 12-message client limit, the controlled AWS and SharePoint questions returned five and three citations respectively, and the formerly failing comparison returned six citations from both libraries. Deeper follow-up resolution and implicit source inference are intentionally deferred under `R-023` and `R-030` rather than hidden inside this fix.


## Incident 2026-10-04 — CRM completeness overstatement in shared synthesis

The first live three-source answer correctly cited all three sources but overstated that no other CRM records existed after bounded retrieval. Updated the final prompt and added an application-owned successful-Salesforce coverage note stating at most ten recent records per type, within current access, with no completeness guarantee. Ten focused tests passed; targeted worker redeployment and final live retest displayed the note. Final job 90592259-7800-47ec-9965-866cf2d2c7b3 passed. The final answer also cited a separate restore-test Case as context; it identified that Case separately, but tighter requested-record relevance remains open. Committed as e303b98. Exact before/after hashes and rollback: integration ledger and one-pass Stage 6B. Broader permission and reliability risks remain in the modernization register.
