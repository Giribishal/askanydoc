# AskAnyDoc issues and resolutions

This is the durable operational record of problems we have actually observed, what caused them, what changed, how the change was verified, and what remains open. Planned work without observed evidence stays in the roadmap rather than being presented as an incident.

## Current priority register

| Priority | Issue | Status | Next acceptance evidence |
| --- | --- | --- | --- |
| 1 | Excessive evidence and input-token cost | Open; research priority | Reduce the 26,226-input-token multi-document baseline while preserving retrieval recall, grounded answer quality, and citation correctness |
| 2 | Duplicate and version-aware ingestion | Open; deferred | Stable logical document/version identity and measured duplicate behavior |
| 3 | Sequential Titan embedding throughput | Open; deferred | Ingestion latency/throttling baseline followed by bounded-concurrency comparison |
| 4 | Failed ingestion is not proactively surfaced | Open; deferred | Document status plus tested CloudWatch/DLQ alert and safe replay path |
| 5 | Answer validation/orchestration recovery and alerting | Partially resolved | Recovery is deployed; validation metrics, terminal-failure alarm, and owned notification route remain |

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

- The largest multi-document recovery used 26,226 input tokens and 1,239 output tokens.
- Recovery/validation outcomes do not yet have dedicated CloudWatch metrics and an owned alert route.
- The frontend still needs a deliberate long-conversation strategy rather than waiting for the 12,000-character history rejection.

Detailed run evidence is in `../evals/F5_LIVE_CORPUS_EVALUATION_2026-09-19.md`.

## Cost-control decision — 2026-09-20

Use one monthly Amazon Bedrock cost budget with a USD 25 limit and actual-cost notifications at USD 10, 15, 20, and 25. These alerts are an early-warning control, not a real-time hard cap, because AWS billing data and Budget evaluation can be delayed. A future enforced stop should be implemented at the AskAnyDoc application boundary using authenticated-user quotas and a measured monthly/daily usage ledger; any AWS Budgets deny action must be separately reviewed so it cannot disable unrelated Bedrock workloads or prevent recovery.

Live status: created successfully in AWS on 2026-09-20 as `askanydoc-bedrock-monthly`. It is a recurring USD 25 monthly cost budget scoped to both `Amazon Bedrock` and `Claude Haiku 4.5 (Amazon Bedrock Edition)`, with actual-cost email alerts at USD 10, 15, 20, and 25. No automatic deny or shutdown action is attached.

The weekly AWS Budgets Report `askanydoc-bedrock-weekly` was also created successfully. It includes only the new Bedrock budget, runs weekly on Sunday, and has one confirmed owner recipient. AWS charges USD 0.01 per delivered report, so it costs roughly USD 0.04–0.05 per month. This complements threshold alerts; it does not enforce a spending stop.

The matching Terraform budget definition is in `../infra/cost_budget.tf`. Because the live budget was created through the console first, import it into Terraform state before enabling the email variable and applying; otherwise Terraform will attempt to create another budget with the same name. The console-created Budget Report is not currently managed by this Terraform configuration.
