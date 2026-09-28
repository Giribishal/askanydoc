"""Tests for the authenticated asynchronous answer-job API."""

import json
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch


API_DIR = Path(__file__).resolve().parent
SHARED_DIR = API_DIR.parent / "shared"
sys.path.insert(0, str(SHARED_DIR))
sys.path.insert(0, str(API_DIR))
os.environ.setdefault("AWS_EC2_METADATA_DISABLED", "true")
os.environ.setdefault("ANSWER_JOBS_TABLE_NAME", "answer-jobs")
os.environ.setdefault("ANSWER_JOBS_QUEUE_URL", "https://sqs.example/answer-jobs")

import answer_job_api_handler as jobs_api


def authenticated_event(route_key: str, **values):
    event = {
        "routeKey": route_key,
        "headers": {"authorization": "Bearer api-access-token"},
        "requestContext": {
            "authorizer": {"jwt": {"claims": {"oid": "user-1", "tid": "tenant-1"}}}
        },
    }
    event.update(values)
    return event


class AnswerJobApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dynamodb = MagicMock()
        self.sqs = MagicMock()

    def test_create_job_persists_owner_and_queues_work(self) -> None:
        event = authenticated_event(
            "POST /jobs",
            body=json.dumps({"question": "Compare both sources", "history": []}),
        )
        with (
            patch.object(jobs_api, "dynamodb_client", self.dynamodb),
            patch.object(jobs_api, "sqs_client", self.sqs),
            patch.object(jobs_api.uuid, "uuid4", return_value="job-1"),
            patch.object(jobs_api.time, "time", return_value=1000),
        ):
            response = jobs_api.handler(event, SimpleNamespace(aws_request_id="request-1"))

        self.assertEqual(response["statusCode"], 202)
        self.assertEqual(json.loads(response["body"]), {"job_id": "job-1", "status": "pending"})
        item = self.dynamodb.put_item.call_args.kwargs["Item"]
        self.assertEqual(item["status"], {"S": "pending"})
        self.assertEqual(item["expires_at"], {"N": "4600"})
        self.assertNotIn("user-1", json.dumps(item))
        queued = json.loads(self.sqs.send_message.call_args.kwargs["MessageBody"])
        self.assertEqual(queued["job_id"], "job-1")
        self.assertEqual(queued["auth_context"]["access_token"], "api-access-token")

    def test_create_job_rejects_invalid_question_before_queueing(self) -> None:
        event = authenticated_event("POST /jobs", body=json.dumps({"question": "  "}))
        with (
            patch.object(jobs_api, "dynamodb_client", self.dynamodb),
            patch.object(jobs_api, "sqs_client", self.sqs),
        ):
            response = jobs_api.handler(event, None)
        self.assertEqual(response["statusCode"], 400)
        self.dynamodb.put_item.assert_not_called()
        self.sqs.send_message.assert_not_called()

    def test_status_hides_job_owned_by_another_user(self) -> None:
        self.dynamodb.get_item.return_value = {
            "Item": {"owner_hash": {"S": "different-owner"}, "status": {"S": "completed"}}
        }
        event = authenticated_event("GET /jobs/{jobId}", pathParameters={"jobId": "job-1"})
        with patch.object(jobs_api, "dynamodb_client", self.dynamodb):
            response = jobs_api.handler(event, None)
        self.assertEqual(response["statusCode"], 404)

    def test_status_returns_completed_answer_to_owner(self) -> None:
        auth = {"tenant_id": "tenant-1", "user_id": "user-1", "access_token": "unused"}
        result = {"answer": "Completed", "source_mode": "organisation_sources", "citations": []}
        self.dynamodb.get_item.return_value = {
            "Item": {
                "owner_hash": {"S": jobs_api._owner_hash(auth)},
                "status": {"S": "completed"},
                "result": {"S": json.dumps(result)},
                "expires_at": {"N": "4600"},
            }
        }
        event = authenticated_event("GET /jobs/{jobId}", pathParameters={"jobId": "job-1"})
        with (
            patch.object(jobs_api, "dynamodb_client", self.dynamodb),
            patch.object(jobs_api.time, "time", return_value=1000),
        ):
            response = jobs_api.handler(event, None)
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(json.loads(response["body"])["result"], result)

    def test_status_rejects_expired_job_even_before_ttl_deletes_it(self) -> None:
        auth = {"tenant_id": "tenant-1", "user_id": "user-1", "access_token": "unused"}
        self.dynamodb.get_item.return_value = {
            "Item": {
                "owner_hash": {"S": jobs_api._owner_hash(auth)},
                "status": {"S": "completed"},
                "result": {"S": json.dumps({"answer": "stale"})},
                "expires_at": {"N": "999"},
            }
        }
        event = authenticated_event("GET /jobs/{jobId}", pathParameters={"jobId": "job-1"})
        with (
            patch.object(jobs_api, "dynamodb_client", self.dynamodb),
            patch.object(jobs_api.time, "time", return_value=1000),
        ):
            response = jobs_api.handler(event, None)
        self.assertEqual(response["statusCode"], 410)
        self.assertEqual(json.loads(response["body"])["status"], "expired")


if __name__ == "__main__":
    unittest.main()
