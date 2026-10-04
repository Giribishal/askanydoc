"""Contract tests for shared answers, source isolation and bounded failures."""
import json
import os
import unittest
from unittest.mock import Mock, patch

import httpx
from botocore.exceptions import ClientError
import shared_source_controller as shared
from salesforce.evidence_endpoint import crm_evidence

os.environ.setdefault("ANSWER_MODEL_ID", "test-model")


def evidence(source):
    return {"chunk_text": "Recorded fact", "source_name": source, "source_type": source,
            "source_uri": "https://example.com/" + source, "location": {}, "object_key": "", "similarity": None}


def envelope(source):
    return {"evidence": [evidence(source)], "truncated": False, "input_tokens": 2, "output_tokens": 1}


def response(value):
    return {"stopReason": "end_turn", "output": {"message": {"content": [{"text": json.dumps(value)}]}},
            "usage": {"inputTokens": 3, "outputTokens": 2}}


class SharedSourceTests(unittest.TestCase):
    def setUp(self):
        self.question = "Use Salesforce CRM, AWS disaster recovery and SharePoint hybrid cloud together."
        self.adapters = {key: shared.SourceAdapter(key, key + " facts", Mock(return_value=envelope(key)), (key,))
                         for key in ("aws", "sharepoint", "salesforce")}
        self.plan = {"disposition": "search", "aws": "disaster recovery", "sharepoint": "hybrid cloud connectivity",
                     "sharepoint_fallback": "hybrid cloud", "salesforce": "Case VPN status"}

    def run_answer(self, final=None):
        with patch.object(shared, "_checked_converse", return_value=response(self.plan)), \
             patch.object(shared, "_converse", return_value=response(final or {"answer": "Supported comparison", "source_mode": "organisation_sources", "citation_numbers": [1, 2, 3]})):
            return shared.run_shared_answer(self.question, [], {}, adapters=self.adapters)

    def test_three_sources_have_independent_queries_and_validated_citations(self):
        answer = self.run_answer()
        self.assertEqual([c["source_type"] for c in answer["citations"]], ["aws", "sharepoint", "salesforce"])
        self.assertEqual(answer["source_outcomes"], dict.fromkeys(self.adapters, "found"))
        self.adapters["salesforce"].fetch.assert_called_once_with("Case VPN status", "")
        self.adapters["aws"].fetch.assert_called_once_with("disaster recovery", "")
        self.assertEqual(answer["input_tokens"], 12)
        self.assertIn("not an exhaustive record list", answer["answer"])

    def test_invalid_plan_executes_no_source(self):
        self.plan["invented"] = "query"
        with self.assertRaises(ValueError):
            self.run_answer()
        for adapter in self.adapters.values():
            adapter.fetch.assert_not_called()

    def test_decline_executes_no_source(self):
        self.plan = {key: "" for key in self.plan}
        self.plan["disposition"] = "decline"
        answer = self.run_answer()
        self.assertEqual(answer["citations"], [])
        for adapter in self.adapters.values():
            adapter.fetch.assert_not_called()

    def test_disconnected_source_keeps_supported_answer_and_discloses_gap(self):
        self.adapters.pop("salesforce")
        self.plan.pop("salesforce")
        answer = self.run_answer({"answer": "Document comparison only", "source_mode": "organisation_sources", "citation_numbers": [1, 2]})
        self.assertEqual(len(answer["citations"]), 2)
        self.assertIn("salesforce (unavailable)", answer["answer"])

    def test_wrong_source_evidence_is_dropped_before_synthesis(self):
        self.adapters["salesforce"].fetch.return_value = envelope("other-user")
        answer = self.run_answer({"answer": "Document facts", "source_mode": "organisation_sources", "citation_numbers": [1, 2]})
        self.assertEqual(answer["source_outcomes"]["salesforce"], "unavailable")
        self.assertEqual(len(answer["citations"]), 2)

    def test_database_resume_preserves_existing_retry(self):
        self.adapters["aws"].fetch.side_effect = ClientError({"Error": {"Code": "DatabaseResumingException"}}, "ExecuteStatement")
        with self.assertRaises(ClientError):
            self.run_answer()

    def test_generic_controller_accepts_another_registered_adapter(self):
        adapter = shared.SourceAdapter("future", "future records", Mock(return_value=envelope("future")), ("future",))
        with patch.object(shared, "_checked_converse", return_value=response({"disposition": "search", "future": "records"})), \
             patch.object(shared, "_converse", return_value=response({"answer": "Fact", "source_mode": "organisation_sources", "citation_numbers": [1]})):
            answer = shared.run_shared_answer("records", [], {}, adapters={"future": adapter}, requested_sources=("future",))
        self.assertEqual(answer["citations"][0]["source_type"], "future")

    def test_redirect_is_not_followed_and_user_token_goes_only_to_fixed_api(self):
        with patch.dict(os.environ, {"SALESFORCE_EVIDENCE_URL": "https://example.execute-api.ap-southeast-2.amazonaws.com/salesforce/evidence"}), \
             patch.object(shared.httpx, "Client") as client:
            client.return_value.__enter__.return_value.post.return_value = httpx.Response(307, headers={"location": "https://attacker.example"}, request=httpx.Request("POST", "https://example.com"))
            adapter = shared._salesforce_adapter({"access_token": "caller-token"})
            with self.assertRaises(httpx.HTTPStatusError):
                adapter.fetch("Case VPN", "")
            self.assertFalse(client.call_args.kwargs["follow_redirects"])
            sent = client.return_value.__enter__.return_value.post.call_args
            self.assertEqual(sent.kwargs["headers"], {"Authorization": "Bearer caller-token"})

    def test_no_match_truncation_and_invalid_citations_are_honest(self):
        self.adapters["aws"].fetch.return_value = {"evidence": [], "truncated": False}
        self.adapters["salesforce"].fetch.return_value["truncated"] = True
        answer = self.run_answer({"answer": "Partial facts", "source_mode": "organisation_sources", "citation_numbers": [1, 2]})
        self.assertEqual(len(answer["citations"]), 2)
        self.assertIn("aws (no_match)", answer["answer"])
        self.assertIn("salesforce (truncated)", answer["answer"])
        with self.assertRaises(ValueError):
            self.run_answer({"answer": "Invented", "source_mode": "organisation_sources", "citation_numbers": [999]})

    def test_evidence_endpoint_uses_claim_owner_and_no_model_identity(self):
        async def read(plan, token, org):
            self.assertEqual(token, "sf-user-token")
            return [evidence("salesforce")], False
        auth = {"tenant_id": "tenant", "user_id": "current", "access_token": "entra"}
        load = Mock(return_value={"access_token": "sf-user-token", "instance_url": "https://demo.my.salesforce.com"})
        kwargs = dict(load_grant=load, refresh_grant=lambda o, g: g, owner_hash=lambda a: a["user_id"], read_crm=read)
        with patch("salesforce.evidence_endpoint.plan_reads", return_value={"reads": [{"object": "Case"}]}):
            status, result = crm_evidence(auth, {"question": "VPN Case status"}, **kwargs)
        self.assertEqual(status, 200)
        load.assert_called_once_with("current")
        self.assertEqual(crm_evidence(auth, {"question": "VPN", "user_id": "other"}, **kwargs)[0], 400)
        self.assertEqual(crm_evidence(None, {"question": "VPN"}, **kwargs)[0], 401)


if __name__ == "__main__":
    unittest.main()
