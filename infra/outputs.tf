output "website_url" {
  value = aws_s3_bucket_website_configuration.bucket_config.website_endpoint

}