# Terraform outputs.
# Displays the deployed endpoints and resource names used during verification.

output "website_url" {
  value = aws_s3_bucket_website_configuration.bucket_config.website_endpoint
}

output "api_url" {
  value = aws_lambda_function_url.lambda_function_url.function_url
}

output "https_website_url" {
  value = "https://${aws_cloudfront_distribution.frontend.domain_name}"
}

output "protected_api_url" {
  value = "${aws_apigatewayv2_api.protected_chat.api_endpoint}/chat"
}

output "document_bucket_name" {
  value = aws_s3_bucket.documents.bucket
}

output "ingestion_lambda_name" {
  value = aws_lambda_function.ingestion.function_name
}

output "ingestion_ecr_repository_url" {
  value = aws_ecr_repository.ingestion_lambda_images.repository_url
}

output "vector_database_cluster_arn" {
  value = aws_rds_cluster.vector_database.arn
}

output "vector_database_secret_arn" {
  value = aws_rds_cluster.vector_database.master_user_secret[0].secret_arn
}

output "vector_database_name" {
  value = aws_rds_cluster.vector_database.database_name
}
