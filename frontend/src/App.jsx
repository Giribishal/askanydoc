// App.jsx — AskAnyDoc chatbot page (conversation version).
// Flow: user types -> clicks Ask -> question added to the list right away ->
// we POST it to the Lambda -> answer comes back -> answer added to the list ->
// React shows the whole conversation as bubbles, and auto-scrolls to the newest.

import { useState, useRef, useEffect } from 'react'   // state + a page pointer + an after-update hook
import ReactMarkdown from 'react-markdown'             // safely turn Claude's Markdown into readable HTML
import { useIsAuthenticated, useMsal } from '@azure/msal-react'
import { InteractionRequiredAuthError } from '@azure/msal-browser'
import { apiUrl, authConfigured, loginRequest } from './authConfig.js'
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

function App() {

  const { instance, accounts } = useMsal()
  const isAuthenticated = useIsAuthenticated()

  // ── the data this page remembers ──
  const [question, setQuestion] = useState("")   // what the user is currently typing
  const [messages, setMessages] = useState([])   // the WHOLE conversation (a list)
  const [loading, setLoading] = useState(false)  // true while we wait for the Lambda

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
      const response = await fetch(apiUrl, {
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
      const responseText = await response.text()
      let data = {}
      try {
        data = responseText ? JSON.parse(responseText) : {}
      } catch {
        data = { error: responseText }
      }
      if (!response.ok) {
        console.error(`AskAnyDoc request rejected ${JSON.stringify({
          status: response.status,
          token: tokenDiagnostics(tokenResponse.accessToken),
        })}`)
        throw new Error(data.error || data.message || `AskAnyDoc request failed (${response.status}).`)
      }

      setMessages(prev => [...prev, {
        role: "ai",
        text: data.answer,
        source_mode: data.source_mode,
        retrieval_score: data.retrieval_score,
        citations: data.citations || [],
        input_tokens: data.input_tokens,
        output_tokens: data.output_tokens,
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
    <div className="app">
      <h1>AskAnyDoc</h1>

      {!authConfigured && (
        <div className="auth-notice">Microsoft sign-in configuration is missing.</div>
      )}
      {authConfigured && !isAuthenticated && (
        <div className="auth-notice">
          <p>Sign in with your organisation account to search permission-aware SharePoint sources.</p>
          <button onClick={() => instance.loginRedirect(loginRequest)}>Sign in with Microsoft</button>
        </div>
      )}
      {isAuthenticated && (
        <div className="auth-row">
          <span>Signed in as {accounts[0]?.username}</span>
          <button onClick={() => instance.logoutRedirect()}>Sign out</button>
        </div>
      )}

      {/* the conversation area: one bubble per message in the list */}
      <div className="chat">
        {/* .map = for EACH message, make one bubble.
            msg = the current message, index = its position (used for key). */}
        {messages.map((msg, index) => (
          // key = a unique label React needs for each item in a mapped list.
          // className picks the style by role: user bubble vs ai bubble (ternary if/else).
          <div key={index} className={msg.role === "user" ? "bubble user" : "bubble ai"}>
            {msg.role === "ai" ? (
              // skipHtml keeps model-written HTML as plain text instead of executing it.
              <div className="message-text"><ReactMarkdown skipHtml>{msg.text}</ReactMarkdown></div>
            ) : (
              <p className="message-text">{msg.text}</p>
            )}
            {msg.source_mode === "organisation_sources" && (
              <span className="confidence">Organisation sources</span>
            )}
            {msg.source_mode === "general_knowledge" && (
              <span className="confidence">General knowledge</span>
            )}
            {msg.source_mode === "organisation_not_found" && (
              <span className="confidence">Organisation sources: no match</span>
            )}
            {/* Retrieval relevance comes from vector search, not model self-confidence. */}
            {msg.source_mode === "organisation_sources" && (
              <span className="confidence">Top source match: {msg.retrieval_score}</span>
            )}
            {msg.input_tokens > 0 && (
              <span className="confidence">Input tokens: {msg.input_tokens}</span>
            )}
            {msg.output_tokens > 0 && (
              <span className="confidence">Output tokens: {msg.output_tokens}</span>
            )}
            {msg.citations?.length > 0 && (
              <div className="citations">
                <strong>Sources</strong>
                <ul>
                  {msg.citations.map((citation, citationIndex) => (
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
            )}
          </div>
        ))}

        {/* show "Thinking..." as a temporary ai-style bubble while waiting */}
        {loading && <div className="bubble ai"><p>Thinking...</p></div>}

        {/* empty marker at the very bottom. bottomRef points here so useEffect can scroll to it. */}
        <div ref={bottomRef}></div>
      </div>

      {/* the input row: textarea + Ask button */}
      <div className="input-row">
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
        <button onClick={askQuestion} disabled={loading || !isAuthenticated}>
          Ask
        </button>
      </div>
    </div>
  )
}

export default App   // make this component available to main.jsx
