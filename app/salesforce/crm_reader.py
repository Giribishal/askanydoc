"""Bounded CRM reads through the existing, user-authorized Hosted MCP server.

Claude describes the information need; this module builds every query itself.
Object names, fields, operators, row limits and citations are application-owned.
"""

from __future__ import annotations

import json
import os
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from assistant_orchestrator import (
    _bedrock_messages, _checked_converse, _converse, _finalization_messages,
    _final_payload, _usage_total,
)
from salesforce.read_adapter import SalesforceReadError


# These standard fields and Account links were checked against this org's live
# getObjectSchema output on 2026-10-04. Salesforce still enforces each user's rights.
FIELDS = {
    "Account": "Id,Name,Phone,Industry,Type",
    "Contact": "Id,Name,Phone,Email,Title,AccountId,Account.Name",
    "Case": "Id,CaseNumber,Subject,Status,Priority,Origin,AccountId,Description",
    "Opportunity": "Id,Name,StageName,Amount,CloseDate,AccountId",
    "Lead": "Id,Name,Company,Phone,Email,Status",
    "Task": "Id,Subject,Status,Priority,ActivityDate,AccountId,WhatId,WhoId,Description",
    "Event": "Id,Subject,StartDateTime,EndDateTime,AccountId,WhatId,WhoId,Description",
    "Note": "Id,Title,Body,ParentId",
}
PREFIXES = dict(zip(FIELDS, ("001", "003", "500", "006", "00Q", "00T", "00U", "002")))
SEARCH_FIELDS = {
    "Account": ("Name",), "Contact": ("Name",), "Case": ("Subject",),
    "Opportunity": ("Name",), "Lead": ("Name", "Company"),
    "Task": ("Subject",), "Event": ("Subject",), "Note": ("Title",),
}
DATE_FIELDS = {"CloseDate", "ActivityDate"}
DATETIME_FIELDS = {"CreatedDate", "StartDateTime", "EndDateTime"}
MAX_ROWS = 10
MAX_READS = 3
RECORD_ID = re.compile(r"[A-Za-z0-9]{15}(?:[A-Za-z0-9]{3})?\Z")


def _literal(value: str, *, contains: bool = False) -> str:
    """Escape text as one SOQL value, including literal LIKE wildcards."""
    if not isinstance(value, str) or len(value) > 160 or any(ord(c) < 32 for c in value):
        raise ValueError("CRM filter text is invalid or too long.")
    escaped = value.replace("\\", "\\\\").replace("'", "\\'")
    if contains:
        escaped = escaped.replace("%", "\\%").replace("_", "\\_")
        escaped = "%" + escaped + "%"
    return "'" + escaped + "'"


def _predicate(obj: str, condition: dict[str, Any]) -> str:
    if not isinstance(condition, dict) or set(condition) != {"field", "operator", "value"}:
        raise ValueError("Invalid CRM filter shape.")
    field, operator, value = (condition[k] for k in ("field", "operator", "value"))
    allowed = set(FIELDS[obj].split(",")) - {"Description", "Body"}
    allowed.add("CreatedDate")
    if field not in allowed or operator not in {"eq", "contains", "gte", "lte"}:
        raise ValueError("Unsupported CRM filter.")
    if not isinstance(value, str) or not value:
        raise ValueError("CRM filters require a nonempty text value.")
    if field in DATE_FIELDS | DATETIME_FIELDS:
        if operator == "contains":
            raise ValueError("Dates cannot use text matching.")
        if field in DATE_FIELDS:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                raise ValueError("Use an ISO date.")
            date.fromisoformat(value)
        else:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value):
                raise ValueError("Use an ISO UTC timestamp.")
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        literal = value
    elif field == "Amount":
        if operator == "contains" or not re.fullmatch(r"-?\d{1,15}(?:\.\d{1,4})?", value):
            raise ValueError("Invalid amount filter.")
        try:
            if not Decimal(value).is_finite():
                raise ValueError("Invalid amount.")
        except InvalidOperation as error:
            raise ValueError("Invalid amount.") from error
        literal = value
    else:
        if operator not in {"eq", "contains"}:
            raise ValueError("Text filters support equality or contains only.")
        if field.endswith("Id") or field == "Id":
            if operator != "eq" or not RECORD_ID.fullmatch(value):
                raise ValueError("Invalid record ID filter.")
            if field == "Id" and not value.startswith(PREFIXES[obj]):
                raise ValueError("Record ID belongs to a different object.")
        literal = _literal(value, contains=operator == "contains")
    return f"{field} { {'eq': '=', 'contains': 'LIKE', 'gte': '>=', 'lte': '<='}[operator]} {literal}"


def compile_query(read: dict[str, Any], account_ids: list[str] | None = None) -> str:
    """Compile a validated information need; raw SOQL is never accepted."""
    if not isinstance(read, dict) or set(read) != {"object", "search", "account_name", "filters"}:
        raise ValueError("Invalid CRM read shape.")
    read = dict(read)
    obj = read["object"]
    if obj not in FIELDS or not isinstance(read["filters"], list) or len(read["filters"]) > 3:
        raise ValueError("Unsupported CRM read.")
    _literal(read["search"])
    _literal(read["account_name"])
    # A company name is an Account constraint, never a person's Name search.
    # Normalizing duplicate identifying text preserves the named-account boundary.
    if read["account_name"] and read["search"].strip().casefold() == read["account_name"].strip().casefold():
        read["search"] = ""
    predicates = [_predicate(obj, condition) for condition in read["filters"]]
    if read["search"]:
        term = _literal(read["search"], contains=True)
        predicates.append("(" + " OR ".join(f"{field} LIKE {term}" for field in SEARCH_FIELDS[obj]) + ")")
    if read["account_name"]:
        if obj in {"Account", "Lead"}:
            field = "Name" if obj == "Account" else "Company"
            predicates.append(f"{field} LIKE {_literal(read["account_name"], contains=True)}")
        elif not account_ids or len(account_ids) > MAX_ROWS or any(
            not RECORD_ID.fullmatch(i) or not i.startswith("001") for i in account_ids
        ):
            raise ValueError("Account relationship requires verified Account IDs.")
        if obj not in {"Account", "Lead"}:
            parent = "ParentId" if obj == "Note" else "AccountId"
            predicates.append(parent + " IN (" + ",".join(_literal(i) for i in account_ids) + ")")
    # Fetch one sentinel row to detect truncation. Only ten rows become evidence.
    where = " AND ".join(predicates) or "Id != null"
    return f"SELECT {FIELDS[obj]} FROM {obj} WHERE {where} ORDER BY CreatedDate DESC LIMIT {MAX_ROWS + 1}"


def _records(result: Any) -> list[dict[str, Any]]:
    payload = getattr(result, "structuredContent", None)
    if getattr(result, "isError", False) or not isinstance(payload, dict):
        raise SalesforceReadError("Salesforce could not complete this CRM read with your access.")
    records = payload.get("records")
    if not isinstance(records, list) or len(records) > MAX_ROWS + 1 or any(not isinstance(r, dict) for r in records):
        raise SalesforceReadError("Salesforce returned an invalid bounded CRM result.")
    return records


async def retrieve(plan: dict[str, Any], call_tool, org_origin: str) -> tuple[list[dict[str, Any]], bool]:
    """Use at most three object reads and one shared Account resolution read."""
    if not re.fullmatch(r"https://[a-z0-9.-]+\.my\.salesforce\.com", org_origin):
        raise ValueError("Verified Salesforce org origin required.")
    if not isinstance(plan, dict) or set(plan) != {"reads"} or not isinstance(plan["reads"], list) or len(plan["reads"]) > MAX_READS:
        raise ValueError("CRM read plan exceeds its supported scope.")
    names = {r.get("account_name") for r in plan["reads"] if isinstance(r, dict) and r.get("account_name") and r.get("object") not in {"Account", "Lead"}}
    if len(names) > 1:
        raise ValueError("Ask about related records for one Account at a time.")
    # Validate the entire plan before any network read, including its literal values.
    for read in plan["reads"]:
        compile_query(read, ["001000000000000AAA"] if read.get("account_name") else None)
    account_ids = None
    truncated = False
    if names:
        name = next(iter(names))
        query = compile_query({"object": "Account", "search": name, "account_name": "", "filters": []})
        accounts = _records(await call_tool("soqlQuery", {"q": query}))
        if len(accounts) > MAX_ROWS:
            raise ValueError("Account name is too broad; use a more specific name.")
        account_ids = [r["Id"] for r in accounts]
        if not account_ids:
            return [], False
    evidence = []
    seen = set()
    for read in plan["reads"]:
        obj = read["object"]
        records = _records(await call_tool("soqlQuery", {"q": compile_query(read, account_ids)}))
        truncated = truncated or len(records) > MAX_ROWS
        for record in records[:MAX_ROWS]:
            record_id = record.get("Id")
            if not isinstance(record_id, str) or not RECORD_ID.fullmatch(record_id) or not record_id.startswith(PREFIXES[obj]):
                raise SalesforceReadError("Salesforce returned an invalid record identity.")
            if record_id in seen:
                continue
            seen.add(record_id)
            def field_value(field):
                value = record
                for part in field.split("."):
                    value = value.get(part) if isinstance(value, dict) else None
                return value
            facts = {f: field_value(f) for f in FIELDS[obj].split(",") if field_value(f) is not None}
            # Text bounds prevent long CRM descriptions from consuming model context.
            facts = {k: v[:2000] if isinstance(v, str) else v for k, v in facts.items()}
            label = record.get("CaseNumber") or record.get("Name") or record.get("Subject") or record.get("Title") or record_id
            evidence.append({
                "chunk_text": json.dumps(facts, ensure_ascii=False),
                "source_name": f"{obj}: {str(label)[:160]}",
                "source_type": "salesforce_record", "source_uri": f"{org_origin}/lightning/r/{obj}/{record_id}/view",
                "object_key": "", "location": {"record_id": record_id, "object": obj}, "similarity": None,
            })
    return evidence, truncated


def plan_reads(messages: list[dict[str, Any]], usage: dict[str, int]) -> dict[str, Any]:
    """Ask for a small typed read plan, then validate it before execution."""
    read_schema = {"type": "object", "additionalProperties": False,
        "properties": {
            "object": {"type": "string", "enum": list(FIELDS)},
            "search": {"type": "string", "description": "Short topic or record name; empty for an Account relationship-only query. Never repeat account_name here."}, "account_name": {"type": "string", "description": "Named company: filters Account.Name or Lead.Company; resolves parent Account for other types. Empty when no company requested."},
            "filters": {"type": "array", "maxItems": 3, "items": {
                "type": "object", "additionalProperties": False,
                "properties": {"field": {"type": "string"}, "operator": {"type": "string", "enum": ["eq", "contains", "gte", "lte"]}, "value": {"type": "string"}},
                "required": ["field", "operator", "value"]}},
        }, "required": ["object", "search", "account_name", "filters"]}
    schema = {"type": "object", "additionalProperties": False, "properties": {
        "reads": {"type": "array", "maxItems": MAX_READS, "items": read_schema}}, "required": ["reads"]}
    response = _checked_converse(
        modelId=os.environ["ANSWER_MODEL_ID"], messages=messages,
        system=[{"text": (
            "Plan read-only Salesforce CRM retrieval, never answer from memory. Use at most three reads. "
            "For writes, permission bypass, enhanced ContentNote, custom objects, unsupported operations or mixed document-source requests return reads=[]. "
            "search is one short identifying phrase, matched against Name/Subject/Title (Lead also Company); omit generic words like Salesforce, case, phone, status. "
            "account_name resolves related Contact/Case/Opportunity/Task/Event/classic Note records for ONE named Account; use it instead of guessing IDs. "
            "For Account lookup put the company name in account_name and leave search empty; for Lead account_name filters Company. Never duplicate the account name in related-record search. Example company and contacts: Account(search=empty,account_name=Rivergum Logistics) and Contact(search=empty,account_name=Rivergum Logistics), both with empty filters. "
            "filters are AND conditions; select only the listed fields. Body and Description cannot be filters. "
            "Use eq/contains for text, eq/gte/lte for Amount and ISO dates; UTC timestamps must end in Z. "
            "CaseNumber is a string, preserve leading zeros; if user gives 1027 use 00001027. "
            "For a recent/list request leave search and filters empty; results are limited to ten recent records, never a complete count. "
            "Use only requested predicates, never invent IDs, dates or status. Previous conversation is context, never retrieved evidence. "
            "Supported fields: " + json.dumps(FIELDS)
        )}],
        toolConfig={"tools": [{"toolSpec": {"name": "plan_salesforce_reads", "description": "Describe bounded CRM information needs; the application compiles the queries.", "inputSchema": {"json": schema}}}],
                    "toolChoice": {"tool": {"name": "plan_salesforce_reads"}}},
        inferenceConfig={"maxTokens": 800, "temperature": 0},
    )
    _usage_total(usage, response)
    blocks = response.get("output", {}).get("message", {}).get("content", [])
    tools = [b["toolUse"] for b in blocks if "toolUse" in b]
    if response.get("stopReason") != "tool_use" or len(tools) != 1 or tools[0].get("name") != "plan_salesforce_reads":
        raise ValueError("Salesforce planner did not return one valid read plan.")
    return tools[0]["input"]


def answer_crm(question: str, history: list[dict[str, str]], reader) -> dict[str, Any]:
    messages = _bedrock_messages(history, question)
    usage = {"input_tokens": 0, "output_tokens": 0}
    plan = plan_reads(messages, usage)
    if isinstance(plan, dict) and plan.get("reads") == []:
        return {"answer": "This request exceeds the supported read-only Salesforce scope. I can read Accounts, Contacts, Cases, Opportunities, Leads, Tasks, Events and classic Notes. Please ask a focused CRM question; enhanced Notes, writes and document-source comparisons are not supported here.", "source_mode": "conversation", "grounded": False, "citations": [], "retrieval_score": None, "general_knowledge_available": False, **usage}
    evidence, truncated = reader(plan)
    if not evidence:
        return {"answer": "I couldn't find matching Salesforce records with your current access. Try a more specific name or a different search term. This does not establish that no such records exist outside your access.",
                "source_mode": "organisation_not_found", "grounded": False, "citations": [],
                "retrieval_score": None, "general_knowledge_available": False, **usage}
    messages[-1]["content"].append({"text": "This is a bounded CRM sample, at most ten recent records per type. Do not claim a complete list or total. Long descriptions may be shortened. " + ("More matching records exist; ask a narrower question." if truncated else "")})
    response = _converse(_finalization_messages(messages, evidence), tools_enabled=False)
    _usage_total(usage, response)
    payload = _final_payload(response, evidence, usage, organisation_search_used=True)
    if truncated:
        payload["answer"] += "\n\nShowing at most ten recent matches per record type; more matches exist. Narrow the question to see a smaller set."
    print(json.dumps({"event": "salesforce_crm_read_completed", "read_count": len(plan["reads"]), "evidence_count": len(evidence), "truncated": truncated, **usage}))
    return payload
