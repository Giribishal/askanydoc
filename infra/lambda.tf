#It does four simple things, in order:

# 1. Gives the code permission to exist and run in AWS (an identity + the right to call Bedrock)
# 2. Zips up handler.py so AWS can upload it
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
      Effect   = "Allow"
      Action   = "bedrock:InvokeModel"
      Resource = "*" # Resource specifies which specific thing 
    }]               # so here * means the role may call all the bedrock models
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

# ── CHUNK 2: PACKAGE -> CREATE -> EXPOSE -> PRINT ──

# Zip lambda handler - code that runs in lambda

# Downloads instructor + pydantic into a build/ folder, and copies handler.py in too.
# null_resource = "run this command" - not a real AWS thing, just a local action.
resource "null_resource" "install_deps" {
  # triggers = re-run this step whenever requirements.txt OR handler.py if these file change.
  triggers = {
    requirements = filesha256("${path.module}/../app/api/requirements.txt")
    handler_code = filesha256("${path.module}/../app/api/handler.py")
  }

  # if (Test-Path ...\build) { Remove-Item -Recurse -Force ...\build } — if a build folder already exists, delete it and everything in it (fresh start).
  # pip install -r ...requirements.txt -t ...\build [flags] — install the deps from requirements.txt into the build folder (-t = target directory, which is what creates build).
  # copy ...\handler.py ...\build\handler.py — copy your handler into that same folder.

  provisioner "local-exec" {
    command     = "if (Test-Path ${path.module}\\build) { Remove-Item -Recurse -Force ${path.module}\\build }; pip install -r ${path.module}/../app/api/requirements.txt -t ${path.module}/build --platform manylinux2014_x86_64 --python-version 3.13 --implementation cp --abi cp313 --only-binary=:all: --upgrade; copy ${path.module}\\..\\app\\api\\handler.py ${path.module}\\build\\handler.py"
    interpreter = ["PowerShell", "-Command"]
  }
}

# Now zip the WHOLE build folder (libraries + handler.py), not just handler.py alone.
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
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256 # compare the handler.py and findout
  handler          = "handler.handler"                                # if any changes in the handler code
  runtime          = "python3.13"                                     # so that terraform knows if to do ZIP
  timeout          = 30                                               # and upload the zip again
  memory_size      = 256

  tags = {
    project    = "askanydoc"
    managed-by = "terraform"
  }
}

# STEP 3 — expose it publicly.


# Its a lambda + lambda url indeed

resource "aws_lambda_function_url" "lambda_function_url" {
  function_name      = aws_lambda_function.lambda_function.function_name
  authorization_type = "NONE" # no login needed

  cors {
    allow_origins = ["*"]
    allow_methods = ["POST"]
    allow_headers = ["content-type"]
  }
}

resource "aws_lambda_permission" "public_url_access" {
  statement_id           = "AllowPublicFunctionUrlAccess"
  action                 = "lambda:InvokeFunctionUrl"
  function_name          = aws_lambda_function.lambda_function.function_name
  principal              = "*"
  function_url_auth_type = "NONE"
}

resource "aws_lambda_permission" "public_invoke_function" {
  statement_id  = "AllowPublicInvokeFunction"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda_function.function_name
  principal     = "*"
}


# STEP 4 — print the URL so you don't dig in the console.

output "api_url" {
  value = aws_lambda_function_url.lambda_function_url.function_url
}

