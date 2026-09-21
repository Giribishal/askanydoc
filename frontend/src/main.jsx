// Decides where to put the tags, where to show them are decided here.

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { MsalProvider } from '@azure/msal-react'
import App from './App.jsx'
import { msalInstance } from './authConfig.js'

await msalInstance.initialize()

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <MsalProvider instance={msalInstance}>
      <App />
    </MsalProvider>
  </StrictMode>,
)
