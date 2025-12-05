/**
 * GraphQL queries and subscriptions for vaspNestAgent dashboard.
 * 
 * Requirements: 15.2, 17.2
 */

import { gql } from '@apollo/client'

// =============================================================================
// Subscriptions
// =============================================================================

/**
 * Subscribe to real-time temperature updates.
 * Updates every 2 seconds with latest temperature reading.
 */
export const TEMPERATURE_SUBSCRIPTION = gql`
  subscription TemperatureUpdates {
    temperatureUpdates {
      ambientTemperature
      targetTemperature
      thermostatId
      timestamp
      humidity
      hvacMode
      differential
    }
  }
`

/**
 * Subscribe to real-time adjustment events.
 * Fires when a temperature adjustment is made.
 */
export const ADJUSTMENT_SUBSCRIPTION = gql`
  subscription AdjustmentEvents {
    adjustmentEvents {
      id
      previousSetting
      newSetting
      ambientTemperature
      triggerReason
      timestamp
      notificationSent
    }
  }
`

// =============================================================================
// Queries
// =============================================================================

/**
 * Get current temperature reading.
 */
export const CURRENT_TEMPERATURE = gql`
  query CurrentTemperature {
    currentTemperature {
      ambientTemperature
      targetTemperature
      thermostatId
      timestamp
      humidity
      hvacMode
      differential
    }
  }
`

/**
 * Get temperature history for charting.
 */
export const TEMPERATURE_HISTORY = gql`
  query TemperatureHistory($hours: Int) {
    temperatureHistory(hours: $hours) {
      ambientTemperature
      targetTemperature
      thermostatId
      timestamp
      humidity
      hvacMode
      differential
    }
  }
`

/**
 * Get adjustment history.
 */
export const ADJUSTMENT_HISTORY = gql`
  query AdjustmentHistory($limit: Int) {
    adjustmentHistory(limit: $limit) {
      id
      previousSetting
      newSetting
      ambientTemperature
      triggerReason
      timestamp
      notificationSent
    }
  }
`

/**
 * Get temperature timeline with readings and adjustments.
 */
export const TEMPERATURE_TIMELINE = gql`
  query TemperatureTimeline($hours: Int) {
    temperatureTimeline(hours: $hours) {
      readings {
        ambientTemperature
        targetTemperature
        timestamp
        differential
      }
      adjustments {
        id
        previousSetting
        newSetting
        ambientTemperature
        timestamp
      }
      startTime
      endTime
    }
  }
`

/**
 * Get health status.
 */
export const HEALTH_STATUS = gql`
  query HealthStatus {
    healthStatus {
      status
      running
      uptimeSeconds
      errorCount
      consecutiveErrors
      adjustmentCount
      notificationCount
      inCooldown
      cooldownRemaining
    }
  }
`

// =============================================================================
// TypeScript Types
// =============================================================================

export interface TemperatureReading {
  ambientTemperature: number
  targetTemperature: number
  thermostatId: string
  timestamp: string
  humidity?: number
  hvacMode?: string
  differential: number
}

export interface AdjustmentEvent {
  id: string
  previousSetting: number
  newSetting: number
  ambientTemperature: number
  triggerReason: string
  timestamp: string
  notificationSent: boolean
}

export interface TemperatureTimeline {
  readings: TemperatureReading[]
  adjustments: AdjustmentEvent[]
  startTime: string
  endTime: string
}

export interface HealthStatus {
  status: string
  running: boolean
  uptimeSeconds: number
  errorCount: number
  consecutiveErrors: number
  adjustmentCount: number
  notificationCount: number
  inCooldown: boolean
  cooldownRemaining: number
}
