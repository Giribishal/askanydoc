"""Focused tests for Claude-led hybrid assistant orchestration."""

import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


API_DIR = Path(__file__).resolve().parent
SHARED_DIR = API_DIR.parent / "shared"
sys.path.insert(0, str(SHARED_DIR))
sys.path.insert(0, str(API_DIR))
os.environ.setdefault("AWS_EC2_METADATA_DISABLED", "true")
os.environ.setdefault("ANSWER_MODEL_ID", "test-model")

from assistant_orchestrator import run_assistant


def final_response(answer, source_mode, citation_numbers=None, input_tokens=20, output_tokens=10):
    result = {
        "answer": answer,
        "source_mode": source_mode,
        "citation_numbers": citation_numbers or [],
    }
    return {
        "stopReason": "end_turn",
        "output": {"message": {"role": "assistant", "content": [{"text": json.dumps(result)}]}},
        "usage": {"inputTokens": input_tokens, "outputTokens": output_tokens},
    }


class AssistantOrchestratorTests(unittest.TestCase):
    def test_claude_handles_normal_conversation_without_source_search(self) -> None:
        response = final_response("I'm AskAnyDoc. How can I help?", "conversation")
        with (
            patch("assistant_orchestrator._converse", return_value=response),
            patch("assistant_orchestrator.execute_organisation_tool") as execute,
        ):
            payload = run_assistant("Who are you?", [])
        self.assertEqual(payload["source_mode"], "conversation")
        self.assertEqual(payload["answer"], "I'm AskAnyDoc. How can I help?")
        execute.assert_not_called()

    def test_claude_can_answer_general_knowledge_without_source_search(self) -> None:
        response = final_response("RAG combines retrieval and generation.", "general_knowledge")
        with (
            patch("assistant_orchestrator._converse", return_value=response),
            patch("assistant_orchestrator.execute_organisation_tool") as execute,
        ):
            payload = run_assistant("How does RAG work?", [])
        self.assertEqual(payload["source_mode"], "general_knowledge")
        self.assertEqual(payload["citations"], [])
        execute.assert_not_called()

    def test_tool_evidence_produces_application_built_citation(self) -> None:
        tool_request = {
            "stopReason": "tool_use",
            "output": {"message": {"role": "assistant", "content": [{"toolUse": {
                "toolUseId": "tool-1",
                "name": "search_organisation_sources",
                "input": {"query": "Essential Eight maturity levels"},
            }}]}},
            "usage": {"inputTokens": 30, "outputTokens": 5},
        }
        final = final_response(
            "There are four maturity levels.",
            "organisation_sources",
            citation_numbers=[1],
            input_tokens=40,
            output_tokens=12,
        )
        evidence = [{
            "chunk_text": "The model has four maturity levels.",
            "source_name": "essential-eight.pdf",
            "source_type": "pdf",
            "source_uri": "s3://documents/essential-eight.pdf",
            "object_key": "uploads/essential-eight.pdf",
            "location": {"page_number": 2},
            "similarity": 0.81,
        }]
        tool_result = {"toolUseId": "tool-1", "content": [{"json": {"evidence": []}}]}
        with (
            patch("assistant_orchestrator._converse", side_effect=[tool_request, final]),
            patch(
                "assistant_orchestrator.execute_organisation_tool",
                return_value=(tool_result, evidence),
            ),
        ):
            payload = run_assistant("What are our maturity levels?", [])
        self.assertTrue(payload["grounded"])
        self.assertEqual(payload["citations"][0]["source_name"], "essential-eight.pdf")
        self.assertEqual(payload["retrieval_score"], 0.81)
        self.assertEqual(payload["input_tokens"], 70)

    def test_model_cannot_invent_a_citation_number(self) -> None:
        response = final_response("Unsupported claim.", "organisation_sources", [1])
        with patch("assistant_orchestrator._converse", return_value=response):
            with self.assertRaisesRegex(ValueError, "not returned by a tool"):
                run_assistant("What is our policy?", [])

    def test_model_cannot_claim_missing_organisation_data_without_searching(self) -> None:
        response = final_response(
            "I could not find that in your organisation's sources.",
            "organisation_not_found",
        )
        with patch("assistant_orchestrator._converse", return_value=response):
            with self.assertRaisesRegex(ValueError, "cannot be claimed without a search"):
                run_assistant("What is our leave policy?", [])

    def test_recent_history_is_sent_to_claude_for_followups(self) -> None:
        history = [
            {"role": "user", "content": "Explain RAG."},
            {
                "role": "assistant",
                "content": "RAG combines retrieval and generation.",
                "source_mode": "general_knowledge",
            },
        ]

        def inspect_messages(messages):
            self.assertEqual(messages[0]["content"][0]["text"], "Explain RAG.")
            self.assertIn("general_knowledge", messages[1]["content"][0]["text"])
            self.assertEqual(messages[-1]["content"][0]["text"], "Explain that more.")
            return final_response("Here is more detail.", "general_knowledge")

        with patch("assistant_orchestrator._converse", side_effect=inspect_messages):
            payload = run_assistant("Explain that more.", history)
        self.assertEqual(payload["answer"], "Here is more detail.")

    def test_claude_interprets_acceptance_of_general_fallback(self) -> None:
        history = [
            {"role": "user", "content": "What is our parental leave policy?"},
            {
                "role": "assistant",
                "content": "I could not find that in your organisation sources.",
                "source_mode": "organisation_not_found",
            },
        ]
        decision = {
            "stopReason": "end_turn",
            "output": {"message": {"role": "assistant", "content": [{"text": json.dumps({
                "intent": "accept_general",
                "answer": "General parental-leave rules vary by jurisdiction.",
            })}]}},
            "usage": {"inputTokens": 50, "outputTokens": 20},
        }
        with (
            patch("assistant_orchestrator.bedrock_client.converse", return_value=decision),
            patch("assistant_orchestrator._converse") as converse,
        ):
            payload = run_assistant("Yes, please continue.", history)
        self.assertEqual(payload["source_mode"], "general_knowledge")
        self.assertEqual(payload["input_tokens"], 50)
        converse.assert_not_called()


if __name__ == "__main__":
    unittest.main()
