# Entra delegated SharePoint setup checklist

> **Execution authority:** Use this checklist only with `SHAREPOINT_RETRIEVAL_SOURCE_OF_TRUTH.md`. That document defines the selected provider, exact order, current evidence, approval requirements, and safe stopping points.

> **Status correction — 2026-09-21:** local Terraform state records this feature as enabled with `graph_search`; therefore item 8 is no longer an effective live control. Terraform source now expresses the agreed target safely—disabled, Copilot Retrieval, and placeholder URLs—but those defaults intentionally differ from applied state. Confirm Copilot entitlement/licensing or pay-as-you-go billing, grant only the required delegated consent, supply approved environment values, complete the Adele/Alex permission matrix, run a protected-API OBO Copilot smoke test and AWS regression, then review the Terraform plan and obtain explicit approval before applying.

1. Register a single-tenant web application in Microsoft Entra ID.
2. Add the deployed HTTPS redirect URI; do not use the current HTTP S3 website.
3. Configure delegated Microsoft Graph permissions for the selected retrieval provider.
4. Grant admin consent only for the scopes that the provider actually requires.
5. Record tenant ID, client ID, redirect URI, and scopes in a private deployment setting.
6. Never commit a client secret, refresh token, bearer token, or authorization code.
7. Prove sign-in and delegated identity first, then test SharePoint retrieval outside Bedrock.
8. Keep `SHAREPOINT_ENABLED=false` until the permission and retrieval smoke tests pass.
