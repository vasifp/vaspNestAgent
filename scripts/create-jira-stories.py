#!/usr/bin/env python3
"""Create Jira stories for vaspNestAgent project.

This script creates all the Jira stories defined in the project specification
using the Jira REST API.

Prerequisites:
    1. Install requests: pip install requests
    2. Set environment variables:
       - JIRA_BASE_URL: https://vaspinet.atlassian.net
       - JIRA_USER_EMAIL: Your Atlassian account email
       - JIRA_API_TOKEN: API token from https://id.atlassian.com/manage-profile/security/api-tokens
       - JIRA_PROJECT_KEY: VASPNET (or your project key)

Usage:
    python scripts/create-jira-stories.py

    # Dry run (don't create, just print):
    python scripts/create-jira-stories.py --dry-run

    # Create specific story:
    python scripts/create-jira-stories.py --story 1
"""

import argparse
import os
import sys
from dataclasses import dataclass

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip install requests")
    sys.exit(1)


@dataclass
class JiraStory:
    """Represents a Jira story to be created."""

    id: int
    summary: str
    description: str
    story_points: int
    priority: str
    labels: list[str]
    acceptance_criteria: list[str]


# Define all stories
STORIES = [
    JiraStory(
        id=1,
        summary="Set up project structure and repository",
        description="""As a developer, I need the project structure and repository configured so that I can start development.

This includes:
- Git repository initialization
- Python backend structure with pyproject.toml
- React frontend structure with Vite
- All dependencies defined""",
        story_points=3,
        priority="High",
        labels=["setup", "infrastructure"],
        acceptance_criteria=[
            "Git repository initialized and connected to GitHub",
            ".gitignore configured for Python, Node.js, and Terraform",
            "README.md with project overview",
            "Python backend project structure with pyproject.toml",
            "React frontend project structure with Vite",
            "All dependencies defined",
        ],
    ),
    JiraStory(
        id=2,
        summary="Implement core data models and configuration management",
        description="""As a developer, I need data models and configuration management so that the application can handle temperature data and settings.

This includes:
- Data models for temperature readings and events
- Configuration loading from environment and Secrets Manager
- Validation with clear error messages""",
        story_points=5,
        priority="High",
        labels=["backend", "models"],
        acceptance_criteria=[
            "TemperatureData, AdjustmentResult, AdjustmentEvent dataclasses",
            "EventType and Severity enums",
            "Configuration loading from environment variables",
            "Configuration loading from AWS Secrets Manager",
            "Configuration validation with error messages",
            "Property tests for data model serialization",
        ],
    ),
    JiraStory(
        id=3,
        summary="Implement NestAgent for thermostat API interactions",
        description="""As a system, I need to interact with the Google Nest API so that I can read and adjust thermostat settings.

This includes:
- OAuth2 authentication with automatic token refresh
- Temperature reading and setting with retry logic
- Strands SDK integration""",
        story_points=8,
        priority="High",
        labels=["backend", "agent", "nest-api"],
        acceptance_criteria=[
            "OAuth2 authentication with token refresh",
            "get_thermostat_data() method with retry logic",
            "set_temperature() method with retry logic",
            "Exponential backoff (max 5 retries for reads, 3 for writes)",
            "Strands SDK tool registration",
            "Property tests for retry limit compliance",
        ],
    ),
    JiraStory(
        id=4,
        summary="Implement LoggingAgent for CloudWatch logging",
        description="""As a system, I need to log events to CloudWatch so that operations can be monitored.

This includes:
- CloudWatch Logs integration
- CloudWatch Metrics for custom metrics
- Strands SDK tool registration""",
        story_points=5,
        priority="High",
        labels=["backend", "agent", "cloudwatch"],
        acceptance_criteria=[
            "CloudWatch Logs client with log group/stream management",
            "CloudWatch Metrics client for custom metrics",
            "log_temperature_reading() tool",
            "log_adjustment() tool",
            "log_notification() tool",
            "Property tests for log event completeness",
        ],
    ),
    JiraStory(
        id=5,
        summary="Implement temperature adjustment decision logic",
        description="""As a system, I need to decide when to adjust temperature so that the thermostat is managed automatically.

Business rules:
- Adjust when ambient is within 5°F of target
- Lower target by 5°F when adjusting
- Enforce 30-minute cooldown between adjustments""",
        story_points=5,
        priority="High",
        labels=["backend", "business-logic"],
        acceptance_criteria=[
            "should_adjust_temperature() function (differential < 5°F threshold)",
            "calculate_new_target() function (lower by 5°F)",
            "Cooldown period tracking (30 minutes)",
            "Property tests for temperature adjustment logic",
            "Property tests for cooldown period enforcement",
        ],
    ),
    JiraStory(
        id=6,
        summary="Implement Google Voice notification service",
        description="""As a user, I want to receive SMS notifications when temperature is adjusted so that I'm informed of changes.

This includes:
- Google Voice SMS integration
- Message formatting with all temperature values
- Rate limiting to prevent spam""",
        story_points=5,
        priority="Medium",
        labels=["backend", "notifications"],
        acceptance_criteria=[
            "Google Voice SMS client with retry logic",
            "Notification message formatting with all temperatures",
            "Rate limiting (max 1 per hour)",
            "Property tests for notification content completeness",
            "Property tests for rate limiting enforcement",
        ],
    ),
    JiraStory(
        id=7,
        summary="Implement main OrchestrationAgent with monitoring loop",
        description="""As a system, I need a main coordinator agent so that all components work together.

This includes:
- Coordination of NestAgent and LoggingAgent
- Monitoring loop with configurable polling
- Error handling and graceful shutdown""",
        story_points=8,
        priority="High",
        labels=["backend", "agent", "orchestration"],
        acceptance_criteria=[
            "Initialize and coordinate NestAgent and LoggingAgent",
            "Monitoring loop with configurable polling interval (60s)",
            "Error handling with recovery (continue after errors)",
            "Graceful shutdown handling",
            "Error threshold alerting",
            "Property tests for error recovery and duplicate prevention",
        ],
    ),
    JiraStory(
        id=8,
        summary="Implement HTTP health and metrics endpoints",
        description="""As a Kubernetes cluster, I need health endpoints so that I can manage pod lifecycle.

This includes:
- Health endpoint for liveness probes
- Ready endpoint for readiness probes
- Metrics endpoint for Prometheus""",
        story_points=3,
        priority="Medium",
        labels=["backend", "health", "kubernetes"],
        acceptance_criteria=[
            "/health endpoint (200 healthy, 503 degraded)",
            "/ready endpoint (200 when ready)",
            "/metrics endpoint (Prometheus format)",
            "Property tests for metrics consistency",
        ],
    ),
    JiraStory(
        id=9,
        summary="Implement GraphQL API for frontend",
        description="""As a frontend, I need a GraphQL API so that I can query and subscribe to temperature data.

This includes:
- GraphQL schema definition
- Query and subscription resolvers
- WebSocket support for real-time updates""",
        story_points=5,
        priority="Medium",
        labels=["backend", "graphql", "api"],
        acceptance_criteria=[
            "GraphQL schema with Query and Subscription types",
            "currentTemperature, temperatureHistory, adjustmentHistory queries",
            "temperatureUpdates, adjustmentEvents subscriptions",
            "WebSocket support for subscriptions",
            "Property tests for GraphQL response completeness",
        ],
    ),
    JiraStory(
        id=10,
        summary="Implement React frontend with temperature dashboard",
        description="""As a user, I want a dashboard to view temperature data so that I can monitor my thermostat.

This includes:
- Temperature display and charts
- Adjustment history
- Real-time updates via GraphQL subscriptions""",
        story_points=8,
        priority="Medium",
        labels=["frontend", "react", "dashboard"],
        acceptance_criteria=[
            "Apollo Client setup with HTTP and WebSocket links",
            "TemperatureDisplay component showing current temps",
            "TemperatureChart component with Recharts",
            "AdjustmentHistory component with table",
            "ConnectionStatus component",
            "Dashboard component composing all components",
            "Real-time updates via subscriptions",
        ],
    ),
    JiraStory(
        id=11,
        summary="Create Docker containers for backend and frontend",
        description="""As a DevOps engineer, I need Docker containers so that the application can be deployed to Kubernetes.

This includes:
- Backend container with Python 3.11
- Frontend container with nginx
- Security best practices""",
        story_points=3,
        priority="Medium",
        labels=["docker", "deployment"],
        acceptance_criteria=[
            "Backend Dockerfile with Python 3.11",
            "Frontend Dockerfile with nginx",
            "Non-root user for security",
            "Application entry point (src/main.py)",
        ],
    ),
    JiraStory(
        id=12,
        summary="Create Terraform VPC module",
        description="""As infrastructure, I need a VPC so that EKS can be deployed securely.

This includes:
- VPC with public and private subnets
- Internet Gateway and NAT Gateways
- Proper routing configuration""",
        story_points=3,
        priority="Medium",
        labels=["terraform", "infrastructure", "vpc"],
        acceptance_criteria=[
            "VPC with CIDR 10.0.0.0/16",
            "Public subnets in 2 AZs",
            "Private subnets in 2 AZs",
            "Internet Gateway and NAT Gateways",
            "Route tables configured",
        ],
    ),
    JiraStory(
        id=13,
        summary="Create Terraform EKS module",
        description="""As infrastructure, I need an EKS cluster so that the application can run on Kubernetes.

This includes:
- EKS cluster with managed node groups
- IAM roles and policies
- OIDC provider for service accounts""",
        story_points=5,
        priority="Medium",
        labels=["terraform", "infrastructure", "eks"],
        acceptance_criteria=[
            "EKS cluster version 1.31+",
            "Managed node group with configurable instance types",
            "IAM roles for cluster and nodes",
            "OIDC provider for service accounts",
            "CloudWatch and Secrets Manager access policies",
        ],
    ),
    JiraStory(
        id=14,
        summary="Create ECR, Secrets, and CloudWatch Terraform modules",
        description="""As infrastructure, I need supporting AWS services for the application.

This includes:
- ECR for container images
- Secrets Manager for credentials
- CloudWatch for monitoring""",
        story_points=5,
        priority="Medium",
        labels=["terraform", "infrastructure"],
        acceptance_criteria=[
            "ECR repositories for backend and frontend",
            "Secrets Manager secrets for credentials",
            "CloudWatch log group and dashboard",
            "CloudWatch alarms for errors",
        ],
    ),
    JiraStory(
        id=15,
        summary="Create Terraform Kubernetes module",
        description="""As infrastructure, I need Kubernetes resources deployed via Terraform.

This includes:
- Deployments for backend and frontend
- Services and Ingress
- ConfigMaps for configuration""",
        story_points=5,
        priority="Medium",
        labels=["terraform", "kubernetes"],
        acceptance_criteria=[
            "Backend Deployment with health probes",
            "Frontend Deployment",
            "Services for backend and frontend",
            "Ingress with ALB annotations",
            "ConfigMap for application settings",
        ],
    ),
    JiraStory(
        id=16,
        summary="Create Terraform root configuration",
        description="""As a DevOps engineer, I need a root Terraform configuration to deploy all modules.

This includes:
- Module composition
- Variable definitions
- Remote state configuration""",
        story_points=3,
        priority="Medium",
        labels=["terraform", "infrastructure"],
        acceptance_criteria=[
            "main.tf composing all modules",
            "variables.tf with all configurable parameters",
            "backend.tf for S3 remote state",
            "outputs.tf with deployment information",
            "README.md with documentation",
        ],
    ),
    JiraStory(
        id=17,
        summary="Create GitHub Actions workflows for CI/CD",
        description="""As a developer, I need CI/CD pipelines so that code is automatically tested and deployed.

This includes:
- CI workflow for testing
- Deploy workflow for production
- Docker image management""",
        story_points=5,
        priority="Medium",
        labels=["ci-cd", "github-actions"],
        acceptance_criteria=[
            "CI workflow with lint, test, and build jobs",
            "Deploy workflow with Terraform plan/apply",
            "Docker image build and push to ECR",
            "Kubernetes deployment updates",
            "Manual approval for production",
        ],
    ),
    JiraStory(
        id=18,
        summary="Integrate GitHub with Jira for ticket tracking",
        description="""As a project manager, I want GitHub integrated with Jira so that ticket status is updated automatically.

This includes:
- GitHub workflow for Jira integration
- Automatic status transitions
- PR linking to tickets""",
        story_points=2,
        priority="Low",
        labels=["integration", "jira"],
        acceptance_criteria=[
            "GitHub workflow for Jira integration",
            "Automatic ticket transition on PR events",
            "PR links added as comments to tickets",
            "Ticket ID validation in PRs",
        ],
    ),
]


class JiraClient:
    """Client for Jira REST API."""

    def __init__(
        self,
        base_url: str,
        email: str,
        api_token: str,
        project_key: str,
    ):
        """Initialize the Jira client.

        Args:
            base_url: Jira instance URL (e.g., https://vaspinet.atlassian.net)
            email: Atlassian account email
            api_token: API token for authentication
            project_key: Jira project key (e.g., VASPNET)
        """
        self.base_url = base_url.rstrip("/")
        self.project_key = project_key
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

    def create_epic(self, summary: str, description: str) -> str | None:
        """Create an epic in Jira.

        Args:
            summary: Epic summary
            description: Epic description

        Returns:
            Epic key if successful, None otherwise
        """
        url = f"{self.base_url}/rest/api/3/issue"
        payload = {
            "fields": {
                "project": {"key": self.project_key},
                "summary": summary,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": description}],
                        }
                    ],
                },
                "issuetype": {"name": "Epic"},
            }
        }

        response = self.session.post(url, json=payload)
        if response.status_code == 201:
            return response.json()["key"]
        else:
            print(f"Error creating epic: {response.status_code} - {response.text}")
            return None

    def create_story(
        self,
        story: JiraStory,
        epic_key: str | None = None,
    ) -> str | None:
        """Create a story in Jira.

        Args:
            story: Story to create
            epic_key: Optional epic to link to

        Returns:
            Story key if successful, None otherwise
        """
        url = f"{self.base_url}/rest/api/3/issue"

        # Build description with acceptance criteria
        description_content = [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": story.description}],
            },
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "\n\nAcceptance Criteria:", "marks": [{"type": "strong"}]}
                ],
            },
        ]

        # Add acceptance criteria as bullet list
        list_items = []
        for criterion in story.acceptance_criteria:
            list_items.append({
                "type": "listItem",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": criterion}],
                    }
                ],
            })

        description_content.append({
            "type": "bulletList",
            "content": list_items,
        })

        payload = {
            "fields": {
                "project": {"key": self.project_key},
                "summary": story.summary,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": description_content,
                },
                "issuetype": {"name": "Story"},
                "labels": story.labels,
                "priority": {"name": story.priority},
            }
        }

        # Add epic link if provided
        if epic_key:
            payload["fields"]["parent"] = {"key": epic_key}

        response = self.session.post(url, json=payload)
        if response.status_code == 201:
            return response.json()["key"]
        else:
            print(f"Error creating story: {response.status_code} - {response.text}")
            return None

    def test_connection(self) -> bool:
        """Test the Jira connection.

        Returns:
            True if connection successful
        """
        url = f"{self.base_url}/rest/api/3/myself"
        response = self.session.get(url)
        return response.status_code == 200


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Create Jira stories for vaspNestAgent")
    parser.add_argument("--dry-run", action="store_true", help="Print stories without creating")
    parser.add_argument("--story", type=int, help="Create specific story by ID")
    args = parser.parse_args()

    # Get configuration from environment
    base_url = os.environ.get("JIRA_BASE_URL", "https://vaspinet.atlassian.net")
    email = os.environ.get("JIRA_USER_EMAIL")
    api_token = os.environ.get("JIRA_API_TOKEN")
    project_key = os.environ.get("JIRA_PROJECT_KEY", "SCRUM")

    if args.dry_run:
        print("=== DRY RUN - Stories to be created ===\n")
        stories_to_create = STORIES if args.story is None else [s for s in STORIES if s.id == args.story]
        for story in stories_to_create:
            print(f"Story {story.id}: {story.summary}")
            print(f"  Priority: {story.priority}")
            print(f"  Story Points: {story.story_points}")
            print(f"  Labels: {', '.join(story.labels)}")
            print(f"  Acceptance Criteria: {len(story.acceptance_criteria)} items")
            print()
        return

    # Validate environment
    if not email or not api_token:
        print("Error: JIRA_USER_EMAIL and JIRA_API_TOKEN environment variables required")
        print("\nSet them with:")
        print("  export JIRA_USER_EMAIL='your-email@example.com'")
        print("  export JIRA_API_TOKEN='your-api-token'")
        print("\nGet an API token from: https://id.atlassian.com/manage-profile/security/api-tokens")
        sys.exit(1)

    # Create client
    client = JiraClient(base_url, email, api_token, project_key)

    # Test connection
    print(f"Connecting to {base_url}...")
    if not client.test_connection():
        print("Error: Failed to connect to Jira. Check your credentials.")
        sys.exit(1)
    print("Connected successfully!\n")

    # Create epic first
    print("Creating epic...")
    epic_key = client.create_epic(
        summary="vaspNestAgent - Google Nest Thermostat Monitoring Agent",
        description="Intelligent temperature monitoring and control system with multi-agent orchestration.",
    )
    if epic_key:
        print(f"Created epic: {epic_key}\n")
    else:
        print("Warning: Could not create epic, stories will be created without epic link\n")

    # Create stories
    stories_to_create = STORIES if args.story is None else [s for s in STORIES if s.id == args.story]
    created = []
    failed = []

    for story in stories_to_create:
        print(f"Creating story {story.id}: {story.summary}...")
        key = client.create_story(story, epic_key)
        if key:
            print(f"  Created: {key}")
            created.append((story.id, key))
        else:
            print("  Failed!")
            failed.append(story.id)

    # Summary
    print("\n=== Summary ===")
    print(f"Created: {len(created)} stories")
    if created:
        for story_id, key in created:
            print(f"  Story {story_id}: {base_url}/browse/{key}")
    if failed:
        print(f"Failed: {len(failed)} stories")
        for story_id in failed:
            print(f"  Story {story_id}")


if __name__ == "__main__":
    main()
