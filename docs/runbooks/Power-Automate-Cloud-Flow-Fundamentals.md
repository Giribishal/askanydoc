# Power Automate cloud flow fundamentals

Classification: General
Audience: Microsoft 365 automation users
Official source: https://learn.microsoft.com/en-us/power-automate/get-started-approvals

## Purpose

Use a cloud flow to start work from an event, perform actions, and optionally wait for a human approval.

## Standard pattern

1. Choose a trigger, such as a new SharePoint file.
2. Add actions that read the item and perform the required work.
3. Add an approval when a person must decide.
4. Branch on the approval outcome.
5. Write the result back to SharePoint or notify Teams.
6. Inspect run history when the flow fails.

## Failure handling

Use explicit success and failure branches. Record the item ID, run ID, action name, and error message. Do not silently continue after a failed security-sensitive action.

## Design rule

Keep connection ownership, data classification, and the users who can run the flow documented with the flow.
