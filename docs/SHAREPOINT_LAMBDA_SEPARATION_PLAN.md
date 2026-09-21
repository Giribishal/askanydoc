# Proposed SharePoint Lambda separation plan

**Status:** proposed architecture; documentation only; not approved or implemented
**Recorded:** 2026-09-21
**Authority:** `SHAREPOINT_RETRIEVAL_SOURCE_OF_TRUTH.md` remains authoritative for the live system.

## Recommendation

Separate Microsoft retrieval into a dedicated `askanydoc-sharepoint-retrieval` Lambda, while retaining one small answer/orchestration Lambda. Do not copy the complete AWS answer Lambda and do not create a second complete AskAnyDoc application.

```text
React + MSAL
  -> API Gateway JWT authorizer
  -> answer/orchestration Lambda
       -> existing AWS retrieval code (unchanged)
       -> synchronous IAM-authorized invocation
          -> SharePoint retrieval Lambda
               -> OBO delegated Graph token
               -> Graph Search
               -> bounded PDF download/extraction
               -> normalized evidence only
  -> Claude final answer and application-built citations
```

This preserves one assistant and one routing policy while isolating the Microsoft capability's dependencies, confidential-client credential access, Graph timeouts, PDF memory use, deployments, metrics, and concurrency controls.

## Why not copy the complete Lambda

- Copying orchestration, Bedrock calls, AWS retrieval, and answer generation would create two applications that can drift.
- Cross-source questions would become harder because two independent answer Lambdas would each own only part of the evidence.
- The SharePoint function should return normalized evidence, never a competing final answer.
- Shared contracts may be packaged from the existing source or a small internal library; live code must have one clear owner.

## Cost

- Lambda has no standing compute charge when an ordinary function is idle.
- A separate function adds an invocation and its own GB-second duration when SharePoint is used.
- If the orchestrator waits synchronously, both functions are billed during the overlap, so this is slightly more expensive than one function.
- At the current test volume, the difference should be small, but it must be measured rather than assumed. Bedrock tokens and PDF-processing duration are likely larger cost drivers.
- Reserved concurrency has no direct charge, but reserved units reduce the regional unreserved concurrency pool. Provisioned concurrency would add cost and is not proposed without measured cold-start need.

## Identity and security boundary

1. API Gateway continues to validate issuer, audience, tenant, and API scope.
2. The orchestrator invokes the SharePoint Lambda only through a narrow IAM permission.
3. The SharePoint Lambda alone receives permission to read the Entra confidential-client secret.
4. The SharePoint Lambda performs OBO and calls Graph as the signed-in user.
5. It returns only allowlisted, permission-trimmed evidence and provenance.
6. Tokens, authorization codes, and document bodies are never logged or persisted.
7. The SharePoint Lambda receives no Aurora, S3 document-corpus, ingestion, or unrelated secret permission.

Microsoft's OBO rule remains unchanged: the protected middle-tier exchanges the incoming API token for a downstream delegated Graph token and must not substitute application-only access for a user-driven request.

## Reliability and concurrency

- Give the SharePoint function a measured reserved-concurrency ceiling so Graph/PDF load cannot consume all answer capacity or overload Microsoft.
- Keep a short function timeout, bounded retries, maximum hydrated files, maximum bytes/pages, and fail-closed errors.
- The orchestrator applies a caller timeout/circuit breaker and can still answer AWS-only questions when the SharePoint capability is unavailable.
- Use separate CloudWatch metrics/alarms for OBO, Graph search, download, extraction, throttling, timeout, memory, and permission denial.
- Do not insert SQS into the interactive retrieval path merely for isolation: a user is waiting for an immediate answer and the delegated token is short-lived. SQS remains appropriate for background ingestion or other asynchronous work.
- Defer Step Functions or durable orchestration until the workflow has enough branching, recovery, or long-running state to justify it.

## Migration gates

1. Finish the current Adele/Alex matrix on the working vertical slice.
2. Capture current latency, memory, failures, tokens, and concurrency baseline.
3. Define and test a versioned request/evidence contract for the SharePoint Lambda.
4. Add the new Lambda, least-privilege role, log group/alarms, and invoke permission in Terraform without changing AWS ingestion or data.
5. Unit-test token redaction, site allowlisting, bounded extraction, timeout, and error mapping.
6. Prepare a Terraform plan and verify the exact IAM/topology changes.
7. Obtain explicit approval with blast radius, cost, downtime, rollback, and evidence.
8. Deploy with the current in-process SharePoint adapter retained as rollback until the full matrix passes.
9. Switch only the SharePoint tool executor to the dedicated Lambda.
10. Remove the in-process copy only after stable evidence and a separate cleanup review.

## Rollback

- Route the SharePoint tool back to the checkpointed in-process adapter or disable SharePoint retrieval.
- Do not modify or roll back the AWS document corpus, ingestion, embeddings, Aurora, or pgvector data.
- Do not automatically fall back to a weaker identity or application-only Graph permission.

## Official basis reviewed on 2026-09-21

- AWS Lambda application design: https://docs.aws.amazon.com/lambda/latest/dg/concepts-application-design.html
- AWS Lambda concurrency and reserved concurrency: https://docs.aws.amazon.com/lambda/latest/dg/lambda-concurrency.html
- AWS Serverless Applications Lens: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/
- AWS serverless AI architecture guidance: https://docs.aws.amazon.com/prescriptive-guidance/latest/agentic-ai-serverless/designing-serverless-ai-architectures.html
- Microsoft OBO guidance: https://learn.microsoft.com/en-us/entra/msidweb/call-downstream-apis/from-web-apis
- Microsoft Zero Trust API-to-API guidance: https://learn.microsoft.com/en-us/security/zero-trust/develop/api-calls-api

