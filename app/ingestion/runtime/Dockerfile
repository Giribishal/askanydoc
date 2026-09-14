# Container recipe for the AskAnyDoc ingestion Lambda.
# It starts with AWS's Python 3.13 Lambda runtime, installs the extraction
# dependencies, and copies the ingestion handler into the Lambda task directory.

# Pin the current linux/amd64 image so repeated v1 builds use the same foundation.
FROM public.ecr.aws/lambda/python:3.13@sha256:8565868e1caeac6b69fc5c75ac2f1509b85672f4b0e69908f5a575d377a63905

COPY app/ingestion/runtime/requirements.txt .
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy the reusable RAG package and ingestion-specific adapters only.
COPY app/shared/askanydoc_rag "${LAMBDA_TASK_ROOT}/askanydoc_rag"
COPY app/ingestion/runtime/*.py "${LAMBDA_TASK_ROOT}/"

CMD ["ingestion_lambda_handler.handler"]
