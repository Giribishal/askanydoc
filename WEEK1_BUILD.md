# AskAnyDoc — Week 1 Build Brief

**Goal of Week 1 (Plan Section 6.4):** rebuild your Terraform skills *by yourself, no AI shortcuts*. By the end of the week you have a **static placeholder site live at a real URL, deployed via Terraform, with CI on GitHub** — and you've run `terraform apply` solo **four times**.

This week is NOT the RAG app. That's Weeks 2–4. This week is foundations: prove you can stand up real AWS infra with Terraform you wrote yourself.

> **The rule for Week 1:** Claude does NOT write your HCL. You write `main.tf` / `variables.tf` / `outputs.tf` yourself. Claude is on call for *concepts* and *debugging* only. The reading and the typing ARE the learning (Rules 9 & 11).

---

## The architecture (what you're building)

The simplest "real URL" static site on AWS: **S3 static website hosting.**

```
[ Your browser ]
        │  HTTP
        ▼
[ S3 bucket configured for static website hosting ]
   ├── index.html   (the placeholder page — already in ../site/)
   └── bucket policy: public read on objects
```

That's the Week 1 target. (CloudFront + HTTPS is a nice upgrade later, but plain S3 website hosting satisfies the "live at a real URL" exit criterion and keeps the Terraform small enough to write solo.)

---

## Resources you'll write in `infra/` (your checklist)

Write these yourself. Order roughly as listed. Look each one up on the Terraform AWS provider docs (registry.terraform.io) — doc-reading is the job skill.

- [ ] `provider "aws"` — region `ap-southeast-2` (Sydney)
- [ ] `aws_s3_bucket` — your site bucket (globally-unique name, e.g. `askanydoc-site-<something>`)
- [ ] `aws_s3_bucket_website_configuration` — index document = `index.html`
- [ ] `aws_s3_bucket_public_access_block` — set to allow public policy (the defaults block it)
- [ ] `aws_s3_bucket_policy` — public `s3:GetObject` on `arn/*`
- [ ] `aws_s3_object` — upload `index.html` (source = `../site/index.html`, content_type = `text/html`)
- [ ] `outputs.tf` — output the `website_endpoint` so you get the URL after apply

**Conventions (non-negotiable, from the protocol):**
- Tag everything `project = "askanydoc"` and `managed-by = "terraform"`.
- Do NOT touch Motherland CIDRs (10.0.0.0/16, 10.1.0.0/16). No VPC needed this week anyway.
- State stays local for now (remote state is a Week 5–6 task).

---

## The loop (your 4 applies will come naturally)

1. `terraform init`
2. `terraform plan` — **read it** before applying
3. `terraform apply` — confirm, then open the `website_endpoint` URL
4. Make a small change (edit the page, re-upload) → `plan` → `apply` again
5. Repeat until the page looks right. Each meaningful `apply` counts toward your 4.
6. **Don't `destroy` this one at the end** — Week 1's exit criterion is a *live* URL. S3 static hosting at rest is effectively free (pennies). You'll keep it up.

---

## CI on GitHub (second half of the exit criterion)

After the site is live:
- [ ] Create a **public** GitHub repo `askanydoc`, push this folder.
- [ ] Add a GitHub Actions workflow (`.github/workflows/`) that runs `terraform fmt -check` + `terraform validate` on every push. (Full OIDC deploy pipeline is Week 6 — this week just lint + validate.)

---

## Week 1 — Definition of Done

- [ ] Static page loads at the S3 website endpoint URL
- [ ] All infra is in `infra/*.tf`, written by you
- [ ] `terraform apply` run solo ≥4 times
- [ ] `project=askanydoc` tags on resources
- [ ] Public GitHub repo exists with the code pushed
- [ ] CI runs `fmt`/`validate` on push
- [ ] Sunday post drafted: "Rebuilding Terraform foundations"

---

## When you're stuck

Ask Claude for the *concept* or to *debug an error* — paste the error. Don't ask Claude to write the resource block for you this week. If you're stuck >2 hrs on the same thing, that's a real blocker (Rule 14) — flag it.
