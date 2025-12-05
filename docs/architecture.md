# Architecture

vaspNestAgent uses a multi-agent architecture built on the Strands SDK for orchestration. This document describes the system components and their interactions.

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         vaspNestAgent                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                   OrchestrationAgent                          │   │
│  │  - Temperature monitoring loop (60s polling)                  │   │
│  │  - Adjustment decision logic                                  │   │
│  │  - Cooldown period enforcement (30 min)                       │   │
│  │  - Notification rate limiting (1/hour)                        │   │
│  │  - Error handling and recovery                                │   │
│  └──────────────────────────────────────────────────────────────┘   │
│           │                                    │                     │
│           ▼                                    ▼                     │
│  ┌─────────────────────┐          ┌─────────────────────┐           │
│  │     NestAgent       │          │    LoggingAgent     │           │
│  │  - get_temperature  │          │  - log_temperature  │           │
│  │  - set_temperature  │          │  - log_adjustment   │           │
│  │  - OAuth2 auth      │          │  - log_notification │           │
│  │  - Retry logic      │          │  - publish_metrics  │           │
│  └─────────────────────┘          └─────────────────────┘           │
│           │                                    │                     │
│           ▼                                    ▼                     │
│  ┌─────────────────────┐          ┌─────────────────────┐           │
│  │   NestAPIClient     │          │  CloudWatchClient   │           │
│  │  - SDM API calls    │          │  - Log events       │           │
│  │  - Token refresh    │          │  - Custom metrics   │           │
│  └─────────────────────┘          └─────────────────────┘           │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                   GoogleVoiceClient                           │   │
│  │  - SMS notifications                                          │   │
│  │  - Retry with exponential backoff                             │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Agent Components

### OrchestrationAgent

The main coordinator that manages the monitoring loop and decision-making.

**Responsibilities:**
- Execute monitoring cycles at configured intervals
- Determine when temperature adjustments are needed
- Enforce cooldown periods between adjustments
- Manage notification rate limiting
- Handle errors and maintain system health
- Coordinate sub-agents (NestAgent, LoggingAgent)

**Key Properties:**
- Property 1: Temperature Adjustment Logic
- Property 2: Cooldown Period Enforcement
- Property 9: Error Recovery
- Property 10: Duplicate Adjustment Prevention
- Property 11: Error Threshold Alerting

### NestAgent

Specialized agent for Nest thermostat API interactions.

**Responsibilities:**
- Authenticate with Google OAuth2
- Read thermostat temperature data
- Set target temperature
- Handle API errors with retry logic

**Tools Provided:**
- `get_temperature` - Get current ambient and target temperatures
- `set_temperature` - Set new target temperature
- `get_nest_status` - Get agent connection status

### LoggingAgent

Specialized agent for CloudWatch logging and metrics.

**Responsibilities:**
- Log temperature readings
- Log adjustment events
- Log notification events
- Publish custom metrics to CloudWatch

**Tools Provided:**
- `log_temperature_reading` - Log temperature data
- `log_adjustment` - Log adjustment events
- `log_notification` - Log notification events
- `log_error` - Log error events

## Service Layer

### NestAPIClient

Low-level client for Google Nest Smart Device Management API.

**Features:**
- OAuth2 token management with automatic refresh
- Exponential backoff retry (max 5 attempts for reads, 3 for writes)
- Temperature conversion (Celsius ↔ Fahrenheit)
- Rate limit handling

### CloudWatchClient

Client for AWS CloudWatch Logs and Metrics.

**Features:**
- Log event buffering and batching
- Custom metric publishing
- Automatic log stream creation
- Sequence token management

### GoogleVoiceClient

Client for sending SMS notifications via Google Voice.

**Features:**
- SMS sending with retry logic
- Exponential backoff (max 3 retries)
- Message formatting for adjustments and alerts

## Data Flow

### Temperature Monitoring Cycle

```
1. OrchestrationAgent.monitor_cycle()
   │
   ├─► NestAgent.get_temperature()
   │   └─► NestAPIClient.get_thermostat_data()
   │       └─► Google SDM API
   │
   ├─► LoggingAgent.log_temperature_reading()
   │   └─► CloudWatchClient.put_log_events()
   │       └─► CloudWatch Logs
   │
   ├─► Check: should_adjust_temperature()?
   │   ├─► Is differential < threshold? (5°F)
   │   └─► Is cooldown expired? (30 min)
   │
   └─► If adjustment needed:
       ├─► NestAgent.set_temperature()
       │   └─► NestAPIClient.set_temperature()
       │       └─► Google SDM API
       │
       ├─► LoggingAgent.log_adjustment()
       │   └─► CloudWatch Logs + Metrics
       │
       └─► GoogleVoiceClient.send_sms()
           └─► Google Voice API
```

## Frontend Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     React Frontend                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                      Dashboard                              │ │
│  │  ┌──────────────────┐  ┌──────────────────────────────┐   │ │
│  │  │ TemperatureDisplay│  │     TemperatureChart         │   │ │
│  │  │ - Current temps   │  │ - Ambient/Target lines       │   │ │
│  │  │ - Differential    │  │ - Adjustment markers         │   │ │
│  │  └──────────────────┘  └──────────────────────────────┘   │ │
│  │  ┌──────────────────┐  ┌──────────────────────────────┐   │ │
│  │  │ ConnectionStatus │  │     AdjustmentHistory        │   │ │
│  │  │ - Backend status │  │ - Recent adjustments         │   │ │
│  │  │ - WebSocket state│  │ - Timestamps & reasons       │   │ │
│  │  └──────────────────┘  └──────────────────────────────┘   │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│                              ▼                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    Apollo Client                            │ │
│  │  - HTTP Link (queries/mutations)                            │ │
│  │  - WebSocket Link (subscriptions)                           │ │
│  │  - Split Link routing                                       │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
└──────────────────────────────┼───────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     GraphQL Server                               │
│  - Queries: currentTemperature, temperatureHistory              │
│  - Subscriptions: temperatureUpdates, adjustmentEvents          │
└─────────────────────────────────────────────────────────────────┘
```

## Infrastructure Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         AWS Cloud                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                        VPC                               │    │
│  │  ┌─────────────────┐    ┌─────────────────┐             │    │
│  │  │  Public Subnet  │    │  Public Subnet  │             │    │
│  │  │   (us-east-1a)  │    │   (us-east-1b)  │             │    │
│  │  │  ┌───────────┐  │    │  ┌───────────┐  │             │    │
│  │  │  │    ALB    │  │    │  │    NAT    │  │             │    │
│  │  │  └───────────┘  │    │  └───────────┘  │             │    │
│  │  └─────────────────┘    └─────────────────┘             │    │
│  │                                                          │    │
│  │  ┌─────────────────┐    ┌─────────────────┐             │    │
│  │  │ Private Subnet  │    │ Private Subnet  │             │    │
│  │  │   (us-east-1a)  │    │   (us-east-1b)  │             │    │
│  │  │  ┌───────────┐  │    │  ┌───────────┐  │             │    │
│  │  │  │ EKS Node  │  │    │  │ EKS Node  │  │             │    │
│  │  │  │ ┌───────┐ │  │    │  │ ┌───────┐ │  │             │    │
│  │  │  │ │Backend│ │  │    │  │ │Frontend│ │  │             │    │
│  │  │  │ └───────┘ │  │    │  │ └───────┘ │  │             │    │
│  │  │  └───────────┘  │    │  └───────────┘  │             │    │
│  │  └─────────────────┘    └─────────────────┘             │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │     ECR      │  │   Secrets    │  │  CloudWatch  │           │
│  │  - Backend   │  │   Manager    │  │  - Logs      │           │
│  │  - Frontend  │  │  - Nest creds│  │  - Metrics   │           │
│  │              │  │  - GV creds  │  │  - Dashboard │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Correctness Properties

The system is designed around 14 correctness properties verified by property-based tests:

| Property | Description | Requirements |
|----------|-------------|--------------|
| 1 | Temperature Adjustment Logic | 2.1 |
| 2 | Cooldown Period Enforcement | 2.5 |
| 3 | Retry Limit Compliance | 1.4, 2.3, 3.3 |
| 4 | Notification Content Completeness | 3.2 |
| 5 | Rate Limiting Enforcement | 3.5 |
| 6 | Configuration Validation | 5.3, 5.4 |
| 7 | Log Event Completeness | 1.5, 2.4, 3.4, 5.5 |
| 8 | Metrics Consistency | 6.4 |
| 9 | Error Recovery | 7.1 |
| 10 | Duplicate Adjustment Prevention | 7.3 |
| 11 | Error Threshold Alerting | 7.5 |
| 12 | Temperature Data Parsing Round-Trip | 1.3 |
| 13 | Graceful Shutdown | 7.4 |
| 14 | GraphQL Response Completeness | 15.1, 17.3 |
