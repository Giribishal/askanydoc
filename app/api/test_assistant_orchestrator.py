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

from assistant_orchestrator import (
    AssistantOrchestrationError,
    _final_payload,
    _finalization_messages,
    run_assistant,
)


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
    def test_finalization_messages_remove_tool_blocks_and_include_evidence(self) -> None:
        messages = [
            {"role": "user", "content": [{"text": "What is our RAG design?"}]},
            {"role": "assistant", "content": [{"toolUse": {
                "toolUseId": "tool-1",
                "name": "search_aws_documents",
                "input": {"query": "RAG design"},
            }}]},
            {"role": "user", "content": [{"toolResult": {
                "toolUseId": "tool-1",
                "content": [{"json": {"evidence": []}}],
            }}]},
        ]
        evidence = [{
            "chunk_text": "Use vector retrieval.",
            "source_name": "rag.pdf",
            "location": {"page_number": 4},
            "similarity": 0.8,
        }]

        final_messages = _finalization_messages(messages, evidence)

        serialized = json.dumps(final_messages, separators=(",", ":"))
        self.assertNotIn("toolUse", serialized)
        self.assertNotIn("toolResult", serialized)
        self.assertIn("What is our RAG design?", serialized)
        self.assertIn("Use vector retrieval.", serialized)
        self.assertIn("evidence_number", serialized)

    def test_multiple_structured_text_blocks_include_diagnostics(self) -> None:
        response = {
            "stopReason": "end_turn",
            "output": {"message": {"content": [
                {"text": '{"answer":"first"}'},
                {"text": '{"answer":"second"}'},
            ]}},
        }

        with self.assertRaises(AssistantOrchestrationError) as raised:
            _final_payload(
                response,
                evidence=[{"similarity": 0.8}],
                usage={"input_tokens": 10, "output_tokens": 5},
                organisation_search_used=True,
            )

        error = raised.exception
        self.assertEqual(error.error_code, "structured_answer_block_count_invalid")
        self.assertEqual(error.failure_stage, "final_response_validation")
        self.assertEqual(error.diagnostics["text_block_count"], 2)
        self.assertEqual(error.diagnostics["content_block_types"], ["text", "text"])
        self.assertEqual(error.diagnostics["evidence_count"], 1)

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

    def test_authenticated_request_exposes_sharepoint_capability_to_converse(self) -> None:
        response = final_response("Ready.", "conversation")
        auth_context = {
            "user_id": "adele",
            "tenant_id": "tenant",
            "access_token": "token",
        }
        with (
            patch("assistant_orchestrator.sharepoint_tool_available", return_value=True),
            patch("assistant_orchestrator._converse", return_value=response) as converse,
        ):
            run_assistant("Hello", [], auth_context)

        self.assertTrue(converse.call_args.kwargs["sharepoint_available"])

    def test_tool_evidence_produces_application_built_citation(self) -> None:
        tool_request = {
            "stopReason": "tool_use",
            "output": {"message": {"role": "assistant", "content": [{"toolUse": {
                "toolUseId": "tool-1",
                "name": "search_aws_documents",
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

    def test_tool_round_limit_forces_final_answer_without_tools(self) -> None:
        tool_request = {
            "stopReason": "tool_use",
            "output": {"message": {"role": "assistant", "content": [{"toolUse": {
                "toolUseId": "tool-1",
                "name": "search_aws_documents",
                "input": {"query": "RAG options"},
            }}]}},
            "usage": {"inputTokens": 30, "outputTokens": 5},
        }
        another_search = {
            "stopReason": "tool_use",
            "output": {"message": {"role": "assistant", "content": [{"toolUse": {
                "toolUseId": "tool-2",
                "name": "search_aws_documents",
                "input": {"query": "more RAG options"},
            }}]}},
            "usage": {"inputTokens": 40, "outputTokens": 6},
        }
        final = final_response(
            "The evidence describes managed and custom RAG options.",
            "organisation_sources",
            citation_numbers=[1],
            input_tokens=50,
            output_tokens=12,
        )
        evidence = [{
            "chunk_text": "Managed and custom RAG options.",
            "source_name": "rag.pdf",
            "source_type": "pdf",
            "source_uri": "s3://documents/rag.pdf",
            "object_key": "uploads/rag.pdf",
            "location": {"page_number": 4},
            "similarity": 0.8,
        }]
        tool_result = {"toolUseId": "tool-1", "content": [{"json": {"evidence": []}}]}
        with (
            patch.dict(os.environ, {"MAX_TOOL_ROUNDS": "1"}),
            patch(
                "assistant_orchestrator._converse",
                side_effect=[tool_request, another_search, final],
            ) as converse,
            patch(
                "assistant_orchestrator.execute_organisation_tool",
                return_value=(tool_result, evidence),
            ),
        ):
            payload = run_assistant("Compare our RAG options.", [])

        self.assertEqual(payload["source_mode"], "organisation_sources")
        self.assertEqual(payload["citations"][0]["source_name"], "rag.pdf")
        self.assertEqual(payload["input_tokens"], 120)
        self.assertEqual(converse.call_args_list[-1].kwargs, {"tools_enabled": False})
        final_messages = converse.call_args_list[-1].args[0]
        self.assertNotIn("toolUse", json.dumps(final_messages))
        self.assertNotIn("toolResult", json.dumps(final_messages))
        self.assertIn("Managed and custom RAG options.", json.dumps(final_messages))

    def test_empty_final_response_gets_one_tool_disabled_recovery(self) -> None:
        empty = {
            "stopReason": "end_turn",
            "output": {"message": {"role": "assistant", "content": []}},
            "usage": {"inputTokens": 60, "outputTokens": 8},
        }
        recovered = final_response(
            "The available evidence supports this answer.",
            "general_knowledge",
            input_tokens=30,
            output_tokens=10,
        )
        with patch(
            "assistant_orchestrator._converse",
            side_effect=[empty, recovered],
        ) as converse:
            payload = run_assistant("Explain RAG.", [])

        self.assertEqual(payload["answer"], "The available evidence supports this answer.")
        self.assertEqual(payload["input_tokens"], 90)
        self.assertEqual(len(converse.call_args_list), 2)
        self.assertEqual(converse.call_args_list[-1].kwargs, {"tools_enabled": False})

    def test_failed_forced_finalization_is_not_retried_again(self) -> None:
        empty = {
            "stopReason": "end_turn",
            "output": {"message": {"role": "assistant", "content": []}},
            "usage": {"inputTokens": 60, "outputTokens": 8},
        }
        with patch(
            "assistant_orchestrator._converse",
            side_effect=[empty, empty],
        ) as converse:
            with self.assertRaises(AssistantOrchestrationError) as raised:
                run_assistant("Explain RAG.", [])

        self.assertEqual(raised.exception.error_code, "forced_finalization_failed")
        self.assertEqual(len(converse.call_args_list), 2)

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

        def inspect_messages(messages, **kwargs):
            self.assertFalse(kwargs["sharepoint_available"])
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
