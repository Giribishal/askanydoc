# AskAnyDoc — Infrastructure Config Reference

> A quick-glance inventory of every Terraform resource in `infra/`. Update this whenever you add, change, or remove a resource. Purpose: see what exists and how it's wired without reading all the HCL.

**Project:** AskAnyDoc
**Region:** ap-southeast-2 (Sydney)
**State:** local (`terraform.tfstate` in `infra/`, git-ignored)
**Providers:** hashicorp/aws `~> 5.92`, hashicorp/archive `~> 2.4` · Terraform `>= 1.2`
**Website output:** http://askanydoc-site-prod-apse2.s3-website-ap-southeast-2.amazonaws.com
**API output:** `api_url` is emitted by Terraform; the current value is kept in local state and the frontend configuration.
**Tagging convention:** `project = "askanydoc"`, `managed-by = "terraform"`

---

## Files

| File | Holds |
|------|-------|
| `infra/main.tf` | Terraform/provider requirements and S3 static-site resources |
| `infra/lambda.tf` | Lambda IAM, dependency packaging, function, Function URL, permissions, and `api_url` output |
| `infra/outputs.tf` | `website_url` output |
| `app/api/requirements.txt` | Python packages installed into the Lambda ZIP |
| `app/api/handler.py` | Lambda entry point, Bedrock structured output, token capture, and Langfuse tracing |

---

## Resources (the inventory)

### 1. Provider setup
- **terraform block** — `required_providers`: aws = `hashicorp/aws` `~> 5.92`, archive = `hashicorp/archive` `~> 2.4`; `required_version = ">= 1.2"`. Pins compatible provider versions.
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

## Lambda API resources (`infra/lambda.tf`)

### 7. `aws_iam_role` — nickname `lambda_exec`
- **What it is:** the execution identity assumed by AWS Lambda.
- **Trust policy:** allows the `lambda.amazonaws.com` service to call `sts:AssumeRole`.
- **Tags:** `project=askanydoc`, `managed-by=terraform`.

### 8. `aws_iam_role_policy_attachment` — nickname `lambda_logs`
- **What it is:** attaches AWS-managed `AWSLambdaBasicExecutionRole` to `lambda_exec`.
- **Purpose:** lets `print()` output and runtime logs reach CloudWatch Logs.

### 9. `aws_iam_role_policy` — nickname `bedrock_invoke`
- **What it is:** inline permission allowing the Lambda role to call `bedrock:InvokeModel`.
- **Current scope:** `Resource = "*"`, intentionally broad for the first demo and still due for least-privilege hardening.

### 10. `aws_iam_role_policy` — nickname `langfuse_secret_access`
- **What it is:** inline permission allowing the Lambda role to call `secretsmanager:GetSecretValue` for the one AskAnyDoc Langfuse secret.
- **Boundary:** the secret was created outside Terraform; only the read permission is managed here. Never store or document its values in the repository.

### 11. `null_resource` — nickname `install_deps`
- **What it is:** local packaging step that rebuilds `infra/build/`, installs `requirements.txt` as manylinux CPython 3.13 binaries, and copies `handler.py` into the build directory.
- **Triggers:** hashes of `requirements.txt` and `handler.py`, so dependency packaging reruns when either changes.
- **Repository note:** `infra/build/` is generated output and should not remain tracked long-term.

### 12. `archive_file` data source — nickname `lambda_zip`
- **What it is:** zips the complete `infra/build/` directory into `infra/lambda.zip` after dependency installation.
- **Used by:** `aws_lambda_function.lambda_function` for `filename` and `source_code_hash`.

### 13. `aws_lambda_function` — nickname `lambda_function`
- **AWS name:** `askanydoc-api`.
- **Runtime:** Python 3.13; handler `handler.handler`; timeout 30 seconds; memory 256 MB.
- **Purpose:** receives a question, gets structured `{answer, confidence}` output from Bedrock, captures token usage, sends a Langfuse trace, and returns JSON.

### 14. `aws_lambda_function_url` — nickname `lambda_function_url`
- **What it is:** public HTTPS entry point for the Lambda.
- **Current settings:** `authorization_type = "NONE"`; CORS allows any origin, `POST`, and `content-type`.
- **Security note:** this is a temporary demo posture and exposes potential invocation cost.

### 15. Lambda permissions — `public_url_access` and `public_invoke_function`
- **Gate 1:** permits any principal to call `lambda:InvokeFunctionUrl` through the unauthenticated Function URL.
- **Gate 2:** permits the matching `lambda:InvokeFunction` action required by the public URL flow.

## Outputs

### `website_url`
- **In:** `outputs.tf`.
- **Value:** `aws_s3_bucket_website_configuration.bucket_config.website_endpoint`.

### `api_url`
- **In:** `lambda.tf`.
- **Value:** `aws_lambda_function_url.lambda_function_url.function_url`.

## External runtime dependency

AWS Secrets Manager contains the manually created `askanydoc/langfuse` secret. On Lambda cold start, `handler.py` reads its public key, secret key, and host, then sets the environment variables expected by the Langfuse SDK. Terraform manages access to this secret but not the secret resource or its values.

---

## The wiring (how they connect)

```
provider (aws, ap-southeast-2)
   ├─ aws_s3_bucket.website
   │    ├─ website configuration → website_url
   │    ├─ public-access block + bucket policy
   │    └─ website_page_upload → site/index.html
   │
   └─ aws_iam_role.lambda_exec
        ├─ AWSLambdaBasicExecutionRole → CloudWatch logs
        ├─ bedrock_invoke policy → Bedrock model calls
        ├─ langfuse_secret_access policy → Secrets Manager
        └─ aws_lambda_function.lambda_function
             ↑ archive_file.lambda_zip
             ↑ null_resource.install_deps (requirements + handler)
             └─ Function URL + two public invoke permissions → api_url

browser/React → api_url → Lambda → Bedrock
                         ├─ JSON answer + confidence + token counts → browser
                         └─ trace → Langfuse Cloud
```

**Flow in one line:** S3 serves the page → React posts a question to the Function URL → Lambda invokes Bedrock → structured JSON returns to React while observability data is flushed to Langfuse.

---

## Reference-pattern cheat (how blocks point at each other)
`<type>.<nickname>.<attribute>` — e.g. `aws_s3_bucket.website.id`, `aws_s3_bucket.website.arn`, `aws_s3_bucket_website_configuration.bucket_config.website_endpoint`. Pick the attribute = the fact you want.

---

## CI / Git
- **Repo:** github.com/Giribishal/askanydoc (public)
- **CI:** `.github/workflows/terraform-ci.yml` — runs `terraform fmt -check -recursive` + `terraform init -backend=false` + `terraform validate` on every push. Green ✓ = formatted & valid.
- **Git-ignored (never pushed):** `terraform.tfstate`, `terraform.tfstate.backup`, `.terraform/`.
- **Current hygiene issue:** `infra/build/` and `infra/lambda.zip` were previously committed, so ignoring them now does not remove them from Git tracking. Clean the index in a deliberate, reviewed change.

---

*Last reconciled: 2026-09-04 against `main.tf`, `lambda.tf`, `outputs.tf`, `handler.py`, and Terraform state serial 104.*
