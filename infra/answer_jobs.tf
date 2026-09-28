# Long-running answer jobs.
#
# API Gateway accepts a question quickly, SQS buffers the work, a dedicated
# worker reuses the existing answer core, and DynamoDB holds the short-lived
# result for the authenticated frontend to collect.

resource "aws_kms_key" "answer_jobs" {
  description             = "Encrypt AskAnyDoc answer-job requests and short-lived results"
  enable_key_rotation     = true
  deletion_window_in_days = 30

  tags = {
    project    = "askanydoc"
    managed-by = "terraform"
    purpose    = "answer-jobs"
  }
}

resource "aws_kms_alias" "answer_jobs" {
  name          = "alias/askanydoc-answer-jobs-prod"
  target_key_id = aws_kms_key.answer_jobs.key_id
}

resource "aws_dynamodb_table" "answer_jobs" {
  name         = "askanydoc-answer-jobs-prod"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "job_id"

  attribute {
    name = "job_id"
    type = "S"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.answer_jobs.arn
  }

  tags = {
    project    = "askanydoc"
    managed-by = "terraform"
    purpose    = "answer-jobs"
  }
}

resource "aws_sqs_queue" "answer_jobs_failed" {
  name                              = "askanydoc-answer-jobs-failed-prod"
  message_retention_seconds         = 3600
  kms_master_key_id                 = aws_kms_key.answer_jobs.arn
  kms_data_key_reuse_period_seconds = 300

  tags = {
    project    = "askanydoc"
    managed-by = "terraform"
    purpose    = "answer-jobs-dlq"
  }
}

resource "aws_sqs_queue" "answer_jobs" {
  name                              = "askanydoc-answer-jobs-prod"
  message_retention_seconds         = 3600
  visibility_timeout_seconds        = 1080
  receive_wait_time_seconds         = 20
  kms_master_key_id                 = aws_kms_key.answer_jobs.arn
  kms_data_key_reuse_period_seconds = 300

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.answer_jobs_failed.arn
    maxReceiveCount     = 5
  })

  tags = {
    project    = "askanydoc"
    managed-by = "terraform"
    purpose    = "answer-jobs"
  }
}

resource "aws_iam_role" "answer_job_api_exec" {
  name = "askanydoc-answer-job-api-exec"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = {
    project    = "askanydoc"
    managed-by = "terraform"
  }
}

resource "aws_iam_role_policy_attachment" "answer_job_api_logs" {
  role       = aws_iam_role.answer_job_api_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "answer_job_api_access" {
  name = "askanydoc-answer-job-api-access"
  role = aws_iam_role.answer_job_api_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem"
        ]
        Resource = aws_dynamodb_table.answer_jobs.arn
      },
      {
        Effect   = "Allow"
        Action   = "sqs:SendMessage"
        Resource = aws_sqs_queue.answer_jobs.arn
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey",
          "kms:Encrypt",
          "kms:GenerateDataKey"
        ]
        Resource = aws_kms_key.answer_jobs.arn
      }
    ]
  })
}

resource "aws_iam_role" "answer_job_worker_exec" {
  name = "askanydoc-answer-job-worker-exec"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = {
    project    = "askanydoc"
    managed-by = "terraform"
  }
}

resource "aws_iam_role_policy_attachment" "answer_job_worker_queue" {
  role       = aws_iam_role.answer_job_worker_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaSQSQueueExecutionRole"
}

resource "aws_iam_role_policy" "answer_job_worker_access" {
  name = "askanydoc-answer-job-worker-access"
  role = aws_iam_role.answer_job_worker_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = "bedrock:InvokeModel"
        Resource = [
          "arn:aws:bedrock:ap-southeast-2:404584456165:inference-profile/au.anthropic.claude-haiku-4-5-20251001-v1:0",
          "arn:aws:bedrock:ap-southeast-2::foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0",
          "arn:aws:bedrock:ap-southeast-4::foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0",
          "arn:aws:bedrock:ap-southeast-2::foundation-model/amazon.titan-embed-text-v2:0"
        ]
      },
      {
        Effect = "Allow"
        Action = "secretsmanager:GetSecretValue"
        Resource = [
          "arn:aws:secretsmanager:ap-southeast-2:404584456165:secret:askanydoc/langfuse-ipOX9p",
          aws_secretsmanager_secret.entra_api_credential.arn,
          aws_rds_cluster.vector_database.master_user_secret[0].secret_arn
        ]
      },
      {
        Effect   = "Allow"
        Action   = "rds-data:ExecuteStatement"
        Resource = aws_rds_cluster.vector_database.arn
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:UpdateItem"
        ]
        Resource = aws_dynamodb_table.answer_jobs.arn
      },
      {
        Effect   = "Allow"
        Action   = "sqs:ChangeMessageVisibility"
        Resource = aws_sqs_queue.answer_jobs.arn
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey",
          "kms:GenerateDataKey"
        ]
        Resource = aws_kms_key.answer_jobs.arn
      }
    ]
  })
}

resource "null_resource" "install_answer_jobs_deps" {
  triggers = {
    requirements = filesha256("${path.module}/../app/api/requirements.txt")
    api_code = sha256(join("", [
      for file in [
        "answer_job_api_handler.py",
        "answer_job_worker.py",
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

  provisioner "local-exec" {
    command     = "if (Test-Path ${path.module}\\answer_jobs_build) { Remove-Item -Recurse -Force ${path.module}\\answer_jobs_build }; pip install -r ${path.module}/../app/api/requirements.txt -t ${path.module}/answer_jobs_build --platform manylinux2014_x86_64 --python-version 3.13 --implementation cp --abi cp313 --only-binary=:all: --upgrade; Copy-Item ${path.module}\\..\\app\\api\\answer_job_api_handler.py,${path.module}\\..\\app\\api\\answer_job_worker.py,${path.module}\\..\\app\\api\\answer_lambda_handler.py,${path.module}\\..\\app\\api\\assistant_orchestrator.py,${path.module}\\..\\app\\api\\organisation_tools.py,${path.module}\\..\\app\\api\\retrieval.py ${path.module}\\answer_jobs_build; New-Item -ItemType Directory -Force ${path.module}\\answer_jobs_build\\askanydoc_rag | Out-Null; Copy-Item ${path.module}\\..\\app\\shared\\askanydoc_rag\\*.py ${path.module}\\answer_jobs_build\\askanydoc_rag; New-Item -ItemType Directory -Force ${path.module}\\answer_jobs_build\\sharepoint | Out-Null; Copy-Item ${path.module}\\..\\app\\sharepoint\\*.py ${path.module}\\answer_jobs_build\\sharepoint"
    interpreter = ["PowerShell", "-Command"]
  }
}

data "archive_file" "answer_jobs_zip" {
  type        = "zip"
  source_dir  = "${path.module}/answer_jobs_build"
  output_path = "${path.module}/answer_jobs.zip"

  depends_on = [null_resource.install_answer_jobs_deps]
}

resource "aws_lambda_function" "answer_job_api" {
  function_name    = "askanydoc-answer-job-api"
  role             = aws_iam_role.answer_job_api_exec.arn
  filename         = data.archive_file.answer_jobs_zip.output_path
  source_code_hash = data.archive_file.answer_jobs_zip.output_base64sha256
  handler          = "answer_job_api_handler.handler"
  runtime          = "python3.13"
  timeout          = 15
  memory_size      = 256

  depends_on = [aws_cloudwatch_log_group.answer_job_api]

  environment {
    variables = {
      ANSWER_JOBS_TABLE_NAME = aws_dynamodb_table.answer_jobs.name
      ANSWER_JOBS_QUEUE_URL  = aws_sqs_queue.answer_jobs.url
      JOB_TTL_SECONDS        = "3600"
      MAX_HISTORY_CHARACTERS = "12000"
      MAX_HISTORY_MESSAGES   = "12"
    }
  }

  tags = {
    project    = "askanydoc"
    managed-by = "terraform"
    purpose    = "answer-jobs-api"
  }
}

resource "aws_lambda_function" "answer_job_worker" {
  function_name    = "askanydoc-answer-job-worker"
  role             = aws_iam_role.answer_job_worker_exec.arn
  filename         = data.archive_file.answer_jobs_zip.output_path
  source_code_hash = data.archive_file.answer_jobs_zip.output_base64sha256
  handler          = "answer_job_worker.handler"
  runtime          = "python3.13"
  timeout          = 180
  memory_size      = 512

  depends_on = [aws_cloudwatch_log_group.answer_job_worker]

  environment {
    variables = {
      ANSWER_JOBS_TABLE_NAME              = aws_dynamodb_table.answer_jobs.name
      ANSWER_JOBS_QUEUE_URL               = aws_sqs_queue.answer_jobs.url
      ANSWER_JOB_LEASE_SECONDS            = "240"
      ANSWER_MODEL_ID                     = "au.anthropic.claude-haiku-4-5-20251001-v1:0"
      DATABASE_RESUME_MAX_WAIT_SECONDS    = "15"
      DATABASE_RESUME_MAX_JOB_ATTEMPTS    = "3"
      DATABASE_RESUME_RETRY_DELAY_SECONDS = "15"
      EMBEDDING_MODEL_ID                  = "amazon.titan-embed-text-v2:0"
      LANGFUSE_SECRET_ID                  = "askanydoc/langfuse"
      MAX_HISTORY_CHARACTERS              = "12000"
      MAX_HISTORY_MESSAGES                = "12"
      MAX_RESPONSE_TOKENS                 = "2048"
      MAX_TOOL_ROUNDS                     = "2"
      MINIMUM_RETRIEVAL_SIMILARITY        = "0.35"
      SHAREPOINT_ENABLED                  = tostring(var.sharepoint_enabled)
      SHAREPOINT_PROVIDER                 = var.sharepoint_provider
      SHAREPOINT_GENERAL_SITE_URL         = var.sharepoint_general_site_url
      SHAREPOINT_RESTRICTED_SITE_URL      = var.sharepoint_restricted_site_url
      SHAREPOINT_MAX_RESULTS              = tostring(var.sharepoint_max_results)
      SHAREPOINT_TIMEOUT_SECONDS          = "8"
      SHAREPOINT_MAX_RETRIES              = "2"
      ENTRA_TENANT_ID                     = var.entra_tenant_id
      ENTRA_API_CLIENT_ID                 = var.entra_api_client_id
      ENTRA_CREDENTIAL_SECRET_ID          = aws_secretsmanager_secret.entra_api_credential.id
      RETRIEVAL_RESULT_LIMIT              = "5"
      VECTOR_DATABASE_ARN                 = aws_rds_cluster.vector_database.arn
      VECTOR_DATABASE_NAME                = aws_rds_cluster.vector_database.database_name
      VECTOR_DATABASE_SECRET_ARN          = aws_rds_cluster.vector_database.master_user_secret[0].secret_arn
    }
  }

  tags = {
    project    = "askanydoc"
    managed-by = "terraform"
    purpose    = "answer-jobs-worker"
  }
}

resource "aws_cloudwatch_log_group" "answer_job_api" {
  name              = "/aws/lambda/askanydoc-answer-job-api"
  retention_in_days = 30

  tags = {
    project    = "askanydoc"
    managed-by = "terraform"
    purpose    = "answer-jobs-api"
  }
}

resource "aws_cloudwatch_log_group" "answer_job_worker" {
  name              = "/aws/lambda/askanydoc-answer-job-worker"
  retention_in_days = 30

  tags = {
    project    = "askanydoc"
    managed-by = "terraform"
    purpose    = "answer-jobs-worker"
  }
}

resource "aws_lambda_event_source_mapping" "answer_jobs" {
  event_source_arn        = aws_sqs_queue.answer_jobs.arn
  function_name           = aws_lambda_function.answer_job_worker.arn
  batch_size              = 1
  enabled                 = true
  function_response_types = ["ReportBatchItemFailures"]

  scaling_config {
    maximum_concurrency = 2
  }
}

resource "aws_apigatewayv2_integration" "answer_jobs" {
  api_id                 = aws_apigatewayv2_api.protected_chat.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.answer_job_api.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "create_answer_job" {
  api_id               = aws_apigatewayv2_api.protected_chat.id
  route_key            = "POST /jobs"
  target               = "integrations/${aws_apigatewayv2_integration.answer_jobs.id}"
  authorization_type   = "JWT"
  authorizer_id        = aws_apigatewayv2_authorizer.entra.id
  authorization_scopes = [var.entra_api_scope_name]
}

resource "aws_apigatewayv2_route" "get_answer_job" {
  api_id               = aws_apigatewayv2_api.protected_chat.id
  route_key            = "GET /jobs/{jobId}"
  target               = "integrations/${aws_apigatewayv2_integration.answer_jobs.id}"
  authorization_type   = "JWT"
  authorizer_id        = aws_apigatewayv2_authorizer.entra.id
  authorization_scopes = [var.entra_api_scope_name]
}

resource "aws_lambda_permission" "api_gateway_answer_jobs" {
  statement_id  = "AllowProtectedApiGatewayAnswerJobs"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.answer_job_api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.protected_chat.execution_arn}/*/*"
}
