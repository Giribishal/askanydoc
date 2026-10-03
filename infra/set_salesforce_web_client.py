"""One-time interactive transfer of the Salesforce web ECA secret to AWS.

The operator reads the values in Salesforce and enters them into a no-echo
terminal prompt. This script never prints the values or writes a local file.
"""

import getpass
import json

import boto3


SECRET_ID = "askanydoc/salesforce-web-client-dev"


def main() -> None:
    client_id = getpass.getpass("Salesforce Consumer Key (hidden): ").strip()
    client_secret = getpass.getpass("Salesforce Consumer Secret (hidden): ").strip()
    if not client_id or not client_secret:
        raise SystemExit("Both values are required; nothing was saved.")
    boto3.client("secretsmanager", region_name="ap-southeast-2").put_secret_value(
        SecretId=SECRET_ID,
        SecretString=json.dumps({"client_id": client_id, "client_secret": client_secret}),
    )
    print("Salesforce web client credential stored in AWS Secrets Manager. Values were not printed.")


if __name__ == "__main__":
    main()
