// Sidebar owns navigation and account presentation only. Persisted chat history,
// folders, and memory can later replace the current-session item without changing
// the main answer surface or authentication boundary.

import { useRef } from 'react'

function accountDisplayName(account) {
  const configuredName = account?.name?.trim()
  if (configuredName) return configuredName
  const username = account?.username || ""
  return username.split("@")[0] || "Account"
}

function accountInitials(displayName) {
  const words = displayName.split(/[\s._-]+/).filter(Boolean)
  return words.slice(0, 2).map(word => word[0]?.toUpperCase()).join("") || "A"
}

function Sidebar({
  account,
  collapsed,
  currentChatTitle,
  loading,
  maxSidebarWidth,
  minSidebarWidth,
  onNewChat,
  onResize,
  onResizeEnd,
  onSignOut,
  onToggle,
  sidebarWidth,
}) {
  const displayName = accountDisplayName(account)
  const initials = accountInitials(displayName)
  const compact = !collapsed && sidebarWidth < 200
  const resizeState = useRef(null)

  function resizedWidth(clientX) {
    const resize = resizeState.current
    if (!resize) return sidebarWidth
    return Math.min(
      maxSidebarWidth,
      Math.max(minSidebarWidth, resize.startWidth + clientX - resize.startX),
    )
  }

  function startResize(event) {
    if (event.button !== 0) return
    event.preventDefault()
    resizeState.current = {
      pointerId: event.pointerId,
      startX: event.clientX,
      startWidth: sidebarWidth,
    }
    event.currentTarget.setPointerCapture(event.pointerId)
  }

  function continueResize(event) {
    if (resizeState.current?.pointerId !== event.pointerId) return
    onResize(resizedWidth(event.clientX))
  }

  function finishResize(event) {
    if (resizeState.current?.pointerId !== event.pointerId) return
    const nextWidth = resizedWidth(event.clientX)
    resizeState.current = null
    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId)
    }
    onResizeEnd(nextWidth)
  }

  function resizeWithKeyboard(event) {
    const step = event.shiftKey ? 32 : 12
    let nextWidth
    if (event.key === "ArrowLeft") nextWidth = sidebarWidth - step
    if (event.key === "ArrowRight") nextWidth = sidebarWidth + step
    if (event.key === "Home") nextWidth = minSidebarWidth
    if (event.key === "End") nextWidth = maxSidebarWidth
    if (nextWidth === undefined) return
    event.preventDefault()
    onResizeEnd(Math.min(maxSidebarWidth, Math.max(minSidebarWidth, nextWidth)))
  }

  return (
    <aside
      className={`sidebar${collapsed ? " collapsed" : ""}${compact ? " compact" : ""}`}
      aria-label="AskAnyDoc navigation"
    >
      <button
        className="sidebar-toggle"
        onClick={onToggle}
        aria-expanded={!collapsed}
        aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
      >
        <span aria-hidden="true">{collapsed ? "›" : "‹"}</span>
      </button>

      <button
        className="new-chat-button"
        onClick={onNewChat}
        disabled={loading}
        title="Start a new browser-session chat"
      >
        <span aria-hidden="true">＋</span>
        <span>New chat</span>
      </button>

      <nav className="sidebar-navigation" aria-label="Chats">
        <h2>Chats</h2>
        {currentChatTitle ? (
          <div className="current-chat" aria-current="page">
            <span>{currentChatTitle}</span>
          </div>
        ) : (
          <p className="sidebar-empty">No current chat</p>
        )}
      </nav>

      <div
        className="account-card"
        aria-label="Signed-in account"
        title={collapsed ? `Signed in as ${displayName}` : undefined}
      >
        <div className="account-avatar" aria-hidden="true">{initials}</div>
        <div className="account-details">
          <strong className="account-name">{displayName}</strong>
          <span className="account-status">Signed in</span>
        </div>
        <button className="account-signout" onClick={onSignOut}>
          <svg
            className="account-signout-icon"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path d="M10 5H6.8A1.8 1.8 0 0 0 5 6.8v10.4A1.8 1.8 0 0 0 6.8 19H10M14.5 8l4 4-4 4M9 12h9" />
          </svg>
          <span>Sign out</span>
        </button>
      </div>

      {!collapsed && (
        <div
          className="sidebar-resize-handle"
          role="separator"
          aria-label="Resize chat sidebar"
          aria-orientation="vertical"
          aria-valuemin={minSidebarWidth}
          aria-valuemax={maxSidebarWidth}
          aria-valuenow={Math.round(sidebarWidth)}
          tabIndex={0}
          title="Drag to resize the sidebar"
          onKeyDown={resizeWithKeyboard}
          onPointerDown={startResize}
          onPointerMove={continueResize}
          onPointerUp={finishResize}
          onPointerCancel={finishResize}
        />
      )}
    </aside>
  )
}

export default Sidebar
