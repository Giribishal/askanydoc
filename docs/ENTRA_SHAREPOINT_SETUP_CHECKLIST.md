# Entra delegated SharePoint setup checklist

> **Execution authority:** Use this checklist only with `SHAREPOINT_RETRIEVAL_SOURCE_OF_TRUTH.md`. That document defines the selected provider, exact order, current evidence, approval requirements, and safe stopping points.

> **Status correction — 2026-09-21 end of day:** Option B is deployed with `graph_search`; checked-in Terraform defaults remain disabled with placeholder URLs and provider `graph_search`. The protected API/OBO flow, AWS regression, and controlled Adele/Alex AskAnyDoc permission matrix passed. Copilot Retrieval remains commercially blocked. Still verify Entra consent read-only and direct isolated SharePoint-site access, then complete timeout/throttling/extraction/adversarial cases. The prior deployment approval is consumed; any further apply or permission change requires a fresh warning, plan, and explicit approval.

1. Register a single-tenant web application in Microsoft Entra ID.
2. Add the deployed HTTPS redirect URI; do not use the current HTTP S3 website.
3. Configure delegated Microsoft Graph permissions for the selected retrieval provider.
4. Grant admin consent only for the scopes that the provider actually requires.
5. Record tenant ID, client ID, redirect URI, and scopes in a private deployment setting.
6. Never commit a client secret, refresh token, bearer token, or authorization code.
7. Prove sign-in and delegated identity first, then test SharePoint retrieval outside Bedrock.
8. Keep `SHAREPOINT_ENABLED=false` until the permission and retrieval smoke tests pass.
