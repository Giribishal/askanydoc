"""SQS worker for answer jobs that may exceed API Gateway's HTTP timeout."""

from __future__ import annotations

import hashlib
import json
import os
import time
from typing import Any

from botocore.exceptions import ClientError

from askanydoc_rag.aws import aws_client
from answer_lambda_handler import (
    _flush_tracing,
    _validated_history,
    answer_question,
    configure_langfuse,
)


dynamodb_client = aws_client("dynamodb")
sqs_client = aws_client("sqs")


def _claim_job(job_id: str) -> int | None:
    """Claim a pending job and return its attempt number, or decline the claim."""
    now = int(time.time())
    lease_seconds = int(os.environ.get("ANSWER_JOB_LEASE_SECONDS", "240"))
    try:
        response = dynamodb_client.update_item(
            TableName=os.environ["ANSWER_JOBS_TABLE_NAME"],
            Key={"job_id": {"S": job_id}},
            UpdateExpression=(
                "SET #status = :processing, updated_at = :now, "
                "lease_expires_at = :lease ADD attempt_count :one"
            ),
            ConditionExpression=(
                "#status = :pending OR "
                "(#status = :processing AND lease_expires_at < :now)"
            ),
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":pending": {"S": "pending"},
                ":processing": {"S": "processing"},
                ":now": {"N": str(now)},
                ":lease": {"N": str(now + lease_seconds)},
                ":one": {"N": "1"},
            },
            ReturnValues="ALL_NEW",
        )
        return int(response["Attributes"]["attempt_count"]["N"])
    except ClientError as error:
        if error.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
            return None
        raise


def _complete_job(job_id: str, payload: dict[str, Any], request_id: str | None) -> None:
    serialized = json.dumps(payload)
    if len(serialized.encode("utf-8")) > 300_000:
        raise ValueError("Answer result exceeds the bounded job-result size.")
    dynamodb_client.update_item(
        TableName=os.environ["ANSWER_JOBS_TABLE_NAME"],
        Key={"job_id": {"S": job_id}},
        UpdateExpression=(
            "SET #status = :completed, #result = :result, updated_at = :now, "
            "request_id = :request_id "
            "REMOVE lease_expires_at, retry_after, last_error_code"
        ),
        ConditionExpression="#status = :processing",
        ExpressionAttributeNames={"#status": "status", "#result": "result"},
        ExpressionAttributeValues={
            ":completed": {"S": "completed"},
            ":processing": {"S": "processing"},
            ":result": {"S": serialized},
            ":now": {"N": str(int(time.time()))},
            ":request_id": {"S": request_id or "unknown"},
        },
    )


def _fail_job(job_id: str, request_id: str | None) -> None:
    dynamodb_client.update_item(
        TableName=os.environ["ANSWER_JOBS_TABLE_NAME"],
        Key={"job_id": {"S": job_id}},
        UpdateExpression=(
            "SET #status = :failed, error_message = :error, updated_at = :now, "
            "request_id = :request_id "
            "REMOVE lease_expires_at, retry_after, last_error_code"
        ),
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={
            ":failed": {"S": "failed"},
            ":error": {"S": "AskAnyDoc could not complete the answer. Please try again."},
            ":now": {"N": str(int(time.time()))},
            ":request_id": {"S": request_id or "unknown"},
        },
    )


def _is_database_resuming(error: Exception) -> bool:
    return (
        isinstance(error, ClientError)
        and error.response.get("Error", {}).get("Code") == "DatabaseResumingException"
    )


def _error_code(error: Exception) -> str:
    if isinstance(error, ClientError):
        return error.response.get("Error", {}).get("Code", "unclassified_client_error")
    return getattr(error, "error_code", "unclassified_exception")


def _schedule_database_resume_retry(
    job_id: str,
    request_id: str | None,
    receipt_handle: str,
    attempt_count: int,
) -> int:
    """Release the job lease and briefly delay only this failed SQS message."""
    if not receipt_handle:
        raise ValueError("Answer job retry receipt handle is missing.")

    base_delay_seconds = int(os.environ.get("DATABASE_RESUME_RETRY_DELAY_SECONDS", "15"))
    delay_seconds = min(base_delay_seconds * (2 ** (attempt_count - 1)), 60)
    now = int(time.time())
    dynamodb_client.update_item(
        TableName=os.environ["ANSWER_JOBS_TABLE_NAME"],
        Key={"job_id": {"S": job_id}},
        UpdateExpression=(
            "SET #status = :pending, updated_at = :now, retry_after = :retry_after, "
            "last_error_code = :error_code, request_id = :request_id "
            "REMOVE lease_expires_at"
        ),
        ConditionExpression="#status = :processing",
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={
            ":pending": {"S": "pending"},
            ":processing": {"S": "processing"},
            ":now": {"N": str(now)},
            ":retry_after": {"N": str(now + delay_seconds)},
            ":error_code": {"S": "DatabaseResumingException"},
            ":request_id": {"S": request_id or "unknown"},
        },
    )
    sqs_client.change_message_visibility(
        QueueUrl=os.environ["ANSWER_JOBS_QUEUE_URL"],
        ReceiptHandle=receipt_handle,
        VisibilityTimeout=delay_seconds,
    )
    return delay_seconds


def _validated_payload(record: dict[str, Any]) -> tuple[str, str, list[dict[str, str]], dict[str, str]]:
    payload = json.loads(record.get("body") or "{}")
    job_id = payload.get("job_id")
    question = payload.get("question")
    auth_context = payload.get("auth_context")
    if not isinstance(job_id, str) or not job_id:
        raise ValueError("Answer job ID is missing.")
    if not isinstance(question, str) or not question.strip() or len(question.strip()) > 4_000:
        raise ValueError("Answer job question is invalid.")
    if not isinstance(auth_context, dict) or not all(
        isinstance(auth_context.get(key), str) and auth_context[key]
        for key in ("user_id", "tenant_id", "access_token")
    ):
        raise ValueError("Answer job identity context is invalid.")
    return job_id, question.strip(), _validated_history(payload.get("history")), auth_context


def _process_record(record: dict[str, Any], context: Any) -> bool:
    """Process one job and report whether this SQS message needs another attempt."""
    job_id, question, history, auth_context = _validated_payload(record)
    attempt_count = _claim_job(job_id)
    if attempt_count is None:
        print(json.dumps({"event": "answer_job_duplicate_ignored", "job_id": job_id}))
        return False

    request_id = getattr(context, "aws_request_id", None)
    question_hash = hashlib.sha256(question.encode("utf-8")).hexdigest()[:12]
    tracing_enabled = configure_langfuse()
    try:
        payload = answer_question(question, history, auth_context)
        _complete_job(job_id, payload, request_id)
        print(json.dumps({
            "event": "answer_job_completed",
            "job_id": job_id,
            "request_id": request_id,
            "question_hash": question_hash,
            "history_messages": len(history),
            "source_mode": payload["source_mode"],
            "citation_count": len(payload["citations"]),
            "input_tokens": payload["input_tokens"],
            "output_tokens": payload["output_tokens"],
        }))
    except Exception as error:
        max_attempts = int(os.environ.get("DATABASE_RESUME_MAX_JOB_ATTEMPTS", "3"))
        if _is_database_resuming(error) and attempt_count < max_attempts:
            try:
                retry_delay = _schedule_database_resume_retry(
                    job_id,
                    request_id,
                    record.get("receiptHandle") or "",
                    attempt_count,
                )
            except Exception as retry_error:
                _fail_job(job_id, request_id)
                print(json.dumps({
                    "event": "answer_job_retry_scheduling_failed",
                    "job_id": job_id,
                    "request_id": request_id,
                    "question_hash": question_hash,
                    "attempt_count": attempt_count,
                    "error_type": type(retry_error).__name__,
                }))
                return False
            print(json.dumps({
                "event": "answer_job_database_resume_retry_scheduled",
                "job_id": job_id,
                "request_id": request_id,
                "question_hash": question_hash,
                "attempt_count": attempt_count,
                "retry_delay_seconds": retry_delay,
            }))
            return True
        _fail_job(job_id, request_id)
        print(json.dumps({
            "event": "answer_job_failed",
            "job_id": job_id,
            "request_id": request_id,
            "question_hash": question_hash,
            "error_type": type(error).__name__,
            "failure_stage": getattr(error, "failure_stage", "answer_question"),
            "error_code": _error_code(error),
            "attempt_count": attempt_count,
        }))
    finally:
        _flush_tracing(tracing_enabled)
    return False


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Process the bounded SQS batch; infrastructure configures one job per batch."""
    batch_item_failures = []
    for record in event.get("Records", []):
        if _process_record(record, context):
            message_id = record.get("messageId")
            if not isinstance(message_id, str) or not message_id:
                raise ValueError("Retryable answer job message ID is missing.")
            batch_item_failures.append({"itemIdentifier": message_id})
    return {"batchItemFailures": batch_item_failures}
