# HTTPS frontend and delegated Microsoft identity boundary for SharePoint retrieval.

variable "entra_tenant_id" {
  description = "Microsoft Entra tenant ID for the AskAnyDoc single-tenant applications."
  type        = string
}

variable "entra_api_client_id" {
  description = "Client ID of the confidential AskAnyDoc API app registration."
  type        = string
}

variable "entra_api_scope" {
  description = "Full delegated API scope, for example api://<api-client-id>/access_as_user."
  type        = string
}

variable "entra_api_scope_name" {
  description = "Scope name emitted in the Microsoft Entra scp claim."
  type        = string
  default     = "access_as_user"
}

variable "sharepoint_enabled" {
  description = "Explicit deployment gate for delegated SharePoint retrieval."
  type        = bool
  default     = false
}

variable "sharepoint_provider" {
  description = "Microsoft retrieval provider. Graph Search with bounded extraction is selected for this environment; Copilot Retrieval remains available for future eligible environments."
  type        = string
  default     = "graph_search"

  validation {
    condition     = contains(["graph_search", "copilot_retrieval"], var.sharepoint_provider)
    error_message = "sharepoint_provider must be graph_search or copilot_retrieval."
  }
}

variable "sharepoint_general_site_url" {
  description = "Approved general SharePoint site URL. Override before enabling SharePoint."
  type        = string
  default     = "https://example.invalid/general"
}

variable "sharepoint_restricted_site_url" {
  description = "Approved restricted SharePoint site URL. Override before enabling SharePoint."
  type        = string
  default     = "https://example.invalid/restricted"
}

variable "sharepoint_max_results" {
  description = "Maximum evidence items requested from the selected Microsoft provider."
  type        = number
  default     = 10

  validation {
    condition     = var.sharepoint_max_results >= 1 && var.sharepoint_max_results <= 25
    error_message = "sharepoint_max_results must be between 1 and 25."
  }
}

resource "aws_secretsmanager_secret" "entra_api_credential" {
  name        = "askanydoc/entra-api-credential-dev"
  description = "Entra confidential API credential for delegated SharePoint OBO. Value managed outside Terraform."

  tags = {
    project    = "askanydoc"
    managed-by = "terraform"
  }
}

resource "aws_cloudfront_origin_access_control" "frontend" {
  name                              = "askanydoc-frontend-oac"
  description                       = "Private S3 access for the AskAnyDoc HTTPS frontend"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "frontend" {
  enabled             = true
  default_root_object = "index.html"

  origin {
    domain_name              = aws_s3_bucket.website.bucket_regional_domain_name
    origin_id                = "askanydoc-frontend-s3"
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend.id
  }

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "askanydoc-frontend-s3"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = {
    project    = "askanydoc"
    managed-by = "terraform"
  }
}

resource "aws_apigatewayv2_api" "protected_chat" {
  name          = "askanydoc-protected-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["https://${aws_cloudfront_distribution.frontend.domain_name}"]
    allow_methods = ["GET", "POST", "OPTIONS"]
    allow_headers = ["authorization", "content-type"]
  }

  tags = {
    project    = "askanydoc"
    managed-by = "terraform"
  }
}

resource "aws_apigatewayv2_integration" "protected_chat" {
  api_id                 = aws_apigatewayv2_api.protected_chat.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.lambda_function.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_authorizer" "entra" {
  api_id           = aws_apigatewayv2_api.protected_chat.id
  authorizer_type  = "JWT"
  identity_sources = ["$request.header.Authorization"]
  name             = "askanydoc-entra-jwt"

  jwt_configuration {
    # Microsoft access tokens may identify this API by its client ID or its
    # default application ID URI. Accept both equivalent audience forms.
    audience = [var.entra_api_client_id, "api://${var.entra_api_client_id}"]
    # This app registration currently issues v1 access tokens, whose `iss`
    # claim uses the tenant-specific STS URL. API Gateway requires an exact
    # issuer match before it will invoke Lambda.
    issuer = "https://sts.windows.net/${var.entra_tenant_id}/"
  }
}

resource "aws_apigatewayv2_route" "chat" {
  api_id               = aws_apigatewayv2_api.protected_chat.id
  route_key            = "POST /chat"
  target               = "integrations/${aws_apigatewayv2_integration.protected_chat.id}"
  authorization_type   = "JWT"
  authorizer_id        = aws_apigatewayv2_authorizer.entra.id
  authorization_scopes = [var.entra_api_scope_name]
}

resource "aws_apigatewayv2_stage" "protected_chat" {
  api_id      = aws_apigatewayv2_api.protected_chat.id
  name        = "$default"
  auto_deploy = true

  default_route_settings {
    throttling_burst_limit = 5
    throttling_rate_limit  = 2
  }

  tags = {
    project    = "askanydoc"
    managed-by = "terraform"
  }
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowProtectedApiGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda_function.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.protected_chat.execution_arn}/*/*"
}
