# Ingestion Lambda infrastructure.
# Runs the ingestion container from ECR, grants limited AWS access, and connects
# document uploads under uploads/ to that Lambda.

# IAM role assumed by the document-ingestion Lambda.
resource "aws_iam_role" "ingestion_lambda_exec" {
  name = "askanydoc-ingestion-prod-exec"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })

  tags = {
    project    = "askanydoc"
    managed-by = "terraform"
    purpose    = "rag-document-ingestion"
  }
}

# Allow the ingestion Lambda to write execution logs to CloudWatch.
resource "aws_iam_role_policy_attachment" "ingestion_lambda_logs" {
  role       = aws_iam_role.ingestion_lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Allow the ingestion Lambda to read only documents under uploads/.
resource "aws_iam_role_policy" "ingestion_s3_read" {
  name = "askanydoc-ingestion-prod-s3-read"
  role = aws_iam_role.ingestion_lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:GetObjectVersion"
        ]
        Resource = "${aws_s3_bucket.documents.arn}/uploads/*"
      }
    ]
  })
}

# Allow the ingestion Lambda to create embeddings with Titan V2.
resource "aws_iam_role_policy" "ingestion_titan_embedding" {
  name = "askanydoc-ingestion-prod-titan-embedding"
  role = aws_iam_role.ingestion_lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "bedrock:InvokeModel"
      Resource = "arn:aws:bedrock:ap-southeast-2::foundation-model/amazon.titan-embed-text-v2:0"
    }]
  })
}

# Allow SQL calls only against the AskAnyDoc vector database.
resource "aws_iam_role_policy" "ingestion_vector_database" {
  name = "askanydoc-ingestion-prod-vector-database"
  role = aws_iam_role.ingestion_lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "rds-data:BatchExecuteStatement",
          "rds-data:BeginTransaction",
          "rds-data:CommitTransaction",
          "rds-data:ExecuteStatement",
          "rds-data:RollbackTransaction"
        ]
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

# Keep failed asynchronous S3 events so an ingestion problem can be investigated.
resource "aws_sqs_queue" "ingestion_failed_events" {
  name                      = "askanydoc-ingestion-failed-events-prod"
  message_retention_seconds = 1209600
  sqs_managed_sse_enabled   = true

  tags = {
    project    = "askanydoc"
    managed-by = "terraform"
    purpose    = "rag-ingestion-failure-recovery"
  }
}

# Lambda uses its execution role to place exhausted asynchronous events in the queue.
resource "aws_iam_role_policy" "ingestion_failed_event_queue" {
  name = "askanydoc-ingestion-prod-failed-event-queue"
  role = aws_iam_role.ingestion_lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "sqs:SendMessage"
      Resource = aws_sqs_queue.ingestion_failed_events.arn
    }]
  })
}

# Create the image-based Lambda that receives and routes document-upload events.
resource "aws_lambda_function" "ingestion" {
  function_name = "askanydoc-ingestion-prod"
  role          = aws_iam_role.ingestion_lambda_exec.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.ingestion_lambda_images.repository_url}@sha256:3fba3a1042c6dae60fd99c20348e93ea149f5fe71a83d98b68aeb5faf97c6740"
  architectures = ["x86_64"]
  timeout       = 300
  memory_size   = 512

  dead_letter_config {
    target_arn = aws_sqs_queue.ingestion_failed_events.arn
  }

  environment {
    variables = {
      EMBEDDING_MODEL_ID         = "amazon.titan-embed-text-v2:0"
      MAX_DOCUMENT_BYTES         = "10485760"
      MAX_DOCUMENT_CHUNKS        = "200"
      VECTOR_DATABASE_ARN        = aws_rds_cluster.vector_database.arn
      VECTOR_DATABASE_SECRET_ARN = aws_rds_cluster.vector_database.master_user_secret[0].secret_arn
      VECTOR_DATABASE_NAME       = aws_rds_cluster.vector_database.database_name
    }
  }

  tags = {
    project    = "askanydoc"
    managed-by = "terraform"
    purpose    = "rag-document-ingestion"
  }
}

# Allow this document bucket to invoke the ingestion Lambda.
resource "aws_lambda_permission" "allow_document_bucket" {
  statement_id   = "AllowDocumentBucketInvoke"
  action         = "lambda:InvokeFunction"
  function_name  = aws_lambda_function.ingestion.function_name
  principal      = "s3.amazonaws.com"
  source_arn     = aws_s3_bucket.documents.arn
  source_account = data.aws_caller_identity.current.account_id

  lifecycle {
    replace_triggered_by = [aws_lambda_function.ingestion.package_type]
  }
}

# Invoke the ingestion Lambda for objects created under uploads/.
resource "aws_s3_bucket_notification" "document_ingestion" {
  bucket = aws_s3_bucket.documents.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.ingestion.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "uploads/"
  }

  depends_on = [aws_lambda_permission.allow_document_bucket]
}
