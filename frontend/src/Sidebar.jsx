// Sidebar owns navigation and account presentation only. Persisted chat history,
// folders, and memory can later replace the current-session item without changing
// the main answer surface or authentication boundary.

import { useRef, useState } from 'react'

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
  view,
  currentChatTitle,
  loading,
  maxSidebarWidth,
  minSidebarWidth,
  onNewChat,
  onResize,
  onResizeEnd,
  onSignOut,
  onConnectSalesforce,
  onDisconnectSalesforce,
  salesforceAvailable,
  salesforceConnected,
  salesforceOrg,
  salesforceBusy,
  salesforceNotice,
  salesforceAuthorizeUrl,
  sidebarWidth,
}) {
  const displayName = accountDisplayName(account)
  const initials = accountInitials(displayName)
  const compact = sidebarWidth < 220
  const narrow = sidebarWidth < 180
  const resizeState = useRef(null)
  const [connectionDetailsOpen, setConnectionDetailsOpen] = useState(false)
  const [pendingConnectionAction, setPendingConnectionAction] = useState(null)

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
      className={`sidebar ${view}-panel${compact ? " compact" : ""}${narrow ? " narrow" : ""}`}
      aria-label={view === 'connections' ? 'Connections panel' : 'Chats panel'}
    >
      {view === 'chats' ? <>
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
      </> : <>
        <header className="connections-header">
          <h2>Connections</h2>
          <p>Choose which services AskAnyDoc can read with your permission.</p>
        </header>
      {salesforceAvailable && (
        <div className="sidebar-connections" aria-label="Connections">
          <button
            className="sidebar-connection-button"
            type="button"
            onClick={() => setConnectionDetailsOpen(value => !value)}
            aria-expanded={connectionDetailsOpen}
            title="Salesforce connection settings"
          >
            <span className="connection-symbol" aria-hidden="true">S</span>
            <span>Salesforce <small>{salesforceConnected ? "Connected" : "Not connected"}</small></span>
            <span className={`connection-dot${salesforceConnected ? " connected" : ""}`} aria-hidden="true" />
          </button>
          {connectionDetailsOpen && (
            <div className="connection-details">
              <p><strong>Status</strong> {salesforceConnected ? "Connected" : "Not connected"}</p>
              {salesforceOrg && <p><strong>Org</strong> {salesforceOrg}</p>}
              <p><strong>Access</strong> CRM records · Read only</p>
              <p>Your Salesforce account is authorized separately from Microsoft sign-in.</p>
              {salesforceConnected && !pendingConnectionAction && <div className="connection-actions">
                <button type="button" disabled={salesforceBusy} onClick={() => setPendingConnectionAction('switch')}>Change account</button>
                <button type="button" disabled={salesforceBusy} onClick={() => setPendingConnectionAction('disconnect')}>Disconnect</button>
              </div>}
              {salesforceConnected && pendingConnectionAction && <div className="connection-confirm">
                <p>{pendingConnectionAction === 'switch'
                  ? 'Revoke this account’s access, then sign in to Salesforce again with the account you choose?'
                  : 'Revoke this account’s Salesforce access to AskAnyDoc?'}</p>
                <div className="connection-actions">
                  <button type="button" disabled={salesforceBusy} onClick={() => { onDisconnectSalesforce(pendingConnectionAction === 'switch'); setPendingConnectionAction(null) }}>{pendingConnectionAction === 'switch' ? 'Revoke and change' : 'Disconnect now'}</button>
                  <button type="button" disabled={salesforceBusy} onClick={() => setPendingConnectionAction(null)}>Cancel</button>
                </div>
              </div>}
              {!salesforceConnected && <button type="button" disabled={salesforceBusy} onClick={() => onConnectSalesforce(false)}>Connect Salesforce</button>}
              {!salesforceConnected && salesforceAuthorizeUrl && <a className="connection-continue" href={salesforceAuthorizeUrl}>Continue to Salesforce</a>}
            </div>
          )}
          {salesforceNotice && <p className="connection-notice" role="status">{salesforceNotice}</p>}
        </div>
      )}
      </>}

      <div
        className="account-card"
        aria-label="Signed-in account"
        title={`Signed in as ${displayName}`}
      >
        <div className="account-avatar" aria-hidden="true">{initials}</div>
        <div className="account-details">
          <strong className="account-name">{displayName}</strong>
          <span className="account-status">Signed in</span>
        </div>
        <button className="account-signout" onClick={onSignOut} aria-label="Sign out" title="Sign out">
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

      <div
          className="sidebar-resize-handle"
          role="separator"
          aria-label="Resize sidebar"
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
    </aside>
  )
}

export default Sidebar
