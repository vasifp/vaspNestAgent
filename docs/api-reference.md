# API Reference

vaspNestAgent exposes a GraphQL API for querying temperature data and subscribing to real-time updates.

## Endpoints

| Endpoint | Protocol | Description |
|----------|----------|-------------|
| `/graphql` | HTTP POST | GraphQL queries and mutations |
| `/graphql` | WebSocket | GraphQL subscriptions |
| `/health` | HTTP GET | Health check |
| `/ready` | HTTP GET | Readiness check |
| `/metrics` | HTTP GET | Prometheus metrics |

## GraphQL Schema

### Types

#### TemperatureReading

Current temperature data from the thermostat.

```graphql
type TemperatureReading {
  ambientTemperature: Float!
  targetTemperature: Float!
  thermostatId: String!
  timestamp: String!
  humidity: Float
  hvacMode: String
  differential: Float!
}
```

| Field | Type | Description |
|-------|------|-------------|
| `ambientTemperature` | Float! | Current room temperature (°F) |
| `targetTemperature` | Float! | Target temperature setting (°F) |
| `thermostatId` | String! | Nest thermostat device ID |
| `timestamp` | String! | ISO 8601 timestamp |
| `humidity` | Float | Relative humidity (%) |
| `hvacMode` | String | HVAC mode (HEAT, COOL, OFF, AUTO) |
| `differential` | Float! | Target - Ambient temperature |

#### AdjustmentEvent

Record of a temperature adjustment.

```graphql
type AdjustmentEvent {
  id: String!
  previousSetting: Float!
  newSetting: Float!
  ambientTemperature: Float!
  triggerReason: String!
  timestamp: String!
  notificationSent: Boolean!
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | String! | Unique adjustment ID |
| `previousSetting` | Float! | Previous target temperature (°F) |
| `newSetting` | Float! | New target temperature (°F) |
| `ambientTemperature` | Float! | Ambient temp at adjustment time (°F) |
| `triggerReason` | String! | Reason for adjustment |
| `timestamp` | String! | ISO 8601 timestamp |
| `notificationSent` | Boolean! | Whether SMS was sent |

#### TemperatureTimeline

Time-series temperature data point.

```graphql
type TemperatureTimeline {
  timestamp: String!
  ambientTemperature: Float!
  targetTemperature: Float!
  adjustment: AdjustmentEvent
}
```

### Queries

#### currentTemperature

Get the latest temperature reading.

```graphql
query {
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
```

**Response:**
```json
{
  "data": {
    "currentTemperature": {
      "ambientTemperature": 72.5,
      "targetTemperature": 75.0,
      "thermostatId": "enterprises/project-id/devices/device-id",
      "timestamp": "2024-01-15T14:30:00Z",
      "humidity": 45.0,
      "hvacMode": "HEAT",
      "differential": 2.5
    }
  }
}
```

#### temperatureHistory

Get historical temperature readings.

```graphql
query TemperatureHistory($hours: Int) {
  temperatureHistory(hours: $hours) {
    ambientTemperature
    targetTemperature
    timestamp
  }
}
```

**Variables:**
```json
{
  "hours": 24
}
```

#### adjustmentHistory

Get recent temperature adjustments.

```graphql
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
```

**Variables:**
```json
{
  "limit": 10
}
```

#### temperatureTimeline

Get temperature timeline with adjustment markers.

```graphql
query TemperatureTimeline($hours: Int) {
  temperatureTimeline(hours: $hours) {
    timestamp
    ambientTemperature
    targetTemperature
    adjustment {
      id
      previousSetting
      newSetting
      triggerReason
    }
  }
}
```

### Subscriptions

#### temperatureUpdates

Subscribe to real-time temperature updates.

```graphql
subscription {
  temperatureUpdates {
    ambientTemperature
    targetTemperature
    timestamp
    differential
  }
}
```

**WebSocket Connection:**
```javascript
const wsLink = new GraphQLWsLink(createClient({
  url: 'ws://localhost:8080/graphql',
}));
```

#### adjustmentEvents

Subscribe to temperature adjustment events.

```graphql
subscription {
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
```

## Health Endpoints

### GET /health

Returns system health status.

**Response (200 OK - Healthy):**
```json
{
  "status": "healthy",
  "running": true,
  "uptime_seconds": 3600.5,
  "error_count": 0,
  "consecutive_errors": 0,
  "last_error": null,
  "adjustment_count": 5,
  "notification_count": 3,
  "in_cooldown": false
}
```

**Response (503 Service Unavailable - Degraded):**
```json
{
  "status": "degraded",
  "running": true,
  "uptime_seconds": 3600.5,
  "error_count": 15,
  "consecutive_errors": 12,
  "last_error": "Failed to connect to Nest API",
  "adjustment_count": 5,
  "notification_count": 3,
  "in_cooldown": false
}
```

### GET /ready

Returns readiness status for Kubernetes probes.

**Response (200 OK - Ready):**
```json
{
  "ready": true,
  "nest_agent_configured": true,
  "logging_agent_configured": true,
  "config_loaded": true
}
```

**Response (503 Service Unavailable - Not Ready):**
```json
{
  "ready": false,
  "nest_agent_configured": false,
  "logging_agent_configured": true,
  "config_loaded": true
}
```

### GET /metrics

Returns Prometheus-compatible metrics.

**Response:**
```
# HELP vaspnestagent_temperature_ambient Current ambient temperature
# TYPE vaspnestagent_temperature_ambient gauge
vaspnestagent_temperature_ambient 72.5

# HELP vaspnestagent_temperature_target Current target temperature
# TYPE vaspnestagent_temperature_target gauge
vaspnestagent_temperature_target 75.0

# HELP vaspnestagent_adjustments_total Total temperature adjustments
# TYPE vaspnestagent_adjustments_total counter
vaspnestagent_adjustments_total 5

# HELP vaspnestagent_notifications_total Total notifications sent
# TYPE vaspnestagent_notifications_total counter
vaspnestagent_notifications_total 3

# HELP vaspnestagent_errors_total Total errors
# TYPE vaspnestagent_errors_total counter
vaspnestagent_errors_total 0

# HELP vaspnestagent_uptime_seconds Agent uptime in seconds
# TYPE vaspnestagent_uptime_seconds gauge
vaspnestagent_uptime_seconds 3600.5
```

## Error Handling

### GraphQL Errors

```json
{
  "errors": [
    {
      "message": "Failed to fetch temperature data",
      "locations": [{"line": 2, "column": 3}],
      "path": ["currentTemperature"],
      "extensions": {
        "code": "NEST_API_ERROR",
        "statusCode": 503
      }
    }
  ],
  "data": {
    "currentTemperature": null
  }
}
```

### Error Codes

| Code | Description |
|------|-------------|
| `NEST_API_ERROR` | Nest API communication failure |
| `AUTHENTICATION_ERROR` | OAuth token expired or invalid |
| `RATE_LIMIT_ERROR` | API rate limit exceeded |
| `VALIDATION_ERROR` | Invalid input parameters |
| `INTERNAL_ERROR` | Unexpected server error |

## Client Examples

### JavaScript (Apollo Client)

```javascript
import { ApolloClient, InMemoryCache, split, HttpLink } from '@apollo/client';
import { GraphQLWsLink } from '@apollo/client/link/subscriptions';
import { createClient } from 'graphql-ws';
import { getMainDefinition } from '@apollo/client/utilities';

const httpLink = new HttpLink({
  uri: 'http://localhost:8080/graphql',
});

const wsLink = new GraphQLWsLink(createClient({
  url: 'ws://localhost:8080/graphql',
}));

const splitLink = split(
  ({ query }) => {
    const definition = getMainDefinition(query);
    return (
      definition.kind === 'OperationDefinition' &&
      definition.operation === 'subscription'
    );
  },
  wsLink,
  httpLink,
);

const client = new ApolloClient({
  link: splitLink,
  cache: new InMemoryCache(),
});
```

### Python (gql)

```python
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport

transport = AIOHTTPTransport(url="http://localhost:8080/graphql")
client = Client(transport=transport, fetch_schema_from_transport=True)

query = gql("""
    query {
        currentTemperature {
            ambientTemperature
            targetTemperature
            differential
        }
    }
""")

result = client.execute(query)
print(result)
```

### cURL

```bash
# Query current temperature
curl -X POST http://localhost:8080/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ currentTemperature { ambientTemperature targetTemperature } }"}'

# Query with variables
curl -X POST http://localhost:8080/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "query($hours: Int) { temperatureHistory(hours: $hours) { timestamp ambientTemperature } }", "variables": {"hours": 6}}'
```
