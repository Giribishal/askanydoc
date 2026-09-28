# SharePoint official-reference test matrix

> Execute this matrix only under the provider, identity, gates, and approval rules in `SHAREPOINT_RETRIEVAL_SOURCE_OF_TRUTH.md`.

## Document metadata

Every reference record must include: title, official URL, Microsoft product, topic, source type, classification, retrieval date, and review date.

## Query matrix

| ID | Question type | Expected source scope | Expected result |
|---|---|---|---|
| Q01 | Single-source | Approvals reference | Clear approval procedure with Microsoft link |
| Q02 | Single-source | Teams reference | Notification guidance with citation |
| Q03 | Single-source | SharePoint connector reference | Connector capabilities and limits |
| Q04 | Single-source | DLP reference | Governance explanation with citation |
| Q05 | Multi-source | Approvals + SharePoint | Combined workflow grounded in both sources |
| Q06 | Multi-source | Pipelines + environments | Dev/Test/Prod deployment explanation |
| Q07 | Missing answer | No matching reference | Explicitly say the library has insufficient evidence |
| Q08 | Restricted answer as Adele | Senior-only DLP/ALM source | No restricted content or citation exposed |
| Q09 | Restricted answer as Alex | Senior-only DLP/ALM source | Grounded answer with citation |
| Q10 | Citation check | Any approved source | Citation points to the exact official reference |

## Evidence to record

- identity and group used;
- question and timestamp;
- returned answer;
- cited reference URLs;
- allowed/denied decision;
- latency and failure details;
- whether the result met the expected outcome.

## Executed evidence

| Timestamp | Identity | Test | Result | Evidence |
|---|---|---|---|---|
| 2026-09-21 17:50 AEST | Bishal | General semantic question before download fallback | Failed closed | Graph Search found a permitted PDF; metadata omitted the download annotation; no content/citation returned |
| 2026-09-21 17:58 AEST | Bishal | General semantic question after fallback | Pass | Grounded answer; `microsoft-cloud-hybrid-architecture.pdf` pages 1, 2, and 3; Lambda duration 13.4 seconds |
| 2026-09-21 17:43 AEST | Unauthenticated | Protected `/chat` | Pass | HTTP 401; SharePoint tool not exposed |
| 2026-09-21 18:00 AEST | Public AWS path | Known SQS question | Pass | `17-lambda-sqs-partial-batch-responses.pdf`, page 5; client latency 33.7 seconds |
| 2026-09-21 18:32 AEST | Alex (`AlexW@y4m7.onmicrosoft.com`) | Controlled General semantic question | Pass | 3 General-site citations to `microsoft-cloud-hybrid-architecture.pdf` pages 2, 1, and 3; request `ff11e96d-5c4a-4b6d-ad19-012535c1c6e0`; Lambda 11.18 seconds; 6,204 input / 315 output tokens |
| 2026-09-21 18:34 AEST | Alex (`AlexW@y4m7.onmicrosoft.com`) | Controlled Restricted semantic question | Pass | 1 Restricted-site citation to `sharepoint-sites-highly-regulated-data.pdf` page 1; request `576daa3f-96ba-4bc9-9715-e8a735e66977`; Lambda 28.08 seconds; 8,029 input / 604 output tokens |
| 2026-09-21 18:56 AEST | Adele (`AdeleV@y4m7.onmicrosoft.com`) | Same controlled General semantic question | Pass | 3 General-site citations to `microsoft-cloud-hybrid-architecture.pdf` pages 2, 1, and 3; request `e54188f1-1cdc-4523-9b7b-bd7b66d85838`; Lambda 17.08 seconds; 6,204 input / 335 output tokens |
| 2026-09-21 18:56 AEST | Adele (`AdeleV@y4m7.onmicrosoft.com`) | Same controlled Restricted semantic question | Pass (denied/no evidence) | `organisation_not_found`; 0 citations; no Restricted URL or document-derived protection list; request `19ef331f-a7e9-48de-8a49-d8d718daeeb7`; Lambda 13.58 seconds; 7,310 input / 616 output tokens |
| 2026-09-22 13:35 AEST | Adele (`AdeleV@y4m7.onmicrosoft.com`) | Direct SharePoint site access | Pass | General site loaded with Adele shown in the account header; Restricted site returned SharePoint `AccessDenied.aspx` |
| 2026-09-22 13:39 AEST | Adele (`AdeleV@y4m7.onmicrosoft.com`) | Generic SharePoint no-match | Pass | Cafeteria-menu question returned `Organisation sources: no match`, no citations, 3,289 input / 161 output tokens |
| 2026-09-22 13:41–13:43 AEST | Adele (`AdeleV@y4m7.onmicrosoft.com`) | Explicit AWS + SharePoint comparison | Fail (diagnosed) | Prompt hashes match the two requests. First request `1e3327cd-715f-4aaa-a0c3-ee87cbaea03a` completed successfully inside Lambda with 5 citations after 34.22 seconds, beyond the HTTP API's 30-second integration ceiling, so the client received `Service Unavailable`. Retry `69dfd28c-a14f-4632-9e5f-f3dc8a40aa7c` failed after 6.91 seconds with `Only organisation-sourced answers may include citations.`, and the handler returned the controlled generic failure. No successful client-visible comparison was claimed |
| 2026-09-22 13:46 AEST | Local source-tree suite | Malicious document, timeout, throttling cap, extraction byte limit | Pass (contract tests) | Added focused tests; complete current source-tree result: 48 passed plus 6 subtests in 1.63 seconds. These are local failure-boundary tests, not live Microsoft fault injection |
| 2026-09-22 13:48 AEST | Tenant administrator (`Bishal@y4m7.onmicrosoft.com`) | Read-only Entra registration and consent audit | Pass | API is single-tenant; enabled `access_as_user`; delegated `Files.Read.All`, `Sites.Read.All`, and `User.Read` all show `Granted for y4m7`. Frontend is single-tenant with the exact CloudFront SPA redirect and requests only `access_as_user` plus `User.Read`. No change made |
| 2026-09-25 | Local source-tree suite | Deterministic source classification | Pass (local only) | Test first reproduced partial cross-source evidence being rejected because the model paired a valid citation with `organisation_not_found`. The root fix makes the application derive `organisation_sources` from validated citations and `organisation_not_found` from a completed search without cited evidence, with no extra model call. A no-search organisation claim still fails closed. Complete source-tree result: 51 passed plus 6 subtests. This supersedes the undeployed retry-only proposal; no deployment or live success claim |
| 2026-09-25 | Production deployment | Deterministic source classification | Deployed; SharePoint proof pending | Reviewed Terraform plan changed only the local build trigger and updated `askanydoc-api` in place. Lambda update status is successful; deployed code SHA-256 `LcHPpnPfDjL7yM7yXKi68t2YqlSZaNLsHXI+/MbyR4A=` |
| 2026-09-25 | Public AWS path | Known SQS question immediately after deployment | Expected operational failure recorded | Request `3397dcf3-51b6-476c-affe-a25fe2724a3a` returned controlled 503. CloudWatch proves `DatabaseResumingException` while the zero-ACU Aurora instance resumed; Lambda duration 40.10 s. This is tracked as modernization risk `R-001`, not attributed to the source-classification change |
| 2026-09-25 | Public AWS path | Same known SQS question after Aurora resumed | Pass | Client completed in 31.35 s with `organisation_sources`, grounded answer, and the expected `17-lambda-sqs-partial-batch-responses.pdf` page 5 citation |
| 2026-09-25 | Adele (`AdeleV@y4m7.onmicrosoft.com`) | Broad General semantic question after deployment | Pass (safe no-match) | Request `8ea8b1dc-ea29-4359-9e18-95491a545581`; `organisation_not_found`, zero citations, 3,306 input / 241 output tokens; Lambda 20.02 s. Retained as query-sensitivity evidence, not a permission or classification failure |
| 2026-09-25 | Adele (`AdeleV@y4m7.onmicrosoft.com`) | Protected request between General checks | Fail before Lambda; recovered by refresh | Browser received HTTP 401 while still showing Adele signed in. Safe token diagnostics showed the expected issuer, API audience, `access_as_user`, and v1 token. No Lambda invocation occurred. Page/session refresh cleared it; root remains unproven and is tracked as `R-026` |
| 2026-09-25 | Adele (`AdeleV@y4m7.onmicrosoft.com`) | Targeted General document question after session refresh | Pass | Request `8b9d8629-9a67-464b-9b68-08ffc27d2f59`; `organisation_sources`; three citations to `microsoft-cloud-hybrid-architecture.pdf` pages 4, 1, and 2; 6,325 input / 451 output tokens; Lambda 13.94 s |
| 2026-09-25 | Adele (`AdeleV@y4m7.onmicrosoft.com`) | Explicit AWS + SharePoint comparison after root fix | Lambda pass; client timeout retained | Request `f3fb33c0-d173-443d-bf20-6d448f7f2271` completed inside Lambda in 38.78 s with `organisation_sources`, five citations, 7,556 input / 552 output tokens. Browser received `Service Unavailable` because the response exceeded the 30-second HTTP API boundary. The prior source-mode/citation defect did not recur |
| 2026-09-26 | Adele (`AdeleV@y4m7.onmicrosoft.com`) | Fresh explicit AWS + SharePoint comparison with Aurora paused | Expected infrastructure failure recorded | Request `5fbe7886-113e-44f6-acba-fc702aa03972` failed after 42.77 s with `DatabaseResumingException` while Aurora resumed. This is R-001, not a SharePoint permission failure |
| 2026-09-26 | Adele (`AdeleV@y4m7.onmicrosoft.com`) | Immediate warmed repeat of the same comparison | Lambda pass; client timeout reproduced | Request `67423134-94a0-4539-bb94-ed0a6e44cd1c` completed in 43.55 s with `organisation_sources` and five citations; the browser still received `Service Unavailable`, proving the 30-second transport boundary is the remaining client-visible cause |
| 2026-09-26 | Local implementation suite | Asynchronous answer job API, worker, expiry, ownership, failure, duplicate, Aurora retry, existing API and SharePoint regressions | Pass (local; not deployed) | 11 focused asynchronous/retry tests and 55 complete API/SharePoint tests passed. Frontend lint and production build passed; temporary polling `429`/`5xx` responses are retried; Terraform 1.16.3 validation passed. Exact saved plan awaits final apply approval |
| 2026-09-27 12:06–12:08 AEST | Adele (`AdeleV@y4m7.onmicrosoft.com`) | First production asynchronous AWS + SharePoint comparison from an Aurora-paused state | Transport pass; controlled answer failure | Job `8710fbc1-c644-44bd-9d0d-b40b966e9b46` was created in 235.76 ms and the browser polled for about 90 seconds, proving the asynchronous transport beyond the former 30-second boundary. Worker request `73e1a631-0248-5a48-9a92-c5037e1e54a2` failed after 88.40 s with `DatabaseResumingException`; the UI showed a controlled error and request ID. SQS and its DLQ were empty afterward, and Aurora capacity moved from 0 to 0.5 ACU. No answer or citations were returned, so the end-to-end acceptance gate failed. |
| 2026-09-28 | Local source tree | Bounded cross-invocation Aurora-resume recovery | Pass locally; deployment pending | Test-first worker recovery makes only `DatabaseResumingException` retryable, releases the owner-bound job lease, delays only the failed SQS message for 15/30 seconds, and caps processing at three total attempts. Five focused worker tests, 35 API tests, and 22 SharePoint tests passed; Python compilation and Terraform validation passed. A targeted read-only Terraform preview showed one local packaging-trigger replacement and five in-place queue/IAM/event-mapping/Lambda updates, with no apply. |
| 2026-09-28 11:47 AEST | Adele (`AdeleV@y4m7.onmicrosoft.com`) | Varied cold AWS disaster-recovery + SharePoint hybrid-cloud comparison | Pass end to end | Job `274b655d-f13d-4219-83b2-96f60d8ed3b9`, worker request `c0fc002f-3934-58f2-a30b-631cf07b4976`, returned `organisation_sources` to the browser with five citations to `13-disaster-recovery-workloads-on-aws.pdf` pages 14, 15, 5, 13, and 35 and three citations to `microsoft-cloud-hybrid-architecture.pdf` pages 1–3. Aurora was 0 ACU before the request. The job completed on attempt one in 47 wall-clock seconds; worker duration 44.43388 s, billed 47.021 s, maximum memory 170 MB; 7,723 input / 741 output tokens. Estimated Claude Haiku 4.5 plus worker compute cost was about USD $0.013, excluding negligible ancillary requests and short Aurora-capacity time. |

The core Adele/Alex permission matrix is complete and passed. The source-classification root fix, asynchronous transport, and bounded Aurora-resume recovery are deployed. A varied cold production comparison now proves a browser-visible grounded answer across AWS and SharePoint beyond the former 30-second boundary. The live request resumed Aurora and completed on attempt one, so the slower cross-invocation retry remains locally test-proven rather than live-triggered. No alert or further production change is authorized without fresh explicit approval. The transient pre-Lambda 401 remains an explicit operational risk. The broader Q01–Q10 content suite and live fault/limit observations remain open.

The first Alex query included filename/site wording and returned no match (request `970f38f8-abb3-40f2-be81-42253d8624b0`, 8.68 seconds). This is retained as query-sensitivity evidence and was not counted as an authorization failure; the controlled questions above were held constant across Alex and Adele.
