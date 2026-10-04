# Optional user-bound Salesforce Hosted MCP connector for the AskAnyDoc web UI.
# This creates separate state, credentials and compute; existing answer jobs stay intact.

variable "salesforce_web_enabled" {
  description = "Deploy the separately authorized Salesforce web connector."
  type        = bool
  default     = false
}

variable "salesforce_org_origin" {
  description = "Exact Developer Edition My Domain origin expected from Salesforce OAuth."
  type        = string
  default     = ""

  validation {
    condition     = !var.salesforce_web_enabled || can(regex("^https://[a-z0-9.-]+\\.my\\.salesforce\\.com$", var.salesforce_org_origin))
    error_message = "salesforce_org_origin must be the expected HTTPS My Domain origin when enabled."
  }
}

resource "aws_dynamodb_table" "salesforce_oauth_states" {
  count        = var.salesforce_web_enabled ? 1 : 0
  name         = "askanydoc-salesforce-oauth-states-dev"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "state_hash"

  attribute {
    name = "state_hash"
    type = "S"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = {
    project    = "askanydoc"
    managed-by = "terraform"
    purpose    = "salesforce-oauth-state"
  }
}

resource "aws_secretsmanager_secret" "salesforce_web_client" {
  count       = var.salesforce_web_enabled ? 1 : 0
  name        = "askanydoc/salesforce-web-client-dev"
  description = "Salesforce web ECA client ID and secret. Value entered after ECA setup, outside Terraform state."

  tags = {
    project    = "askanydoc"
    managed-by = "terraform"
    purpose    = "salesforce-web-client"
  }
}

resource "aws_iam_role" "salesforce_web_exec" {
  count = var.salesforce_web_enabled ? 1 : 0
  name  = "askanydoc-salesforce-web-exec"

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
    purpose    = "salesforce-web"
  }
}

resource "aws_iam_role_policy_attachment" "salesforce_web_logs" {
  count      = var.salesforce_web_enabled ? 1 : 0
  role       = aws_iam_role.salesforce_web_exec[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "salesforce_web_access" {
  count = var.salesforce_web_enabled ? 1 : 0
  name  = "askanydoc-salesforce-web-access"
  role  = aws_iam_role.salesforce_web_exec[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["dynamodb:PutItem", "dynamodb:DeleteItem"]
        Resource = aws_dynamodb_table.salesforce_oauth_states[0].arn
      },
      {
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = aws_secretsmanager_secret.salesforce_web_client[0].arn
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:CreateSecret",
          "secretsmanager:GetSecretValue",
          "secretsmanager:PutSecretValue",
          "secretsmanager:TagResource"
        ]
        Resource = "arn:aws:secretsmanager:ap-southeast-2:${data.aws_caller_identity.current.account_id}:secret:askanydoc/salesforce-grants-dev/*"
      },
      {
        Effect = "Allow"
        Action = ["bedrock:InvokeModel"]
        Resource = [
          "arn:aws:bedrock:ap-southeast-2:${data.aws_caller_identity.current.account_id}:inference-profile/au.anthropic.claude-haiku-4-5-20251001-v1:0",
          "arn:aws:bedrock:ap-southeast-2::foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0",
          "arn:aws:bedrock:ap-southeast-4::foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0"
        ]
      }
    ]
  })
}

resource "null_resource" "salesforce_web_package" {
  count = var.salesforce_web_enabled ? 1 : 0

  triggers = {
    source = sha256(join("", [for file in [
      "app/salesforce/__init__.py",
      "app/salesforce/read_adapter.py",
      "app/salesforce/crm_reader.py",
      "app/salesforce/evidence_endpoint.py",
      "app/salesforce/web_handler.py",
      "app/api/assistant_orchestrator.py",
      "app/api/answer_lambda_handler.py",
      "app/api/organisation_tools.py",
      "app/api/retrieval.py",
      "app/api/requirements.txt"
      , "infra/build_salesforce_web.ps1"
    ] : filesha256("${path.module}/../${file}")]))
  }

  provisioner "local-exec" {
    interpreter = ["PowerShell", "-Command"]
    command     = "& '${path.module}/build_salesforce_web.ps1'"
  }
}

data "archive_file" "salesforce_web_zip" {
  count       = var.salesforce_web_enabled ? 1 : 0
  type        = "zip"
  source_dir  = "${path.module}/salesforce_web_build"
  output_path = "${path.module}/salesforce_web.zip"

  depends_on = [null_resource.salesforce_web_package]
}

resource "aws_cloudwatch_log_group" "salesforce_web" {
  count             = var.salesforce_web_enabled ? 1 : 0
  name              = "/aws/lambda/askanydoc-salesforce-web-dev"
  retention_in_days = 30

  tags = {
    project    = "askanydoc"
    managed-by = "terraform"
    purpose    = "salesforce-web"
  }
}

resource "aws_lambda_function" "salesforce_web" {
  count            = var.salesforce_web_enabled ? 1 : 0
  function_name    = "askanydoc-salesforce-web-dev"
  role             = aws_iam_role.salesforce_web_exec[0].arn
  filename         = data.archive_file.salesforce_web_zip[0].output_path
  source_code_hash = data.archive_file.salesforce_web_zip[0].output_base64sha256
  handler          = "salesforce.web_handler.handler"
  runtime          = "python3.13"
  timeout          = 29
  memory_size      = 512

  depends_on = [aws_cloudwatch_log_group.salesforce_web]

  environment {
    variables = {
      SALESFORCE_WEB_CLIENT_SECRET_ID = aws_secretsmanager_secret.salesforce_web_client[0].id
      SALESFORCE_OAUTH_STATES_TABLE   = aws_dynamodb_table.salesforce_oauth_states[0].name
      SALESFORCE_WEB_CALLBACK_URL     = "https://${aws_cloudfront_distribution.frontend.domain_name}/"
      SALESFORCE_ORG_ORIGIN           = var.salesforce_org_origin
      ANSWER_MODEL_ID                 = "au.anthropic.claude-haiku-4-5-20251001-v1:0"
      MAX_RESPONSE_TOKENS             = "2048"
    }
  }

  tags = {
    project    = "askanydoc"
    managed-by = "terraform"
    purpose    = "salesforce-web"
  }
}

resource "aws_apigatewayv2_integration" "salesforce_web" {
  count                  = var.salesforce_web_enabled ? 1 : 0
  api_id                 = aws_apigatewayv2_api.protected_chat.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.salesforce_web[0].invoke_arn
  payload_format_version = "2.0"
  timeout_milliseconds   = 29000
}

resource "aws_apigatewayv2_route" "salesforce_connect" {
  count                = var.salesforce_web_enabled ? 1 : 0
  api_id               = aws_apigatewayv2_api.protected_chat.id
  route_key            = "POST /salesforce/connect"
  target               = "integrations/${aws_apigatewayv2_integration.salesforce_web[0].id}"
  authorization_type   = "JWT"
  authorizer_id        = aws_apigatewayv2_authorizer.entra.id
  authorization_scopes = [var.entra_api_scope_name]
}

resource "aws_apigatewayv2_route" "salesforce_disconnect" {
  count                = var.salesforce_web_enabled ? 1 : 0
  api_id               = aws_apigatewayv2_api.protected_chat.id
  route_key            = "POST /salesforce/disconnect"
  target               = "integrations/${aws_apigatewayv2_integration.salesforce_web[0].id}"
  authorization_type   = "JWT"
  authorizer_id        = aws_apigatewayv2_authorizer.entra.id
  authorization_scopes = [var.entra_api_scope_name]
}

resource "aws_apigatewayv2_route" "salesforce_complete" {
  count                = var.salesforce_web_enabled ? 1 : 0
  api_id               = aws_apigatewayv2_api.protected_chat.id
  route_key            = "POST /salesforce/complete"
  target               = "integrations/${aws_apigatewayv2_integration.salesforce_web[0].id}"
  authorization_type   = "JWT"
  authorizer_id        = aws_apigatewayv2_authorizer.entra.id
  authorization_scopes = [var.entra_api_scope_name]
}

resource "aws_apigatewayv2_route" "salesforce_status" {
  count                = var.salesforce_web_enabled ? 1 : 0
  api_id               = aws_apigatewayv2_api.protected_chat.id
  route_key            = "GET /salesforce/status"
  target               = "integrations/${aws_apigatewayv2_integration.salesforce_web[0].id}"
  authorization_type   = "JWT"
  authorizer_id        = aws_apigatewayv2_authorizer.entra.id
  authorization_scopes = [var.entra_api_scope_name]
}

resource "aws_apigatewayv2_route" "salesforce_ask" {
  count                = var.salesforce_web_enabled ? 1 : 0
  api_id               = aws_apigatewayv2_api.protected_chat.id
  route_key            = "POST /salesforce/ask"
  target               = "integrations/${aws_apigatewayv2_integration.salesforce_web[0].id}"
  authorization_type   = "JWT"
  authorizer_id        = aws_apigatewayv2_authorizer.entra.id
  authorization_scopes = [var.entra_api_scope_name]
}

resource "aws_lambda_permission" "api_gateway_salesforce_web" {
  count         = var.salesforce_web_enabled ? 1 : 0
  statement_id  = "AllowProtectedApiGatewaySalesforceWeb"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.salesforce_web[0].function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.protected_chat.execution_arn}/*/*"
}

output "salesforce_web_callback_url" {
  value = var.salesforce_web_enabled ? "https://${aws_cloudfront_distribution.frontend.domain_name}/" : null
}

resource "aws_apigatewayv2_route" "salesforce_evidence" {
  count                = var.salesforce_web_enabled ? 1 : 0
  api_id               = aws_apigatewayv2_api.protected_chat.id
  route_key            = "POST /salesforce/evidence"
  target               = "integrations/${aws_apigatewayv2_integration.salesforce_web[0].id}"
  authorization_type   = "JWT"
  authorizer_id        = aws_apigatewayv2_authorizer.entra.id
  authorization_scopes = [var.entra_api_scope_name]
}
