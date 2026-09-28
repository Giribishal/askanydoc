# AskAnyDoc

**Project 1 of 3 · Weeks 1–6 · Hybrid AI and RAG assistant on AWS**

## Status: 🔄 In progress — permission-aware AWS + SharePoint answers work end to end; operational hardening remains

- Started: 2026-06-13
- Shipped v1.0: (TBD)
- Live app: use the current Terraform `cloudfront_url` output. The former S3 website URL is historical; the website bucket is now private behind CloudFront.
- GitHub repo: https://github.com/Giribishal/askanydoc

### Verified progress

- Week 1 shipped: Terraform-managed S3 placeholder site, public repository, and green Terraform CI.
- Local Bedrock smoke test completed with token usage recorded.
- Lambda API implemented with Pydantic/Instructor structured output: `{answer, confidence}`.
- Terraform state contains the Lambda execution role, Bedrock and Secrets Manager permissions, Python 3.13 Lambda, Function URL, and public invoke permissions.
- Langfuse Cloud tracing is integrated; credentials are fetched at runtime from AWS Secrets Manager.
- React + Vite conversation UI is implemented and a local production `dist/` build exists.
- React deployment was verified live on 2026-09-04.
- A fresh browser → Lambda → Bedrock smoke test returned a structured answer with confidence `0.95`, using 802 input tokens and 82 output tokens.
- That smoke call cost approximately **USD $0.00133** at the AU Haiku 4.5 rates recorded in `app/api/bedrock_smoke.py` (model inference only).
- Sunday post #2 / AskAnyDoc v0.1 launch was confirmed from Bishal's LinkedIn screenshot on 2026-09-04; it had been published about three weeks earlier.
- Multi-format ingestion now sends PDF, DOCX, TXT, and Markdown through extraction, chunking, Titan V2 embeddings, and Aurora PostgreSQL with pgvector.
- The answer Lambda embeds each question with the same Titan configuration, retrieves relevant chunks, and gives Claude only numbered evidence.
- Live verification returned a grounded answer with a real PDF page citation; an unrelated question returned `grounded: false` without invoking Claude.
- The deployed React chat displays citations and handles API failures. Terraform now manages the complete built frontend rather than the Week 1 placeholder.
- Claude now acts as the conversational assistant and can request the custom organisation-source search as a controlled Bedrock Converse tool.
- The browser sends bounded recent history for follow-ups. Responses distinguish conversation, general knowledge, organisation evidence, and missing organisation information.
- Organisation citations are built from stored provenance only after the application validates Claude's selected evidence numbers.
- The first Microsoft 365 slice now has Entra/MSAL, an API Gateway JWT boundary, delegated on-behalf-of exchange, SharePoint providers, source routing, and a two-site/two-user test environment in the working tree.
- The SharePoint corpus contains 8 general and 4 restricted documents. The controlled identity matrix is live-proven: Alex retrieved General and Restricted sources with correct citations; Adele retrieved General and received no Restricted evidence or citation.
- Option B—delegated Microsoft Graph Search plus bounded on-demand PDF extraction—is selected and deployed for the current test environment because the tenant lacks Copilot Retrieval commercial eligibility. Checked-in Terraform still defaults SharePoint off; the live test environment uses reviewed values. The previous deployment approval is consumed, so every future apply requires a fresh reviewed plan and explicit approval.
- Live source routing exposes `search_aws_documents` and adds `search_sharepoint` only for an enabled request with validated Microsoft identity. It searches one likely source by default, both only when required, and permits one bounded different-source fallback.
- Current SharePoint execution authority: `docs/SHAREPOINT_RETRIEVAL_SOURCE_OF_TRUTH.md`. It records Options A/B/C, permissions, current versus deployed state, exact gates, approval boundaries, rollback, and next actions.
- Read-only Entra inspection confirms the live single-tenant registrations, enabled `access_as_user` scope, exact CloudFront redirect, and tenant-granted delegated Graph permissions. The deterministic source classifier, asynchronous answer contract, and bounded Aurora-resume recovery are deployed. On 2026-09-28, a varied comparison began with Aurora at 0 ACU and returned a browser-visible `organisation_sources` answer in 47 seconds with five citations from `13-disaster-recovery-workloads-on-aws.pdf` and three from `microsoft-cloud-hybrid-architecture.pdf`. The worker completed on attempt one with 7,723 input / 741 output tokens; the slower retry branch remains focused-test proven. The exact configuration, code hash, cost estimate, risks, and rollback boundary are recorded in the SharePoint source of truth, test matrix, implementation log, and modernization register. Observability and alerts are next, after review and fresh approval.

### Week 2 outcome

- ✅ Live React frontend on S3
- ✅ Browser → Lambda → Bedrock structured response
- ✅ Confidence and token usage displayed in the UI
- ✅ Langfuse integration present in the deployed handler path
- ✅ Cost-per-call measured from a fresh request
- ✅ Sunday post #2 published

Prompt-tutorial and assigned-reading status remain personal learning-log follow-ups; they do not block beginning Week 3. The uncommitted authored work and generated dependency churn still need a deliberate Git-hygiene pass.

### Current verified hybrid boundary

- Direct S3/AWS SDK ingestion and custom pgvector retrieval are working end to end.
- A public Function URL still exists for the historical AWS-only demo path. It is not an acceptable SharePoint identity boundary. CloudFront/private-S3 frontend delivery plus the API Gateway/Entra JWT path now carry the permission-tested SharePoint flow; Function URL retirement remains a separate approval-controlled hardening change.
- Retrieval currently uses top-5 cosine similarity with a configurable `0.35` minimum. This threshold must be calibrated with the F5 evaluation set rather than treated as universally optimal.
- Claude Haiku 4.5 is configuration-selected through the AU inference profile. Model quality, latency, lifecycle, and cost must be evaluated before a company rollout.
- Recent history is client-supplied and browser-local. Authentication, server-owned sessions, tenant isolation, and source ACL filtering remain mandatory company-deployment gates.
- Scanned-PDF OCR and additional file formats remain deferred.

The detailed current boundary and staged company-readiness gates are documented in [`docs/hybrid_assistant_architecture.md`](docs/hybrid_assistant_architecture.md). The single current list of risks, known issues, official-architecture gaps, and planned infrastructure/application changes is [`docs/MODERNIZATION_RISK_AND_CHANGE_REGISTER.md`](docs/MODERNIZATION_RISK_AND_CHANGE_REGISTER.md). Observed incident history remains in [`docs/ISSUES_AND_RESOLUTIONS.md`](docs/ISSUES_AND_RESOLUTIONS.md); token-efficiency experiments have their own research record in [`docs/research/TOKEN_EFFICIENCY.md`](docs/research/TOKEN_EFFICIENCY.md).

The next permission-aware source slice is specified in [`docs/SHAREPOINT_SOURCE_PLAN.md`](docs/SHAREPOINT_SOURCE_PLAN.md).

Architecture evolution, current official reference links, provider strategy, and the exact AWS approval boundary are recorded in [`docs/ARCHITECTURE_DECISIONS.md`](docs/ARCHITECTURE_DECISIONS.md). Current implementation evidence and superseded setup assumptions are recorded in [`docs/SHAREPOINT_IMPLEMENTATION_LOG.md`](docs/SHAREPOINT_IMPLEMENTATION_LOG.md).

The live AWS budget `askanydoc-bedrock-monthly` is USD 25 per month with actual-cost alerts at USD 10, 15, 20, and 25, scoped to Amazon Bedrock plus the deployed Claude Haiku 4.5 Bedrock billing entry. The weekly Sunday report is `askanydoc-bedrock-weekly`. AWS Budgets is delayed cost alerting, not an instantaneous hard spending cap. The matching definition is in `infra/cost_budget.tf`; because the live budget was created in the console, follow the import note in that file before enabling it in Terraform.

---

## What this becomes

A web application where users upload supported text-bearing documents (`.pdf`, `.docx`, `.txt`, and `.md`) and ask questions. Format-specific extractors normalize text and provenance before the shared chunking, Titan embedding, and Aurora PostgreSQL/pgvector pipeline. The system retrieves relevant passages with citations and answers using Claude on AWS Bedrock.

Excel/CSV, PowerPoint, images, scanned-document OCR, and other formats are explicitly deferred until after the core RAG learning plan.

## Plan section reference

Full per-day build plan: **Section 6 of `Bishal Giri - Build and Ship Plan v5.pdf`**.

## Target folder structure

```
askanydoc/
├── README.md (this file, kept updated)
├── architecture.png (Excalidraw export, end of Week 6)
├── /app
│   ├── api/                    (Lambda code)
│   ├── ingestion/
│   │   ├── runtime/            (deployed Lambda code and container recipe)
│   │   ├── learning/           (local step-by-step RAG scripts)
│   │   └── tests/              (ingestion tests)
│   ├── shared/                 (chunking.py, embeddings.py, retrieval.py)
│   └── requirements.txt
├── /frontend
│   ├── src/                    (React + Vite)
│   └── package.json
├── /infra
│   ├── main.tf, variables.tf, outputs.tf
│   ├── modules/network/
│   ├── modules/data/
│   ├── modules/compute/
│   ├── modules/observability/
│   └── modules/frontend/
├── /evals
│   ├── golden_set.csv          (30 hand-written Q&A pairs)
│   ├── run_evals.py
│   └── error_analysis.md       (the 50-trace look-at-your-data writeup)
├── /docs
│   └── teaching_post_rag.md    (Teaching Post 1)
└── /.github/workflows
    └── deploy.yml              (CI/CD with OIDC)
```

Current ingestion navigation is documented in [`app/ingestion/README.md`](app/ingestion/README.md). Architecture references and the accompanying concept notes are kept together under [`docs/architecture/`](docs/architecture/).

For the answer Lambda, `app/api/requirements.in` records the libraries chosen directly by the application, while `app/api/requirements.txt` locks the complete deployment package. Terraform generates `infra/build/` and `infra/lambda.zip`; neither belongs in Git.

## Exit criteria for shipping (end of Week 6)

- [ ] Live demo URL working
- [ ] Public GitHub repo with thorough README
- [ ] Architecture diagram (PNG in repo)
- [ ] 90-second demo video (Loom)
- [ ] Evals: 30-Q golden set, automated runner, error_analysis.md committed
- [ ] CI/CD: GitHub Actions with OIDC, eval gate on PR
- [ ] CloudWatch dashboard live, alarms set
- [ ] Langfuse traces showing every LLM call
- [ ] IAM least-privilege verified
- [ ] Interview talking points doc in repo
- [ ] Teaching Post 1 (RAG explainer) and Teaching Post 2 (Evals explainer) published on LinkedIn

---

*Update this README's status section as the project progresses.*
