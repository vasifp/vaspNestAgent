"""GraphQL Schema for vaspNestAgent.

Defines the GraphQL types, queries, and subscriptions for the temperature
monitoring dashboard.
"""

# GraphQL Schema Definition
TYPE_DEFS = """
    type Query {
        currentTemperature: TemperatureReading
        temperatureHistory(hours: Int = 24): [TemperatureReading!]!
        adjustmentHistory(limit: Int = 10): [AdjustmentEvent!]!
        temperatureTimeline(hours: Int = 24): TemperatureTimeline!
        healthStatus: HealthStatus!
    }
    
    type Subscription {
        temperatureUpdates: TemperatureReading!
        adjustmentEvents: AdjustmentEvent!
    }
    
    type TemperatureReading {
        ambientTemperature: Float!
        targetTemperature: Float!
        thermostatId: String!
        timestamp: String!
        humidity: Float
        hvacMode: String
        differential: Float!
    }
    
    type AdjustmentEvent {
        id: ID!
        previousSetting: Float!
        newSetting: Float!
        ambientTemperature: Float!
        triggerReason: String!
        timestamp: String!
        notificationSent: Boolean!
    }
    
    type TemperatureTimeline {
        readings: [TemperatureReading!]!
        adjustments: [AdjustmentEvent!]!
        startTime: String!
        endTime: String!
    }
    
    type HealthStatus {
        status: String!
        running: Boolean!
        uptimeSeconds: Float!
        errorCount: Int!
        consecutiveErrors: Int!
        adjustmentCount: Int!
        notificationCount: Int!
        inCooldown: Boolean!
        cooldownRemaining: Int!
    }
"""


def get_type_defs() -> str:
    """Get the GraphQL type definitions.
    
    Returns:
        GraphQL SDL string.
    """
    return TYPE_DEFS
