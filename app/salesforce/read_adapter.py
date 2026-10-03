"""Turn bounded Salesforce MCP Case reads into citation-ready evidence.

The caller owns OAuth and the MCP session. This module never receives credentials,
and it never allows a model or user to supply SOQL directly.
"""

from __future__ import annotations

import re
from collections.abc import Awaitable, Callable
from typing import Any


CASE_ID = re.compile(r"500[A-Za-z0-9]{12}(?:[A-Za-z0-9]{3})?\Z")
CASE_FIELDS = "Id, CaseNumber, Subject, Status, Priority, Origin, AccountId"
MAX_RECORDS = 1


class SalesforceReadError(RuntimeError):
    """A Salesforce read failed without exposing OAuth or raw server details."""


def case_query(case_id: str) -> str:
    """Accept a Case record ID and build a narrow, indexed SOQL query."""
    if not isinstance(case_id, str) or not CASE_ID.fullmatch(case_id):
        raise ValueError("A valid Salesforce Case ID is required.")
    return f"SELECT {CASE_FIELDS} FROM Case WHERE Id = '{case_id}' LIMIT {MAX_RECORDS}"


def _records(result: Any) -> list[dict[str, Any]]:
    """Validate the Salesforce tool's structured result before using any record."""
    if getattr(result, "isError", False):
        raise SalesforceReadError("Salesforce did not complete the Case read.")
    payload = getattr(result, "structuredContent", None)
    if not isinstance(payload, dict):
        raise SalesforceReadError("Salesforce returned no structured Case data.")
    records = payload.get("records")
    if not isinstance(records, list) or len(records) > MAX_RECORDS:
        raise SalesforceReadError("Salesforce returned an unexpected Case result.")
    if any(not isinstance(record, dict) for record in records):
        raise SalesforceReadError("Salesforce returned a malformed Case record.")
    return records


def case_as_answer_evidence(case: dict[str, Any]) -> dict[str, Any]:
    """Shape a verified Case read for AskAnyDoc's existing answer/citation contract."""
    facts = case["facts"]
    return {
        "chunk_text": "\n".join(
            f"{label}: {facts[label]}"
            for label in ("CaseNumber", "Subject", "Status", "Priority", "Origin", "AccountId")
            if facts.get(label) is not None
        ),
        "source_name": case["source_name"],
        "source_type": "salesforce_case",
        "source_uri": case["source_uri"],
        "object_key": "",
        "location": {"record_id": case["record_id"]},
        "similarity": None,
    }


async def read_case(
    case_id: str,
    call_tool: Callable[[str, dict[str, str]], Awaitable[Any]],
    *,
    org_origin: str,
) -> dict[str, Any] | None:
    """Read one permitted Case and return its facts with a Salesforce citation."""
    query = case_query(case_id)
    if not re.fullmatch(r"https://[a-z0-9.-]+\.salesforce\.com", org_origin):
        raise ValueError("A verified Salesforce org origin is required.")
    try:
        # The live Hosted MCP input schema on 2026-10-03 requires `q`, even
        # though the current prose reference labels this parameter `query`.
        result = await call_tool("soqlQuery", {"q": query})
        records = _records(result)
    except SalesforceReadError:
        raise
    except Exception as exc:
        raise SalesforceReadError("Salesforce Case read was unavailable.") from exc
    if not records:
        return None
    record = records[0]
    if record.get("Id") != case_id:
        raise SalesforceReadError("Salesforce returned a different Case.")
    facts = {field: record.get(field) for field in (
        "CaseNumber", "Subject", "Status", "Priority", "Origin", "AccountId"
    )}
    return {
        "source_type": "salesforce_case",
        "source_name": f"Case {facts['CaseNumber'] or case_id}",
        "source_uri": f"{org_origin}/lightning/r/Case/{case_id}/view",
        "record_id": case_id,
        "facts": facts,
    }
