# Shared answers across extensible sources

**Current checkpoint, 4 October 2026:** Bishal approved the exact protected-path impact. Three-source AWS + SharePoint + Salesforce synthesis is now deployed and visibly tested, including all three citation groups and bounded CRM coverage. AWS-only, SharePoint-only, AWS+SharePoint and Salesforce-only regressions passed; a mixed missing-CRM test disclosed no_match and cited only found AWS evidence. Existing grants, IAM, data and original retrieval implementations were preserved. The sections describing pending activation below are historical. Exact actions, hashes, safe request IDs, tests and rollback are in [the integration ledger](SALESFORCE_MCP_INTEGRATION_PLAN.md) and [existing one-pass guide, Stage 6B](SALESFORCE_MCP_ONE_PASS_INTEGRATION.md#stage-6b--add-shared-aws-sharepoint-and-salesforce-answers). Source remains uncommitted; Terraform reconciliation, two-user permissions, refresh/revoke and reliability gates remain open.


**Recorded:** 2026-10-04. **Status:** Bishal's requested direction; design and acceptance criteria, not an implemented or deployment-approved controller change.

Bishal wants AskAnyDoc to answer questions using relevant evidence from multiple connected systems, including AWS documents, SharePoint and Salesforce, with future connectors such as Snowflake or HubSpot. These examples are candidates, not connected or selected services. A connector must not require another complete assistant or an ever-growing chain of source-name conditionals.

## Actual starting point

The existing document controller plans bounded AWS/SharePoint searches, normalizes evidence and validates citations before returning one answer. `app/api/organisation_tools.py` currently names two tools and dispatches between those two providers. `assistant_orchestrator.py` and SharePoint source planning contain the corresponding two-source contracts. The deployed Salesforce route is separate: the frontend sends explicitly Salesforce questions to the dedicated user-bound Salesforce API. Its bounded CRM reader reuses finalization helpers but does not participate in deployed document-source planning. Three-source synthesis is therefore not implemented.

## Smallest durable direction

1. Keep one application-owned answer controller and a small registry of approved adapters. Each adapter declares its source identity, useful capabilities, typed input contract, request-specific availability and execution/evidence limits. Direct APIs and verified MCP tools can both implement this boundary; MCP alone does not provide retrieval quality or authorization.
2. Build the available source catalogue from validated identity and active grants on each request. A model chooses only among these authorized capabilities. Authentication, credentials and permission enforcement stay in the adapters/server; no browser-supplied user identity or shared service account replaces delegated access.
3. Decompose a question into focused source-specific requests. Enforce per-source and global call, row, byte, token and deadline budgets in application code. An ordinary question should not query every connected system. An explicit multi-source request selects relevant authorized sources and identifies unavailable ones.
4. Normalize document excerpts and CRM/database facts into the existing evidence shape: source identifier, text/facts, application-controlled URI/record reference, location/page when applicable, and freshness/version metadata when available. Keep source-specific authorization metadata separate from employee-visible output. Reject malformed evidence before synthesis.
5. Produce one answer from returned evidence, validate cited references in application code, and disclose no-match, denied/unavailable source, truncation and partial failure. Treat retrieved instructions as untrusted data. Preserve contradictions and label inference; never claim all-source coverage merely because one source answered.
6. Combining evidence is not an automatic cross-system database join. A question relating the same customer or product across systems needs a verified shared identifier or explicit mapping. Ambiguous names require clarification or a clearly limited answer, rather than invented relationships.
7. Add a connector through a thin adapter, approved capability registration and contract/permission tests. Keep vendor-specific syntax and query compilation out of the controller. Reuse existing services and dependencies unless a measured gate requires more infrastructure. Assess synchronous Salesforce's 29-second boundary against the existing async answer path before choosing live execution wiring.

These are project design choices informed by the official interfaces below, not a claim that one mandatory industry architecture exists. No new generic framework, index, gateway or service is justified solely by this direction.

## Next bounded acceptance slice

After reviewing the exact shared-code/deployment impact, add Salesforce as the third registered source while preserving the existing retrieval adapters. Prove one synthetic question whose answer requires CRM facts plus relevant AWS and SharePoint documents. Require all three correct citation groups, source-specific queries, no invented cross-system relationship, honest partial-source failures, and unchanged AWS-only, SharePoint-only, AWS+SharePoint and Salesforce-only behavior. Add disconnected/denied-source and two-user permission tests before broader release. Future Snowflake/HubSpot selection requires current first-party capability, permission, processing, cost and sample-data verification; no capability is inferred from the connector's name.

**Change boundary:** Read `SHAREPOINT_RETRIEVAL_SOURCE_OF_TRUTH.md` fully before further SharePoint architecture work. A shared controller changes protected answer-path code and deployed packages. Present exact files/resources, authorization handling, failure modes, cost exposure, test evidence and rollback, and obtain Bishal's explicit approval immediately before the protected-path mutation. The present direction does not authorize that mutation, permissions, billing or deployment.

## Permanent regression gate requested by Bishal

After any applied change, test AWS-only, SharePoint-only, AWS+SharePoint combined and Salesforce-only application behavior. After three-source support exists, add an AWS+SharePoint+Salesforce question; add source-specific and relevant combined tests as further connectors are introduced. Observe the answer and inspect actual citation provenance, missing evidence and failure behavior. Unit tests or a Connected badge alone do not satisfy this gate. Record query, identity, outcome, safe job/request identifier where available, and remaining quality limits before declaring completion or commit readiness.

## Official grounding, checked 2026-10-04

- [Amazon Bedrock tool use](https://docs.aws.amazon.com/bedrock/latest/userguide/tool-use.html): tool definitions and model-requested operations can be executed by the application and returned for final synthesis. This supports the existing application-owned execution boundary.
- [MCP tools specification, 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25/server/tools): discovery, named tools, input/output schemas and structured results define an interface; they do not establish source search quality or final answer correctness.
- [Microsoft Graph SharePoint/OneDrive search](https://learn.microsoft.com/en-us/graph/search-concept-files): source search and results are distinct from AskAnyDoc's bounded extraction and final answer generation. Retain the selected Graph provider and current permission boundaries.
- [Salesforce Hosted MCP best practices](https://developer.salesforce.com/docs/platform/hosted-mcp-servers/guide/general-best-practices.html): retain the existing read-only scope, verified tool contracts and source permission enforcement. Live schema and tested capability evidence remain in `SALESFORCE_MCP_INTEGRATION_PLAN.md`.

No application configuration/code was changed by this document. Documentation rollback: remove this new file and the associated brief/checkpoint paragraphs after review; preserve append-only test history. Applied Salesforce/frontend rollback remains in the integration ledger.
