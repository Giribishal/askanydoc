"""Authenticated request/status boundary for long-running AskAnyDoc answers."""

from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from typing import Any

from askanydoc_rag.aws import aws_client
from answer_lambda_handler import _auth_context, _validated_history


dynamodb_client = aws_client("dynamodb")
sqs_client = aws_client("sqs")


def _response(status_code: int, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
        },
        "body": json.dumps(payload),
    }


def _owner_hash(auth_context: dict[str, str]) -> str:
    """Create a stable owner key without storing Entra identity claims in the job row."""
    owner = f"{auth_context['tenant_id']}:{auth_context['user_id']}"
    return hashlib.sha256(owner.encode("utf-8")).hexdigest()


def _validated_request(event: dict[str, Any]) -> tuple[str, list[dict[str, str]]]:
    try:
        body = json.loads(event.get("body") or "{}")
    except (json.JSONDecodeError, TypeError) as error:
        raise ValueError("Request body must be valid JSON.") from error

    question = body.get("question")
    if not isinstance(question, str) or not question.strip():
        raise ValueError("Question must be non-empty text.")
    question = question.strip()
    if len(question) > 4_000:
        raise ValueError("Question must be 4,000 characters or fewer.")
    return question, _validated_history(body.get("history"))


def _create_job(event: dict[str, Any], context: Any) -> dict[str, Any]:
    auth_context = _auth_context(event)
    if auth_context is None:
        return _response(401, {"error": "A valid organisation sign-in is required."})

    try:
        question, history = _validated_request(event)
    except ValueError as error:
        return _response(400, {"error": str(error)})

    job_id = str(uuid.uuid4())
    now = int(time.time())
    expires_at = now + int(os.environ.get("JOB_TTL_SECONDS", "3600"))
    request_id = getattr(context, "aws_request_id", None)
    question_hash = hashlib.sha256(question.encode("utf-8")).hexdigest()[:12]

    dynamodb_client.put_item(
        TableName=os.environ["ANSWER_JOBS_TABLE_NAME"],
        Item={
            "job_id": {"S": job_id},
            "owner_hash": {"S": _owner_hash(auth_context)},
            "status": {"S": "pending"},
            "question_hash": {"S": question_hash},
            "created_at": {"N": str(now)},
            "updated_at": {"N": str(now)},
            "expires_at": {"N": str(expires_at)},
        },
        ConditionExpression="attribute_not_exists(job_id)",
    )

    job_payload = {
        "job_id": job_id,
        "question": question,
        "history": history,
        "auth_context": auth_context,
    }
    try:
        sqs_client.send_message(
            QueueUrl=os.environ["ANSWER_JOBS_QUEUE_URL"],
            MessageBody=json.dumps(job_payload),
        )
    except Exception:
        dynamodb_client.update_item(
            TableName=os.environ["ANSWER_JOBS_TABLE_NAME"],
            Key={"job_id": {"S": job_id}},
            UpdateExpression="SET #status = :failed, error_message = :error, updated_at = :now",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":failed": {"S": "failed"},
                ":error": {"S": "The answer job could not be queued. Please try again."},
                ":now": {"N": str(int(time.time()))},
            },
        )
        raise

    print(json.dumps({
        "event": "answer_job_created",
        "job_id": job_id,
        "request_id": request_id,
        "question_hash": question_hash,
        "history_messages": len(history),
    }))
    return _response(202, {"job_id": job_id, "status": "pending"})


def _get_job(event: dict[str, Any]) -> dict[str, Any]:
    auth_context = _auth_context(event)
    if auth_context is None:
        return _response(401, {"error": "A valid organisation sign-in is required."})

    path_parameters = event.get("pathParameters") or {}
    job_id = path_parameters.get("jobId")
    if not isinstance(job_id, str) or not job_id:
        return _response(400, {"error": "Job ID is required."})

    response = dynamodb_client.get_item(
        TableName=os.environ["ANSWER_JOBS_TABLE_NAME"],
        Key={"job_id": {"S": job_id}},
        ConsistentRead=True,
    )
    item = response.get("Item")
    if not item or item.get("owner_hash", {}).get("S") != _owner_hash(auth_context):
        return _response(404, {"error": "Answer job was not found."})

    try:
        expires_at = int(item["expires_at"]["N"])
    except (KeyError, TypeError, ValueError):
        return _response(500, {
            "job_id": job_id,
            "status": "failed",
            "error": "The stored answer job is invalid.",
        })
    if int(time.time()) >= expires_at:
        return _response(410, {
            "job_id": job_id,
            "status": "expired",
            "error": "This answer job has expired. Please ask the question again.",
        })

    status = item.get("status", {}).get("S")
    if status in {"pending", "processing"}:
        return _response(202, {"job_id": job_id, "status": status})
    if status == "completed":
        try:
            result = json.loads(item["result"]["S"])
        except (KeyError, json.JSONDecodeError, TypeError):
            return _response(500, {
                "job_id": job_id,
                "status": "failed",
                "error": "The stored answer result is invalid.",
            })
        return _response(200, {"job_id": job_id, "status": status, "result": result})
    if status == "failed":
        return _response(200, {
            "job_id": job_id,
            "status": status,
            "error": item.get("error_message", {}).get(
                "S", "AskAnyDoc could not complete the answer. Please try again."
            ),
            "request_id": item.get("request_id", {}).get("S"),
        })
    return _response(500, {"job_id": job_id, "status": "failed", "error": "Invalid job state."})


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Create an answer job or return its status for the authenticated owner."""
    route_key = event.get("routeKey") or event.get("requestContext", {}).get("routeKey")
    try:
        if route_key == "POST /jobs":
            return _create_job(event, context)
        if route_key == "GET /jobs/{jobId}":
            return _get_job(event)
        return _response(404, {"error": "Route not found."})
    except Exception as error:
        print(json.dumps({
            "event": "answer_job_api_failed",
            "request_id": getattr(context, "aws_request_id", None),
            "error_type": type(error).__name__,
        }))
        return _response(503, {
            "error": "AskAnyDoc could not manage the answer job. Please try again.",
            "request_id": getattr(context, "aws_request_id", None),
        })
