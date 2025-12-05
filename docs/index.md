# vaspNestAgent Documentation

**Intelligent Google Nest Thermostat Monitoring Agent**

vaspNestAgent is an autonomous temperature monitoring system that uses multi-agent orchestration to manage your Google Nest thermostat. It automatically adjusts temperature settings based on configurable thresholds and sends notifications via Google Voice.

## Quick Links

- [Getting Started](getting-started.md) - Installation and setup
- [Architecture](architecture.md) - System design and components
- [Configuration](configuration.md) - Environment variables and settings
- [API Reference](api-reference.md) - GraphQL API documentation
- [Deployment](deployment.md) - AWS EKS deployment guide
- [Development](development.md) - Contributing and testing
- [Jira Integration](jira-integration.md) - GitHub-Jira workflow automation
- [Jira Stories](jira-stories.md) - Project stories for import

## Features

### 🌡️ Temperature Monitoring
- Polls Nest thermostat every 60 seconds (configurable)
- Monitors ambient and target temperatures
- Calculates temperature differential in real-time

### 🔄 Automatic Adjustment
- Adjusts target temperature when ambient approaches target (within 5°F threshold)
- Enforces 30-minute cooldown between adjustments
- Prevents duplicate adjustments on restart

### 📱 Smart Notifications
- Sends SMS via Google Voice on temperature adjustments
- Rate-limited to 1 notification per hour
- Error threshold alerting for system issues

### 📊 Real-time Dashboard
- React frontend with live temperature charts
- GraphQL subscriptions for real-time updates
- Adjustment history with visual markers

### ☁️ Cloud-Native
- Deploys to AWS EKS with Terraform
- CloudWatch dashboard for monitoring
- Secrets Manager for credential storage

## System Requirements

- Python 3.11+
- Node.js 20+
- AWS Account with EKS access
- Google Nest Developer Account
- Google Voice Account

## License

MIT License - See [LICENSE](../LICENSE) for details.
