# AskAnyDoc SharePoint integration — architecture and delivery plan

**Status:** historical planning baseline; implementation now exists but the permission matrix and deployment reconciliation remain incomplete
**Reviewed:** 2026-09-21
**Purpose:** add permission-aware SharePoint retrieval to the AWS-hosted AskAnyDoc assistant without copying the whole SharePoint tenant or inventing a second authorization system.

> **Superseding execution note — 2026-09-21:** Read `SHAREPOINT_RETRIEVAL_SOURCE_OF_TRUTH.md` for the current decision, state, gates, approval boundaries, and next action. Microsoft 365 Copilot Retrieval is the agreed SharePoint grounding provider. Graph Search is retained only as an explicit diagnostic/entitlement fallback, not as a prerequisite baseline. Query-time site scoping plus response URL filtering is mandatory. Entitlement/licensing or pay-as-you-go billing, delegated consent, and the two-user permission matrix remain activation gates. Retain the remainder of this file as the original delivery plan.

## 1. Capability and first proof

An employee signs in to AskAnyDoc with Microsoft Entra ID and asks about organisation information. AskAnyDoc searches SharePoint in that employee's delegated identity, receives only evidence that employee may read, asks Claude on Amazon Bedrock to answer from it, and returns citations to the original SharePoint items.

The first vertical slice must prove:

1. `Employee Test` and `Senior Test` can sign in.
2. Both can retrieve and cite a general-site document.
3. Only `Senior Test` can retrieve or cite a restricted-site document.
4. `Employee Test` receives no restricted title, snippet, URL, or answer for the same question.
5. Existing S3/Aurora retrieval continues to work.
6. One cross-source question can use both source tools and cite both correctly.
7. Authentication, retrieval, answer, citation, failure, latency, token, and external-call evidence is observable without logging tokens or document contents.

Not in the first slice:

- SharePoint write, upload, sharing, or deletion actions;
- copying all SharePoint files to S3/Aurora;
- a second SharePoint ACL database;
- delta sync, change notifications, or background ingestion;
- OneDrive;
- real employer data or production claims;
- GDAP, which is partner administration rather than employee authorization.

## 2. Architecture decision

### Historical preferred target — Microsoft 365 Copilot Retrieval API

Use:

```text
POST https://graph.microsoft.com/v1.0/copilot/retrieval
```

Microsoft performs query transformation and hybrid retrieval over its Microsoft 365 index, returns relevant extracts, and security-trims them for the signed-in user. AskAnyDoc does not download every file, chunk it, create Titan embeddings, or synchronize SharePoint permissions into Aurora.

This is the preferred provider because Microsoft positions it for grounding custom generative-AI applications without maintaining a separate index.

### Entitlement gate

The developer tenant currently has Microsoft 365 E5 Developer licences but no verified Microsoft 365 Copilot licence. Retrieval API use must be proven with one harmless request before selection. Pay-as-you-go use for non-Copilot users is currently preview, requires eligible Azure/Microsoft billing and at least one Copilot licence in the tenant, and is charged per API call.

### Development fallback — Microsoft Graph Search

If Retrieval API access is blocked only by entitlement, use delegated Microsoft Graph Search for the first slice. It still searches in the signed-in user's context, but it is a lower-level search interface rather than Microsoft's RAG-focused retrieval interface. AskAnyDoc might need to fetch a small bounded set of permitted files and extract their text.

This is one replaceable provider behind the same adapter contract, not a second architecture. When Retrieval API access becomes available, swap providers and rerun the same tests.

### Deferred — external SharePoint vector index

Do not start with Azure AI Search indexing or an AWS SharePoint ingestion pipeline. Those add file/version/deletion synchronization, ACL synchronization, permission-filtered retrieval, duplicate storage, and reconciliation. Microsoft's current Azure AI Search guidance points permission-sensitive RAG toward a remote SharePoint knowledge source backed by Retrieval API; traditional ACL indexing has more complexity and preview elements.

Reconsider external indexing only when measurement proves a named latency, recall, availability, cost, or cross-source-ranking limitation.

| Question | Decision |
|---|---|
| Where do SharePoint files remain? | SharePoint. |
| Who searches them? | Retrieval API; Graph Search only as entitlement fallback. |
| Who authorizes the result? | Microsoft using the signed-in user's delegated permissions. |
| Titan embeddings for SharePoint? | No. |
| SharePoint text in Aurora? | No, not in this slice. |
| Who chooses the tool? | Claude may request one; application code validates and executes it. |
| Who generates the answer? | Claude Haiku 4.5 on Bedrock. |
| Who builds citations? | AskAnyDoc from provider provenance, never Claude-authored URLs. |
| Remove existing S3 RAG? | No; it remains another source adapter. |

## 3. Two different data flows

Existing S3 is **ingest first, search later**:

```text
Upload -> extract -> chunk -> Titan embeddings -> Aurora pgvector
Question -> Titan embedding -> Aurora search -> Claude -> citations
```

SharePoint is **search live as the employee**:

```text
Employee question -> Microsoft permission-aware retrieval -> evidence extracts
                  -> Claude -> SharePoint citations
```

There is no SharePoint ingestion Lambda in the preferred architecture.

## 4. Target architecture

```text
React + MSAL Browser
  -> Entra authorization code + PKCE
  -> AskAnyDoc API access token
  -> HTTPS
Amazon API Gateway HTTP API
  -> JWT validation: signature + tenant issuer + API audience + expiry + scope
  -> validated claims
Answer Lambda
  -> Claude selects search_aws_documents and/or search_sharepoint
  -> SharePoint adapter performs Entra on-behalf-of exchange
  -> delegated Microsoft Graph token
Microsoft provider
  -> preferred: Copilot Retrieval API
  -> fallback: Graph Search API
  -> Microsoft permission trimming
  -> extracts + source provenance
Answer Lambda
  -> common evidence contract
  -> Claude grounded answer
  -> evidence-number validation
  -> application-built citations
React
  <- answer + citations
```

Trust boundaries:

1. The browser is untrusted and cannot choose identity, permissions, or citation provenance.
2. API Gateway accepts only an Entra access token issued for this tenant, API audience, and scope.
3. Lambda exchanges the API token through OBO; it never trusts a user ID in request JSON.
4. Microsoft decides which SharePoint evidence the delegated user may read.
5. Retrieved text is untrusted data, not instructions.
6. Application code constructs citations only from evidence actually returned and supplied to Claude.

## 5. Stack and responsibilities

| Layer | Technology | Responsibility |
|---|---|---|
| UI | Existing React + Vite | Chat, sign-in/out, authenticated request, citations. |
| Browser identity | `@azure/msal-browser`, `@azure/msal-react` | Authorization code + PKCE and AskAnyDoc API tokens. |
| Identity | Microsoft Entra ID | Users, groups, app registrations, delegated tokens. |
| HTTPS frontend | CloudFront + private S3 + Origin Access Control | Secure SPA origin and redirect URI. |
| API ingress | API Gateway HTTP API | `/chat`, JWT authorizer, scope, CORS, throttling. |
| Compute | Existing Python 3.13 Answer Lambda | OBO, tools, providers, evidence, validation. |
| Answer model | Claude Haiku 4.5 through Bedrock Converse | Tool choice and grounded synthesis. |
| AWS documents | Titan V2 + Aurora pgvector | Existing application-owned source. |
| Microsoft token library | MSAL Python | OBO exchange and supported token caching. |
| SharePoint retrieval | Copilot Retrieval API v1.0 | Microsoft-managed RAG retrieval and security trimming. |
| Fallback | Microsoft Graph Search v1.0 | Delegated search and bounded content fetch. |
| Secrets | AWS Secrets Manager | Confidential API credential and rotation metadata. |
| IaC | Terraform | AWS boundary, config, IAM, logs, alarms. |
| Observability | CloudWatch + existing Langfuse | Operational events and model traces without raw content. |

Deliberately not added:

- Cognito: Entra already supplies the organisation identity.
- another vector database: unnecessary for live SharePoint retrieval;
- a connector framework: one thin provider is enough;
- MCP in this application slice: direct Microsoft REST APIs demonstrate the service integration. A separate MCP learning slice can follow after its exact supported tools are verified.

## 6. Microsoft test tenant

Use only synthetic accounts and documents.

| Identity/group | General site | Restricted site |
|---|---:|---:|
| `Employee Test` | Read | None |
| `Senior Test` | Read | Read |
| `AskAnyDoc-General-Readers` | Read | None |
| `AskAnyDoc-Senior-Readers` | Optional | Read |

Create:

```text
AskAnyDoc-General/Shared Documents/
  General Remote Work Policy.docx
  Shared Incident Escalation.pdf

AskAnyDoc-Restricted/Shared Documents/
  Leadership Budget Decision.docx
  Restricted Acquisition Plan.pdf
```

Each file contains one unique harmless fact. Record expected answers before testing. Use Entra groups and normal SharePoint permissions; do not encode `employee` or `senior` roles inside AskAnyDoc.

### App registration A — `askanydoc-spa-dev`

- Single tenant.
- Type: SPA/public client.
- Redirects: local Vite origin and deployed HTTPS CloudFront origin only.
- Authorization code + PKCE; no legacy implicit flow.
- No client secret.
- Delegated permission to the API's `access_as_user` scope.

### App registration B — `askanydoc-api-dev`

- Single tenant.
- Type: confidential web API.
- Expose Application ID URI and delegated `access_as_user` scope.
- Preferred Retrieval API delegated Graph permissions: `Files.Read.All` and `Sites.Read.All`.
- No application permissions in the first slice.
- Development credential: short-lived client secret stored only in Secrets Manager, with owner and expiry.
- Company target: evaluate certificate or supported workload federation.
- Record exact admin consent, owner, tenant, scopes, date, and reason.

These are broad delegated scopes, but effective access remains the intersection of app consent and the signed-in user's permissions. Keep them in the isolated developer tenant and review production consent separately.

### Authentication sequence

1. Browser signs in with Entra authorization code + PKCE.
2. Browser obtains an access token for AskAnyDoc API, not Microsoft Graph.
3. Browser calls API Gateway with `Authorization: Bearer ...` over HTTPS.
4. API Gateway validates signature, tenant issuer, API audience, time claims, and `access_as_user`.
5. Lambda reads validated claims from the authorizer context.
6. Only when SharePoint is needed, Lambda uses MSAL OBO with the incoming API token.
7. Entra issues a Microsoft Graph token for the same user.
8. Lambda calls the chosen retrieval provider.
9. Microsoft applies the user's SharePoint access.

Never use an ID token as API authorization, accept a Graph token at the AskAnyDoc API, use password grant, or place the API secret in React.

## 7. AWS configuration

### HTTPS frontend first

The current S3 website uses HTTP. Before deployed Microsoft sign-in:

1. Put CloudFront before a private S3 origin.
2. Use Origin Access Control; remove public-read dependence.
3. Redirect HTTP to HTTPS.
4. Initially use the CloudFront HTTPS domain; add custom DNS/certificate only when needed.
5. Register that exact origin in Entra.
6. Frontend configuration contains only public tenant/client/scope/API identifiers.

### Protected API

- API Gateway HTTP API route: `POST /chat`.
- Integration: existing Answer Lambda.
- Issuer: tenant-specific Entra v2 issuer, never `/common`.
- Audience: the actual `aud` observed in an AskAnyDoc API access token.
- Required scope: `access_as_user`.
- CORS: exact local and CloudFront origins; headers `authorization`, `content-type`.
- Conservative measured throttling.
- Access logs exclude headers and bodies.

Retain the Function URL only for temporary rollback. Remove public Function URL permissions after authenticated deployment passes.

### Secret and environment contract

Secrets Manager secret: `askanydoc/entra-api-credential-dev`. Terraform creates the container/reference; the value is supplied outside committed files. Lambda receives read access to this one secret only.

Non-secret environment values:

```text
ENTRA_TENANT_ID
ENTRA_AUTHORITY=https://login.microsoftonline.com/<tenant-id>
ENTRA_API_CLIENT_ID
ENTRA_API_SCOPE=api://<api-client-id>/access_as_user
ENTRA_GRAPH_SCOPES=https://graph.microsoft.com/.default
ENTRA_CREDENTIAL_SECRET_ID
SHAREPOINT_PROVIDER=copilot_retrieval | graph_search
MICROSOFT_GRAPH_BASE_URL=https://graph.microsoft.com/v1.0
SHAREPOINT_ALLOWED_PATHS=<optional application-owned allowlist>
SHAREPOINT_MAX_RESULTS
SHAREPOINT_TIMEOUT_SECONDS
SHAREPOINT_MAX_RETRIES
```

No token, client secret, or private key belongs in documentation, React, Terraform variables, Git, logs, or traces.

## 8. Planned code/file structure

```text
app/api/
  answer_lambda_handler.py        HTTP validation + authenticated context
  assistant_orchestrator.py       Claude tool loop + final validation
  organisation_tools.py           tool schemas + dispatch
  retrieval.py                    existing Aurora retrieval
  evidence.py                     source-neutral evidence/citation model
  microsoft_identity.py           OBO only
  sharepoint_source.py            provider interface + normalization
  copilot_retrieval_provider.py   preferred provider
  graph_search_provider.py        entitlement fallback

frontend/src/
  authConfig.js                   public Entra configuration
  AuthenticatedApp.jsx            sign-in boundary
  apiClient.js                    token acquisition + `/chat`
  App.jsx                         existing chat

infra/
  frontend_delivery.tf            CloudFront + private S3/OAC
  api_gateway.tf                  HTTP API + JWT authorizer
  entra_secret.tf                 secret container + IAM read
  answer_lambda.tf                package modules + environment
```

Add matching unit tests for identity, provider, normalization, tools, orchestrator, handler, and frontend auth/API behaviour.

### Source-neutral evidence

The current shape assumes S3 object keys and vector similarity; SharePoint may provide neither. Use:

```text
evidence_number
source_system        aws_documents | sharepoint
source_type
source_name
source_uri
location             page/section/path/null
text
rank
score                number/null
tenant_id            internal only
site_id              internal provenance
drive_id             internal provenance
item_id              internal provenance
etag_or_version
last_modified
authorization_subject  hash(tenant + user object id)
retrieved_at
```

Only answer-relevant fields go to Claude. Identity, tokens, and authorization internals do not.

### Tool contract

```text
search_aws_documents(query)
search_sharepoint(query, optional_application_scope)
```

Separate tools make source choice, calls, latency, failures, and citations inspectable. A cross-source question may invoke both within bounded tool rounds. Tools do not accept arbitrary endpoints, URLs, tenant IDs, tokens, KQL, drive IDs, or item IDs from the model/user. Any site filter is produced from an application allowlist.

## 9. Exact request orchestration

1. React asks MSAL for an AskAnyDoc API access token.
2. React sends question and bounded history to API Gateway.
3. API Gateway rejects missing, expired, wrong-issuer, wrong-audience, or missing-scope tokens.
4. Lambda creates request-scoped auth context from verified claims; body-supplied identity is ignored.
5. Claude receives conversation plus narrow tool schemas.
6. Claude answers ordinary conversation/general knowledge without a source call.
7. Claude requests AWS, SharePoint, or both tools for organisation questions.
8. SharePoint tool requires authenticated context.
9. `microsoft_identity.py` reads the incoming API token from request context, not tool arguments.
10. MSAL exchanges it through OBO using the Secrets Manager credential.
11. The Graph token stays in memory and is never logged/returned.
12. Preferred provider calls `/v1.0/copilot/retrieval` with fixed SharePoint data source, one bounded natural-language query, bounded results, and only application-owned optional filters.
13. Microsoft applies query transformation, hybrid retrieval, tenant policy, and user permissions.
14. Provider handles `401`, `403`, `429`, `5xx`, timeout, and invalid response separately.
15. Transient retry is bounded by the request deadline, honours `Retry-After`, and uses jitter; authorization denials are not retried.
16. Provider normalizes extracts/provenance into common evidence.
17. Under Graph fallback, search returns delegated `driveItem` hits; if snippets are insufficient, fetch only a small bounded set of already permitted items and reuse the relevant extractor without persisting/embedding/indexing.
18. Evidence is bounded, deduplicated, numbered across sources, and labelled untrusted.
19. Claude writes a structured answer and selects evidence numbers.
20. Existing validation rejects unknown numbers, uncited organisation answers, unsupported citations, and empty output.
21. Application maps valid numbers to citations from stored provenance.
22. SharePoint citation uses the provider web URL, not a temporary tokenized link.
23. Opening a citation causes SharePoint to authorize the user again.
24. Model-output recovery reuses evidence and never silently reruns a paid retrieval call.

## 10. Security and failure requirements

First-slice controls:

- single-tenant registrations;
- PKCE SPA flow;
- access token and required API scope;
- tenant-specific issuer and exact audience;
- delegated Graph permissions only;
- OBO in backend;
- fixed provider hosts and bounded inputs/results/timeouts;
- no tokens, secrets, raw questions, document text, or restricted URLs in logs;
- no shared retrieval cache in the first slice;
- retrieved instructions treated as prompt-injection data;
- application-built citations;
- exact CORS origins;
- credential expiry/rotation owner and alert.

| Threat/test | Required result |
|---|---|
| Employee asks for restricted plan | No restricted title, snippet, URL, or answer. |
| Employee guesses item URL/ID | Microsoft denial; no metadata leak. |
| Body supplies another user ID | Ignored/rejected. |
| Graph token sent to AskAnyDoc | Wrong-audience rejection. |
| ID token sent | Scope/audience rejection. |
| Token from another tenant | Issuer rejection. |
| Document contains malicious instruction | Treated only as data. |
| Claude invents evidence number/URL | Validator/application citation boundary rejects it. |
| Permission removed | Next live query no longer returns evidence. |

Error taxonomy:

```text
auth_missing | auth_invalid_issuer | auth_invalid_audience | auth_expired
auth_missing_scope | obo_consent_required | obo_invalid_assertion
obo_credential_expired | sharepoint_not_entitled | sharepoint_forbidden
sharepoint_throttled | sharepoint_timeout | sharepoint_upstream_error
sharepoint_response_invalid | sharepoint_no_evidence
evidence_normalization_failed | answer_validation_failed
citation_validation_failed
```

A permission denial must never be described as proof that a document does not exist.

Log only request ID, hashed tenant/user, tool/provider, call count, status category, stage latency, result/evidence/citation counts, source mode, Bedrock tokens, retry count, and terminal error code. Never log bearer tokens, secrets, raw questions/evidence, full restricted URLs, or Graph bodies.

Retry rules:

- no loops on consent, credential, or `403` errors;
- small bounded retries for transient Microsoft responses, respecting `Retry-After`;
- at most one valid token refresh path for expiry;
- retain controlled Bedrock finalization recovery without rerunning tools;
- UI offers explicit retry rather than silently repeating a paid call.

Metrics: retrieval attempts/successes, authorization/entitlement failures, throttles, timeouts, empty-evidence rate, latency, evidence/citations, terminal answers, and Retrieval API call count. Set alarm thresholds after measuring a baseline.

## 11. Cost and limits

Before paid enablement, re-verify current licensing, price, preview/SLA status, query/result/rate limits, and supported file types. Currently documented facts include:

- Retrieval API access for appropriately licensed Copilot users;
- pay-as-you-go preview for eligible unlicensed users at USD 0.10/API call;
- maximum 25 results and one data source per request;
- per-user throttling and bounded query length;
- no production SLA for pay-as-you-go preview.

Controls:

- normally one provider call per focused search;
- separate tool-round and SharePoint-call limits;
- no paid-call retry for model schema validation;
- call count per request/user hash;
- Microsoft/Azure budget before pay-as-you-go;
- separate Microsoft retrieval and Bedrock token cost reporting;
- bounded/deduplicated evidence with measured quality before compression.

## 12. Delivery phases

Each phase ends in recorded evidence, not configuration claims.

### Phase 0 — design and baseline

1. Approve this document or record changes.
2. Record current AWS deployment/tests/public boundaries and unrelated Git changes.
3. Confirm synthetic data only.
4. Record tenant ID/domain, sandbox state, and licences without secrets.
5. Make one harmless Retrieval API entitlement test after consent is configured.
6. Select `copilot_retrieval`, or select `graph_search` only with a recorded entitlement blocker.

Exit: decision record, entitlement result/time, provider/reason, workspace baseline.

### Phase 1 — permission test world

1. Create/verify two users and two groups.
2. Create two sites/libraries and four documents.
3. Assign permissions through groups.
4. Manually sign in as both users and prove the access matrix.
5. Confirm Employee cannot discover/open restricted content.

Exit: safe site/library IDs, membership matrix, document/question manifest, direct-access evidence.

### Phase 2 — identity boundary

1. Create SPA and API registrations.
2. Expose and grant `access_as_user`.
3. Configure redirects and single-tenant settings.
4. Add exact delegated Graph permissions and admin consent.
5. Create short-lived development credential.
6. Put it in Secrets Manager and record rotation owner/date.
7. Unit-test claim/audience handling with synthetic tokens/claims.

Exit: redacted config, permissions/consent record, secret reference/expiry, no secret leakage.

### Phase 3 — Microsoft retrieval smoke test without Claude

1. Build the smallest local OBO/provider harness.
2. Obtain an AskAnyDoc API token through supported interactive sign-in for each user.
3. Exchange via OBO and call the provider.
4. Run the same general/restricted queries for both users.
5. Inspect extracts, provenance, URLs, latency, limits, and error shape.
6. Prove zero restricted metadata for Employee.
7. Record actual fields safe for evidence/citations.

Exit: four-query permission matrix, redacted response shape, latency/calls, security-trimming result, error evidence.

Stop if delegated context is absent or restricted metadata leaks.

### Phase 4 — authenticated HTTPS boundary

1. Add CloudFront/private S3/OAC.
2. Add API Gateway `/chat` and Entra JWT authorizer.
3. Set exact CORS and pass claims to Lambda.
4. Test missing/invalid/expired/wrong-tenant/wrong-audience/wrong-scope tokens.
5. Verify existing assistant path through protected API.
6. Remove public Function URL permissions after rollback confidence.

Exit: HTTPS UI/API, auth rejection matrix, authorized smoke test, Terraform validation/plan/deployment evidence.

### Phase 5 — provider and orchestration integration

1. Introduce source-neutral evidence.
2. Adapt Aurora results without changing existing behaviour.
3. Add OBO service and safe errors.
4. Add selected SharePoint provider and normalization.
5. Add AWS/SharePoint tools and bounded multi-source use.
6. Update nullable score/provenance citation validation.
7. Ensure model recovery never reruns retrieval.

Exit: new and existing backend tests green; mocked auth/failure tests; acceptable Lambda package/runtime.

### Phase 6 — normal-user frontend

1. Add MSAL public config and sign-in/out UI.
2. Acquire API token silently when possible, interactively when required.
3. Call protected `/chat` with bearer token.
4. Handle consent, expiry, unauthorized, unavailable, and no-evidence states.
5. Clear chat/history when user changes or signs out.
6. Render source-aware citations without internal IDs.

Exit: both users work through deployed UI; no bundle secret; user-switch isolation; AWS/SharePoint paths pass.

### Phase 7 — evaluation and operational proof

1. Run two-user permission matrix.
2. Run general, restricted, missing, AWS-only, and cross-source questions.
3. Test auth failures, removed permission, guessed item, deletion/move, timeout, throttle, upstream/malformed response, prompt injection, invented citation, and empty model output.
4. Verify citation open/deny behaviour.
5. Record retrieval/total latency, Microsoft calls, evidence, Bedrock tokens, citations, and estimated cost.
6. Compare providers using the same questions when entitlement permits.
7. Run frontend lint/build, Python tests, Terraform format/validate/plan, and deployed smoke tests.
8. Update issues, README, architecture, and evaluation report.

Exit: versioned evaluation, zero restricted leakage, citation report, failure results, cost/latency baseline, limitations and rollback.

### Phase 8 — evidence-based next increment

Choose only after Phase 7: keep Retrieval API, replace Graph fallback, add OneDrive, add a verified MCP learning slice, add Snowflake, or investigate indexing for a measured limitation.

## 13. Acceptance matrix

| Case | Source | Expected result |
|---|---|---|
| Greeting | None | Conversation; no Microsoft call. |
| General knowledge | None | General answer; no Microsoft call. |
| General SharePoint fact / either user | SharePoint | Grounded answer + general citation. |
| Restricted fact / Senior | SharePoint | Grounded answer + restricted citation. |
| Restricted fact / Employee | SharePoint | No restricted evidence; safe not-found/neutral limitation. |
| Existing S3 fact | AWS | Existing grounded answer + S3 citation. |
| Cross-source comparison | Both | Only retrieved evidence cited. |
| Missing organisation fact | Relevant tool(s) | `organisation_not_found`; no invention. |
| Wrong tenant/audience/ID token | None | Rejected before Lambda. |
| Permission removed | SharePoint | Next request has no old evidence. |
| Prompt injection | SharePoint | Not followed. |
| Throttle | SharePoint | Bounded retry + safe response + event. |
| Repeated model searches | Bounded tools | Forced finalization prevents unbounded calls. |
| Malformed model output | No tool rerun | One controlled recovery with existing evidence. |

## 14. Definition of done and rollback

Done means HTTPS + Entra sign-in, protected API, OBO delegated retrieval, correct two-user differences with zero restricted leakage, AWS/SharePoint/cross-source answers and application-built citations, green tests, observable failures, no secret/token/content leakage, cost/latency/call/token/citation evidence, updated documentation, and Bishal able to explain authentication, authorization, retrieval, generation, and citations.

Rollback:

1. Disable SharePoint tool by feature flag without removing AWS retrieval.
2. Disable registrations or revoke credential/consent if unsafe.
3. Route to last known protected API build.
4. Never restore public SharePoint capability through the Function URL.
5. Preserve redacted request IDs/results for diagnosis.

## 15. Official references

Checked 2026-09-20; recheck version-sensitive details before implementation or payment.

- Retrieval API overview: https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/api/ai-services/retrieval/overview
- Retrieval API v1.0 reference: https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/api/ai-services/retrieval/copilotroot-retrieval
- Copilot API security: https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/copilot-apis-security-authentication
- Microsoft agent best practices: https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/declarative-agent-best-practices
- Retrieval pay-as-you-go: https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/api/ai-services/retrieval/paygo-retrieval
- OAuth OBO: https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-on-behalf-of-flow
- MSAL flows: https://learn.microsoft.com/en-us/entra/identity-platform/msal-authentication-flows
- Graph delegated access: https://learn.microsoft.com/en-us/graph/auth-v2-user
- Graph Search overview: https://learn.microsoft.com/en-us/graph/search-concept-overview
- Graph Search query: https://learn.microsoft.com/en-us/graph/api/search-query?view=graph-rest-1.0
- Graph permissions: https://learn.microsoft.com/en-us/graph/permissions-overview
- Azure AI Search SharePoint guidance: https://learn.microsoft.com/en-us/azure/search/search-how-to-index-sharepoint-online
- Azure AI Search SharePoint ACL guidance: https://learn.microsoft.com/en-us/azure/search/search-indexer-sharepoint-access-control-lists
- Copilot development environment: https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/prerequisites
- API Gateway JWT authorizer: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-jwt-authorizer.html
- CloudFront OAC: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html

## 16. First action after approval

Do not begin by editing Claude or adding Graph calls to Lambda. Begin with Phase 1: create the two test users/groups/sites and four synthetic documents, then manually prove the SharePoint access matrix. Next create the two app registrations and prove delegated retrieval outside the assistant. This order makes failures diagnosable: SharePoint permissions first, then identity/OBO, then retrieval, then AWS integration, then Claude orchestration.
