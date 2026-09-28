// Sidebar owns navigation and account presentation only. Persisted chat history,
// folders, and memory can later replace the current-session item without changing
// the main answer surface or authentication boundary.

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

function Sidebar({ account, collapsed, currentChatTitle, loading, onNewChat, onSignOut, onToggle }) {
  const displayName = accountDisplayName(account)
  const initials = accountInitials(displayName)

  return (
    <aside
      className={collapsed ? "sidebar collapsed" : "sidebar"}
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
      </div>
    </aside>
  )
}

export default Sidebar
