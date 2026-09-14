# S3 bucket infrastructure.
# Creates the public frontend bucket and the separate private document bucket.

# Public bucket that hosts the AskAnyDoc frontend.
resource "aws_s3_bucket" "website" {
  bucket = "askanydoc-site-prod-apse2"

  tags = {
    project    = "askanydoc"
    managed-by = "terraform"
  }
}

# Configure the public bucket as a static website.
resource "aws_s3_bucket_website_configuration" "bucket_config" {
  bucket = aws_s3_bucket.website.id

  index_document {
    suffix = "index.html"
  }
}

# Permit public website access. This applies only to the frontend bucket.
resource "aws_s3_bucket_public_access_block" "website_public_access" {
  bucket = aws_s3_bucket.website.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# Allow browsers to read the static website files.
resource "aws_s3_bucket_policy" "bucket_policy" {
  bucket = aws_s3_bucket.website.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.website.arn}/*"
      }
    ]
  })
}

# Preserve the existing Terraform-managed index while moving to the React build.
moved {
  from = aws_s3_object.website_page_upload
  to   = aws_s3_object.frontend_files["index.html"]
}

# Upload every built React asset with correct browser metadata.
resource "aws_s3_object" "frontend_files" {
  for_each = fileset("${path.module}/../frontend/dist", "**")

  bucket = aws_s3_bucket.website.id
  key    = each.value
  source = "${path.module}/../frontend/dist/${each.value}"
  etag   = filemd5("${path.module}/../frontend/dist/${each.value}")
  content_type = lookup({
    css  = "text/css"
    html = "text/html"
    js   = "application/javascript"
    svg  = "image/svg+xml"
  }, try(reverse(split(".", each.value))[0], ""), "application/octet-stream")
  cache_control = can(regex("^assets/", each.value)) ? "public,max-age=31536000,immutable" : "no-cache"
}

# Private bucket that stores original documents for RAG ingestion.
resource "aws_s3_bucket" "documents" {
  bucket = "askanydoc-documents-prod-apse2"

  tags = {
    project    = "askanydoc"
    managed-by = "terraform"
    purpose    = "rag-document-ingestion"
  }
}

# Encrypt uploaded documents at rest with S3-managed keys.
resource "aws_s3_bucket_server_side_encryption_configuration" "documents" {
  bucket = aws_s3_bucket.documents.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Retain older object versions when a document is replaced.
resource "aws_s3_bucket_versioning" "documents" {
  bucket = aws_s3_bucket.documents.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Prevent public access to company documents.
resource "aws_s3_bucket_public_access_block" "documents" {
  bucket = aws_s3_bucket.documents.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
