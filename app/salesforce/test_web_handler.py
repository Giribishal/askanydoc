"""Check the cross-user OAuth boundary and that the web route reads a user's grant."""

import json
import os
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from botocore.exceptions import ClientError

from salesforce import web_handler as web


class SalesforceWebBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.auth = {"tenant_id": "tenant", "user_id": "person", "access_token": "entra-token"}
        self.environment = patch.dict(os.environ, {
            "SALESFORCE_WEB_CALLBACK_URL": "https://example.cloudfront.net/",
            "SALESFORCE_ORG_ORIGIN": "https://demo.my.salesforce.com",
            "SALESFORCE_OAUTH_STATES_TABLE": "test-states",
        })
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def test_other_user_cannot_complete_an_oauth_state(self):
        denied = ClientError({"Error": {"Code": "ConditionalCheckFailedException", "Message": "Denied"}}, "DeleteItem")
        with patch.object(web.dynamodb_client, "delete_item", side_effect=denied) as delete_item, \
                patch.object(web, "_exchange") as exchange:
            response = web._complete(self.auth, {"code": "code", "state": "state"})
        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(delete_item.call_args.kwargs["ExpressionAttributeValues"][":owner"]["S"], web._owner_hash(self.auth))
        exchange.assert_not_called()

    def test_case_question_uses_only_current_users_grant(self):
        case_id = "500bm00003BZO62AAH"
        grant = {"access_token": "salesforce-token", "instance_url": "https://demo.my.salesforce.com"}
        case = {"record_id": case_id, "source_name": "Case 00001027", "source_uri": "https://demo.my.salesforce.com/case", "facts": {"CaseNumber": "00001027", "Status": "New"}}
        with patch.object(web, "_load_grant", return_value=grant) as load, \
                patch.object(web, "_refresh_grant", return_value=grant), \
                patch.object(web, "_read_case_mcp", return_value=case) as read, \
                patch.object(web, "run_assistant", return_value={"answer": "New", "citations": []}):
            response = web._ask(self.auth, {"question": f"What is Salesforce Case {case_id}?"})
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(json.loads(response["body"])["answer"], "New")
        load.assert_called_once_with(web._owner_hash(self.auth))
        self.assertEqual(read.call_args.args[1], "salesforce-token")
        self.assertNotIn("salesforce-token", response["body"])

    def test_change_account_requires_fresh_salesforce_login(self):
        with patch.object(web, "_client_info", return_value={"client_id": "public-id"}), \
                patch.object(web.dynamodb_client, "put_item"):
            response = web._connect(self.auth, force_login=True)
        params = parse_qs(urlsplit(json.loads(response["body"])["authorization_url"]).query)
        self.assertEqual(params["prompt"], ["login"])
        self.assertEqual(params["code_challenge_method"], ["S256"])
        self.assertEqual(params["scope"], ["mcp_api refresh_token"])

    def test_disconnect_revokes_only_current_users_refresh_grant(self):
        grant = {"refresh_token": "secret-refresh", "instance_url": "https://demo.my.salesforce.com"}
        class Response:
            status_code = 200
            def raise_for_status(self):
                pass
        class Client:
            sent = None
            def __init__(self, **kwargs):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def post(self, url, data):
                Client.sent = (url, data)
                return Response()
        with patch.object(web, "_load_grant", return_value=grant) as load, \
                patch.object(web, "_save_grant") as save, \
                patch.object(web.httpx, "Client", Client):
            response = web._disconnect(self.auth)
        owner = web._owner_hash(self.auth)
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(json.loads(response["body"])["connected"], False)
        load.assert_called_once_with(owner)
        self.assertEqual(save.call_args.args[0], owner)
        self.assertEqual(Client.sent, (
            "https://demo.my.salesforce.com/services/oauth2/revoke",
            {"token": "secret-refresh"},
        ))
        self.assertNotIn("refresh_token", save.call_args.args[1])
        self.assertNotIn("access_token", save.call_args.args[1])

    def test_failed_revocation_retains_existing_grant(self):
        grant = {"refresh_token": "secret-refresh", "instance_url": "https://demo.my.salesforce.com"}
        class Response:
            status_code = 503
            def raise_for_status(self):
                raise RuntimeError("Salesforce unavailable")
        class Client:
            def __init__(self, **kwargs):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def post(self, url, data):
                return Response()
        with patch.object(web, "_load_grant", return_value=grant), \
                patch.object(web, "_save_grant") as save, \
                patch.object(web.httpx, "Client", Client):
            with self.assertRaises(RuntimeError):
                web._disconnect(self.auth)
        save.assert_not_called()

    def test_disconnected_secret_cannot_be_used_as_a_grant(self):
        owner = web._owner_hash(self.auth)
        value = json.dumps({
            "owner_hash": owner,
            "instance_url": "https://demo.my.salesforce.com",
            "disconnected_at": 1234567890,
        })
        with patch.object(web.secrets_client, "get_secret_value", return_value={"SecretString": value}):
            self.assertIsNone(web._load_grant(owner))


if __name__ == "__main__":
    unittest.main()
