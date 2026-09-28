"""Tests for the long-running answer worker."""

import json
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError


API_DIR = Path(__file__).resolve().parent
SHARED_DIR = API_DIR.parent / "shared"
sys.path.insert(0, str(SHARED_DIR))
sys.path.insert(0, str(API_DIR))
os.environ.setdefault("AWS_EC2_METADATA_DISABLED", "true")
os.environ.setdefault("ANSWER_JOBS_TABLE_NAME", "answer-jobs")
os.environ.setdefault("ANSWER_JOBS_QUEUE_URL", "https://sqs.example/answer-jobs")

import answer_job_worker as worker


def queue_event(job_id: str = "job-1") -> dict:
    return {
        "Records": [{
            "messageId": "message-1",
            "receiptHandle": "receipt-1",
            "body": json.dumps({
                "job_id": job_id,
                "question": "Compare both sources",
                "history": [],
                "auth_context": {
                    "user_id": "user-1",
                    "tenant_id": "tenant-1",
                    "access_token": "api-access-token",
                },
            })
        }]
    }


class AnswerJobWorkerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dynamodb = MagicMock()
        self.dynamodb.update_item.return_value = {
            "Attributes": {"attempt_count": {"N": "1"}}
        }
        self.sqs = MagicMock()
        self.answer = {
            "answer": "Completed answer",
            "source_mode": "organisation_sources",
            "citations": [{"source_name": "source.pdf"}],
            "input_tokens": 100,
            "output_tokens": 20,
        }

    def test_worker_claims_and_completes_job(self) -> None:
        with (
            patch.object(worker, "dynamodb_client", self.dynamodb),
            patch.object(worker, "configure_langfuse", return_value=False),
            patch.object(worker, "answer_question", return_value=self.answer) as answer,
        ):
            response = worker.handler(queue_event(), SimpleNamespace(aws_request_id="request-1"))

        self.assertEqual(response, {"batchItemFailures": []})
        answer.assert_called_once()
        self.assertEqual(self.dynamodb.update_item.call_count, 2)
        completion = self.dynamodb.update_item.call_args.kwargs
        self.assertEqual(completion["ExpressionAttributeValues"][":completed"], {"S": "completed"})
        self.assertIn("retry_after", completion["UpdateExpression"])
        self.assertIn("last_error_code", completion["UpdateExpression"])
        stored = json.loads(completion["ExpressionAttributeValues"][":result"]["S"])
        self.assertEqual(stored, self.answer)

    def test_worker_records_controlled_failure(self) -> None:
        with (
            patch.object(worker, "dynamodb_client", self.dynamodb),
            patch.object(worker, "configure_langfuse", return_value=False),
            patch.object(worker, "answer_question", side_effect=RuntimeError("private detail")),
        ):
            worker.handler(queue_event(), SimpleNamespace(aws_request_id="request-failed"))

        failure = self.dynamodb.update_item.call_args.kwargs
        self.assertEqual(failure["ExpressionAttributeValues"][":failed"], {"S": "failed"})
        self.assertNotIn("private detail", json.dumps(failure))

    def test_database_resume_marks_job_pending_and_retries_only_failed_message(self) -> None:
        resume_error = ClientError(
            {"Error": {"Code": "DatabaseResumingException", "Message": "resuming"}},
            "ExecuteStatement",
        )
        with (
            patch.dict(os.environ, {
                "DATABASE_RESUME_MAX_JOB_ATTEMPTS": "3",
                "DATABASE_RESUME_RETRY_DELAY_SECONDS": "15",
            }),
            patch.object(worker, "dynamodb_client", self.dynamodb),
            patch.object(worker, "sqs_client", self.sqs),
            patch.object(worker, "configure_langfuse", return_value=False),
            patch.object(worker, "answer_question", side_effect=resume_error),
        ):
            response = worker.handler(
                queue_event(), SimpleNamespace(aws_request_id="request-resuming")
            )

        self.assertEqual(response, {
            "batchItemFailures": [{"itemIdentifier": "message-1"}]
        })
        retry_update = self.dynamodb.update_item.call_args.kwargs
        self.assertEqual(retry_update["ExpressionAttributeValues"][":pending"], {"S": "pending"})
        self.assertEqual(
            retry_update["ExpressionAttributeValues"][":error_code"],
            {"S": "DatabaseResumingException"},
        )
        self.sqs.change_message_visibility.assert_called_once_with(
            QueueUrl="https://sqs.example/answer-jobs",
            ReceiptHandle="receipt-1",
            VisibilityTimeout=15,
        )

    def test_database_resume_fails_job_after_attempt_cap(self) -> None:
        self.dynamodb.update_item.return_value = {
            "Attributes": {"attempt_count": {"N": "3"}}
        }
        resume_error = ClientError(
            {"Error": {"Code": "DatabaseResumingException", "Message": "resuming"}},
            "ExecuteStatement",
        )
        with (
            patch.dict(os.environ, {"DATABASE_RESUME_MAX_JOB_ATTEMPTS": "3"}),
            patch.object(worker, "dynamodb_client", self.dynamodb),
            patch.object(worker, "sqs_client", self.sqs),
            patch.object(worker, "configure_langfuse", return_value=False),
            patch.object(worker, "answer_question", side_effect=resume_error),
        ):
            response = worker.handler(
                queue_event(), SimpleNamespace(aws_request_id="request-terminal")
            )

        self.assertEqual(response, {"batchItemFailures": []})
        failure = self.dynamodb.update_item.call_args.kwargs
        self.assertEqual(failure["ExpressionAttributeValues"][":failed"], {"S": "failed"})
        self.sqs.change_message_visibility.assert_not_called()

    def test_worker_ignores_duplicate_or_already_completed_job(self) -> None:
        self.dynamodb.update_item.side_effect = ClientError(
            {"Error": {"Code": "ConditionalCheckFailedException", "Message": "condition"}},
            "UpdateItem",
        )
        with (
            patch.object(worker, "dynamodb_client", self.dynamodb),
            patch.object(worker, "answer_question") as answer,
        ):
            worker.handler(queue_event(), SimpleNamespace(aws_request_id="request-duplicate"))
        answer.assert_not_called()


if __name__ == "__main__":
    unittest.main()
