# AskAnyDoc Hybrid Assistant Architecture

> **SharePoint execution authority:** The source-neutral orchestration described here does not select or authorize a Microsoft provider. Follow `SHAREPOINT_RETRIEVAL_SOURCE_OF_TRUTH.md` for the current provider, evidence state, gates, and approval rules.

## Product contract

AskAnyDoc is a general Claude assistant with controlled access to organisation-owned tools.
It is not a document search box and it must not treat general conversation as a failed search.

For every response, the API identifies the source mode:

| Source mode | Meaning |
|---|---|
| `conversation` | Social or conversational response; no factual source claim |
| `general_knowledge` | Claude answered from model knowledge, not organisation information |
| `organisation_sources` | The answer relies on retrieved organisation evidence and must cite it |
| `organisation_not_found` | The user requested organisation information but sufficient evidence was unavailable |

## Current request flow

```text
Browser sends current message + bounded recent history
                         |
                         v
                  Answer Lambda
             validates size and roles
                         |
                         v
                Claude on Bedrock
              /                  \
     answer normally        request organisation tool
                                  |
                                  v
                  search_aws_documents
                     Titan question embedding
                              |
                     Aurora pgvector search
                              |
                  text + immutable provenance
                              |
                              v
                 Claude writes final answer
                              |
             application validates evidence numbers
                              |
          application builds citations from database fields
```

Claude decides whether a tool is needed. The application executes tools, applies limits, and
owns permissions. Claude never receives AWS credentials and cannot directly query Aurora.

## Citation guarantee

The retrieval tool assigns a number to each returned evidence record. Claude may select those
numbers in its structured response. The application rejects unknown numbers and refuses to
label an answer `organisation_sources` without at least one valid citation. Citation filenames,
URIs, locations, and similarity values are copied from stored provenance, never model-authored.

Retrieved text is untrusted reference data. System instructions explicitly prohibit following
instructions found inside documents. A later company deployment must add guardrail and adversarial
testing rather than treating a prompt instruction alone as complete protection.

## Conversation boundary

The browser sends up to 12 recent user/assistant messages and at most 12,000 history characters.
This enables natural follow-ups while bounding latency and token cost. The current history is
browser-session state: it is neither persistent nor a secure user memory system.

Persistent memory requires authentication, server-owned conversation IDs, per-user authorization,
retention rules, deletion, encryption, and audit controls. Do not store trusted memory based only
on the current public client-supplied history.

## Adding future organisation capabilities

New systems should enter through narrow tools, for example:

```text
search_aws_documents(query)
search_sharepoint(query, site_scope)
query_business_database(approved_query)
create_support_ticket(validated_fields)
```

Every tool requires its own input schema, least-privilege identity, authorization check, timeout,
result-size limit, audit event, error contract, and tests. A connector does not automatically
provide semantic search, RAG, or permission-safe retrieval.

## Delivery gates toward company use

### Gate 1 — hybrid core (current feature)

- Claude-led conversation and tool choice
- custom S3/Titan/Aurora retrieval tool
- bounded recent history
- structured source mode
- application-built citations
- privacy-conscious logs and tracing

### Gate 2 — measured reliability

- golden question set and failure taxonomy
- retrieval threshold and result-count calibration
- groundedness, citation, refusal, latency, and cost measurements
- prompt and model regression tests

### Gate 3 — secure users and data

- API Gateway plus organisation identity provider/Cognito
- user, group, tenant, and document-level authorization
- ACL metadata propagated through ingestion and filtered during retrieval
- WAF, quotas, throttling, abuse controls, and Bedrock Guardrails
- secrets, encryption, retention, deletion, and audit policies

### Gate 4 — protected attachments, durable conversations, and more sources

- separate temporary chat attachments from persistent organisation sources
- direct-to-S3 uploads using short-lived, narrowly scoped upload requests
- format, size, integrity, malware, retention, and deletion controls
- multimodal Claude input for supported images and documents
- extraction adapters for email files and other unsupported formats
- server-owned conversation/session storage
- authorized SharePoint/Microsoft 365 and other source adapters
- source sync, deletion propagation, freshness, and reconciliation
- explicit tool permission and confirmation policy for write actions

### Gate 5 — operational scale and governance

- separate development, staging, and production accounts/environments
- CI/CD with security and evaluation gates
- dashboards, alarms, distributed traces, SLOs, and incident runbooks
- queues, concurrency strategy, backpressure, disaster recovery, and cost budgets
- model lifecycle reviews and configuration-driven model migration

The current public Function URL and shared source collection are suitable only for the learning
demo. They are not an authorization boundary for confidential company data.
