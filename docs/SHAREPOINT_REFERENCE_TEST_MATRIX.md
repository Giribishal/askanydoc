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

The Adele/Alex rows remain mandatory and incomplete.
