"""One-shot local OAuth/MCP proof; never persists tokens or changes AWS resources.

Usage: set ASKANYDOC_SF_CLIENT_ID to the ECA consumer key, then run this module
with a Case ID. Open the printed Salesforce URL in the visible side-browser tab.
The localhost callback is received in memory and immediately removed from the
browser address bar. No password, token, OAuth code, or client secret is logged.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

import httpx
from mcp import ClientSession
from mcp.client.auth import OAuthClientProvider
from mcp.client.streamable_http import streamable_http_client
from mcp.shared.auth import OAuthClientInformationFull, OAuthClientMetadata, OAuthToken
from pydantic import AnyUrl

from app.salesforce.read_adapter import case_as_answer_evidence, read_case


SERVER_URL = "https://api.salesforce.com/platform/mcp/v1/platform/sobject-reads"
CALLBACK_URL = "http://localhost:6276/oauth/callback"
ISSUER = "https://login.salesforce.com"


class MemoryStorage:
    """Keep the pre-registered client ID and short-lived tokens in this process."""

    def __init__(self, client_id: str):
        self.client_info = OAuthClientInformationFull(
            client_id=client_id,
            issuer=ISSUER,
            redirect_uris=[AnyUrl(CALLBACK_URL)],
            token_endpoint_auth_method="none",
            grant_types=["authorization_code", "refresh_token"],
            response_types=["code"],
            scope="mcp_api refresh_token",
        )
        self.tokens: OAuthToken | None = None

    async def get_tokens(self) -> OAuthToken | None:
        return self.tokens

    async def set_tokens(self, tokens: OAuthToken) -> None:
        self.tokens = tokens

    async def get_client_info(self) -> OAuthClientInformationFull:
        return self.client_info

    async def set_client_info(self, client_info: OAuthClientInformationFull) -> None:
        self.client_info = client_info


class LoopbackCallback:
    """Receive one OAuth callback on localhost without exposing its code in output."""

    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.future: asyncio.Future[tuple[str, str | None]] = loop.create_future()
        future = self.future

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                path = urlsplit(self.path)
                if path.path == "/oauth/callback":
                    params = parse_qs(path.query)
                    code = params.get("code", [None])[0]
                    state = params.get("state", [None])[0]
                    if not code or not state:
                        self.send_error(400, "OAuth callback incomplete")
                        return
                    loop.call_soon_threadsafe(future.set_result, (code, state))
                    self.send_response(302)
                    self.send_header("Location", "/complete")
                    self.end_headers()
                    return
                if path.path == "/complete":
                    body = b"Salesforce authorization complete. Return to Codex."
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain; charset=utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    return
                self.send_error(404)

            def log_message(self, _format, *_args):
                # HTTP server logs would include the OAuth code in the URL.
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 6276), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_exc):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)


async def probe(client_id: str, case_id: str, org_origin: str) -> dict | None:
    """Authorize once, discover the read tool, and ask for one bounded Case."""
    loop = asyncio.get_running_loop()
    with LoopbackCallback(loop) as callback:
        async def show_url(auth_url: str) -> None:
            print(f"OPEN_SALESFORCE_URL={auth_url}", flush=True)

        async def receive_code() -> tuple[str, str | None]:
            return await asyncio.wait_for(callback.future, timeout=180)

        auth = OAuthClientProvider(
            server_url=SERVER_URL,
            client_metadata=OAuthClientMetadata(
                client_name="AskAnyDoc Salesforce local read proof",
                redirect_uris=[AnyUrl(CALLBACK_URL)],
                token_endpoint_auth_method="none",
                grant_types=["authorization_code", "refresh_token"],
                response_types=["code"],
                scope="mcp_api refresh_token",
            ),
            storage=MemoryStorage(client_id),
            redirect_handler=show_url,
            callback_handler=receive_code,
            timeout=180,
        )
        async with httpx.AsyncClient(auth=auth, timeout=httpx.Timeout(30)) as http_client:
            async with streamable_http_client(SERVER_URL, http_client=http_client) as (read, write, _session_id):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    names = sorted(tool.name for tool in tools.tools)
                    print(f"READ_TOOLS={','.join(names)}", flush=True)
                    if "soqlQuery" not in names:
                        raise RuntimeError("The read-only SOQL tool is unavailable.")
                    soql_tool = next(tool for tool in tools.tools if tool.name == "soqlQuery")
                    print(f"SOQL_INPUT_SCHEMA={json.dumps(soql_tool.inputSchema, sort_keys=True)}", flush=True)
                    if soql_tool.inputSchema.get("required") != ["q"] or \
                            "q" not in soql_tool.inputSchema.get("properties", {}):
                        raise RuntimeError("Salesforce SOQL input schema changed; review the adapter before querying.")

                    async def diagnostic_call(name: str, arguments: dict[str, str]):
                        result = await session.call_tool(name, arguments)
                        if result.isError:
                            # Diagnostic text is bounded and redacted; the adapter itself
                            # never returns raw Salesforce errors to an end user.
                            detail = " ".join(
                                item.text for item in result.content
                                if getattr(item, "type", None) == "text"
                            )[:500]
                            detail = re.sub(r"eyJ[A-Za-z0-9_.-]{30,}", "<redacted-token>", detail)
                            print(f"SOQL_TOOL_ERROR={detail or 'no detail'}", flush=True)
                        return result

                    return await read_case(case_id, diagnostic_call, org_origin=org_origin)


def main() -> None:
    parser = argparse.ArgumentParser(description="One-shot local Salesforce MCP Case proof")
    parser.add_argument("case_id", help="Salesforce Case record ID")
    parser.add_argument("--answer", action="store_true", help="Also run the local AskAnyDoc answer path")
    args = parser.parse_args()
    client_id = os.environ.get("ASKANYDOC_SF_CLIENT_ID", "")
    org_origin = os.environ.get("ASKANYDOC_SF_ORG_ORIGIN", "")
    if not client_id:
        parser.error("ASKANYDOC_SF_CLIENT_ID must be set to the ECA consumer key")
    if not org_origin:
        parser.error("ASKANYDOC_SF_ORG_ORIGIN must be set to the verified org URL")
    result = asyncio.run(probe(client_id, args.case_id, org_origin))
    if result is None:
        print("CASE_NOT_FOUND")
    else:
        print(f"CASE={result['source_name']} STATUS={result['facts']['Status']} "
              f"PRIORITY={result['facts']['Priority']} URL={result['source_uri']}")
    if args.answer:
        # AskAnyDoc receives verified evidence, never the OAuth token or MCP session.
        from assistant_orchestrator import run_assistant

        question = f"What is the status and priority of Salesforce Case {args.case_id}?"
        evidence = case_as_answer_evidence(result) if result is not None else None
        answer = run_assistant(
            question, [],
            salesforce_case_reader=lambda _case_id: evidence,
        )
        print(f"ASKANYDOC_ANSWER={answer['answer']}")
        print(f"ASKANYDOC_GROUNDED={answer['grounded']}")
        print(f"ASKANYDOC_CITATIONS={json.dumps(answer['citations'], sort_keys=True)}")


if __name__ == "__main__":
    main()
