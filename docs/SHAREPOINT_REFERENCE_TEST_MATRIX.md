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

The core Adele/Alex permission matrix is complete and passed. Still open: the broader Q01–Q10 content suite, a generic missing-answer case independent of access control, malicious-document instructions, throttling, timeout, extraction-limit, and direct isolated SharePoint-site navigation evidence.

The first Alex query included filename/site wording and returned no match (request `970f38f8-abb3-40f2-be81-42253d8624b0`, 8.68 seconds). This is retained as query-sensitivity evidence and was not counted as an authorization failure; the controlled questions above were held constant across Alex and Adele.
