/**
 * Connection status indicator component.
 * 
 * Shows the current connection status to the backend.
 * Requirements: 15.5
 */

import React from 'react'

export type ConnectionState = 'connected' | 'connecting' | 'disconnected' | 'error'

interface ConnectionStatusProps {
  status: ConnectionState
  lastUpdate?: string
  errorMessage?: string
}

/**
 * Displays connection status indicator.
 */
export const ConnectionStatus: React.FC<ConnectionStatusProps> = ({
  status,
  lastUpdate,
  errorMessage,
}) => {
  const getStatusInfo = () => {
    switch (status) {
      case 'connected':
        return {
          icon: '●',
          label: 'Connected',
          className: 'connected',
        }
      case 'connecting':
        return {
          icon: '◐',
          label: 'Connecting...',
          className: 'connecting',
        }
      case 'disconnected':
        return {
          icon: '○',
          label: 'Disconnected',
          className: 'disconnected',
        }
      case 'error':
        return {
          icon: '✕',
          label: 'Error',
          className: 'error',
        }
    }
  }

  const statusInfo = getStatusInfo()

  const formatLastUpdate = (timestamp?: string) => {
    if (!timestamp) return null
    const date = new Date(timestamp)
    const now = new Date()
    const diffSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)
    
    if (diffSeconds < 60) return `${diffSeconds}s ago`
    if (diffSeconds < 3600) return `${Math.floor(diffSeconds / 60)}m ago`
    return date.toLocaleTimeString()
  }

  return (
    <div className={`connection-status ${statusInfo.className}`}>
      <span className="status-icon">{statusInfo.icon}</span>
      <span className="status-label">{statusInfo.label}</span>
      
      {lastUpdate && status === 'connected' && (
        <span className="last-update">
          Last update: {formatLastUpdate(lastUpdate)}
        </span>
      )}
      
      {errorMessage && status === 'error' && (
        <span className="error-message" title={errorMessage}>
          {errorMessage.length > 50 
            ? `${errorMessage.substring(0, 50)}...` 
            : errorMessage}
        </span>
      )}
    </div>
  )
}

export default ConnectionStatus
