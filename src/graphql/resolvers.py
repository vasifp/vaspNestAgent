"""GraphQL Resolvers for vaspNestAgent.

Implements query and subscription resolvers for the temperature monitoring API.
"""

import asyncio
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from ariadne import QueryType, SubscriptionType

if TYPE_CHECKING:
    from src.agents.orchestration import OrchestrationAgent

# Create resolver types
query = QueryType()
subscription = SubscriptionType()


def _format_temperature_reading(data: dict) -> dict:
    """Format a temperature reading for GraphQL response.

    Property 14: GraphQL Response Completeness
    The response SHALL contain all required fields.

    Args:
        data: Raw temperature data dictionary.

    Returns:
        Formatted dictionary with GraphQL field names.
    """
    ambient = data.get("ambient_temperature", 0)
    target = data.get("target_temperature", 0)

    return {
        "ambientTemperature": ambient,
        "targetTemperature": target,
        "thermostatId": data.get("thermostat_id", "unknown"),
        "timestamp": data.get("timestamp", datetime.now().isoformat()),
        "humidity": data.get("humidity"),
        "hvacMode": data.get("hvac_mode"),
        "differential": target - ambient,
    }


def _format_adjustment_event(data: dict) -> dict:
    """Format an adjustment event for GraphQL response.

    Args:
        data: Raw adjustment event dictionary.

    Returns:
        Formatted dictionary with GraphQL field names.
    """
    return {
        "id": data.get("id", "unknown"),
        "previousSetting": data.get("previous_setting", 0),
        "newSetting": data.get("new_setting", 0),
        "ambientTemperature": data.get("ambient_temperature", 0),
        "triggerReason": data.get("trigger_reason", ""),
        "timestamp": data.get("timestamp", datetime.now().isoformat()),
        "notificationSent": data.get("notification_sent", False),
    }


# =============================================================================
# Query Resolvers
# =============================================================================

@query.field("currentTemperature")
async def resolve_current_temperature(_, info) -> dict | None:
    """Get current temperature reading.

    Property 14: GraphQL Response Completeness
    For any GraphQL query for temperature data, the response SHALL contain
    all required fields (ambientTemperature, targetTemperature, thermostatId, timestamp).

    Validates: Requirements 15.1, 17.3
    """
    agent: OrchestrationAgent = info.context.get("agent")
    if agent is None:
        return None

    data = agent.get_latest_temperature()
    if data is None:
        return None

    return _format_temperature_reading(data)


@query.field("temperatureHistory")
async def resolve_temperature_history(_, info, hours: int = 24) -> list[dict]:
    """Get temperature history for the specified hours.

    Args:
        hours: Number of hours of history to return.

    Returns:
        List of temperature readings.
    """
    agent: OrchestrationAgent = info.context.get("agent")
    if agent is None:
        return []

    history = agent.get_temperature_history(hours)
    return [_format_temperature_reading(data) for data in history]


@query.field("adjustmentHistory")
async def resolve_adjustment_history(_, info, limit: int = 10) -> list[dict]:
    """Get recent adjustment events.

    Args:
        limit: Maximum number of adjustments to return.

    Returns:
        List of adjustment events (most recent first).
    """
    agent: OrchestrationAgent = info.context.get("agent")
    if agent is None:
        return []

    history = agent.get_adjustment_history(limit)
    return [_format_adjustment_event(data) for data in history]


@query.field("temperatureTimeline")
async def resolve_temperature_timeline(_, info, hours: int = 24) -> dict:
    """Get temperature timeline with readings and adjustments.

    Args:
        hours: Number of hours of history to return.

    Returns:
        Timeline with readings and adjustments.
    """
    agent: OrchestrationAgent = info.context.get("agent")

    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)

    if agent is None:
        return {
            "readings": [],
            "adjustments": [],
            "startTime": start_time.isoformat(),
            "endTime": end_time.isoformat(),
        }

    readings = agent.get_temperature_history(hours)
    adjustments = agent.get_adjustment_history(limit=100)

    # Filter adjustments to the time window
    start_str = start_time.isoformat()
    filtered_adjustments = [
        adj for adj in adjustments
        if adj.get("timestamp", "") >= start_str
    ]

    return {
        "readings": [_format_temperature_reading(r) for r in readings],
        "adjustments": [_format_adjustment_event(a) for a in filtered_adjustments],
        "startTime": start_time.isoformat(),
        "endTime": end_time.isoformat(),
    }


@query.field("healthStatus")
async def resolve_health_status(_, info) -> dict:
    """Get current health status.

    Returns:
        Health status dictionary.
    """
    agent: OrchestrationAgent = info.context.get("agent")

    if agent is None:
        return {
            "status": "unknown",
            "running": False,
            "uptimeSeconds": 0,
            "errorCount": 0,
            "consecutiveErrors": 0,
            "adjustmentCount": 0,
            "notificationCount": 0,
            "inCooldown": False,
            "cooldownRemaining": 0,
        }

    health = agent.get_health_status()

    return {
        "status": health.get("status", "unknown"),
        "running": health.get("running", False),
        "uptimeSeconds": health.get("uptime_seconds", 0),
        "errorCount": health.get("error_count", 0),
        "consecutiveErrors": health.get("consecutive_errors", 0),
        "adjustmentCount": health.get("adjustment_count", 0),
        "notificationCount": health.get("notification_count", 0),
        "inCooldown": health.get("in_cooldown", False),
        "cooldownRemaining": agent.get_cooldown_remaining_seconds(),
    }


# =============================================================================
# Subscription Resolvers
# =============================================================================

@subscription.source("temperatureUpdates")
async def temperature_updates_source(_, info) -> AsyncGenerator[dict, None]:
    """Subscribe to real-time temperature updates.

    Property 13: GraphQL Subscription Latency
    For any temperature update event, the GraphQL subscription SHALL deliver
    the update to connected clients within 2 seconds of the data being available.

    Validates: Requirements 15.2
    """
    agent: OrchestrationAgent = info.context.get("agent")

    while True:
        if agent is not None:
            data = agent.get_latest_temperature()
            if data is not None:
                yield _format_temperature_reading(data)

        # Poll every 2 seconds to meet latency requirement
        await asyncio.sleep(2)


@subscription.field("temperatureUpdates")
def temperature_updates_resolver(temperature: dict, _info) -> dict:
    """Resolve temperature update subscription."""
    return temperature


@subscription.source("adjustmentEvents")
async def adjustment_events_source(_, info) -> AsyncGenerator[dict, None]:
    """Subscribe to real-time adjustment events."""
    agent: OrchestrationAgent = info.context.get("agent")
    last_count = 0

    while True:
        if agent is not None:
            current_count = agent.adjustment_state.adjustment_count

            if current_count > last_count:
                # New adjustment occurred
                history = agent.get_adjustment_history(limit=1)
                if history:
                    yield _format_adjustment_event(history[0])
                last_count = current_count

        await asyncio.sleep(1)


@subscription.field("adjustmentEvents")
def adjustment_events_resolver(event: dict, _info) -> dict:
    """Resolve adjustment event subscription."""
    return event


def get_resolvers() -> list:
    """Get all resolver instances.

    Returns:
        List of resolver type instances.
    """
    return [query, subscription]
