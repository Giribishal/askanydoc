"""CRM evidence only; invoked by the existing JWT-protected Salesforce handler."""
from __future__ import annotations

import asyncio
import json

from assistant_orchestrator import _bedrock_messages
from salesforce.crm_reader import plan_reads


def crm_evidence(auth, body, *, load_grant, refresh_grant, owner_hash, read_crm):
    """Resolve grants from validated claims, never from request identity/credentials."""
    if not auth or not all(auth.get(k) for k in ("tenant_id", "user_id", "access_token")):
        return 401, {"error": "Sign in to AskAnyDoc first."}
    if not isinstance(body, dict) or set(body) != {"question"}:
        return 400, {"error": "Only a focused CRM question is accepted."}
    question = body["question"]
    if not isinstance(question, str) or not question.strip() or len(question) > 2000:
        return 400, {"error": "CRM question must be 1 to 2,000 characters."}
    owner = owner_hash(auth)
    grant = load_grant(owner)
    if grant is None:
        return 409, {"error": "Connect your Salesforce account to retrieve CRM evidence."}
    grant = refresh_grant(owner, grant)
    usage = {"input_tokens": 0, "output_tokens": 0}
    plan = plan_reads(_bedrock_messages([], question.strip()), usage)
    if isinstance(plan, dict) and plan.get("reads") == []:
        return 422, {"error": "This request exceeds the bounded read-only CRM scope."}
    evidence, truncated = asyncio.run(read_crm(plan, grant["access_token"], grant["instance_url"]))
    result = {"evidence": evidence, "truncated": truncated, **usage}
    if len(json.dumps(result).encode()) > 200_000:
        raise ValueError("CRM evidence exceeds the response budget.")
    return 200, result
