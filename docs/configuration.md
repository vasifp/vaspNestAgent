# Configuration

vaspNestAgent uses a combination of environment variables and AWS Secrets Manager for configuration. This document details all available settings.

## Configuration Sources

| Source | Use Case | Security Level |
|--------|----------|----------------|
| Environment Variables | Non-sensitive settings | Low |
| AWS Secrets Manager | API credentials, tokens | High |
| `.env` file | Local development | Development only |

## Environment Variables

### Application Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `POLLING_INTERVAL` | int | `60` | Seconds between temperature checks (10-3600) |
| `COOLDOWN_PERIOD` | int | `1800` | Seconds between adjustments (60-86400) |
| `TEMPERATURE_THRESHOLD` | float | `5.0` | °F differential to trigger adjustment (1.0-20.0) |
| `TEMPERATURE_ADJUSTMENT` | float | `5.0` | °F to lower target by (1.0-20.0) |
| `HTTP_PORT` | int | `8080` | HTTP server port (1-65535) |
| `ERROR_THRESHOLD` | int | `10` | Errors before alerting (≥1) |
| `NOTIFICATION_RATE_LIMIT_ENABLED` | bool | `true` | Enable notification rate limiting |
| `NOTIFICATION_RATE_LIMIT_SECONDS` | int | `3600` | Rate limit window in seconds |

### AWS Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `AWS_REGION` | string | `us-east-1` | AWS region for services |
| `CLOUDWATCH_LOG_GROUP` | string | `/vaspNestAgent/logs` | CloudWatch log group name |

### Nest API Credentials (Local Development)

| Variable | Type | Description |
|----------|------|-------------|
| `NEST_CLIENT_ID` | string | OAuth2 client ID |
| `NEST_CLIENT_SECRET` | string | OAuth2 client secret |
| `NEST_REFRESH_TOKEN` | string | OAuth2 refresh token |
| `NEST_PROJECT_ID` | string | Device Access project ID |

### Google Voice Credentials (Local Development)

| Variable | Type | Description |
|----------|------|-------------|
| `GOOGLE_VOICE_CREDENTIALS` | string | Google Voice OAuth token |
| `GOOGLE_VOICE_PHONE_NUMBER` | string | Target phone number (e.g., `480-442-0574`) |

## AWS Secrets Manager

In production, sensitive credentials are stored in AWS Secrets Manager.

### Nest Credentials Secret

**Secret Name:** `vaspnestagent/nest-credentials`

```json
{
  "client_id": "your_oauth_client_id",
  "client_secret": "your_oauth_client_secret",
  "refresh_token": "your_refresh_token",
  "project_id": "your_device_access_project_id"
}
```

### Google Voice Secret

**Secret Name:** `vaspnestagent/google-voice`

```json
{
  "credentials": "your_google_voice_oauth_token",
  "phone_number": "480-442-0574"
}
```

## Validation Rules

The configuration system validates all values on startup:

### Polling Interval
- Minimum: 10 seconds (prevent API abuse)
- Maximum: 3600 seconds (1 hour)

### Cooldown Period
- Minimum: 60 seconds (1 minute)
- Maximum: 86400 seconds (24 hours)

### Temperature Threshold
- Minimum: 1.0°F
- Maximum: 20.0°F

### Temperature Adjustment
- Minimum: 1.0°F
- Maximum: 20.0°F

### Phone Number Format
Accepted formats:
- `480-442-0574`
- `(480) 442-0574`
- `4804420574`
- `+14804420574`

### AWS Region Format
Must match pattern: `^[a-z]{2}-[a-z]+-\d+$`
Examples: `us-east-1`, `eu-west-2`, `ap-southeast-1`

### CloudWatch Log Group
Must start with `/`

## Configuration Loading

### Production (EKS)

```python
from src.config import Config

# Load from environment + Secrets Manager
config = await Config.load(use_secrets_manager=True)
```

### Local Development

```python
from src.config import Config

# Load from environment only
config = Config.from_environment()
```

### Programmatic Configuration

```python
from src.config import Config

config = Config(
    polling_interval=30,
    cooldown_period=900,
    temperature_threshold=3.0,
    temperature_adjustment=3.0,
    nest_client_id="...",
    nest_client_secret="...",
    nest_refresh_token="...",
    nest_project_id="...",
    google_voice_credentials="...",
    google_voice_phone_number="480-442-0574",
)
config.validate()
```

## Example .env File

```bash
# ===========================================
# vaspNestAgent Configuration
# ===========================================

# Application Settings
POLLING_INTERVAL=60
COOLDOWN_PERIOD=1800
TEMPERATURE_THRESHOLD=5.0
TEMPERATURE_ADJUSTMENT=5.0
HTTP_PORT=8080
ERROR_THRESHOLD=10
NOTIFICATION_RATE_LIMIT_ENABLED=true
NOTIFICATION_RATE_LIMIT_SECONDS=3600

# AWS Settings
AWS_REGION=us-east-1
CLOUDWATCH_LOG_GROUP=/vaspNestAgent/logs

# Nest API Credentials
NEST_CLIENT_ID=your_client_id_here
NEST_CLIENT_SECRET=your_client_secret_here
NEST_REFRESH_TOKEN=your_refresh_token_here
NEST_PROJECT_ID=your_project_id_here

# Google Voice Credentials
GOOGLE_VOICE_CREDENTIALS=your_credentials_here
GOOGLE_VOICE_PHONE_NUMBER=480-442-0574
```

## Kubernetes ConfigMap

For EKS deployment, non-sensitive settings are stored in a ConfigMap:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: vaspnestagent-config
  namespace: vaspnestagent
data:
  POLLING_INTERVAL: "60"
  COOLDOWN_PERIOD: "1800"
  TEMPERATURE_THRESHOLD: "5.0"
  TEMPERATURE_ADJUSTMENT: "5.0"
  HTTP_PORT: "8080"
  ERROR_THRESHOLD: "10"
  NOTIFICATION_RATE_LIMIT_ENABLED: "true"
  NOTIFICATION_RATE_LIMIT_SECONDS: "3600"
  AWS_REGION: "us-east-1"
  CLOUDWATCH_LOG_GROUP: "/vaspNestAgent/logs"
```

## Troubleshooting

### Configuration Validation Failed

```
ConfigurationError: Configuration validation failed:
  - polling_interval must be at least 10 seconds
```

**Solution:** Check that all values are within valid ranges.

### Secrets Manager Access Denied

```
ConfigurationError: Failed to load Nest credentials from Secrets Manager
```

**Solution:** Ensure the EKS pod has IAM permissions to access Secrets Manager.

### Invalid Phone Number Format

```
ConfigurationError: Invalid phone number format: ***-***-1234
```

**Solution:** Use a valid phone number format (10-15 digits with optional formatting).
