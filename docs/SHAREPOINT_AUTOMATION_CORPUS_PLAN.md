# SharePoint Microsoft 365 automation corpus

## Purpose

This SharePoint test corpus is intentionally separate from the AWS/RAG project. It represents a Microsoft-authored reference library covering Power Automate, SharePoint, Teams, Outlook, governance, deployment, and operational guidance. We will not present locally invented procedures as official Microsoft guidance.

## General site

These documents are intended for `AskAnyDoc-General-Readers`:

1. `Power-Automate-Cloud-Flow-Fundamentals.pdf`
2. `Microsoft-365-Approval-Workflow-Runbook.pdf`
3. `SharePoint-Document-Lifecycle-Automation.pdf`
4. `Teams-Notification-Automation-Patterns.pdf`
5. `Outlook-Email-Automation-Runbook.pdf`
6. `Power-Platform-Environment-Overview.pdf`

## Restricted senior site

These documents are intended for `AskAnyDoc-Senior-Readers`:

1. `Power-Automate-Governance-and-DLP.pdf`
2. `Microsoft-365-Automation-Security-Architecture.pdf`
3. `Power-Platform-ALM-and-Deployment-Runbook.pdf`
4. `Production-Flow-Monitoring-and-Recovery-Runbook.pdf`
5. `SharePoint-Permissions-and-Compliance-Architecture.pdf`
6. `Power-Automate-Cost-and-Quota-Management.pdf`

## Required reference metadata

Each stored reference or link record should contain:

- purpose and audience;
- Microsoft publication title and source type (`Learn`, architecture PDF, or official guide);
- official publication URL and retrieval date;
- a short neutral description, without changing Microsoft's meaning;
- licensing/download status; only permitted Microsoft PDFs are uploaded;
- a classification label: `General` or `Senior-Restricted`.

## Validation questions

1. How do I create a Power Automate approval flow?
2. What should happen when a SharePoint document is uploaded?
3. How can a flow notify a Teams channel?
4. What is the recovery process when a production flow fails?
5. Which governance and DLP controls are required?
6. Can a general user see the production monitoring runbook? The expected result is no.
7. Which answer requires evidence from both a general document and a restricted document?
8. What should the assistant say when no document contains the answer?

## Access matrix

| Identity | General corpus | Restricted corpus |
|---|---:|---:|
| Adele Vance / `AskAnyDoc-General-Readers` | Allowed | Denied |
| Alex Wilber / `AskAnyDoc-Senior-Readers` | Allowed | Allowed |

## Execution order

1. Collect the twelve approved Microsoft references.
2. Upload only permitted official PDFs; store link/index records for Learn pages.
3. Verify the files and metadata in both libraries.
4. Test direct access with the two synthetic identities.
5. Run the validation questions and record citations, denials, empty answers, and failures.
6. Compare live SharePoint retrieval with the existing indexed S3 pattern before implementing the connector.
