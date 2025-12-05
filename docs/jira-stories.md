# Jira Stories for vaspNestAgent

This document contains all Jira stories for the vaspNestAgent project, ready to be imported into Jira.

**Project:** SCRUM  
**URL:** https://vaspinet.atlassian.net

## Epic: vaspNestAgent - Google Nest Thermostat Monitoring Agent

### Story 1: Project Setup and Repository Configuration
**Summary:** Set up project structure and repository  
**Type:** Story  
**Priority:** High  
**Story Points:** 3  
**Labels:** setup, infrastructure

**Description:**
As a developer, I need the project structure and repository configured so that I can start development.

**Acceptance Criteria:**
- [ ] Git repository initialized and connected to GitHub
- [ ] .gitignore configured for Python, Node.js, and Terraform
- [ ] README.md with project overview
- [ ] Python backend project structure with pyproject.toml
- [ ] React frontend project structure with Vite
- [ ] All dependencies defined

---

### Story 2: Core Data Models and Configuration
**Summary:** Implement core data models and configuration management  
**Type:** Story  
**Priority:** High  
**Story Points:** 5  
**Labels:** backend, models

**Description:**
As a developer, I need data models and configuration management so that the application can handle temperature data and settings.

**Acceptance Criteria:**
- [ ] TemperatureData, AdjustmentResult, AdjustmentEvent dataclasses
- [ ] EventType and Severity enums
- [ ] Configuration loading from environment variables
- [ ] Configuration loading from AWS Secrets Manager
- [ ] Configuration validation with error messages
- [ ] Property tests for data model serialization

---

### Story 3: NestAgent Implementation
**Summary:** Implement NestAgent for thermostat API interactions  
**Type:** Story  
**Priority:** High  
**Story Points:** 8  
**Labels:** backend, agent, nest-api

**Description:**
As a system, I need to interact with the Google Nest API so that I can read and adjust thermostat settings.

**Acceptance Criteria:**
- [ ] OAuth2 authentication with token refresh
- [ ] get_thermostat_data() method with retry logic
- [ ] set_temperature() method with retry logic
- [ ] Exponential backoff (max 5 retries for reads, 3 for writes)
- [ ] Strands SDK tool registration
- [ ] Property tests for retry limit compliance

---

### Story 4: LoggingAgent Implementation
**Summary:** Implement LoggingAgent for CloudWatch logging  
**Type:** Story  
**Priority:** High  
**Story Points:** 5  
**Labels:** backend, agent, cloudwatch

**Description:**
As a system, I need to log events to CloudWatch so that operations can be monitored.

**Acceptance Criteria:**
- [ ] CloudWatch Logs client with log group/stream management
- [ ] CloudWatch Metrics client for custom metrics
- [ ] log_temperature_reading() tool
- [ ] log_adjustment() tool
- [ ] log_notification() tool
- [ ] Property tests for log event completeness

---

### Story 5: Temperature Adjustment Logic
**Summary:** Implement temperature adjustment decision logic  
**Type:** Story  
**Priority:** High  
**Story Points:** 5  
**Labels:** backend, business-logic

**Description:**
As a system, I need to decide when to adjust temperature so that the thermostat is managed automatically.

**Acceptance Criteria:**
- [ ] should_adjust_temperature() function (differential < 5°F threshold)
- [ ] calculate_new_target() function (lower by 5°F)
- [ ] Cooldown period tracking (30 minutes)
- [ ] Property tests for temperature adjustment logic
- [ ] Property tests for cooldown period enforcement

---

### Story 6: Notification Service
**Summary:** Implement Google Voice notification service  
**Type:** Story  
**Priority:** Medium  
**Story Points:** 5  
**Labels:** backend, notifications

**Description:**
As a user, I want to receive SMS notifications when temperature is adjusted so that I'm informed of changes.

**Acceptance Criteria:**
- [ ] Google Voice SMS client with retry logic
- [ ] Notification message formatting with all temperatures
- [ ] Rate limiting (max 1 per hour)
- [ ] Property tests for notification content completeness
- [ ] Property tests for rate limiting enforcement

---

### Story 7: OrchestrationAgent Implementation
**Summary:** Implement main OrchestrationAgent with monitoring loop  
**Type:** Story  
**Priority:** High  
**Story Points:** 8  
**Labels:** backend, agent, orchestration

**Description:**
As a system, I need a main coordinator agent so that all components work together.

**Acceptance Criteria:**
- [ ] Initialize and coordinate NestAgent and LoggingAgent
- [ ] Monitoring loop with configurable polling interval (60s)
- [ ] Error handling with recovery (continue after errors)
- [ ] Graceful shutdown handling
- [ ] Error threshold alerting
- [ ] Property tests for error recovery and duplicate prevention

---

### Story 8: HTTP Health Server
**Summary:** Implement HTTP health and metrics endpoints  
**Type:** Story  
**Priority:** Medium  
**Story Points:** 3  
**Labels:** backend, health, kubernetes

**Description:**
As a Kubernetes cluster, I need health endpoints so that I can manage pod lifecycle.

**Acceptance Criteria:**
- [ ] /health endpoint (200 healthy, 503 degraded)
- [ ] /ready endpoint (200 when ready)
- [ ] /metrics endpoint (Prometheus format)
- [ ] Property tests for metrics consistency

---

### Story 9: GraphQL API
**Summary:** Implement GraphQL API for frontend  
**Type:** Story  
**Priority:** Medium  
**Story Points:** 5  
**Labels:** backend, graphql, api

**Description:**
As a frontend, I need a GraphQL API so that I can query and subscribe to temperature data.

**Acceptance Criteria:**
- [ ] GraphQL schema with Query and Subscription types
- [ ] currentTemperature, temperatureHistory, adjustmentHistory queries
- [ ] temperatureUpdates, adjustmentEvents subscriptions
- [ ] WebSocket support for subscriptions
- [ ] Property tests for GraphQL response completeness

---

### Story 10: React Frontend Components
**Summary:** Implement React frontend with temperature dashboard  
**Type:** Story  
**Priority:** Medium  
**Story Points:** 8  
**Labels:** frontend, react, dashboard

**Description:**
As a user, I want a dashboard to view temperature data so that I can monitor my thermostat.

**Acceptance Criteria:**
- [ ] Apollo Client setup with HTTP and WebSocket links
- [ ] TemperatureDisplay component showing current temps
- [ ] TemperatureChart component with Recharts
- [ ] AdjustmentHistory component with table
- [ ] ConnectionStatus component
- [ ] Dashboard component composing all components
- [ ] Real-time updates via subscriptions

---

### Story 11: Docker Containers
**Summary:** Create Docker containers for backend and frontend  
**Type:** Story  
**Priority:** Medium  
**Story Points:** 3  
**Labels:** docker, deployment

**Description:**
As a DevOps engineer, I need Docker containers so that the application can be deployed to Kubernetes.

**Acceptance Criteria:**
- [ ] Backend Dockerfile with Python 3.11
- [ ] Frontend Dockerfile with nginx
- [ ] Non-root user for security
- [ ] Application entry point (src/main.py)

---

### Story 12: Terraform VPC Module
**Summary:** Create Terraform VPC module  
**Type:** Story  
**Priority:** Medium  
**Story Points:** 3  
**Labels:** terraform, infrastructure, vpc

**Description:**
As infrastructure, I need a VPC so that EKS can be deployed securely.

**Acceptance Criteria:**
- [ ] VPC with CIDR 10.0.0.0/16
- [ ] Public subnets in 2 AZs
- [ ] Private subnets in 2 AZs
- [ ] Internet Gateway and NAT Gateways
- [ ] Route tables configured

---

### Story 13: Terraform EKS Module
**Summary:** Create Terraform EKS module  
**Type:** Story  
**Priority:** Medium  
**Story Points:** 5  
**Labels:** terraform, infrastructure, eks

**Description:**
As infrastructure, I need an EKS cluster so that the application can run on Kubernetes.

**Acceptance Criteria:**
- [ ] EKS cluster version 1.31+
- [ ] Managed node group with configurable instance types
- [ ] IAM roles for cluster and nodes
- [ ] OIDC provider for service accounts
- [ ] CloudWatch and Secrets Manager access policies

---

### Story 14: Terraform Supporting Modules
**Summary:** Create ECR, Secrets, and CloudWatch Terraform modules  
**Type:** Story  
**Priority:** Medium  
**Story Points:** 5  
**Labels:** terraform, infrastructure

**Description:**
As infrastructure, I need supporting AWS services for the application.

**Acceptance Criteria:**
- [ ] ECR repositories for backend and frontend
- [ ] Secrets Manager secrets for credentials
- [ ] CloudWatch log group and dashboard
- [ ] CloudWatch alarms for errors

---

### Story 15: Terraform Kubernetes Module
**Summary:** Create Terraform Kubernetes module  
**Type:** Story  
**Priority:** Medium  
**Story Points:** 5  
**Labels:** terraform, kubernetes

**Description:**
As infrastructure, I need Kubernetes resources deployed via Terraform.

**Acceptance Criteria:**
- [ ] Backend Deployment with health probes
- [ ] Frontend Deployment
- [ ] Services for backend and frontend
- [ ] Ingress with ALB annotations
- [ ] ConfigMap for application settings

---

### Story 16: Terraform Root Configuration
**Summary:** Create Terraform root configuration  
**Type:** Story  
**Priority:** Medium  
**Story Points:** 3  
**Labels:** terraform, infrastructure

**Description:**
As a DevOps engineer, I need a root Terraform configuration to deploy all modules.

**Acceptance Criteria:**
- [ ] main.tf composing all modules
- [ ] variables.tf with all configurable parameters
- [ ] backend.tf for S3 remote state
- [ ] outputs.tf with deployment information
- [ ] README.md with documentation

---

### Story 17: GitHub Actions CI/CD
**Summary:** Create GitHub Actions workflows for CI/CD  
**Type:** Story  
**Priority:** Medium  
**Story Points:** 5  
**Labels:** ci-cd, github-actions

**Description:**
As a developer, I need CI/CD pipelines so that code is automatically tested and deployed.

**Acceptance Criteria:**
- [ ] CI workflow with lint, test, and build jobs
- [ ] Deploy workflow with Terraform plan/apply
- [ ] Docker image build and push to ECR
- [ ] Kubernetes deployment updates
- [ ] Manual approval for production

---

### Story 18: Jira Integration
**Summary:** Integrate GitHub with Jira for ticket tracking  
**Type:** Story  
**Priority:** Low  
**Story Points:** 2  
**Labels:** integration, jira

**Description:**
As a project manager, I want GitHub integrated with Jira so that ticket status is updated automatically.

**Acceptance Criteria:**
- [ ] GitHub workflow for Jira integration
- [ ] Automatic ticket transition on PR events
- [ ] PR links added as comments to tickets
- [ ] Ticket ID validation in PRs

---

## Import Instructions

### Option 1: Manual Creation
Create each story manually in Jira using the information above.

### Option 2: CSV Import
Export this to CSV format and use Jira's CSV import feature.

### Option 3: Jira REST API
Use the Jira REST API to create issues programmatically. See `scripts/create-jira-stories.py`.

## Workflow States

Configure your Jira workflow with these states:
1. **To Do** - Initial state
2. **In Progress** - Development started
3. **In Review** - PR opened
4. **Done** - PR merged

## Labels

- `setup` - Project setup tasks
- `backend` - Python backend work
- `frontend` - React frontend work
- `agent` - Strands agent implementation
- `terraform` - Infrastructure as Code
- `infrastructure` - AWS infrastructure
- `ci-cd` - CI/CD pipelines
- `integration` - External integrations
