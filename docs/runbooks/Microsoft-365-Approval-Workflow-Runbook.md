# Microsoft 365 approval workflow runbook

Classification: General
Audience: Microsoft 365 automation users
Official source: https://learn.microsoft.com/en-us/power-automate/get-started-approvals

## Procedure

1. Define the business event and the approver.
2. Create an approval flow from the relevant connector.
3. Use a stable record identifier in the approval title and details.
4. Assign the request to the intended person or group.
5. Handle Approve, Reject, timeout, and failure separately.
6. Update the source record and notify the requester.

## Operational checks

- Confirm the approver has the required Microsoft 365 access.
- Avoid putting sensitive content into broad notification messages.
- Preserve the approval response and timestamp for auditability.
- Use run history to distinguish business rejection from technical failure.
