# AskAnyDoc

**Project 1 of 3 · Weeks 1–6 · Production-grade RAG knowledge assistant on AWS**

## Status: 🔄 In progress — Week 3 (embeddings + pgvector retrieval foundation)

- Started: 2026-06-13
- Shipped v1.0: (TBD)
- Live app: http://askanydoc-site-prod-apse2.s3-website-ap-southeast-2.amazonaws.com
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

### Week 2 outcome

- ✅ Live React frontend on S3
- ✅ Browser → Lambda → Bedrock structured response
- ✅ Confidence and token usage displayed in the UI
- ✅ Langfuse integration present in the deployed handler path
- ✅ Cost-per-call measured from a fresh request
- ✅ Sunday post #2 published

Prompt-tutorial and assigned-reading status remain personal learning-log follow-ups; they do not block beginning Week 3. The uncommitted authored work and generated dependency churn still need a deliberate Git-hygiene pass.

---

## What this becomes

A web application where users upload PDF documents (initial corpus: ~10 ACSC cybersecurity guidelines) and ask questions. The system retrieves relevant passages with citations and answers using Claude on AWS Bedrock. Polished UI, real evals, full production deployment.

## Plan section reference

Full per-day build plan: **Section 6 of `Bishal Giri - Build and Ship Plan v5.pdf`**.

## Target folder structure

```
askanydoc/
├── README.md (this file, kept updated)
├── architecture.png (Excalidraw export, end of Week 6)
├── /app
│   ├── api/                    (Lambda code)
│   ├── ingestion/              (Lambda code)
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
