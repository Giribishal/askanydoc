# Container-image storage for the ingestion Lambda.
# Terraform creates this private ECR repository; Docker will later push the
# built ingestion image into it before Lambda is switched from ZIP to image.

moved {
  from = aws_ecr_repository.ingestion
  to   = aws_ecr_repository.ingestion_lambda_images
}

resource "aws_ecr_repository" "ingestion_lambda_images" {
  name                 = "askanydoc-ingestion-lambda-images-prod"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    project    = "askanydoc"
    managed-by = "terraform"
    purpose    = "rag-document-ingestion"
  }
}
