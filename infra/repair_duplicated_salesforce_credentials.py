"""Repair exactly duplicated OAuth credentials without printing their values."""

import json

import boto3


SECRET_ID = "askanydoc/salesforce-web-client-dev"


def main():
    client = boto3.client("secretsmanager", region_name="ap-southeast-2")
    record = client.get_secret_value(SecretId=SECRET_ID)
    credentials = json.loads(record["SecretString"])
    repaired = []
    for field in ("client_id", "client_secret"):
        value = credentials.get(field, "")
        midpoint = len(value) // 2
        if midpoint and len(value) % 2 == 0 and value[:midpoint] == value[midpoint:]:
            credentials[field] = value[:midpoint]
            repaired.append(field)
    if not repaired:
        raise RuntimeError("No exactly duplicated Salesforce credential found; no change made.")
    client.put_secret_value(SecretId=SECRET_ID, SecretString=json.dumps(credentials))
    print("Duplicated Salesforce credential field(s) repaired; values were not printed.")


if __name__ == "__main__":
    main()
