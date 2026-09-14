// App.jsx — AskAnyDoc chatbot page (conversation version).
// Flow: user types -> clicks Ask -> question added to the list right away ->
// we POST it to the Lambda -> answer comes back -> answer added to the list ->
// React shows the whole conversation as bubbles, and auto-scrolls to the newest.

import { useState, useRef, useEffect } from 'react'   // state + a page pointer + an after-update hook
import './App.css'                                     // the styling for this page

function App() {

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
    if (!question) return   // do nothing if the box is empty

    setLoading(true)   // we are now waiting

    // add the user's question to the list RIGHT AWAY (so it shows while AI thinks).
    // [...prev, newItem] = keep all old messages, add the new one at the end.
    setMessages(prev => [...prev, { role: "user", text: question }])

    try {
      const response = await fetch("https://v7vhq6uuwh4jvrv3qash7faamy0ngslw.lambda-url.ap-southeast-2.on.aws/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: question }),
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.error || "AskAnyDoc could not answer.")

      setMessages(prev => [...prev, {
        role: "ai",
        text: data.answer,
        confidence: data.confidence,
        grounded: data.grounded,
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

      {/* the conversation area: one bubble per message in the list */}
      <div className="chat">
        {/* .map = for EACH message, make one bubble.
            msg = the current message, index = its position (used for key). */}
        {messages.map((msg, index) => (
          // key = a unique label React needs for each item in a mapped list.
          // className picks the style by role: user bubble vs ai bubble (ternary if/else).
          <div key={index} className={msg.role === "user" ? "bubble user" : "bubble ai"}>
            <p>{msg.text}</p>
            {/* show confidence ONLY for ai messages (user messages have none) */}
            {msg.confidence && <span className="confidence">Confidence: {msg.confidence}</span>}
            {msg.input_tokens && <span className="confidence">Input tokens: {msg.input_tokens}</span>}
            {msg.output_tokens && <span className="confidence">Output tokens: {msg.output_tokens}</span>}
            {msg.citations?.length > 0 && (
              <div className="citations">
                <strong>Sources</strong>
                <ul>
                  {msg.citations.map((citation, citationIndex) => (
                    <li key={`${citation.source_uri}-${citationIndex}`}>{citationLabel(citation)}</li>
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
          placeholder="Ask a question..."
          rows="2"
        />
        {/* onClick points to the function (no () -> run on click, not on load).
            disabled while loading so the user can't double-send. */}
        <button onClick={askQuestion} disabled={loading}>
          Ask
        </button>
      </div>
    </div>
  )
}

export default App   // make this component available to main.jsx
