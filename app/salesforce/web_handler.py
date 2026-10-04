"""User-bound Salesforce OAuth and one-Case AskAnyDoc web slice.

This Lambda is separate from the established answer-job worker. Entra identifies
the AskAnyDoc caller; Salesforce OAuth supplies that caller's Salesforce rights.
Tokens are held only in Secrets Manager and this process, never in SQS or prompts.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import os
import secrets
import time
from typing import Any
from urllib.parse import urlencode, urlsplit

import httpx
from botocore.exceptions import ClientError
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from askanydoc_rag.aws import aws_client
from answer_lambda_handler import _auth_context, _validated_history
from assistant_orchestrator import SALESFORCE_CASE_ID_PATTERN, run_assistant
from salesforce.read_adapter import case_as_answer_evidence, read_case
from salesforce.crm_reader import answer_crm, retrieve
from salesforce.evidence_endpoint import crm_evidence


SALESFORCE_MCP_URL = "https://api.salesforce.com/platform/mcp/v1/platform/sobject-reads"
SALESFORCE_AUTHORIZE_URL = "https://login.salesforce.com/services/oauth2/authorize"
SALESFORCE_TOKEN_URL = "https://login.salesforce.com/services/oauth2/token"
GRANT_PREFIX = "askanydoc/salesforce-grants-dev/"
STATE_LIFETIME_SECONDS = 600

dynamodb_client = aws_client("dynamodb")
secrets_client = aws_client("secretsmanager")


def _response(status: int, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json", "Cache-Control": "no-store"},
        "body": json.dumps(body),
    }


def _owner_hash(auth: dict[str, str]) -> str:
    """Name one user's grant without exposing Entra identifiers in the secret name."""
    return hashlib.sha256(f"{auth['tenant_id']}:{auth['user_id']}".encode()).hexdigest()


def _state_hash(state: str) -> str:
    return hashlib.sha256(state.encode()).hexdigest()


def _grant_name(owner: str) -> str:
    return f"{GRANT_PREFIX}{owner}"


def _urls() -> tuple[str, str]:
    """Require the exact public callback and expected Salesforce org origin."""
    callback = os.environ["SALESFORCE_WEB_CALLBACK_URL"]
    org_origin = os.environ["SALESFORCE_ORG_ORIGIN"]
    if not callback.startswith("https://") or urlsplit(callback).query or urlsplit(callback).fragment:
        raise ValueError("The Salesforce web callback must be a clean HTTPS URL.")
    if not org_origin.startswith("https://") or not org_origin.endswith(".my.salesforce.com"):
        raise ValueError("The expected Salesforce org origin is invalid.")
    return callback, org_origin


def _client_info() -> dict[str, str]:
    """Read the web ECA identity only on the server side."""
    value = secrets_client.get_secret_value(
        SecretId=os.environ["SALESFORCE_WEB_CLIENT_SECRET_ID"]
    )
    info = json.loads(value["SecretString"])
    if not all(isinstance(info.get(key), str) and info[key] for key in ("client_id", "client_secret")):
        raise ValueError("Salesforce web client credentials are incomplete.")
    return info


def _connect(auth: dict[str, str], *, force_login: bool = False) -> dict[str, Any]:
    callback, _org_origin = _urls()
    client_id = _client_info()["client_id"]
    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    now = int(time.time())
    # DynamoDB TTL is asynchronous; the completion route also checks expiry.
    dynamodb_client.put_item(
        TableName=os.environ["SALESFORCE_OAUTH_STATES_TABLE"],
        Item={
            "state_hash": {"S": _state_hash(state)},
            "owner_hash": {"S": _owner_hash(auth)},
            "code_verifier": {"S": verifier},
            "expires_at": {"N": str(now + STATE_LIFETIME_SECONDS)},
        },
        ConditionExpression="attribute_not_exists(state_hash)",
    )
    parameters = {
        'response_type': 'code', 'client_id': client_id,
        'redirect_uri': callback, 'scope': 'mcp_api refresh_token',
        'resource': SALESFORCE_MCP_URL, 'state': state,
        'code_challenge': challenge, 'code_challenge_method': 'S256',
    }
    # A changed account must reauthenticate even if this browser has an old
    # Salesforce session. Salesforce still chooses which user can authorize.
    if force_login:
        parameters['prompt'] = 'login'
    url = f"{SALESFORCE_AUTHORIZE_URL}?{urlencode(parameters)}"
    return _response(200, {"authorization_url": url})


def _token_expiry(token: dict[str, Any]) -> int:
    """Use expiry only as a refresh hint; Salesforce still validates every MCP call."""
    if token.get("expires_in") is not None:
        return int(time.time()) + int(token["expires_in"])
    try:
        segment = token["access_token"].split(".")[1]
        payload = json.loads(base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4)))
        return int(payload["exp"])
    except (IndexError, KeyError, TypeError, ValueError):
        return 0  # A non-JWT token is refreshed before use.


def _exchange(form: dict[str, str]) -> dict[str, Any]:
    with httpx.Client(timeout=15, follow_redirects=False) as client:
        response = client.post(SALESFORCE_TOKEN_URL, data=form)
        if response.is_error:
            try:
                oauth_error = response.json().get("error")
            except (ValueError, AttributeError):
                oauth_error = None
            print(json.dumps({
                "event": "salesforce_oauth_exchange_rejected",
                "status": response.status_code,
                "oauth_error": oauth_error if isinstance(oauth_error, str) and len(oauth_error) < 80 else None,
            }))
        response.raise_for_status()
        token = response.json()
    if not isinstance(token, dict) or not isinstance(token.get("access_token"), str):
        raise ValueError("Salesforce returned an incomplete OAuth token response.")
    return token


def _save_grant(owner: str, grant: dict[str, Any]) -> None:
    value = json.dumps(grant, separators=(",", ":"))
    name = _grant_name(owner)
    try:
        secrets_client.create_secret(
            Name=name,
            Description="User-bound Salesforce Hosted MCP grant for AskAnyDoc development",
            SecretString=value,
            Tags=[{"Key": "project", "Value": "askanydoc"},
                  {"Key": "purpose", "Value": "salesforce-user-grant"}],
        )
    except ClientError as error:
        if error.response.get("Error", {}).get("Code") != "ResourceExistsException":
            raise
        secrets_client.put_secret_value(SecretId=name, SecretString=value)


def _complete(auth: dict[str, str], body: dict[str, Any]) -> dict[str, Any]:
    code = body.get("code")
    state = body.get("state")
    if not isinstance(code, str) or not code or len(code) > 2048 or \
            not isinstance(state, str) or not state or len(state) > 256:
        return _response(400, {"error": "Salesforce authorization response is invalid."})
    owner = _owner_hash(auth)
    try:
        consumed = dynamodb_client.delete_item(
            TableName=os.environ["SALESFORCE_OAUTH_STATES_TABLE"],
            Key={"state_hash": {"S": _state_hash(state)}},
            ConditionExpression="owner_hash = :owner AND expires_at >= :now",
            ExpressionAttributeValues={
                ":owner": {"S": owner}, ":now": {"N": str(int(time.time()))},
            },
            ReturnValues="ALL_OLD",
        )["Attributes"]
    except (ClientError, KeyError):
        return _response(400, {"error": "Salesforce connection expired or belongs to another user."})

    callback, org_origin = _urls()
    info = _client_info()
    token = _exchange({
        "grant_type": "authorization_code", "code": code,
        "client_id": info["client_id"], "client_secret": info["client_secret"],
        "redirect_uri": callback, "code_verifier": consumed["code_verifier"]["S"],
    })
    if token.get("instance_url") != org_origin or not token.get("refresh_token"):
        return _response(400, {"error": "Salesforce returned a different org or no refresh grant."})
    _save_grant(owner, {
        "owner_hash": owner,
        "access_token": token["access_token"],
        "refresh_token": token["refresh_token"],
        "instance_url": org_origin,
        "expires_at": _token_expiry(token),
    })
    return _response(200, {"connected": True})


def _load_grant(owner: str) -> dict[str, Any] | None:
    try:
        value = secrets_client.get_secret_value(SecretId=_grant_name(owner))
    except ClientError as error:
        if error.response.get("Error", {}).get("Code") == "ResourceNotFoundException":
            return None
        raise
    grant = json.loads(value["SecretString"])
    if grant.get("owner_hash") != owner or grant.get("instance_url") != _urls()[1]:
        raise ValueError("The saved Salesforce grant does not match the signed-in user and org.")
    if grant.get("disconnected_at"):
        return None
    return grant


def _disconnect(auth: dict[str, str]) -> dict[str, Any]:
    """Revoke this user's refresh grant, then remove usable tokens from current state."""
    owner = _owner_hash(auth)
    grant = _load_grant(owner)
    if grant is None:
        return _response(200, {"connected": False})
    _callback, org_origin = _urls()
    with httpx.Client(timeout=15, follow_redirects=False) as client:
        response = client.post(
            f"{org_origin}/services/oauth2/revoke",
            data={"token": grant["refresh_token"]},
        )
    if response.status_code == 400:
        # Salesforce returns invalid_token when the grant was already revoked.
        try:
            invalid = response.json().get("error") == "invalid_token"
        except (ValueError, AttributeError):
            invalid = False
        if not invalid:
            response.raise_for_status()
    else:
        response.raise_for_status()
    # Replacing the current secret version with a token-free tombstone lets a
    # user reconnect immediately under the same secret name. The revoked old
    # version may remain in Secrets Manager history until AWS retires it.
    _save_grant(owner, {
        "owner_hash": owner,
        "instance_url": org_origin,
        "disconnected_at": int(time.time()),
    })
    return _response(200, {"connected": False})


def _refresh_grant(owner: str, grant: dict[str, Any]) -> dict[str, Any]:
    if int(grant.get("expires_at") or 0) > int(time.time()) + 60:
        return grant
    info = _client_info()
    token = _exchange({
        "grant_type": "refresh_token", "refresh_token": grant["refresh_token"],
        "client_id": info["client_id"], "client_secret": info["client_secret"],
    })
    grant = {
        **grant,
        "access_token": token["access_token"],
        "refresh_token": token.get("refresh_token") or grant["refresh_token"],
        "expires_at": _token_expiry(token),
    }
    _save_grant(owner, grant)
    return grant


async def _read_case_mcp(case_id: str, access_token: str, org_origin: str) -> dict[str, Any] | None:
    """Call only the read server and verify its live SOQL input contract."""
    async with httpx.AsyncClient(
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=httpx.Timeout(20),
    ) as client:
        async with streamable_http_client(SALESFORCE_MCP_URL, http_client=client) as (read, write, _id):
            async with ClientSession(read, write) as session:
                await session.initialize()
                listing = await session.list_tools()
                soql = next((tool for tool in listing.tools if tool.name == "soqlQuery"), None)
                if soql is None or soql.inputSchema.get("required") != ["q"]:
                    raise ValueError("The Salesforce SOQL tool schema changed.")
                return await read_case(case_id, session.call_tool, org_origin=org_origin)


async def _read_crm_mcp(plan: dict[str, Any], access_token: str, org_origin: str):
    async with httpx.AsyncClient(headers={"Authorization": f"Bearer {access_token}"}, timeout=httpx.Timeout(20)) as client:
        async with streamable_http_client(SALESFORCE_MCP_URL, http_client=client) as (read, write, _id):
            async with ClientSession(read, write) as session:
                await session.initialize()
                listing = await session.list_tools()
                soql = next((tool for tool in listing.tools if tool.name == "soqlQuery"), None)
                if soql is None or soql.inputSchema.get("required") != ["q"]:
                    raise ValueError("The Salesforce SOQL tool schema changed.")
                return await retrieve(plan, session.call_tool, org_origin)


def _ask(auth: dict[str, str], body: dict[str, Any]) -> dict[str, Any]:
    question = body.get("question")
    if not isinstance(question, str) or not question.strip() or len(question) > 4000:
        return _response(400, {"error": "Question must be 1 to 4,000 characters."})
    match = SALESFORCE_CASE_ID_PATTERN.search(question)
    if "salesforce" not in question.casefold():
        return _response(400, {"error": "Specify Salesforce as the source for this CRM question."})
    try:
        history = _validated_history(body.get("history"))
    except ValueError as error:
        return _response(400, {"error": str(error)})
    owner = _owner_hash(auth)
    grant = _load_grant(owner)
    if grant is None:
        return _response(409, {"error": "Connect your Salesforce account before asking about CRM records."})
    grant = _refresh_grant(owner, grant)
    if match is None:
        return _response(200, answer_crm(
            question.strip(), history,
            reader=lambda plan: asyncio.run(_read_crm_mcp(plan, grant["access_token"], grant["instance_url"])),
        ))
    case = asyncio.run(_read_case_mcp(match.group(0), grant["access_token"], grant["instance_url"]))
    evidence = case_as_answer_evidence(case) if case is not None else None
    answer = run_assistant(
        question.strip(), history,
        salesforce_case_reader=lambda requested: evidence if requested == match.group(0) else None,
    )
    return _response(200, answer)


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Entra-protected Salesforce routes; never log OAuth codes or tokens."""
    route = event.get("routeKey") or event.get("requestContext", {}).get("routeKey")
    auth = _auth_context(event)
    if auth is None:
        return _response(401, {"error": "Sign in to AskAnyDoc first."})
    try:
        if route == "GET /salesforce/status":
            grant = _load_grant(_owner_hash(auth))
            return _response(200, {
                "connected": grant is not None,
                "org": urlsplit(grant["instance_url"]).hostname if grant else None,
            })
        body = json.loads(event.get("body") or "{}")
        if not isinstance(body, dict):
            return _response(400, {"error": "Request body must be an object."})
        if route == "POST /salesforce/connect":
            return _connect(auth, force_login=body.get("force_login") is True)
        if route == "POST /salesforce/disconnect":
            return _disconnect(auth)
        if route == "POST /salesforce/complete":
            return _complete(auth, body)
        if route == "POST /salesforce/evidence":
            status, payload = crm_evidence(auth, body, load_grant=_load_grant,
                refresh_grant=_refresh_grant, owner_hash=_owner_hash, read_crm=_read_crm_mcp)
            return _response(status, payload)
        if route == "POST /salesforce/ask":
            return _ask(auth, body)
        return _response(404, {"error": "Route not found."})
    except (json.JSONDecodeError, TypeError):
        return _response(400, {"error": "Request body must be valid JSON."})
    except Exception as error:
        def leaf_types(item):
            if isinstance(item, BaseExceptionGroup):
                return [kind for child in item.exceptions for kind in leaf_types(child)]
            return [type(item).__name__]
        causes = leaf_types(error)
        def protocol_details(item):
            if isinstance(item, BaseExceptionGroup):
                return [detail for child in item.exceptions for detail in protocol_details(child)]
            data = getattr(item, "error", None)
            if type(item).__name__ != "McpError" or data is None:
                return []
            message = str(getattr(data, "message", "")).casefold()
            categories = [label for label, words in {
                "session": ("session", "initializ"), "authorization": ("token", "auth", "permission"),
                "rate_limit": ("rate", "quota", "limit"), "input": ("argument", "parameter", "invalid"),
                "timeout": ("timeout", "timed out"), "tool": ("tool", "query"),
            }.items() if any(word in message for word in words)]
            code = getattr(data, "code", None)
            return [{"code": code if isinstance(code, int) else None, "categories": categories}]
        protocol = protocol_details(error)
        print(json.dumps({
            "event": "salesforce_web_request_failed",
            "route": route,
            "error_type": type(error).__name__,
            "cause_types": causes,
            "mcp_errors": protocol,
            "aws_error_code": error.response.get("Error", {}).get("Code") if isinstance(error, ClientError) else None,
            "request_id": getattr(context, "aws_request_id", None),
        }))
        return _response(503, {"error": "Salesforce connection is unavailable. Please try again."})
