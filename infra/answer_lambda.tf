# Answer Lambda infrastructure.
# Packages the answer handler, grants its AWS permissions, creates the Lambda,
# and exposes it through a Lambda Function URL.

# It does four simple things, in order:

# 1. Gives the code permission to exist and run in AWS (an identity + the right to call Bedrock)
# 2. Packages the HTTP handler, assistant orchestrator, organisation tool, and shared code
# 3. Creates the actual live Lambda function from that zip
# 4. Gives it a public web address (URL) so you can curl it


# ------------------------------------------------------------------------------

# Create IAM role for Lambda Execution
# It is all making a role and defining who can take this role. Lambda in our case
resource "aws_iam_role" "lambda_exec" { # nick name here like- lambda-exec are just for terraform to reference that aws never sees
  name = "askanydoc-lambda-exec"        # and this name is real name that ends up showing in AWS console

  # assume_role_policy = the TRUST policy: WHO may wear this policy
  # Principal.Service = the Lambda service itself; sts:AssumeRole = "put badge on"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow" # Principal is allowed to Action - assume role 
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = {
    project    = "askanydoc"
    managed-by = "terraform"
  }
}

# AWS's ready-made logging policy — so print() reaches CloudWatch.
# aws-MANAGED policy: AWS pre-wrote it; you reference it by ARN.
# ---------------------------------------------------------------------

# above was about making a role and defining who can take this role,
# And here we are attaching existing policy to the role

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Creating bedrock invoke policy from kind of scratch.

resource "aws_iam_role_policy" "bedrock_invoke" {
  name = "askanydoc-bedrock-invoke"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = "bedrock:InvokeModel"
      Resource = [
        "arn:aws:bedrock:ap-southeast-2:404584456165:inference-profile/au.anthropic.claude-haiku-4-5-20251001-v1:0",
        "arn:aws:bedrock:ap-southeast-2::foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0",
        "arn:aws:bedrock:ap-southeast-4::foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0",
        "arn:aws:bedrock:ap-southeast-2::foundation-model/amazon.titan-embed-text-v2:0"
      ]
    }]
  })
}



# Grants the Lambda's role permission to READ this one specific secret.
# Same pattern as bedrock_invoke - a custom policy, written by us, attached to the role.
resource "aws_iam_role_policy" "langfuse_secret_access" {
  name = "askanydoc-langfuse-secret-access"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "secretsmanager:GetSecretValue"
      Resource = "arn:aws:secretsmanager:ap-southeast-2:404584456165:secret:askanydoc/langfuse-ipOX9p"
    }]
  })
}

resource "aws_iam_role_policy" "entra_secret_access" {
  name = "askanydoc-entra-secret-access"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "secretsmanager:GetSecretValue"
      Resource = aws_secretsmanager_secret.entra_api_credential.arn
    }]
  })
}

# Let the answer Lambda read only the shared vector database through Data API.
resource "aws_iam_role_policy" "answer_vector_database" {
  name = "askanydoc-answer-vector-database"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "rds-data:ExecuteStatement"
        Resource = aws_rds_cluster.vector_database.arn
      },
      {
        Effect   = "Allow"
        Action   = "secretsmanager:GetSecretValue"
        Resource = aws_rds_cluster.vector_database.master_user_secret[0].secret_arn
      }
    ]
  })
}

# ── CHUNK 2: PACKAGE -> CREATE -> EXPOSE -> PRINT ──

# Zip lambda handler - code that runs in lambda

# Installs pinned runtime dependencies and copies only deployable Python modules into build/.
# null_resource = "run this command" - not a real AWS thing, just a local action.
resource "null_resource" "install_deps" {
  # triggers = re-run this step whenever requirements.txt or answer_lambda_handler.py changes.
  triggers = {
    requirements = filesha256("${path.module}/../app/api/requirements.txt")
    api_code = sha256(join("", [
      for file in [
        "answer_lambda_handler.py",
        "assistant_orchestrator.py",
        "organisation_tools.py",
        "retrieval.py"
      ] :
      filesha256("${path.module}/../app/api/${file}")
    ]))
    shared_code = sha256(join("", [
      for file in fileset("${path.module}/../app/shared/askanydoc_rag", "*.py") :
      filesha256("${path.module}/../app/shared/askanydoc_rag/${file}")
    ]))
    sharepoint_code = sha256(join("", [
      for file in fileset("${path.module}/../app/sharepoint", "*.py") :
      filesha256("${path.module}/../app/sharepoint/${file}")
    ]))
  }

  # if (Test-Path ...\build) { Remove-Item -Recurse -Force ...\build } — if a build folder already exists, delete it and everything in it (fresh start).
  # pip install -r ...requirements.txt -t ...\build [flags] — install the deps from requirements.txt into the build folder (-t = target directory, which is what creates build).
  # copy the answer handler into that same build folder.

  provisioner "local-exec" {
    command     = "if (Test-Path ${path.module}\\build) { Remove-Item -Recurse -Force ${path.module}\\build }; pip install -r ${path.module}/../app/api/requirements.txt -t ${path.module}/build --platform manylinux2014_x86_64 --python-version 3.13 --implementation cp --abi cp313 --only-binary=:all: --upgrade; Copy-Item ${path.module}\\..\\app\\api\\answer_lambda_handler.py,${path.module}\\..\\app\\api\\assistant_orchestrator.py,${path.module}\\..\\app\\api\\organisation_tools.py,${path.module}\\..\\app\\api\\retrieval.py ${path.module}\\build; New-Item -ItemType Directory -Force ${path.module}\\build\\askanydoc_rag | Out-Null; Copy-Item ${path.module}\\..\\app\\shared\\askanydoc_rag\\*.py ${path.module}\\build\\askanydoc_rag; New-Item -ItemType Directory -Force ${path.module}\\build\\sharepoint | Out-Null; Copy-Item ${path.module}\\..\\app\\sharepoint\\*.py ${path.module}\\build\\sharepoint"
    interpreter = ["PowerShell", "-Command"]
  }
}

# Now zip the whole build folder containing libraries and answer_lambda_handler.py.
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/build"
  output_path = "${path.module}/lambda.zip"

  depends_on = [null_resource.install_deps] # wait for pip install to finish first
}


# Create lambda function
# It not a real API but a lambda function that works similar, receives request and sends back
# then upload the zip file
# lambda function Url comes in next block

resource "aws_lambda_function" "lambda_function" {
  function_name    = "askanydoc-api"
  role             = aws_iam_role.lambda_exec.arn
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256 # redeploy when the ZIP content changes
  handler          = "answer_lambda_handler.handler"                  # module.function inside the deployment ZIP
  runtime          = "python3.13"                                     # so that terraform knows if to do ZIP
  timeout          = 60
  memory_size      = 512

  environment {
    variables = {
      ANSWER_MODEL_ID              = "au.anthropic.claude-haiku-4-5-20251001-v1:0"
      EMBEDDING_MODEL_ID           = "amazon.titan-embed-text-v2:0"
      LANGFUSE_SECRET_ID           = "askanydoc/langfuse"
      MAX_HISTORY_CHARACTERS       = "12000"
      MAX_HISTORY_MESSAGES         = "12"
      MAX_RESPONSE_TOKENS          = "2048"
      MAX_TOOL_ROUNDS              = "2"
      MINIMUM_RETRIEVAL_SIMILARITY = "0.35"
      # SharePoint is an explicit, environment-specific gate. Safe defaults keep it
      # disabled until Copilot entitlement, identity, and retrieval tests are approved.
      SHAREPOINT_ENABLED             = tostring(var.sharepoint_enabled)
      SHAREPOINT_PROVIDER            = var.sharepoint_provider
      SHAREPOINT_GENERAL_SITE_URL    = var.sharepoint_general_site_url
      SHAREPOINT_RESTRICTED_SITE_URL = var.sharepoint_restricted_site_url
      SHAREPOINT_MAX_RESULTS         = tostring(var.sharepoint_max_results)
      SHAREPOINT_TIMEOUT_SECONDS     = "8"
      SHAREPOINT_MAX_RETRIES         = "2"
      ENTRA_TENANT_ID                = var.entra_tenant_id
      ENTRA_API_CLIENT_ID            = var.entra_api_client_id
      ENTRA_CREDENTIAL_SECRET_ID     = aws_secretsmanager_secret.entra_api_credential.id
      RETRIEVAL_RESULT_LIMIT         = "5"
      VECTOR_DATABASE_ARN            = aws_rds_cluster.vector_database.arn
      VECTOR_DATABASE_NAME           = aws_rds_cluster.vector_database.database_name
      VECTOR_DATABASE_SECRET_ARN     = aws_rds_cluster.vector_database.master_user_secret[0].secret_arn
    }
  }

  tags = {
    project    = "askanydoc"
    managed-by = "terraform"
  }
}

# STEP 3 — expose it publicly.


# Its a lambda + lambda url indeed

# Gate 1 for lambda URL - Gives a door to lambda
resource "aws_lambda_function_url" "lambda_function_url" {
  function_name      = aws_lambda_function.lambda_function.function_name
  authorization_type = "NONE" # no login needed
  # Gate 2 - CORS - the browser check - tells browser its ok for a webpage to call me
  # CORS is enforced by browser not Lambda
  cors {
    allow_origins = ["http://askanydoc-site-prod-apse2.s3-website-ap-southeast-2.amazonaws.com"]
    allow_methods = ["POST"]
    allow_headers = ["content-type"]
  }
}

# Gate 3 - two invoke Permissions
# allow invoke lambd through url
resource "aws_lambda_permission" "public_url_access" {
  statement_id           = "AllowPublicFunctionUrlAccess"
  action                 = "lambda:InvokeFunctionUrl"
  function_name          = aws_lambda_function.lambda_function.function_name
  principal              = "*"
  function_url_auth_type = "NONE"
}

# allow run lambda
resource "aws_lambda_permission" "public_invoke_function" {
  statement_id  = "AllowPublicInvokeFunction"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda_function.function_name
  principal     = "*"
}



