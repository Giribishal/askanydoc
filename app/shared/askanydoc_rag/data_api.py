"""RDS Data API helpers that tolerate an Aurora Serverless cold resume."""

from __future__ import annotations

import time
import os
from collections.abc import Callable
from typing import Any

from botocore.exceptions import ClientError


def call_with_database_resume_retry(call: Callable[..., Any], **arguments: Any) -> Any:
    """Retry only Aurora's explicit auto-resume response with bounded backoff."""
    max_wait_seconds = float(os.environ.get("DATABASE_RESUME_MAX_WAIT_SECONDS", "14"))
    waited_seconds = 0.0
    delay_seconds = 2.0
    while True:
        try:
            return call(**arguments)
        except ClientError as error:
            code = error.response.get("Error", {}).get("Code")
            if code != "DatabaseResumingException" or waited_seconds >= max_wait_seconds:
                raise
            bounded_delay = min(delay_seconds, max_wait_seconds - waited_seconds)
            if bounded_delay <= 0:
                raise
            time.sleep(bounded_delay)
            waited_seconds += bounded_delay
            delay_seconds = min(delay_seconds * 2, 8.0)
