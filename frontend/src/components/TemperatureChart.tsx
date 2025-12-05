/**
 * Temperature chart component with adjustment markers.
 * 
 * Plots ambient and target temperature lines using Recharts.
 * Adds vertical reference lines for adjustment events.
 * 
 * Requirements: 15.3, 15.4
 */

import React, { useMemo } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'
import type { TemperatureReading, AdjustmentEvent } from '../graphql/queries'

interface TemperatureChartProps {
  readings: TemperatureReading[]
  adjustments: AdjustmentEvent[]
  hours?: number
}

interface ChartDataPoint {
  time: string
  timestamp: number
  ambient: number
  target: number
  differential: number
}

/**
 * Custom tooltip for the temperature chart.
 */
const CustomTooltip: React.FC<{
  active?: boolean
  payload?: Array<{ value: number; name: string; color: string }>
  label?: string
}> = ({ active, payload, label }) => {
  if (!active || !payload || !payload.length) return null

  return (
    <div className="chart-tooltip">
      <p className="time">{label}</p>
      {payload.map((entry, index) => (
        <p key={index} style={{ color: entry.color }}>
          {entry.name}: {entry.value.toFixed(1)}°F
        </p>
      ))}
    </div>
  )
}

/**
 * Temperature chart with ambient/target lines and adjustment markers.
 */
export const TemperatureChart: React.FC<TemperatureChartProps> = ({
  readings,
  adjustments,
  hours = 24,
}) => {
  // Transform readings to chart data
  const chartData = useMemo<ChartDataPoint[]>(() => {
    return readings.map((reading) => {
      const date = new Date(reading.timestamp)
      return {
        time: date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        timestamp: date.getTime(),
        ambient: reading.ambientTemperature,
        target: reading.targetTemperature,
        differential: reading.differential,
      }
    })
  }, [readings])

  // Get adjustment timestamps for reference lines
  const adjustmentTimestamps = useMemo(() => {
    return adjustments.map((adj) => ({
      timestamp: new Date(adj.timestamp).getTime(),
      label: `${adj.previousSetting}→${adj.newSetting}°F`,
      time: new Date(adj.timestamp).toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit' 
      }),
    }))
  }, [adjustments])

  // Calculate Y-axis domain
  const yDomain = useMemo(() => {
    if (chartData.length === 0) return [60, 80]
    
    const allTemps = chartData.flatMap((d) => [d.ambient, d.target])
    const min = Math.floor(Math.min(...allTemps) - 5)
    const max = Math.ceil(Math.max(...allTemps) + 5)
    return [min, max]
  }, [chartData])

  if (chartData.length === 0) {
    return (
      <div className="temperature-chart no-data">
        <p>No temperature data available for the last {hours} hours</p>
      </div>
    )
  }

  return (
    <div className="temperature-chart">
      <h3>Temperature History ({hours}h)</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis 
            dataKey="time" 
            stroke="#9CA3AF"
            tick={{ fill: '#9CA3AF' }}
          />
          <YAxis 
            domain={yDomain}
            stroke="#9CA3AF"
            tick={{ fill: '#9CA3AF' }}
            tickFormatter={(value) => `${value}°F`}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          
          {/* Adjustment reference lines */}
          {adjustmentTimestamps.map((adj, index) => (
            <ReferenceLine
              key={index}
              x={chartData.find(d => d.timestamp >= adj.timestamp)?.time}
              stroke="#EF4444"
              strokeDasharray="5 5"
              label={{
                value: '⚡',
                position: 'top',
                fill: '#EF4444',
              }}
            />
          ))}
          
          <Line
            type="monotone"
            dataKey="ambient"
            name="Ambient"
            stroke="#3B82F6"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
          <Line
            type="monotone"
            dataKey="target"
            name="Target"
            stroke="#10B981"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
      
      {adjustments.length > 0 && (
        <div className="adjustment-legend">
          <span className="marker">⚡</span> = Temperature adjustment
        </div>
      )}
    </div>
  )
}

export default TemperatureChart
