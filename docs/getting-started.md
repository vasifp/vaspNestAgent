# Getting Started

This guide walks you through setting up vaspNestAgent for local development and testing.

## Prerequisites

### Required Software

- **Python 3.11+** - Backend runtime
- **Node.js 20+** - Frontend build tools
- **Docker** - Container builds
- **Terraform 1.6+** - Infrastructure deployment
- **AWS CLI** - AWS interactions

### Required Accounts

- **Google Cloud Platform** - For Nest Smart Device Management API
- **Google Voice** - For SMS notifications
- **AWS Account** - For EKS deployment

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/vasifp/vaspNestAgent.git
cd vaspNestAgent
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

### 3. Set Up Frontend

```bash
cd frontend
npm install
cd ..
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Nest API Configuration
NEST_CLIENT_ID=your_client_id
NEST_CLIENT_SECRET=your_client_secret
NEST_REFRESH_TOKEN=your_refresh_token
NEST_PROJECT_ID=your_project_id

# Google Voice Configuration
GOOGLE_VOICE_CREDENTIALS=your_credentials
GOOGLE_VOICE_PHONE_NUMBER=480-442-0574

# Application Settings
POLLING_INTERVAL=60
COOLDOWN_PERIOD=1800
TEMPERATURE_THRESHOLD=5.0
TEMPERATURE_ADJUSTMENT=5.0
HTTP_PORT=8080

# AWS Settings (for CloudWatch)
AWS_REGION=us-east-1
CLOUDWATCH_LOG_GROUP=/vaspNestAgent/logs
```

## Google Nest API Setup

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing
3. Enable the **Smart Device Management API**

### 2. Create OAuth Credentials

1. Go to **APIs & Services > Credentials**
2. Click **Create Credentials > OAuth client ID**
3. Select **Web application**
4. Add authorized redirect URI: `https://www.google.com`
5. Save the **Client ID** and **Client Secret**

### 3. Create Device Access Project

1. Go to [Device Access Console](https://console.nest.google.com/device-access)
2. Create a new project
3. Link your OAuth client
4. Note the **Project ID**

### 4. Get Refresh Token

```bash
# Step 1: Get authorization code
# Open this URL in browser (replace YOUR_CLIENT_ID and YOUR_PROJECT_ID):
https://nestservices.google.com/partnerconnections/YOUR_PROJECT_ID/auth?redirect_uri=https://www.google.com&access_type=offline&prompt=consent&client_id=YOUR_CLIENT_ID&response_type=code&scope=https://www.googleapis.com/auth/sdm.service

# Step 2: Exchange code for tokens
curl -X POST https://oauth2.googleapis.com/token \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "code=AUTHORIZATION_CODE" \
  -d "grant_type=authorization_code" \
  -d "redirect_uri=https://www.google.com"
```

Save the `refresh_token` from the response.

## Running Locally

### Backend Only

```bash
# Run with local configuration (no Secrets Manager)
python -m src.main --local
```

### Frontend Development Server

```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:5173`

### Full Stack with Docker

```bash
# Build images
docker build -t vaspnestagent/backend .
docker build -t vaspnestagent/frontend ./frontend

# Run backend
docker run -p 8080:8080 --env-file .env vaspnestagent/backend

# Run frontend
docker run -p 80:80 vaspnestagent/frontend
```

## Running Tests

### All Tests

```bash
pytest tests/ -v
```

### Property-Based Tests Only

```bash
pytest tests/property/ -v --hypothesis-profile=ci
```

### With Coverage

```bash
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

### Frontend Tests

```bash
cd frontend
npm test
```

## Verifying Setup

### 1. Check Configuration

```bash
python -c "from src.config import Config; c = Config.from_environment(); print('Config OK')"
```

### 2. Test Nest API Connection

```bash
python -c "
import asyncio
from src.config import Config
from src.agents.nest import NestAgent

async def test():
    config = Config.from_environment()
    agent = NestAgent(config)
    await agent.initialize()
    result = await agent.get_temperature()
    print(f'Temperature: {result}')
    await agent.close()

asyncio.run(test())
"
```

### 3. Verify Health Endpoint

```bash
# Start the server
python -m src.main --local &

# Check health
curl http://localhost:8080/health

# Check readiness
curl http://localhost:8080/ready
```

## Next Steps

- [Configuration Guide](configuration.md) - Detailed configuration options
- [Architecture](architecture.md) - System design overview
- [Deployment](deployment.md) - Deploy to AWS EKS
- [API Reference](api-reference.md) - GraphQL API documentation
