import { PublicClientApplication } from '@azure/msal-browser'

const tenantId = import.meta.env.VITE_ENTRA_TENANT_ID
const spaClientId = import.meta.env.VITE_ENTRA_SPA_CLIENT_ID
const apiScope = import.meta.env.VITE_ENTRA_API_SCOPE

export const authConfigured = Boolean(tenantId && spaClientId && apiScope)
export const apiUrl = import.meta.env.VITE_API_URL
export const answerJobsUrl = apiUrl?.replace(/\/chat\/?$/, '/jobs')
export const salesforceUrl = apiUrl?.replace(/\/chat\/?$/, '/salesforce')
export const loginRequest = { scopes: apiScope ? [apiScope] : [] }

export const msalInstance = new PublicClientApplication({
  auth: {
    clientId: spaClientId || '00000000-0000-0000-0000-000000000000',
    authority: `https://login.microsoftonline.com/${tenantId || 'organizations'}`,
    redirectUri: window.location.origin,
    postLogoutRedirectUri: window.location.origin,
  },
  cache: {
    cacheLocation: 'sessionStorage',
  },
})
