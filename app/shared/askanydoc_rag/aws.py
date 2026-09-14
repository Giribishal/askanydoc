"""Create regional AWS clients with one consistent retry policy."""

from __future__ import annotations

import boto3
from botocore.config import Config


AWS_CLIENT_CONFIG = Config(retries={"mode": "standard", "max_attempts": 4})


def aws_client(service_name: str):
    """Return an AWS client configured for AskAnyDoc's deployment Region."""
    return boto3.client(
        service_name,
        region_name="ap-southeast-2",
        config=AWS_CLIENT_CONFIG,
    )
