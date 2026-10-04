"""Security and data-contract checks for the bounded CRM compiler/executor."""
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from salesforce.crm_reader import compile_query, retrieve
from salesforce.read_adapter import SalesforceReadError


def read(obj="Case", search="VPN", account="", filters=None):
    return {"object": obj, "search": search, "account_name": account, "filters": filters or []}


def result(records, error=False):
    return SimpleNamespace(isError=error, structuredContent={"records": records})


class QueryTests(unittest.TestCase):
    def test_quote_and_wildcards_cannot_expand_query(self):
        query = compile_query(read(search="x' OR Id != null OR Subject LIKE '%_\\"))
        self.assertIn("x\\' OR Id != null OR Subject LIKE \\'\\%\\_\\\\", query)
        self.assertTrue(query.endswith("LIMIT 11"))

    def test_disallowed_objects_fields_and_operators_rejected(self):
        for item in (read(obj="User"), read(filters=[{"field": "Password", "operator": "eq", "value": "x"}]),
                     read(filters=[{"field": "Description", "operator": "contains", "value": "x"}]),
                     read(filters=[{"field": "Status", "operator": "gte", "value": "New"}])):
            with self.subTest(item=item), self.assertRaises(ValueError):
                compile_query(item)

    def test_raw_query_and_wrong_record_ids_rejected(self):
        for item in ({**read(), "q": "SELECT Id FROM User"}, read(filters=[{"field": "Id", "operator": "eq", "value": "001000000000000AAA"}])):
            with self.assertRaises(ValueError):
                compile_query(item)

    def test_typed_date_and_amount_filters(self):
        query = compile_query(read("Opportunity", "", filters=[{"field": "Amount", "operator": "gte", "value": "1000"}, {"field": "CloseDate", "operator": "lte", "value": "2026-12-31"}]))
        self.assertIn("Amount >= 1000 AND CloseDate <= 2026-12-31", query)
        for value in ("2026-02-30", "2026-12-31 OR Id != null"):
            with self.assertRaises(ValueError):
                compile_query(read("Opportunity", "", filters=[{"field": "CloseDate", "operator": "eq", "value": value}]))

    def test_relationship_requires_verified_account_id(self):
        with self.assertRaises(ValueError):
            compile_query(read("Task", "", "Rivergum"))
        self.assertIn("AccountId IN ('001000000000000AAA')", compile_query(read("Task", "", "Rivergum"), ["001000000000000AAA"]))

    def test_duplicate_company_name_stays_within_account_boundary(self):
        query = compile_query(read("Contact", "Rivergum Logistics", "Rivergum Logistics"), ["001000000000000AAA"])
        self.assertNotIn("Name LIKE", query)
        self.assertIn("AccountId IN ('001000000000000AAA')", query)

    def test_company_filter_has_defined_account_and_lead_meaning(self):
        self.assertIn("Name LIKE '%Rivergum%'", compile_query(read("Account", "Rivergum", "Rivergum")))
        self.assertIn("Company LIKE '%Fenwick%'", compile_query(read("Lead", "", "Fenwick")))


class RetrievalTests(unittest.IsolatedAsyncioTestCase):
    async def test_rejects_entire_invalid_plan_before_network(self):
        call = AsyncMock()
        with self.assertRaises(ValueError):
            await retrieve({"reads": [read(), read("User")]}, call, "https://demo.my.salesforce.com")
        call.assert_not_called()

    async def test_related_records_resolve_account_once(self):
        account = "001000000000000AAA"
        call = AsyncMock(side_effect=[result([{"Id": account}]), result([{"Id": "00T000000000000AAA", "Subject": "Call"}]), result([])])
        evidence, truncated = await retrieve({"reads": [read("Task", "", "Rivergum"), read("Event", "", "Rivergum")]}, call, "https://demo.my.salesforce.com")
        self.assertEqual(call.await_count, 3)
        self.assertEqual(evidence[0]["location"]["object"], "Task")
        self.assertEqual(evidence[0]["source_uri"], "https://demo.my.salesforce.com/lightning/r/Task/00T000000000000AAA/view")
        self.assertFalse(truncated)

    async def test_sentinel_row_never_becomes_evidence(self):
        rows = [{"Id": "500" + str(i).zfill(12), "Subject": "VPN"} for i in range(11)]
        evidence, truncated = await retrieve({"reads": [read()]}, AsyncMock(return_value=result(rows)), "https://demo.my.salesforce.com")
        self.assertEqual(len(evidence), 10)
        self.assertTrue(truncated)

    async def test_no_match_and_permission_failure_cannot_create_citations(self):
        evidence, _ = await retrieve({"reads": [read()]}, AsyncMock(return_value=result([])), "https://demo.my.salesforce.com")
        self.assertEqual(evidence, [])
        with self.assertRaises(SalesforceReadError):
            await retrieve({"reads": [read()]}, AsyncMock(return_value=result([], True)), "https://demo.my.salesforce.com")

    async def test_wrong_object_result_rejected(self):
        with self.assertRaises(SalesforceReadError):
            await retrieve({"reads": [read()]}, AsyncMock(return_value=result([{"Id": "001000000000000AAA"}])), "https://demo.my.salesforce.com")

    async def test_contact_company_name_is_grounded_in_returned_relationship(self):
        call = AsyncMock(return_value=result([{"Id": "003000000000000AAA", "Name": "Elena", "Account": {"Name": "Bluehaven Utilities"}}]))
        evidence, _ = await retrieve({"reads": [read("Contact", "Elena")]}, call, "https://demo.my.salesforce.com")
        self.assertIn('"Account.Name": "Bluehaven Utilities"', evidence[0]["chunk_text"])
        self.assertIn("Account.Name", call.call_args.args[1]["q"])

    async def test_read_budget_enforced(self):
        call = AsyncMock()
        with self.assertRaises(ValueError):
            await retrieve({"reads": [read()] * 4}, call, "https://demo.my.salesforce.com")
        call.assert_not_called()


if __name__ == "__main__":
    unittest.main()
