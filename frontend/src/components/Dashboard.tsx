/**
 * Main dashboard component composing all temperature monitoring components.
 * 
 * Requirements: 15.5
 */

import React, { useState, useEffect } from 'react'
import { useQuery, useSubscription } from '@apollo/client'
import {
  CURRENT_TEMPERATURE,
  TEMPERATURE_TIMELINE,
  ADJUSTMENT_HISTORY,
  TEMPERATURE_SUBSCRIPTION,
  ADJUSTMENT_SUBSCRIPTION,
  type TemperatureReading,
  type AdjustmentEvent,
} from '../graphql/queries'
import { TemperatureDisplay } from './TemperatureDisplay'
import { TemperatureChart } from './TemperatureChart'
import { AdjustmentHistory } from './AdjustmentHistory'
import { ConnectionStatus, type ConnectionState } from './ConnectionStatus'

interface DashboardProps {
  hours?: number
  adjustmentLimit?: number
}

/**
 * Main dashboard displaying temperature monitoring data.
 */
export const Dashboard: React.FC<DashboardProps> = ({
  hours = 24,
  adjustmentLimit = 10,
}) => {
  const [connectionStatus, setConnectionStatus] = useState<ConnectionState>('connecting')
  const [currentTemp, setCurrentTemp] = useState<TemperatureReading | null>(null)
  const [lastUpdate, setLastUpdate] = useState<string | undefined>()
  const [errorMessage, setErrorMessage] = useState<string | undefined>()

  // Query for initial data
  const { 
    data: timelineData, 
    loading: timelineLoading,
    error: timelineError,
    refetch: refetchTimeline,
  } = useQuery(TEMPERATURE_TIMELINE, {
    variables: { hours },
    pollInterval: 60000, // Refresh every minute
  })

  const {
    data: adjustmentData,
    loading: adjustmentLoading,
    refetch: refetchAdjustments,
  } = useQuery(ADJUSTMENT_HISTORY, {
    variables: { limit: adjustmentLimit },
    pollInterval: 30000, // Refresh every 30 seconds
  })

  // Subscribe to real-time temperature updates
  const { data: tempSubData, error: tempSubError } = useSubscription(
    TEMPERATURE_SUBSCRIPTION,
    {
      onData: ({ data }) => {
        if (data?.data?.temperatureUpdates) {
          setCurrentTemp(data.data.temperatureUpdates)
          setLastUpdate(new Date().toISOString())
          setConnectionStatus('connected')
          setErrorMessage(undefined)
        }
      },
      onError: (error) => {
        console.error('Temperature subscription error:', error)
        setConnectionStatus('error')
        setErrorMessage(error.message)
      },
    }
  )

  // Subscribe to adjustment events
  const { data: adjSubData } = useSubscription(
    ADJUSTMENT_SUBSCRIPTION,
    {
      onData: () => {
        // Refetch adjustment history when new adjustment occurs
        refetchAdjustments()
        refetchTimeline()
      },
    }
  )

  // Update connection status based on subscription state
  useEffect(() => {
    if (tempSubError) {
      setConnectionStatus('error')
      setErrorMessage(tempSubError.message)
    } else if (tempSubData?.temperatureUpdates) {
      setConnectionStatus('connected')
    }
  }, [tempSubData, tempSubError])

  // Handle query errors
  useEffect(() => {
    if (timelineError) {
      setConnectionStatus('error')
      setErrorMessage(timelineError.message)
    }
  }, [timelineError])

  // Get readings and adjustments from timeline data
  const readings = timelineData?.temperatureTimeline?.readings || []
  const timelineAdjustments = timelineData?.temperatureTimeline?.adjustments || []
  const adjustments = adjustmentData?.adjustmentHistory || []

  // Use subscription data for current temp, or fall back to latest reading
  const displayTemp = currentTemp || (readings.length > 0 ? readings[readings.length - 1] : null)

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>vaspNestAgent Dashboard</h1>
        <ConnectionStatus 
          status={connectionStatus}
          lastUpdate={lastUpdate}
          errorMessage={errorMessage}
        />
      </header>

      <main className="dashboard-content">
        <section className="current-temperature">
          <TemperatureDisplay
            ambient={displayTemp?.ambientTemperature}
            target={displayTemp?.targetTemperature}
            humidity={displayTemp?.humidity}
            hvacMode={displayTemp?.hvacMode}
            timestamp={displayTemp?.timestamp}
            loading={timelineLoading && !displayTemp}
          />
        </section>

        <section className="temperature-chart-section">
          <TemperatureChart
            readings={readings}
            adjustments={timelineAdjustments}
            hours={hours}
          />
        </section>

        <section className="adjustment-history-section">
          <AdjustmentHistory
            adjustments={adjustments}
            loading={adjustmentLoading}
            highlightLatest={true}
          />
        </section>
      </main>

      <footer className="dashboard-footer">
        <p>vaspNestAgent - Temperature Monitoring System</p>
      </footer>
    </div>
  )
}

export default Dashboard
