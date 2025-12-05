/**
 * Temperature display component showing current ambient and target temperatures.
 * 
 * Requirements: 15.1
 */

import React from 'react'

interface TemperatureDisplayProps {
  ambient?: number
  target?: number
  humidity?: number
  hvacMode?: string
  timestamp?: string
  loading?: boolean
}

/**
 * Displays current temperature readings with differential indicator.
 */
export const TemperatureDisplay: React.FC<TemperatureDisplayProps> = ({
  ambient,
  target,
  humidity,
  hvacMode,
  timestamp,
  loading = false,
}) => {
  if (loading) {
    return (
      <div className="temperature-display loading">
        <div className="loading-spinner" />
        <span>Loading temperature data...</span>
      </div>
    )
  }

  if (ambient === undefined || target === undefined) {
    return (
      <div className="temperature-display no-data">
        <span>No temperature data available</span>
      </div>
    )
  }

  const differential = target - ambient
  const differentialClass = 
    differential < 5 ? 'warning' : 
    differential < 0 ? 'danger' : 
    'normal'

  const formatTime = (ts?: string) => {
    if (!ts) return ''
    const date = new Date(ts)
    return date.toLocaleTimeString()
  }

  return (
    <div className="temperature-display">
      <div className="temperature-card ambient">
        <div className="label">Ambient</div>
        <div className="value">{ambient.toFixed(1)}°F</div>
        {humidity !== undefined && (
          <div className="humidity">{humidity.toFixed(0)}% humidity</div>
        )}
      </div>

      <div className="temperature-card target">
        <div className="label">Target</div>
        <div className="value">{target.toFixed(1)}°F</div>
        {hvacMode && (
          <div className="hvac-mode">{hvacMode.toUpperCase()}</div>
        )}
      </div>

      <div className={`temperature-card differential ${differentialClass}`}>
        <div className="label">Differential</div>
        <div className="value">{differential.toFixed(1)}°F</div>
        <div className="status">
          {differential < 5 ? 'Adjustment may occur' : 'Normal range'}
        </div>
      </div>

      {timestamp && (
        <div className="timestamp">
          Last updated: {formatTime(timestamp)}
        </div>
      )}
    </div>
  )
}

export default TemperatureDisplay
