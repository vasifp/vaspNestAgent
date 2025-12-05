/**
 * Adjustment history component displaying recent temperature adjustments.
 * 
 * Requirements: 15.4
 */

import React from 'react'
import type { AdjustmentEvent } from '../graphql/queries'

interface AdjustmentHistoryProps {
  adjustments: AdjustmentEvent[]
  loading?: boolean
  highlightLatest?: boolean
}

/**
 * Formats a timestamp for display.
 */
const formatTimestamp = (timestamp: string): string => {
  const date = new Date(timestamp)
  return date.toLocaleString([], {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/**
 * Displays a table of recent temperature adjustments.
 */
export const AdjustmentHistory: React.FC<AdjustmentHistoryProps> = ({
  adjustments,
  loading = false,
  highlightLatest = true,
}) => {
  if (loading) {
    return (
      <div className="adjustment-history loading">
        <div className="loading-spinner" />
        <span>Loading adjustment history...</span>
      </div>
    )
  }

  if (adjustments.length === 0) {
    return (
      <div className="adjustment-history no-data">
        <p>No temperature adjustments recorded</p>
      </div>
    )
  }

  return (
    <div className="adjustment-history">
      <h3>Recent Adjustments</h3>
      <table>
        <thead>
          <tr>
            <th>Time</th>
            <th>Previous</th>
            <th>New</th>
            <th>Ambient</th>
            <th>Reason</th>
            <th>Notified</th>
          </tr>
        </thead>
        <tbody>
          {adjustments.map((adjustment, index) => (
            <tr 
              key={adjustment.id}
              className={highlightLatest && index === 0 ? 'latest' : ''}
            >
              <td className="timestamp">{formatTimestamp(adjustment.timestamp)}</td>
              <td className="temperature">{adjustment.previousSetting.toFixed(1)}°F</td>
              <td className="temperature">{adjustment.newSetting.toFixed(1)}°F</td>
              <td className="temperature">{adjustment.ambientTemperature.toFixed(1)}°F</td>
              <td className="reason">{adjustment.triggerReason}</td>
              <td className="notification">
                {adjustment.notificationSent ? (
                  <span className="sent" title="Notification sent">✓</span>
                ) : (
                  <span className="not-sent" title="No notification">—</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default AdjustmentHistory
