"""Checks for bounded Salesforce queries and provenance validation."""

import asyncio
import unittest
from types import SimpleNamespace

from app.salesforce.read_adapter import SalesforceReadError, case_as_answer_evidence, case_query, read_case


CASE_ID = "500bm00003BZO62AAH"
ORG = "https://orgfarm-cc062a4e4e-dev-ed.develop.my.salesforce.com"


class ReadAdapterTests(unittest.TestCase):
    def test_query_is_bounded_and_rejects_injection(self):
        self.assertEqual(case_query(CASE_ID), (
            "SELECT Id, CaseNumber, Subject, Status, Priority, Origin, AccountId "
            f"FROM Case WHERE Id = '{CASE_ID}' LIMIT 1"
        ))
        for bad in ("", "500abc' OR Name != ''", "001bm000031S8dFAAS", CASE_ID + " "):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                case_query(bad)

    def test_record_and_citation_are_validated(self):
        calls = []

        async def call_tool(name, arguments):
            calls.append((name, arguments))
            return SimpleNamespace(isError=False, structuredContent={"records": [{
                "Id": CASE_ID, "CaseNumber": "00001027", "Subject": "Warehouse VPN intermittently disconnects",
                "Status": "New", "Priority": "High", "Origin": "Phone", "AccountId": "001bm000031S8dFAAS",
            }]})

        evidence = asyncio.run(read_case(CASE_ID, call_tool, org_origin=ORG))
        self.assertEqual(evidence["facts"]["Status"], "New")
        self.assertEqual(evidence["facts"]["Priority"], "High")
        self.assertEqual(evidence["source_uri"], f"{ORG}/lightning/r/Case/{CASE_ID}/view")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], "soqlQuery")
        self.assertEqual(calls[0][1], {"q": case_query(CASE_ID)})
        answer_evidence = case_as_answer_evidence(evidence)
        self.assertIn("Status: New", answer_evidence["chunk_text"])
        self.assertIn("Priority: High", answer_evidence["chunk_text"])
        self.assertEqual(answer_evidence["location"], {"record_id": CASE_ID})
        self.assertEqual(answer_evidence["source_uri"], evidence["source_uri"])

    def test_missing_and_mismatched_records(self):
        async def missing(*_):
            return SimpleNamespace(isError=False, structuredContent={"records": []})

        async def wrong(*_):
            return SimpleNamespace(isError=False, structuredContent={"records": [{"Id": "500bm00003BZO63AAH"}]})

        self.assertIsNone(asyncio.run(read_case(CASE_ID, missing, org_origin=ORG)))
        with self.assertRaises(SalesforceReadError):
            asyncio.run(read_case(CASE_ID, wrong, org_origin=ORG))

    def test_tool_error_and_untrusted_org_fail_closed(self):
        async def tool_error(*_):
            return SimpleNamespace(isError=True, structuredContent={"records": []})

        with self.assertRaises(SalesforceReadError):
            asyncio.run(read_case(CASE_ID, tool_error, org_origin=ORG))
        with self.assertRaises(ValueError):
            asyncio.run(read_case(CASE_ID, tool_error, org_origin="https://example.com"))


if __name__ == "__main__":
    unittest.main()
