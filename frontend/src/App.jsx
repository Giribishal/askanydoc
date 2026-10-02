// App.jsx — AskAnyDoc chatbot page (conversation version).
// Flow: user types -> clicks Ask -> question added to the list right away ->
// we POST it to the Lambda -> answer comes back -> answer added to the list ->
// React shows the whole conversation as bubbles, and auto-scrolls to the newest.

import { useState, useRef, useEffect } from 'react'   // state + a page pointer + an after-update hook
import ReactMarkdown from 'react-markdown'             // safely turn Claude's Markdown into readable HTML
import { useIsAuthenticated, useMsal } from '@azure/msal-react'
import { InteractionRequiredAuthError } from '@azure/msal-browser'
import { answerJobsUrl, authConfigured, loginRequest } from './authConfig.js'
import Sidebar from './Sidebar.jsx'
import './App.css'                                     // the styling for this page

function tokenDiagnostics(accessToken) {
  try {
    const segment = accessToken.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')
    const payload = JSON.parse(atob(segment))
    return {
      issuer: payload.iss,
      audience: payload.aud,
      scope: payload.scp,
      version: payload.ver,
    }
  } catch {
    return { token_parse: 'failed' }
  }
}

// Citation provenance is created by the backend, so the UI can label a source
// without trusting model-written answer text or exposing storage details by default.
function citationSourceSystem(citation) {
  const sourceType = citation?.source_type?.toLowerCase()
  const sourceUri = citation?.source_uri?.toLowerCase() || ""
  if (sourceType === "sharepoint" || sourceUri.includes(".sharepoint.com/")) {
    return "sharepoint"
  }
  if (sourceUri.startsWith("s3://") || citation?.object_key) return "aws"
  return "other"
}

function sourceBadgeLabel(message) {
  if (message.source_mode === "general_knowledge") return "Source: General knowledge"
  if (message.source_mode === "organisation_not_found") return "No organisation source found"
  if (message.source_mode === "conversation") return "Conversation"
  if (message.source_mode !== "organisation_sources") return null

  const sourceSystems = new Set((message.citations || []).map(citationSourceSystem))
  if (sourceSystems.has("aws") && sourceSystems.has("sharepoint")) {
    return "Sources: AWS document library + SharePoint"
  }
  if (sourceSystems.has("sharepoint")) return "Source: SharePoint"
  if (sourceSystems.has("aws")) return "Source: AWS document library"
  return "Source: Organisation documents"
}

function groupedCitations(citations = []) {
  const groups = {
    aws: { label: "AWS document library", citations: [] },
    sharepoint: { label: "SharePoint", citations: [] },
    other: { label: "Other organisation sources", citations: [] },
  }
  citations.forEach(citation => groups[citationSourceSystem(citation)].citations.push(citation))
  return Object.values(groups).filter(group => group.citations.length > 0)
}

function initialSidebarState() {
  try {
    return window.localStorage.getItem("askanydoc-sidebar-collapsed") === "true"
  } catch {
    return false
  }
}

const DEFAULT_SIDEBAR_WIDTH = 168
const MIN_SIDEBAR_WIDTH = 160
const MAX_SIDEBAR_WIDTH = 360

function clampSidebarWidth(width) {
  return Math.min(MAX_SIDEBAR_WIDTH, Math.max(MIN_SIDEBAR_WIDTH, Math.round(width)))
}

function initialSidebarWidth() {
  try {
    const savedWidth = Number(window.localStorage.getItem("askanydoc-sidebar-width"))
    if (Number.isFinite(savedWidth)) return clampSidebarWidth(savedWidth)
  } catch {
    // A blocked preference store should not prevent the interface from loading.
  }
  return DEFAULT_SIDEBAR_WIDTH
}

function initialTheme() {
  try {
    const savedTheme = window.localStorage.getItem("askanydoc-theme")
    if (savedTheme === "light" || savedTheme === "dark") return savedTheme
  } catch {
    // A blocked preference store should not prevent the interface from loading.
  }
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light"
}

function App() {

  const { instance, accounts } = useMsal()
  const isAuthenticated = useIsAuthenticated()

  // ── the data this page remembers ──
  const [question, setQuestion] = useState("")   // what the user is currently typing
  const [messages, setMessages] = useState([])   // the WHOLE conversation (a list)
  const [loading, setLoading] = useState(false)  // true while we wait for the Lambda
  const [sidebarCollapsed, setSidebarCollapsed] = useState(initialSidebarState)
  const [sidebarWidth, setSidebarWidth] = useState(initialSidebarWidth)
  const [theme, setTheme] = useState(initialTheme)
  const currentChatTitle = messages.find(message => message.role === "user")?.text

  function startNewChat() {
    setMessages([])
    setQuestion("")
  }

  function toggleSidebar() {
    setSidebarCollapsed(currentValue => {
      const nextValue = !currentValue
      try {
        window.localStorage.setItem("askanydoc-sidebar-collapsed", String(nextValue))
      } catch {
        // A blocked preference store should not prevent the sidebar from working now.
      }
      return nextValue
    })
  }

  function updateSidebarWidth(width, persist = false) {
    const nextWidth = clampSidebarWidth(width)
    setSidebarWidth(nextWidth)
    if (!persist) return
    try {
      window.localStorage.setItem("askanydoc-sidebar-width", String(nextWidth))
    } catch {
      // The resized sidebar still works even when browser storage is unavailable.
    }
  }

  function toggleTheme() {
    setTheme(currentTheme => {
      const nextTheme = currentTheme === "dark" ? "light" : "dark"
      try {
        window.localStorage.setItem("askanydoc-theme", nextTheme)
      } catch {
        // The current theme still changes even when browser storage is unavailable.
      }
      return nextTheme
    })
  }

  async function readJsonResponse(response) {
    const responseText = await response.text()
    try {
      return responseText ? JSON.parse(responseText) : {}
    } catch {
      return { error: responseText }
    }
  }

  async function waitForAnswerJob(jobId, accessToken) {
    const startedAt = Date.now()
    const maximumWaitMilliseconds = 180_000
    while (Date.now() - startedAt < maximumWaitMilliseconds) {
      await new Promise(resolve => setTimeout(resolve, 2_000))
      const response = await fetch(`${answerJobsUrl}/${encodeURIComponent(jobId)}`, {
        headers: { "Authorization": `Bearer ${accessToken}` },
      })
      const data = await readJsonResponse(response)
      // Polling is safe to retry: it only reads an existing job. A brief API
      // throttle or service error must not discard an answer still being prepared.
      if (response.status === 429 || response.status >= 500) continue
      if (!response.ok) {
        throw new Error(data.error || data.message || `Answer status failed (${response.status}).`)
      }
      if (data.status === "completed") return data.result
      if (data.status === "failed") {
        const requestSuffix = data.request_id ? ` Request ID: ${data.request_id}` : ""
        throw new Error(`${data.error || "AskAnyDoc could not complete the answer."}${requestSuffix}`)
      }
      if (data.status === "expired") {
        throw new Error(data.error || "This answer job has expired. Please ask the question again.")
      }
    }
    throw new Error(`The answer is still not ready after three minutes. Job ID: ${jobId}`)
  }

  function citationLabel(citation) {
    const location = citation.location || {}
    if (location.page_number) return `${citation.source_name}, page ${location.page_number}`
    if (location.heading_path?.length) return `${citation.source_name}, ${location.heading_path.join(" > ")}`
    if (location.heading) return `${citation.source_name}, ${location.heading}`
    if (location.line_start) return `${citation.source_name}, lines ${location.line_start}-${location.line_end}`
    return citation.source_name
  }

  // bottomRef = a POINTER to an empty marker at the very bottom of the chat.
  // useRef lets us reach a real element on the page so we can act on it (here: scroll to it).
  const bottomRef = useRef(null)

  // useEffect = run code AFTER the page updates. [messages] = only run it when messages changes.
  // So: a new message is added -> React draws it -> THEN this runs -> scroll the marker into view.
  // (We can't scroll inside askQuestion directly, because the new bubble isn't drawn yet at that point.)
  useEffect(() => {
    bottomRef.current.scrollIntoView({ behavior: "smooth" })   // smoothly scroll down to the bottom marker
  }, [messages])

  // ── the function the Ask button runs ──
  // async = this function waits for slow things (the Lambda call takes 2-3 seconds).
  async function askQuestion() {
    if (!question || !isAuthenticated) return   // SharePoint access requires a signed-in user

    const submittedQuestion = question
    const history = messages
      .filter((message, index, conversation) => (
        !message.error && !(message.role === "user" && conversation[index + 1]?.error)
      ))
      .slice(-12)
      .map(message => {
        const role = message.role === "ai" ? "assistant" : "user"
        return {
          role: role,
          content: message.text,
          ...(role === "assistant" && message.source_mode
            ? { source_mode: message.source_mode }
            : {}),
        }
      })

    setLoading(true)   // we are now waiting

    // add the user's question to the list RIGHT AWAY (so it shows while AI thinks).
    // [...prev, newItem] = keep all old messages, add the new one at the end.
    setMessages(prev => [...prev, { role: "user", text: question }])

    try {
      let tokenResponse
      try {
        tokenResponse = await instance.acquireTokenSilent({
          ...loginRequest,
          account: accounts[0],
        })
      } catch (error) {
        if (error instanceof InteractionRequiredAuthError) {
          await instance.acquireTokenRedirect(loginRequest)
          return
        }
        throw error
      }
      const response = await fetch(answerJobsUrl, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${tokenResponse.accessToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: submittedQuestion,
          history: history,
        }),
      })
      const data = await readJsonResponse(response)
      if (!response.ok) {
        console.error(`AskAnyDoc request rejected ${JSON.stringify({
          status: response.status,
          token: tokenDiagnostics(tokenResponse.accessToken),
        })}`)
        throw new Error(data.error || data.message || `AskAnyDoc request failed (${response.status}).`)
      }

      if (!data.job_id) throw new Error("AskAnyDoc did not return an answer job ID.")
      const answer = await waitForAnswerJob(data.job_id, tokenResponse.accessToken)

      setMessages(prev => [...prev, {
        role: "ai",
        text: answer.answer,
        source_mode: answer.source_mode,
        retrieval_score: answer.retrieval_score,
        citations: answer.citations || [],
        input_tokens: answer.input_tokens,
        output_tokens: answer.output_tokens,
      }])
      setQuestion("")
    } catch (error) {
      setMessages(prev => [...prev, { role: "ai", text: error.message, error: true }])
    } finally {
      setLoading(false)
    }
  }

  // ── what the page looks like, based on the current data ──
  return (
    <div className={isAuthenticated
      ? `app-shell authenticated${sidebarCollapsed ? " sidebar-collapsed" : ""}`
      : "app-shell"}
      data-theme={theme}
      style={isAuthenticated ? { "--sidebar-width": `${sidebarWidth}px` } : undefined}
    >
      {isAuthenticated && (
        <Sidebar
          account={accounts[0]}
          collapsed={sidebarCollapsed}
          currentChatTitle={currentChatTitle}
          loading={loading}
          onNewChat={startNewChat}
          onSignOut={() => instance.logoutRedirect()}
          onToggle={toggleSidebar}
          sidebarWidth={sidebarWidth}
          minSidebarWidth={MIN_SIDEBAR_WIDTH}
          maxSidebarWidth={MAX_SIDEBAR_WIDTH}
          onResize={width => updateSidebarWidth(width)}
          onResizeEnd={width => updateSidebarWidth(width, true)}
        />
      )}

      <main className="app">
        <header className="brand-header">
          <div className="brand-lockup">
            <img className="brand-mark" src="/askanydoc-mark.png" alt="" />
            <h1><span>AskAny</span><span className="brand-doc">Doc</span></h1>
          </div>
          <p className="brand-tagline">Trusted answers from your organization</p>
          <button
            className="theme-toggle"
            type="button"
            onClick={toggleTheme}
            aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
            title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
          >
            <span aria-hidden="true">{theme === "dark" ? "☀" : "☾"}</span>
            <span>{theme === "dark" ? "Light" : "Dark"}</span>
          </button>
        </header>

      {!authConfigured && (
        <div className="auth-notice">Microsoft sign-in configuration is missing.</div>
      )}
      {authConfigured && !isAuthenticated && (
        <div className="auth-notice">
          <p>Sign in with your organisation account to search permission-aware SharePoint sources.</p>
          <button onClick={() => instance.loginRedirect(loginRequest)}>Sign in with Microsoft</button>
        </div>
      )}
      {/* the conversation area: one bubble per message in the list */}
      <div className="chat">
        {/* .map = for EACH message, make one bubble.
            msg = the current message, index = its position (used for key). */}
        {messages.map((msg, index) => (
          // key = a unique label React needs for each item in a mapped list.
          // className picks the style by role: user bubble vs ai bubble (ternary if/else).
          <div key={index} className={`${msg.role === "user" ? "bubble user" : "bubble ai"}${msg.error ? " error" : ""}`}>
            {msg.role === "ai" ? (
              // skipHtml keeps model-written HTML as plain text instead of executing it.
              <div className="message-text"><ReactMarkdown skipHtml>{msg.text}</ReactMarkdown></div>
            ) : (
              <p className="message-text">{msg.text}</p>
            )}
            {sourceBadgeLabel(msg) && (
              <span className="source-badge">{sourceBadgeLabel(msg)}</span>
            )}
            {msg.role === "ai" && !msg.error && (
              <details className="answer-details">
                <summary>Sources &amp; answer details</summary>
                <div className="answer-details-content">
                  {groupedCitations(msg.citations).map(group => (
                    <div className="citation-group" key={group.label}>
                      <strong>{group.label}</strong>
                      <ul>
                        {group.citations.map((citation, citationIndex) => (
                          <li key={`${citation.source_uri}-${citationIndex}`}>
                            {citation.source_uri ? (
                              <a href={citation.source_uri} target="_blank" rel="noreferrer">
                                {citationLabel(citation)}
                              </a>
                            ) : citationLabel(citation)}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                  {msg.citations?.length === 0 && (
                    <p className="detail-note">No document citations were used for this answer.</p>
                  )}
                  {/* Only the AWS vector index currently returns a comparable similarity score. */}
                  {Number.isFinite(msg.retrieval_score) && (
                    <p className="detail-note detail-score">
                      Best AWS semantic match: {msg.retrieval_score}
                    </p>
                  )}
                </div>
              </details>
            )}
            {msg.role === "ai" && !msg.error && (msg.input_tokens > 0 || msg.output_tokens > 0) && (
              <details className="answer-details token-details">
                <summary>Tokens</summary>
                <div className="answer-details-content token-details-content">
                  {msg.input_tokens > 0 && <span>Input: {msg.input_tokens}</span>}
                  {msg.output_tokens > 0 && <span>Output: {msg.output_tokens}</span>}
                </div>
              </details>
            )}
          </div>
        ))}

        {/* show "Thinking..." as a temporary ai-style bubble while waiting */}
        {loading && <div className="bubble ai loading"><p>Working on your answer<span aria-hidden="true">…</span></p></div>}

        {/* empty marker at the very bottom. bottomRef points here so useEffect can scroll to it. */}
        <div ref={bottomRef}></div>
      </div>

      {/* the input row: textarea + Ask button */}
      <div className="input-row">
        <span className="composer-icon" aria-hidden="true">✦</span>
        <textarea
          value={question}                                // data -> box
          onChange={(e) => setQuestion(e.target.value)}   // box -> data
          onKeyDown={(e) => {
            // Enter (without Shift) sends. Shift+Enter makes a new line.
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault()   // stop Enter from adding a new line
              askQuestion()        // send instead
            }
          }}
          placeholder={isAuthenticated ? "Ask a question..." : "Sign in to ask questions"}
          disabled={!isAuthenticated}
          rows="2"
        />
        {/* onClick points to the function (no () -> run on click, not on load).
            disabled while loading so the user can't double-send. */}
        <button
          className="ask-button"
          onClick={askQuestion}
          disabled={loading || !isAuthenticated}
          aria-label="Ask"
          title="Ask"
        >
          <span className="ask-arrow" aria-hidden="true">↑</span>
        </button>
      </div>

      </main>
    </div>
  )
}

export default App   // make this component available to main.jsx
