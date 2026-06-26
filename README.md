# AskAnyDoc

**Project 1 of 3 · Weeks 1–6 · Production-grade RAG knowledge assistant on AWS**

## Status: 🔄 In progress — Week 1 (Terraform foundations)

Started: 2026-06-13  
Shipped v1.0: (TBD)  
Live demo: (TBD)  
GitHub repo: (TBD)

**Week 1 goal:** static placeholder site live at a real URL via Terraform, CI on GitHub, `terraform apply` run solo 4×. See `WEEK1_BUILD.md`.

---

## What this becomes

A web application where users upload PDF documents (initial corpus: ~10 ACSC cybersecurity guidelines) and ask questions. The system retrieves relevant passages with citations and answers using Claude on AWS Bedrock. Polished UI, real evals, full production deployment.

## Plan section reference

Full per-day build plan: **Section 6 of `Bishal Giri - Build and Ship Plan v5.pdf`**.

## Suggested local folder structure (start populating from Week 1)

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
