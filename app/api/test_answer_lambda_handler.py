"""Focused tests for the grounded answer HTTP boundary."""

import json
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


API_DIR = Path(__file__).resolve().parent
SHARED_DIR = API_DIR.parent / "shared"
sys.path.insert(0, str(SHARED_DIR))
sys.path.insert(0, str(API_DIR))
os.environ.setdefault("AWS_EC2_METADATA_DISABLED", "true")

from answer_lambda_handler import answer_question, handler


class AnswerLambdaTests(unittest.TestCase):
    def test_invalid_question_is_rejected_before_retrieval(self) -> None:
        with patch("answer_lambda_handler.answer_question") as answer:
            response = handler({"body": json.dumps({"question": "   "})}, None)
        self.assertEqual(response["statusCode"], 400)
        answer.assert_not_called()

    def test_no_evidence_returns_grounded_false_without_claude(self) -> None:
        with (
            patch("answer_lambda_handler.retrieve_evidence", return_value=[]),
            patch("answer_lambda_handler.generate_grounded_answer") as generate,
        ):
            payload = answer_question("What is the leave policy?")
        self.assertFalse(payload["grounded"])
        self.assertEqual(payload["citations"], [])
        generate.assert_not_called()

    def test_http_response_preserves_grounded_answer_and_citations(self) -> None:
        payload = {
            "answer": "Use phishing-resistant MFA.",
            "confidence": 0.91,
            "grounded": True,
            "citations": [{"source_name": "security.pdf", "location": {"page_number": 4}}],
            "input_tokens": 100,
            "output_tokens": 20,
        }
        with patch("answer_lambda_handler.answer_question", return_value=payload):
            response = handler(
                {"body": json.dumps({"question": "What MFA is recommended?"})},
                SimpleNamespace(aws_request_id="request-1"),
            )
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(json.loads(response["body"]), payload)


if __name__ == "__main__":
    unittest.main()
