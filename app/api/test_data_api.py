"""Tests for bounded Aurora Serverless resume retries."""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError


SHARED_DIR = Path(__file__).resolve().parents[1] / "shared"
sys.path.insert(0, str(SHARED_DIR))

from askanydoc_rag.data_api import call_with_database_resume_retry


def resuming_error() -> ClientError:
    return ClientError(
        {"Error": {"Code": "DatabaseResumingException", "Message": "resuming"}},
        "ExecuteStatement",
    )


class DataApiRetryTests(unittest.TestCase):
    def test_default_retry_budget_preserves_existing_two_four_eight_backoff(self) -> None:
        call = MagicMock(side_effect=[resuming_error(), resuming_error(), resuming_error(), {"ok": True}])
        with (
            patch.dict(os.environ, {}, clear=False),
            patch("askanydoc_rag.data_api.time.sleep") as sleep,
        ):
            os.environ.pop("DATABASE_RESUME_MAX_WAIT_SECONDS", None)
            result = call_with_database_resume_retry(call)
        self.assertEqual(result, {"ok": True})
        self.assertEqual([item.args[0] for item in sleep.call_args_list], [2.0, 4.0, 8.0])

    def test_worker_can_use_a_longer_bounded_resume_budget(self) -> None:
        call = MagicMock(side_effect=[resuming_error()] * 6 + [{"ok": True}])
        with (
            patch.dict(os.environ, {"DATABASE_RESUME_MAX_WAIT_SECONDS": "38"}),
            patch("askanydoc_rag.data_api.time.sleep") as sleep,
        ):
            result = call_with_database_resume_retry(call)
        self.assertEqual(result, {"ok": True})
        self.assertEqual(sum(item.args[0] for item in sleep.call_args_list), 38.0)

    def test_non_resume_errors_are_not_retried(self) -> None:
        error = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "denied"}},
            "ExecuteStatement",
        )
        call = MagicMock(side_effect=error)
        with patch("askanydoc_rag.data_api.time.sleep") as sleep:
            with self.assertRaises(ClientError):
                call_with_database_resume_retry(call)
        sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
