# F5 live corpus and frontend evaluation — 2026-09-19

## Outcome

The ingestion path worked end to end for every supported PDF selected for this run. Sixteen PDFs (17,275,382 bytes / 16.475 MiB) were uploaded through the AWS S3 console, and CloudWatch showed 16 distinct successful extraction events. The indexed corpus contains 558 pages and 1,411 chunks.

The answering path worked functionally but was not reliable enough to call complete. Of 23 normal frontend attempts:

- 12 returned grounded answers with organisation citations.
- 1 returned general knowledge.
- 1 correctly reported that organisation information was not found.
- 8 returned `AskAnyDoc could not complete the answer. Please try again.`
- 1 was rejected because accumulated chat history exceeded 12,000 characters.

That is 14/23 completed answers (60.9%) and 9/23 user-visible failures or rejections (39.1%). Completed requests averaged 6.957 seconds. The main finding is that ingestion is healthy, retrieval and citation can work well, but answer orchestration has intermittent failure and no controlled recovery.

## Test environment

- Region: `ap-southeast-2` (Sydney)
- S3 destination: `s3://askanydoc-documents-prod-apse2/uploads/`
- Ingestion Lambda: `askanydoc-ingestion-prod`
- Answer Lambda: `askanydoc-api`
- Public frontend: `http://askanydoc-site-prod-apse2.s3-website-ap-southeast-2.amazonaws.com`
- Test method: ordinary S3 console upload followed by ordinary questions through the public frontend
- Ingestion constraints checked before upload: PDF under 10 MiB and no more than 200 generated chunks

## Corpus selection and preflight

### Uploaded and indexed

| File | Size (bytes) | Pages | Chunks | Purpose |
|---|---:|---:|---:|---|
| `01-rag-options-and-architectures.pdf` | 806,902 | 38 | 102 | RAG implementation options |
| `02-writing-best-practices-rag.pdf` | 339,015 | 18 | 44 | Content practices for retrieval |
| `03-automated-pdf-analysis.pdf` | 428,733 | 16 | 38 | Event-driven PDF processing |
| `05-enterprise-ready-generative-ai-platform.pdf` | 769,476 | 37 | 110 | Enterprise GenAI platform controls |
| `07-agentic-ai-patterns.pdf` | 5,081,172 | 85 | 174 | Agent workflow patterns |
| `09-serverless-multi-tier-architectures.pdf` | 929,432 | 32 | 79 | Serverless web architecture |
| `10-serverless-data-analytics-pipeline.pdf` | 914,077 | 31 | 79 | Serverless analytics pipeline |
| `11-creating-a-data-strategy-on-aws.pdf` | 827,152 | 25 | 58 | Data strategy and governance |
| `12-aurora-postgresql-integration.pdf` | 494,284 | 29 | 73 | Aurora PostgreSQL integrations |
| `13-disaster-recovery-workloads-on-aws.pdf` | 2,048,359 | 40 | 110 | Disaster recovery strategies |
| `14-hybrid-cloud-best-practices.pdf` | 1,701,521 | 51 | 128 | Hybrid cloud design |
| `15-saas-architecture-fundamentals.pdf` | 650,501 | 44 | 105 | SaaS control and application planes |
| `16-data-security-lifecycle-strategy-genai.pdf` | 505,612 | 29 | 100 | Known issue 2: lifecycle/version governance |
| `17-lambda-sqs-partial-batch-responses.pdf` | 314,643 | 14 | 32 | Known issue 3: throughput and partial retries |
| `18-security-overview-aws-lambda.pdf` | 890,796 | 33 | 85 | Known issue 4: monitoring/security |
| `19-generative-ai-workload-assessment.pdf` | 573,707 | 36 | 94 | Known issue 5: validation and operational readiness |

### Downloaded but deliberately not uploaded

These documents passed the file-size check but exceeded the deployed 200-chunk ingestion limit. Excluding them prevented predictable partial failures.

| Candidate | Pages | Chunks | Decision |
|---|---:|---:|---|
| `04-aws-sra-ai-security.pdf` | 79 | 250 | Excluded; over chunk limit |
| `06-generative-ai-inference-architecture.pdf` | 90 | 254 | Excluded; over chunk limit |
| `08-serverless-applications-lens.pdf` | 104 | 269 | Excluded; over chunk limit |
| `18-cloudwatch-logging-monitoring.pdf` | 100 | 321 | Replaced by the Lambda security overview |
| `19-genai-lifecycle-operational-excellence.pdf` | 105 | 369 | Replaced by the GenAI workload assessment |

## Transfer and ingestion timing

- S3 upload started: `2026-09-19T04:36:48.822Z`
- S3 upload completed: `2026-09-19T04:37:02.876Z`
- S3 upload duration: **14.054 seconds**
- S3 console result: **16 succeeded, 0 failed**
- First successful ingestion event: `2026-09-19T04:38:23.529Z` (94.707 seconds after upload start)
- Last successful ingestion event: `2026-09-19T04:39:23.803Z`
- Upload start to fully indexed: **154.981 seconds**
- Upload completion to fully indexed: **140.927 seconds**

CloudWatch contained 16 unique success messages and no duplicate document success. The console footer displayed “17 events loaded,” but direct row inspection showed 16 document messages plus table/UI rows; it was not a duplicate ingestion.

### Ingestion completion order

| UTC completion | File |
|---|---|
| 04:38:23.529 | `17-lambda-sqs-partial-batch-responses.pdf` |
| 04:38:26.269 | `12-aurora-postgresql-integration.pdf` |
| 04:38:26.665 | `19-generative-ai-workload-assessment.pdf` |
| 04:38:26.672 | `18-security-overview-aws-lambda.pdf` |
| 04:38:26.863 | `10-serverless-data-analytics-pipeline.pdf` |
| 04:38:27.328 | `15-saas-architecture-fundamentals.pdf` |
| 04:38:27.328 | `16-data-security-lifecycle-strategy-genai.pdf` |
| 04:38:27.461 | `01-rag-options-and-architectures.pdf` |
| 04:38:27.651 | `13-disaster-recovery-workloads-on-aws.pdf` |
| 04:38:27.966 | `07-agentic-ai-patterns.pdf` |
| 04:38:46.779 | `03-automated-pdf-analysis.pdf` |
| 04:38:50.876 | `11-creating-a-data-strategy-on-aws.pdf` |
| 04:38:50.931 | `02-writing-best-practices-rag.pdf` |
| 04:38:57.658 | `09-serverless-multi-tier-architectures.pdf` |
| 04:39:19.065 | `05-enterprise-ready-generative-ai-platform.pdf` |
| 04:39:23.803 | `14-hybrid-cloud-best-practices.pdf` |

## Frontend evaluation summary

| Metric | Result |
|---|---:|
| Total attempts | 23 |
| Grounded organisation answers | 12 |
| General-knowledge answers | 1 |
| Correct organisation-not-found answers | 1 |
| Backend completion failures | 8 |
| History-limit rejections | 1 |
| Completed-answer rate | 60.9% |
| Mean completed latency | 6.957 s |
| Indexed documents represented in successful citations | 14/16 |

The two indexed documents not represented in successful citations were `02-writing-best-practices-rag.pdf` and `09-serverless-multi-tier-architectures.pdf`. Both were queried. The first returned a runtime failure; the second initially failed and its paraphrased retry returned uncited general knowledge instead of using the indexed PDF.

## Every frontend attempt

| # | Type | Question | Seconds | Result / answer obtained | Source evidence |
|---:|---|---|---:|---|---|
| 1 | Exact, RAG | What are the main RAG implementation options described in the AWS guidance, and how do they differ? | 17.855 | Failed: `AskAnyDoc could not complete the answer. Please try again.` | CloudWatch `RuntimeError` |
| 2 | Paraphrase, issue 3 | What problem does SQS partial batch response solve? | 4.453 | Explained that default batch failure redrives every message; partial response retries only failed messages, reducing repeat transfer and improving throughput. | `17...pdf`, p.5; score 0.7826 |
| 3 | Workflow | What happens after a PDF is uploaded to S3 in the automated analysis architecture? | 5.473 | S3 ObjectCreated invokes Lambda; Lambda sends the PDF to Textract; template-based post-processing extracts data; results go to DynamoDB and an S3 JSON output. | `03...pdf`, pp.6,10; score 0.7025 |
| 4 | Paraphrase, Aurora | How does Aurora PostgreSQL integrate with AWS services and external databases? | 6.503 | Described `aws_s3`, `aws_lambda`, CloudWatch/Redshift integration, FDWs, federated queries, and performance/management considerations. | `12...pdf`, pp.4,5,8,9,10; score 0.7696 |
| 5 | Comparison, DR | Compare backup/restore, pilot light, warm standby, and multi-site by RTO and cost. | 11.653 | Correctly ordered strategies from slowest/lowest cost to near-zero recovery/highest cost and explained pilot-light versus warm-standby readiness. | `13...pdf`, pp.14,15,23,24,28; score 0.5220 |
| 6 | Workflow, serverless | Walk through a serverless three-tier request. | 4.472 | Failed with generic completion error. | CloudWatch `RuntimeError` |
| 7 | Architecture, analytics | Describe layers/services in a serverless analytics pipeline. | 4.433 | Failed with generic completion error. | CloudWatch `RuntimeError` |
| 8 | Concept, SaaS | Why separate control plane and application plane? | 5.463 | Distinguished global tenant-management/operations capabilities from tenant-facing business services and isolation. | `15...pdf`, pp.16–17; score 0.7970 |
| 9 | Paraphrase, issue 2 | How should a GenAI knowledge base keep changing documents current, traceable, and safe? | 6.501 | Covered data preparation, retained versions, refresh processes, governance, RBAC, classification, audits, PII handling, and traceability. | `16...pdf`, pp.9,25 and `19...pdf`, p.27; score 0.6165 |
| 10 | Cross-topic, issue 4 | How should production Lambda be monitored and secured for quick failure detection? | 6.520 | Recommended CloudWatch metrics/alarms, CloudTrail, code signing, encryption, access controls, and runtime vulnerability management. | `18...pdf`, pp.11,15,23; score 0.7549 |
| 11 | Cross-topic, issue 5 | What should a GenAI workload assessment test before production? | 8.604 | Covered answer metrics/human review, bias, edge cases, adversarial testing, prompt injection/data poisoning, encryption/access/audit, alerts, scaling, and continuous monitoring. | `19...pdf`, pp.16,23,24; `05...pdf`, pp.18,31; `16...pdf`, p.21; score 0.6575 |
| 12 | Semantic, agentic | When should routing, parallelization, reflection, or orchestrator-worker patterns replace one model call? | 4.434 | Failed with generic completion error. | CloudWatch `RuntimeError` |
| 13 | Broad, hybrid | Main hybrid-cloud concerns for connectivity, identity, security, and operations? | 8.578 | Covered VPN/Direct Connect resilience, latency, defense in depth, access consistency, edge capacity, distributed operations, transfer cost, and compliance. | `14...pdf`, pp.12,20,26,34; score 0.6137 |
| 14 | Multi-document synthesis | Recommend a secure, operable RAG architecture using multiple documents. | 6.504 | Failed with generic completion error. | CloudWatch `RuntimeError` |
| 15 | Unanswerable | What was our exact AWS bill last month and who approved it? | 3.414 | Correctly said the facts were not in organisation sources and suggested billing/accounting/approval systems without inventing an answer. | Organisation sources: no match |
| 16 | Retry of #6 | Describe browser → API → Lambda → database → response. | 5.467 | Produced a technically plausible path, but used **General knowledge** rather than the indexed serverless PDF. | No citation |
| 17 | Retry of #7 | Describe ingestion, storage, processing, analytics, and presentation stages. | 6.495 | Recovered successfully and described the five layers, AppFlow ingestion, a central data lake, transformation, analytics, and presentation. | `10...pdf`, pp.11,15; score 0.8405 |
| 18 | Retry of #12 | Give practical examples of routing, parallel, self-review, and manager-worker workflows. | 7.554 | Recovered successfully with practical routing and concurrency examples plus self-review and hierarchy use cases. | `07...pdf`, pp.53,55,74; score 0.4343 |
| 19 | Retry of #14 | Combine RAG, lifecycle, and Lambda guidance into one design. | 10.724 | Recovered with ingestion, S3/KMS/IAM, governance/catalog/audit, vector retrieval, Lambda security, CloudWatch alarms, CloudTrail, lineage, and feedback. | Six PDFs: `01`, `05`, `07`, `11`, `16`, `18`; score 0.7368 |
| 20 | Retry of #1 | Summarise managed versus custom RAG choices. | 0.340 | Rejected: `History may contain at most 12000 characters.` | HTTP validation, before answering |
| 21 | Fresh-session retry of #1 | Same RAG trade-off intent after page reload. | 4.455 | Failed with generic completion error. | CloudWatch `RuntimeError` |
| 22 | Fresh-session, writing | Which writing/content practices improve RAG retrieval? | 3.458 | Failed with generic completion error. | CloudWatch `RuntimeError` |
| 23 | Fresh-session, enterprise platform | Main security and operational components of an enterprise GenAI platform? | 3.519 | Failed with generic completion error. | CloudWatch `RuntimeError` |

## What worked well

1. **Ingestion integrity:** every supported file produced a success event with the expected page count, character count, chunk count, SHA-256, S3 version ID, and source URI.
2. **Semantic retrieval:** successful answers handled literal questions, paraphrases, comparisons, and broad conceptual prompts.
3. **Page-level citations:** grounded responses named the source PDF and page number.
4. **Cross-document synthesis:** attempt 19 used six different uploaded PDFs in one answer.
5. **Safe absence handling:** attempt 15 did not invent organisation-specific billing or approval data.
6. **Useful source metadata:** the UI showed source mode, top similarity, token usage, and citations.

## Issues and limitations found

### P1 — Answer orchestration fails intermittently and does not recover

Eight requests reached `askanydoc-api` and were logged as `answer_failed` with `error_type: RuntimeError`. The frontend returned only the generic retry message. The Lambda log deliberately records the exception type but not the exception message, so the exact branch cannot be proven from production logs.

In the current code, the relevant `RuntimeError` paths are the organisation tool-call-round limit and failure to produce a final response. This makes a tool-orchestration exhaustion the leading hypothesis, not a confirmed root cause. There is no automatic controlled retry, reduced-scope retry, or user-visible incident identifier beyond the request ID in the HTTP payload.

Impact: normal document questions fail unpredictably even though the PDFs are indexed. This directly confirms known issue 5.

### P1 — Long conversations hit a hard 12,000-character history rejection

After several detailed answers, the next request was rejected in 0.340 seconds with `History may contain at most 12000 characters.` The frontend does not truncate, summarise, start a new conversation automatically, or warn that the limit is approaching. Reloading clears history, but that is not explained to the user.

Impact: a normal long research session eventually stops working.

### P2 — Source routing can fall back to general knowledge despite an indexed matching document

The serverless three-tier question initially failed. Its rephrased retry returned a plausible answer marked `General knowledge`, even though `09-serverless-multi-tier-architectures.pdf` had successfully indexed with 79 chunks.

Impact: an answer can be technically correct but ungrounded and uncited when the user's intent is clearly document-based.

### P2 — Failure telemetry is insufficient for diagnosis and alerting

CloudWatch records `RuntimeError` but omits the exception message and orchestration round/state. There was no observed proactive alert. Diagnosing the exact failure would require richer structured fields or a separate trace system.

Recommended fields: failure stage, safe error code, tool round, tool name, evidence count, stop reason, model request ID, retry count, and terminal exception class/message category. This confirms known issue 4 and part of known issue 5.

### P2 — Citation rendering is difficult to read

The UI concatenates repeated citations, for example `03...pdf, page 603...pdf, page 6`, without separators or deduplication. Some answers cite the same page repeatedly.

Impact: the underlying evidence is present, but users have to parse an ambiguous source string.

### P2 — Corpus constraints require manual preflight

Five useful AWS PDFs were below 10 MiB but would have failed because they generated 250–369 chunks, above the 200-chunk limit. The S3 upload UI does not communicate this application-specific constraint.

Impact: a normal uploader can successfully place a document in S3 but later receive no usable indexed document, matching known issue 4's silent-failure concern.

### P3 — Low similarity can still produce confident-looking grounded answers

The recovered agent-pattern answer cited sources with a top score of 0.4343. It was broadly reasonable, but the UI does not explain confidence thresholds or distinguish strong from weak retrieval.

Impact: users may over-trust a low-match answer.

## Recommended next acceptance gates

1. Add a controlled retry for structured-output or tool-round failures, with a strict retry cap and a simpler fallback prompt.
2. Log safe diagnostic categories and emit a CloudWatch metric/alarm for `answer_failed`.
3. Fix conversation history handling in the frontend: trim/summarise older turns or offer a visible “new conversation” action before the API rejects the request.
4. Make document-intent routing deterministic when a user says “uploaded document,” names a document/topic, or explicitly requests sources.
5. Render citations as a deduplicated list with clear separators and clickable source/page items.
6. Surface ingestion status and rejection reason per S3 object; ideally run the same preflight before or immediately after upload.
7. Add repeatable evaluation cases for: exact match, paraphrase, multi-document synthesis, no-match refusal, low-similarity evidence, tool-round exhaustion, and history-size boundary.

## Final verdict

**Ingestion: pass.** All 16 supported PDFs landed and indexed correctly within roughly 2 minutes 35 seconds from upload start.

**Retrieval and grounding: partial pass.** When orchestration completed, answers were generally useful and 12 were grounded with page citations; multi-document synthesis and safe no-match behavior both worked.

**Normal-user reliability: fail for the current acceptance gate.** A 39.1% combined failure/rejection rate in this run is too high. The next work should focus on controlled answer recovery, observable failure reasons, history management, and deterministic source routing before adding more corpus volume.

## Diagnostic logging deployment and repeat run — 2026-09-19/20

The answer Lambda was updated without adding retry or changing answer policy. Failed requests now log:

- safe exception message and traceback;
- failure stage and stable error code;
- history-message count;
- tool round, configured round limit, stop reason, and requested tool names;
- evidence count and organisation-search status;
- input/output token totals;
- final response content-block and text-block counts where applicable.

The change passed 12 API/orchestration tests and Python compilation. AWS reported the deployed `askanydoc-api` function as `Active` with `LastUpdateStatus: Successful` and code SHA-256 `EKhKaF+BoLYVlg/B+22Vmx2nQCvU16iX61ZbZ6M3ueA=`.

### Controlled repeat

The original 15 distinct questions were repeated exactly, each in a fresh frontend session to remove accumulated history as a variable.

- 10 completed.
- 5 failed.
- Failure rate: 33.3%.
- Failed subjects: RAG options, disaster recovery comparison, analytics layers, GenAI workload assessment, and multi-document RAG synthesis.

### Exact failure causes

Four failures had the same confirmed cause:

`organisation_tool_round_limit_exceeded`

The configured maximum is two completed search rounds. On the final allowed iteration, Claude returned `stopReason: tool_use` and requested `search_organisation_sources` again instead of producing the final structured answer. The application correctly stopped the loop, but then returned a generic 503 with no recovery.

| Question | Evidence accumulated | Input tokens | Output tokens | Requested action at failure |
|---|---:|---:|---:|---|
| RAG implementation options | 10 chunks | 7,920 | 192 | A third organisation search |
| Disaster recovery comparison | 15 chunks | 8,977 | 249 | A third organisation search |
| Serverless analytics layers | 10 chunks | 7,418 | 207 | A third organisation search |
| GenAI workload assessment | 10 chunks | 7,854 | 204 | A third organisation search |

The fifth failure was different:

`structured_answer_block_count_invalid`

For the multi-document synthesis question, Bedrock returned `stopReason: end_turn` but the message contained zero content blocks and zero text blocks. The request had already accumulated 15 evidence chunks, consumed 6,630 input tokens and 204 output tokens, and then produced no structured answer for the application to validate.

### Multi-document reproducibility check

The exact multi-document question was repeated three more times in fresh sessions after the finer-grained structured-output diagnostic was deployed:

1. Completed successfully in 20.682 seconds.
2. Failed with `structured_answer_block_count_invalid`: `end_turn`, zero content blocks, 15 evidence chunks, 6,630 input tokens, 204 output tokens.
3. Failed with `organisation_tool_round_limit_exceeded`: requested three more organisation searches at the limit, after accumulating 35 evidence chunks, 17,174 input tokens and 538 output tokens.

This proves the failure is nondeterministic but not unexplained. The same input can complete, terminate with an empty structured response, or continue searching until the application limit is reached.

### Diagnostic conclusion

The failures are not caused by missing PDFs, S3 ingestion, vector storage, or a conversation-history overflow in this controlled repeat. They occur inside the answer orchestration after evidence retrieval:

1. The model keeps requesting additional searches after the allowed search budget is exhausted.
2. Less frequently, the model reports an end turn but returns no structured content block.

No retry behavior had been added at this diagnostic stage. The public failure response remained unchanged while CloudWatch preserved enough detail to select and verify a recovery design. This historical status is superseded by the bounded recovery deployment below.

## Bounded answer recovery deployment and verification — 2026-09-20

The answer orchestrator now stops after the existing two-search budget instead of throwing when the model requests another search. It removes the raw tool-use protocol blocks, supplies the already-retrieved evidence as explicitly untrusted numbered data, and makes exactly one final Bedrock call with tools disabled. The same single bounded recovery is used when Bedrock reports `end_turn` but returns no usable answer content. The recovery never reruns retrieval tools and still applies the existing answer and citation validation before returning a response.

The first recovery deployment exposed a Bedrock request-contract error: a request containing historical `toolUse` or `toolResult` blocks must also include `toolConfig`. Because forced finalization deliberately disables tools, the model call was rejected with a `ValidationException`. The implementation was corrected by creating clean finalization messages containing only conversational text and the retrieved evidence; that corrected version was deployed before acceptance testing.

Verification evidence:

- All 16 API unit tests passed, including tool-budget exhaustion, empty-response recovery, one-attempt-only behavior, recovery failure, tool-block removal, evidence preservation, and structured failure logging.
- The final Lambda deployment completed successfully with code SHA-256 `F1fu8fuFOUNXD8iW9iPYacSoZWDyujMWq4CtlmB86ns=` and AWS `LastUpdateStatus: Successful`.
- The five questions that failed in the diagnostic rerun were repeated exactly in fresh frontend sessions; all five completed successfully.
- CloudWatch recorded five `answer_recovery_succeeded` events, five `answer_completed` events, and zero `answer_failed` events for the corrected-deployment verification window.
- Every answer used `organisation_sources` and retained citations. Citation counts for the five answers were 6, 7, 6, 6, and 14 respectively.

| Previously failing question | Result after fix | Frontend latency | Citations |
| --- | --- | ---: | ---: |
| Main RAG implementation options and differences | Completed | 12.487 s | 6 |
| Backup and restore vs pilot light vs warm standby vs multi-site DR | Completed | 8.418 s | 7 |
| Serverless data analytics pipeline layers and services | Completed | 7.406 s | 6 |
| Generative AI workload assessment before production | Completed | 8.437 s | 6 |
| Multi-document secure and operable AWS RAG architecture | Completed | 14.548 s | 14 |

The correctness failure is mitigated for the reproduced cases, but efficiency remains a follow-up concern. The multi-document recovery used 26,226 total input tokens and 1,239 output tokens because 35 evidence items were carried into finalization. Evidence deduplication, reranking, and a smaller final evidence budget should be evaluated separately without weakening citation grounding.
