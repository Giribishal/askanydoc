"""Public HTTP boundary for the AskAnyDoc hybrid assistant."""

from __future__ import annotations

import hashlib
import json
import os
from functools import lru_cache
from typing import Any

from langfuse import get_client, observe

from askanydoc_rag.aws import aws_client
from assistant_orchestrator import SOURCE_MODES, run_assistant


secrets_client = aws_client("secretsmanager")


@lru_cache(maxsize=1)
def configure_langfuse() -> bool:
    """Load tracing credentials once; tracing failure must not block answers."""
    try:
        response = secrets_client.get_secret_value(SecretId=os.environ["LANGFUSE_SECRET_ID"])
        credentials = json.loads(response["SecretString"])
        os.environ["LANGFUSE_PUBLIC_KEY"] = credentials["langfuse_public_key"]
        os.environ["LANGFUSE_SECRET_KEY"] = credentials["langfuse_secret_key"]
        os.environ["LANGFUSE_HOST"] = credentials["langfuse_host"]
        return True
    except Exception as error:
        print(json.dumps({"event": "tracing_unavailable", "error_type": type(error).__name__}))
        return False


def _flush_tracing(tracing_enabled: bool) -> None:
    if tracing_enabled:
        try:
            get_client().flush()
        except Exception as error:
            print(json.dumps({"event": "trace_flush_failed", "error_type": type(error).__name__}))


@observe(name="hybrid-assistant", as_type="generation", capture_input=False, capture_output=False)
def answer_question(question: str, history: list[dict[str, str]]) -> dict[str, Any]:
    """Run one privacy-conscious, Claude-led hybrid assistant turn."""
    return run_assistant(question, history)


def _validated_history(value: Any) -> list[dict[str, str]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("History must be a list of messages.")

    max_messages = int(os.environ.get("MAX_HISTORY_MESSAGES", "12"))
    max_characters = int(os.environ.get("MAX_HISTORY_CHARACTERS", "12000"))
    if len(value) > max_messages:
        raise ValueError(f"History may contain at most {max_messages} messages.")

    history: list[dict[str, str]] = []
    total_characters = 0
    for item in value:
        if not isinstance(item, dict):
            raise ValueError("Each history message must be an object.")
        if not {"role", "content"}.issubset(item):
            raise ValueError("Each history message must contain role and content.")
        role = item["role"]
        content = item["content"]
        expected_fields = {"role", "content"} if role == "user" else {
            "role", "content", "source_mode"
        }
        if not set(item).issubset(expected_fields):
            raise ValueError("History messages contain unsupported fields.")
        if role not in {"user", "assistant"}:
            raise ValueError("History roles must be user or assistant.")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("History message content must be non-empty text.")
        content = content.strip()
        total_characters += len(content)
        if total_characters > max_characters:
            raise ValueError(f"History may contain at most {max_characters} characters.")
        validated_message = {"role": role, "content": content}
        source_mode = item.get("source_mode")
        if source_mode is not None:
            if role != "assistant" or source_mode not in SOURCE_MODES:
                raise ValueError("History source mode is invalid.")
            validated_message["source_mode"] = source_mode
        history.append(validated_message)
    return history


def _response(status_code: int, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload),
    }


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Validate one HTTP chat turn and return a source-attributed answer."""
    try:
        body = json.loads(event.get("body") or "{}")
    except (json.JSONDecodeError, TypeError):
        return _response(400, {"error": "Request body must be valid JSON."})

    question = body.get("question")
    if not isinstance(question, str) or not question.strip():
        return _response(400, {"error": "Question must be non-empty text."})
    question = question.strip()
    if len(question) > 4_000:
        return _response(400, {"error": "Question must be 4,000 characters or fewer."})
    try:
        history = _validated_history(body.get("history"))
    except ValueError as error:
        return _response(400, {"error": str(error)})

    request_id = getattr(context, "aws_request_id", None)
    question_hash = hashlib.sha256(question.encode("utf-8")).hexdigest()[:12]
    tracing_enabled = configure_langfuse()
    try:
        payload = answer_question(question, history)
        print(json.dumps({
            "event": "answer_completed",
            "request_id": request_id,
            "question_hash": question_hash,
            "history_messages": len(history),
            "source_mode": payload["source_mode"],
            "citation_count": len(payload["citations"]),
            "input_tokens": payload["input_tokens"],
            "output_tokens": payload["output_tokens"],
        }))
        return _response(200, payload)
    except Exception as error:
        print(json.dumps({
            "event": "answer_failed",
            "request_id": request_id,
            "question_hash": question_hash,
            "error_type": type(error).__name__,
        }))
        return _response(503, {
            "error": "AskAnyDoc could not complete the answer. Please try again.",
            "request_id": request_id,
        })
    finally:
        _flush_tracing(tracing_enabled)
