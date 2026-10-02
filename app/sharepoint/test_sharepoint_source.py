import json
from email.message import Message
import urllib.error
import urllib.request

import pytest

from .copilot_retrieval_provider import CopilotRetrievalProvider
from .copilot_retrieval_provider import _allowed_site_filter as copilot_site_filter
from .graph_search_provider import _download_drive_item, _scoped_query
from .pdf_grounding import rank_page_texts
from .sharepoint_config import load_sharepoint_config
from .sharepoint_source import SharePointError, match_allowed_site, search_sharepoint
from .source_router import plan_sources

from organisation_tools import organisation_tool_config, sharepoint_tool_available


class FakeProvider:
    def __init__(self, items=None, error=None):
        self.items, self.error, self.calls = items or [], error, []

    def search(self, query, user_context, max_results):
        self.calls.append((query, user_context, max_results))
        if self.error:
            raise self.error
        return self.items


def item(name="guide.pdf", classification="general"):
    return {"text": "approved guidance", "name": name, "web_url": "https://sharepoint/item", "site": "general", "classification": classification}


def test_disabled_feature_flag_does_not_call_provider():
    provider = FakeProvider([item()])
    config = load_sharepoint_config({"SHAREPOINT_ENABLED": "false"})
    assert search_sharepoint(provider, "approval flow", {}, config) == []
    assert provider.calls == []


def test_enabled_search_normalises_provenance_and_user_context():
    provider = FakeProvider([item()])
    config = load_sharepoint_config({"SHAREPOINT_ENABLED": "true"})
    user_context = {"user_id": "adele", "access_token": "api-token"}
    result = search_sharepoint(provider, "approval flow", user_context, config)
    assert result[0].source_uri == "https://sharepoint/item"
    assert provider.calls[0][1] == user_context


def test_malformed_provider_response_is_not_retried():
    provider = FakeProvider([{"text": "missing provenance"}])
    config = load_sharepoint_config({"SHAREPOINT_ENABLED": "true"})
    try:
        search_sharepoint(
            provider,
            "question",
            {"user_id": "adele", "access_token": "api-token"},
            config,
        )
    except SharePointError as error:
        assert error.code == "malformed_response"
    else:
        raise AssertionError("expected malformed response")


def test_router_preserves_aws_and_supports_cross_source():
    assert plan_sources("What is in S3?", True).sources == ("aws",)
    assert plan_sources("Compare S3 with SharePoint", True).sources == ("aws", "sharepoint")
    assert plan_sources("Power Automate approval flow", True).sources == ("sharepoint",)
    assert plan_sources("What problem do partial batch responses solve in SQS?", True).sources == ("aws",)
    assert plan_sources("What principles guide Microsoft 365 hybrid-cloud architecture?", True).sources == ("sharepoint",)
    assert plan_sources(
        "How do S3 disaster recovery and Microsoft 365 hybrid-cloud design complement each other?",
        True,
    ).sources == ("aws", "sharepoint")
    assert plan_sources("Hello, how are you?", True).sources == ()
    assert plan_sources("What draws people to this design?", True).sources == ()


def test_router_records_source_specific_signals_for_query_planning():
    plan = plan_sources(
        "What disaster-recovery strategies protect workloads, and how does hybrid cloud "
        "connect on-premises systems? Compare them.",
        True,
    )

    assert plan.sources == ("aws", "sharepoint")
    assert plan.aws_signals == ("disaster-recovery",)
    assert plan.sharepoint_signals == ("hybrid cloud",)


def test_graph_search_query_is_scoped_to_both_approved_sites():
    config = load_sharepoint_config({
        "SHAREPOINT_GENERAL_SITE_URL": "https://tenant.sharepoint.com/sites/general",
        "SHAREPOINT_RESTRICTED_SITE_URL": "https://tenant.sharepoint.com/sites/restricted",
    })
    query = _scoped_query('approval OR Path:"https://outside.example"', config)
    assert query.startswith('(approval OR Path:"https://outside.example") AND (')
    assert 'Path:"https://tenant.sharepoint.com/sites/general"' in query
    assert 'Path:"https://tenant.sharepoint.com/sites/restricted"' in query


def test_copilot_retrieval_filter_is_scoped_to_both_approved_sites():
    config = load_sharepoint_config({
        "SHAREPOINT_GENERAL_SITE_URL": "https://tenant.sharepoint.com/sites/general/",
        "SHAREPOINT_RESTRICTED_SITE_URL": "https://tenant.sharepoint.com/sites/restricted/",
    })
    site_filter = copilot_site_filter(config)
    assert site_filter == (
        'path:"https://tenant.sharepoint.com/sites/general" OR '
        'path:"https://tenant.sharepoint.com/sites/restricted"'
    )


def test_response_allowlist_requires_exact_host_and_site_path_boundary():
    config = load_sharepoint_config({
        "SHAREPOINT_GENERAL_SITE_URL": "https://tenant.sharepoint.com/sites/general",
        "SHAREPOINT_RESTRICTED_SITE_URL": "https://tenant.sharepoint.com/sites/restricted",
    })
    assert match_allowed_site(
        "https://tenant.sharepoint.com/sites/general/Shared%20Documents/guide.pdf",
        config,
    ).name == "general"
    assert match_allowed_site(
        "https://tenant.sharepoint.com/sites/general-evil/guide.pdf",
        config,
    ) is None
    assert match_allowed_site(
        "https://tenant.sharepoint.com.evil.example/sites/general/guide.pdf",
        config,
    ) is None


def test_graph_search_is_the_selected_environment_default_provider():
    assert load_sharepoint_config({}).provider == "graph_search"


def test_copilot_retrieval_uses_obo_scoping_and_returns_extracts(monkeypatch):
    config = load_sharepoint_config({
        "SHAREPOINT_ENABLED": "true",
        "SHAREPOINT_PROVIDER": "copilot_retrieval",
        "SHAREPOINT_GENERAL_SITE_URL": "https://tenant.sharepoint.com/sites/general",
        "SHAREPOINT_RESTRICTED_SITE_URL": "https://tenant.sharepoint.com/sites/restricted",
    })
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return json.dumps({
                "retrievalHits": [{
                    "webUrl": "https://tenant.sharepoint.com/sites/general/Shared Documents/guide.pdf",
                    "extracts": [
                        {"text": "Grounded paragraph one.", "relevanceScore": 0.72},
                        {"text": "Grounded paragraph two.", "relevanceScore": 0.91},
                    ],
                    "resourceMetadata": {"title": "Guide"},
                }],
            }).encode("utf-8")

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["authorization"] = request.headers["Authorization"]
        captured["payload"] = json.loads(request.data)
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(
        "sharepoint.copilot_retrieval_provider.acquire_graph_token",
        lambda token, timeout: "obo-graph-token",
    )
    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    result = CopilotRetrievalProvider(config).search(
        "What does the guide say?",
        {"access_token": "api-token"},
        10,
    )

    assert captured["url"] == "https://graph.microsoft.com/v1.0/copilot/retrieval"
    assert captured["authorization"] == "Bearer obo-graph-token"
    assert captured["payload"] == {
        "queryString": "What does the guide say?",
        "dataSource": "sharePoint",
        "filterExpression": (
            'path:"https://tenant.sharepoint.com/sites/general" OR '
            'path:"https://tenant.sharepoint.com/sites/restricted"'
        ),
        "resourceMetadata": ["title"],
        "maximumNumberOfResults": 10,
    }
    assert result[0]["text"] == "Grounded paragraph one. Grounded paragraph two."
    assert result[0]["relevance_score"] == 0.91
    assert result[0]["classification"] == "general"


def test_copilot_retrieval_rejects_query_above_documented_limit():
    config = load_sharepoint_config({"SHAREPOINT_ENABLED": "true"})
    with pytest.raises(SharePointError) as captured:
        CopilotRetrievalProvider(config).search(
            "x" * 1501,
            {"access_token": "api-token"},
            10,
        )
    assert captured.value.code == "invalid_request"


def test_copilot_retrieval_maps_invalid_json_to_safe_error(monkeypatch):
    config = load_sharepoint_config({"SHAREPOINT_ENABLED": "true"})

    class InvalidJsonResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b"not-json"

    monkeypatch.setattr(
        "sharepoint.copilot_retrieval_provider.acquire_graph_token",
        lambda token, timeout: "obo-graph-token",
    )
    monkeypatch.setattr(urllib.request, "urlopen", lambda *_args, **_kwargs: InvalidJsonResponse())

    with pytest.raises(SharePointError) as captured:
        CopilotRetrievalProvider(config).search(
            "What does the guide say?",
            {"access_token": "api-token"},
            10,
        )
    assert captured.value.code == "malformed_response"
    assert not captured.value.retryable


def test_copilot_retrieval_rejects_invalid_response_shape(monkeypatch):
    config = load_sharepoint_config({"SHAREPOINT_ENABLED": "true"})

    class InvalidShapeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return json.dumps({"retrievalHits": {"unexpected": "object"}}).encode("utf-8")

    monkeypatch.setattr(
        "sharepoint.copilot_retrieval_provider.acquire_graph_token",
        lambda token, timeout: "obo-graph-token",
    )
    monkeypatch.setattr(urllib.request, "urlopen", lambda *_args, **_kwargs: InvalidShapeResponse())

    with pytest.raises(SharePointError) as captured:
        CopilotRetrievalProvider(config).search(
            "What does the guide say?",
            {"access_token": "api-token"},
            10,
        )
    assert captured.value.code == "malformed_response"


def test_copilot_retrieval_maps_network_failure_to_retryable_error(monkeypatch):
    config = load_sharepoint_config({"SHAREPOINT_ENABLED": "true"})
    monkeypatch.setattr(
        "sharepoint.copilot_retrieval_provider.acquire_graph_token",
        lambda token, timeout: "obo-graph-token",
    )

    def unavailable(*_args, **_kwargs):
        raise urllib.error.URLError("network unavailable")

    monkeypatch.setattr(urllib.request, "urlopen", unavailable)

    with pytest.raises(SharePointError) as captured:
        CopilotRetrievalProvider(config).search(
            "What does the guide say?",
            {"access_token": "api-token"},
            10,
        )
    assert captured.value.code == "sharepoint_upstream_error"
    assert captured.value.retryable


def test_unauthenticated_request_receives_only_aws_search_tool():
    names = [tool["toolSpec"]["name"] for tool in organisation_tool_config(False)["tools"]]
    assert names == ["search_aws_documents"]


def test_authenticated_request_can_receive_both_search_tools():
    names = [tool["toolSpec"]["name"] for tool in organisation_tool_config(True)["tools"]]
    assert names == ["search_aws_documents", "search_sharepoint"]


def test_sharepoint_tool_requires_complete_identity_and_enablement(monkeypatch):
    monkeypatch.setenv("SHAREPOINT_ENABLED", "true")
    assert not sharepoint_tool_available(None)
    assert not sharepoint_tool_available({"user_id": "adele", "access_token": "token"})
    assert sharepoint_tool_available({
        "user_id": "adele",
        "tenant_id": "tenant",
        "access_token": "token",
    })


def test_pdf_page_ranking_prefers_query_terms_and_stays_bounded():
    pages = [
        (1, "Introduction and copyright"),
        (2, "Teams chat service stores messages and coordinates conversations."),
        (3, "Teams meetings use media services and signalling components."),
    ]
    ranked = rank_page_texts(
        pages,
        "What services support Teams chat?",
        max_pages=2,
        max_characters=45,
    )
    assert ranked[0]["page_number"] == 2
    assert len(ranked) == 2
    assert len(ranked[0]["text"]) <= 45


def test_graph_download_never_forwards_bearer_token_to_storage_host(monkeypatch):
    calls = []

    class Response:
        def __init__(self, body):
            self.body = body

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, *_args):
            return self.body

    def fake_urlopen(request, timeout):
        calls.append((request, timeout))
        if isinstance(request, urllib.request.Request):
            return Response(json.dumps({
                "size": 4,
                "@microsoft.graph.downloadUrl": "https://storage.example/file",
            }).encode("utf-8"))
        return Response(b"%PDF")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    assert _download_drive_item("secret-token", "drive", "item", 100, 8) == b"%PDF"
    assert calls[0][0].get_header("Authorization") == "Bearer secret-token"
    assert calls[1][0] == "https://storage.example/file"


def test_graph_download_uses_content_redirect_when_annotation_is_omitted(monkeypatch):
    calls = []

    class Response:
        def __init__(self, body):
            self.body = body

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, *_args):
            return self.body

    class ContentOpener:
        def open(self, request, timeout):
            calls.append((request, timeout))
            headers = Message()
            headers["Location"] = "https://storage.example/content-file"
            raise urllib.error.HTTPError(request.full_url, 302, "Found", headers, None)

    def fake_urlopen(request, timeout):
        calls.append((request, timeout))
        if isinstance(request, urllib.request.Request):
            return Response(json.dumps({"size": 4}).encode("utf-8"))
        return Response(b"%PDF")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(urllib.request, "build_opener", lambda *_handlers: ContentOpener())

    assert _download_drive_item("secret-token", "drive", "item", 100, 8) == b"%PDF"
    assert calls[0][0].get_header("Authorization") == "Bearer secret-token"
    assert calls[1][0].full_url.endswith("/drives/drive/items/item/content")
    assert calls[1][0].get_header("Authorization") == "Bearer secret-token"
    assert calls[2][0] == "https://storage.example/content-file"


def test_graph_download_maps_metadata_timeout_to_retryable_error(monkeypatch):
    def timeout(*_args, **_kwargs):
        raise TimeoutError("metadata request timed out")

    monkeypatch.setattr(urllib.request, "urlopen", timeout)

    with pytest.raises(SharePointError) as captured:
        _download_drive_item("token", "drive", "item", 100, 8)

    assert captured.value.code == "sharepoint_timeout"
    assert captured.value.retryable


def test_graph_download_rejects_file_above_configured_byte_limit(monkeypatch):
    calls = []

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, *_args):
            return json.dumps({
                "size": 101,
                "@microsoft.graph.downloadUrl": "https://storage.example/file",
            }).encode("utf-8")

    def fake_urlopen(request, timeout):
        calls.append((request, timeout))
        return Response()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    with pytest.raises(SharePointError) as captured:
        _download_drive_item("token", "drive", "item", 100, 8)

    assert captured.value.code == "document_too_large"
    assert not captured.value.retryable
    assert len(calls) == 1


def test_throttled_provider_stops_after_configured_retry_cap(monkeypatch):
    provider = FakeProvider(
        error=SharePointError(
            "sharepoint_throttled",
            "Microsoft Graph throttled the request",
            retryable=True,
        )
    )
    config = load_sharepoint_config({
        "SHAREPOINT_ENABLED": "true",
        "SHAREPOINT_MAX_RETRIES": "2",
    })
    monkeypatch.setattr("sharepoint.sharepoint_source.time.sleep", lambda *_args: None)

    with pytest.raises(SharePointError) as captured:
        search_sharepoint(
            provider,
            "approval flow",
            {"user_id": "adele", "access_token": "api-token"},
            config,
        )

    assert captured.value.code == "sharepoint_throttled"
    assert len(provider.calls) == 3
