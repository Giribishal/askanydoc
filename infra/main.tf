terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~>5.92"
    }
  }

  required_version = ">=1.2"
}

provider "aws" {
  region = "ap-southeast-2"
}

# Create S3 bucket
resource "aws_s3_bucket" "website" {
  bucket = "askanydoc-site-prod-apse2"

  tags = {
    project    = "askanydoc"
    managed-by = "terraform"
  }
}

resource "aws_s3_bucket_website_configuration" "bucket_config" {

  # type = resource type - aws_s3_bucket   nickname = name we gave = bucket_config
  # attribute = specific Value we want from it like - website_endpoint, ID etc
  bucket = aws_s3_bucket.website.id

  index_document {
    suffix = "index.html"
  }
}

# Unlock public accesss to guardrails (aws blocks public by default)
resource "aws_s3_bucket_public_access_block" "website_public_access" {
  bucket = aws_s3_bucket.website.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# Actual Permission- Anyone may read the files
resource "aws_s3_bucket_policy" "bucket_policy" {
  bucket = aws_s3_bucket.website.id
  policy = jsonencode({
    Version = "2012-10-17" # Policy language version - Fixed magic no
    Statement = [          # List of rules
      {
        Sid       = "PublicReadGetObject" # Statement Id
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.website.arn}/*"
      }
    ]
  })
}

resource "aws_s3_object" "website_page_upload" {
  bucket       = aws_s3_bucket.website.id
  key          = "index.html"
  source       = "../site/index.html"
  content_type = "text/html"

}
