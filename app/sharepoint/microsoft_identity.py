"""Exchange an AskAnyDoc API access token for a delegated Microsoft Graph token."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from functools import lru_cache

import boto3

from .sharepoint_source import SharePointError


@lru_cache(maxsize=1)
def _client_secret() -> str:
    secret_id = os.environ["ENTRA_CREDENTIAL_SECRET_ID"]
    response = boto3.client("secretsmanager").get_secret_value(SecretId=secret_id)
    value = json.loads(response["SecretString"])
    secret = value.get("client_secret")
    if not isinstance(secret, str) or not secret:
        raise SharePointError("obo_credential_invalid", "The Entra API credential is unavailable")
    return secret


def acquire_graph_token(api_access_token: str, timeout_seconds: float) -> str:
    """Use OAuth OBO so Microsoft Graph receives the same signed-in user identity."""
    token_url = (
        f"https://login.microsoftonline.com/{os.environ['ENTRA_TENANT_ID']}"
        "/oauth2/v2.0/token"
    )
    body = urllib.parse.urlencode({
        "client_id": os.environ["ENTRA_API_CLIENT_ID"],
        "client_secret": _client_secret(),
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": api_access_token,
        "requested_token_use": "on_behalf_of",
        "scope": "https://graph.microsoft.com/.default",
    }).encode("utf-8")
    request = urllib.request.Request(
        token_url,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            payload = json.loads(response.read())
    except urllib.error.HTTPError as error:
        details = json.loads(error.read() or b"{}")
        code = details.get("error", "obo_token_failed")
        print(json.dumps({
            "event": "obo_token_exchange_failed",
            "error": code,
            "error_description": details.get("error_description", "")[:1000],
            "correlation_id": details.get("correlation_id"),
        }))
        category = "obo_consent_required" if code in {"invalid_grant", "interaction_required"} else "obo_token_failed"
        raise SharePointError(category, "Microsoft delegated token exchange failed") from error
    token = payload.get("access_token")
    if not isinstance(token, str) or not token:
        raise SharePointError("obo_response_invalid", "Microsoft did not return a Graph access token")
    return token
