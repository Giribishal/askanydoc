"""RDS Data API helpers that tolerate an Aurora Serverless cold resume."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from botocore.exceptions import ClientError


def call_with_database_resume_retry(call: Callable[..., Any], **arguments: Any) -> Any:
    """Retry only Aurora's explicit auto-resume response with bounded backoff."""
    for attempt, delay_seconds in enumerate((2, 4, 8, 0), start=1):
        try:
            return call(**arguments)
        except ClientError as error:
            code = error.response.get("Error", {}).get("Code")
            if code != "DatabaseResumingException" or attempt == 4:
                raise
            time.sleep(delay_seconds)
    raise RuntimeError("Aurora retry loop ended unexpectedly.")
