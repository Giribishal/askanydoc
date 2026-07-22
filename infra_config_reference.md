# AskAnyDoc — Infrastructure Config Reference

> A quick-glance inventory of every Terraform resource in `infra/`. Update this whenever you add, change, or remove a resource. Purpose: see what exists and how it's wired without reading all the HCL.

**Project:** AskAnyDoc
**Region:** ap-southeast-2 (Sydney)
**State:** local (`terraform.tfstate` in `infra/`, git-ignored)
**Provider:** hashicorp/aws `~> 5.92` · Terraform `>= 1.2`
**Live URL:** http://askanydoc-site-prod-apse2.s3-website-ap-southeast-2.amazonaws.com
**Tagging convention:** `project = "askanydoc"`, `managed-by = "terraform"`

---

## Files

| File | Holds |
|------|-------|
| `infra/main.tf` | terraform block, provider, all resources |
| `infra/outputs.tf` | output values (the live URL) |

---

## Resources (the inventory)

### 1. Provider setup
- **terraform block** — `required_providers`: aws = `hashicorp/aws` `~> 5.92`; `required_version = ">= 1.2"`. Pins versions so nothing silently upgrades.
- **`provider "aws"`** — `region = "ap-southeast-2"`. Sets cloud + region for everything below.

### 2. `aws_s3_bucket` — nickname `website`
- **What it is:** the storage bucket that holds the site files.
- **Key settings:** `bucket = "askanydoc-site-prod-apse2"` (globally-unique name); tags `project`/`managed-by`.
- **Referenced by:** all the blocks below, via `aws_s3_bucket.website.id` (and `.arn` in the policy).

### 3. `aws_s3_bucket_website_configuration` — nickname `bucket_config`
- **What it is:** flips the bucket into a static website.
- **Key settings:** `bucket = aws_s3_bucket.website.id`; `index_document { suffix = "index.html" }` (the homepage).
- **Exposes:** `.website_endpoint` → the live URL (used in outputs).

### 4. `aws_s3_bucket_public_access_block` — nickname `website_public_access`
- **What it is:** unlocks AWS's default public-access guardrail (a veto that otherwise blocks public buckets).
- **Key settings:** `bucket = aws_s3_bucket.website.id`; all four flags `false` (`block_public_acls`, `block_public_policy`, `ignore_public_acls`, `restrict_public_buckets`).
- **Note:** unlocking ≠ granting. This only removes the veto; the actual permission is the policy below.

### 5. `aws_s3_bucket_policy` — nickname `bucket_policy`
- **What it is:** the permission that lets the public READ the files.
- **Key settings:** `bucket = aws_s3_bucket.website.id`; `policy = jsonencode({...})` granting `s3:GetObject` to `Principal "*"` (everyone) on `Resource = "${aws_s3_bucket.website.arn}/*"` (all objects in the bucket).
- **Depends on:** #4 (guardrail must be down first). Applied fine without explicit `depends_on` because #4 already existed at apply time.

### 6. `aws_s3_object` — nickname `website_page_upload`
- **What it is:** uploads the local `index.html` into the bucket.
- **Key settings:** `bucket = aws_s3_bucket.website.id`; `key = "index.html"` (name in bucket); `source = "../site/index.html"` (local file to read); `content_type = "text/html"` (so browsers render it).
- **To update the live page:** edit `site/index.html` → `terraform apply` (Terraform detects the change and re-uploads).

### 7. Output — `website_url`
- **In:** `outputs.tf`.
- **Value:** `aws_s3_bucket_website_configuration.bucket_config.website_endpoint`.
- **Purpose:** prints the live URL after apply (no need to dig in the console). View anytime with `terraform output`.

---

## The wiring (how they connect)

```
provider (aws, ap-southeast-2)
   └─ aws_s3_bucket.website  (the bucket)
        ├─ aws_s3_bucket_website_configuration.bucket_config   → makes it a website, gives .website_endpoint
        ├─ aws_s3_bucket_public_access_block.website_public_access → unlocks public access
        ├─ aws_s3_bucket_policy.bucket_policy                  → grants public read (needs ↑ unlocked first)
        └─ aws_s3_object.website_page_upload                   → uploads index.html
   outputs.tf → website_url  = bucket_config.website_endpoint
```

**Flow in one line:** make a bucket → turn it into a website → unlock public access → grant public read → upload the page → print the URL.

---

## Reference-pattern cheat (how blocks point at each other)
`<type>.<nickname>.<attribute>` — e.g. `aws_s3_bucket.website.id`, `aws_s3_bucket.website.arn`, `aws_s3_bucket_website_configuration.bucket_config.website_endpoint`. Pick the attribute = the fact you want.

---

## CI / Git
- **Repo:** github.com/Giribishal/askanydoc (public)
- **CI:** `.github/workflows/terraform-ci.yml` — runs `terraform fmt -check -recursive` + `terraform init -backend=false` + `terraform validate` on every push. Green ✓ = formatted & valid.
- **Git-ignored (never pushed):** `terraform.tfstate`, `terraform.tfstate.backup`, `.terraform/`.

---

*Last updated: end of the S3 static-site build. Update the Resources table whenever infra changes.*
