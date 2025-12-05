# vaspNestAgent

[![CI](https://github.com/vasifp/vaspNestAgent/actions/workflows/ci.yml/badge.svg)](https://github.com/vasifp/vaspNestAgent/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An intelligent Google Nest Thermostat monitoring and control system built with Python using the Strands SDK for multi-agent orchestration. The system automatically adjusts temperature settings based on ambient conditions and sends notifications via Google Voice.

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Getting Started](docs/getting-started.md) | Installation and setup guide |
| [Architecture](docs/architecture.md) | System design and components |
| [Configuration](docs/configuration.md) | Environment variables and settings |
| [API Reference](docs/api-reference.md) | GraphQL API documentation |
| [Deployment](docs/deployment.md) | AWS EKS deployment guide |
| [Development](docs/development.md) | Contributing and testing |

## Features

- **Real-time Temperature Monitoring**: Continuously polls Nest thermostat for ambient and target temperatures
- **Automatic Temperature Adjustment**: Lowers target temperature by 5°F when ambient is within 5°F of target
- **Google Voice Notifications**: Sends SMS alerts when temperature adjustments are made
- **Multi-Agent Architecture**: Uses Strands SDK with Orchestration Agent, NestAgent, and LoggingAgent
- **Real-time Dashboard**: React frontend with GraphQL subscriptions for live temperature monitoring
- **CloudWatch Observability**: All events logged to CloudWatch with dedicated dashboard
- **Infrastructure as Code**: Full Terraform configuration for AWS EKS deployment

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     AWS EKS Cluster                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              vaspNestAgent Backend                   │   │
│  │  ┌─────────────────┐  ┌─────────────┐  ┌─────────┐  │   │
│  │  │ Orchestration   │  │  NestAgent  │  │ Logging │  │   │
│  │  │     Agent       │──│             │  │  Agent  │  │   │
│  │  └────────┬────────┘  └──────┬──────┘  └────┬────┘  │   │
│  │           │                  │               │       │   │
│  │  ┌────────┴────────┐        │               │       │   │
│  │  │  GraphQL API    │        │               │       │   │
│  │  │  /graphql       │        │               │       │   │
│  │  └─────────────────┘        │               │       │   │
│  └─────────────────────────────┼───────────────┼───────┘   │
│                                │               │            │
│  ┌─────────────────────────────┼───────────────┼───────┐   │
│  │         React Frontend      │               │       │   │
│  │  ┌─────────────────────┐   │               │       │   │
│  │  │  Temperature Chart  │   │               │       │   │
│  │  │  Adjustment History │   │               │       │   │
│  │  └─────────────────────┘   │               │       │   │
│  └─────────────────────────────┼───────────────┼───────┘   │
└────────────────────────────────┼───────────────┼───────────┘
                                 │               │
                    ┌────────────┴──┐    ┌───────┴────────┐
                    │  Google Nest  │    │   CloudWatch   │
                    │     API       │    │  Logs/Metrics  │
                    └───────────────┘    └────────────────┘
```

## Project Structure

```
vaspNestAgent/
├── src/                          # Python backend
│   ├── agents/                   # Strands agents
│   │   ├── orchestration.py      # Main coordinator
│   │   ├── nest.py               # Nest API agent
│   │   └── logging.py            # CloudWatch agent
│   ├── models/                   # Data models
│   ├── services/                 # External service clients
│   ├── graphql/                  # GraphQL schema and resolvers
│   └── server/                   # HTTP and GraphQL servers
├── frontend/                     # React frontend
│   └── src/
│       ├── components/           # React components
│       ├── graphql/              # GraphQL queries
│       └── apollo/               # Apollo Client config
├── terraform/                    # Infrastructure as Code
│   └── modules/                  # Terraform modules
├── tests/                        # Test suites
│   ├── unit/
│   ├── property/                 # Hypothesis property tests
│   └── integration/
└── .github/workflows/            # CI/CD pipelines
```

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker
- AWS CLI configured
- Terraform 1.5+
- Google Nest Developer Account
- Google Voice Account

## Quick Start

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/vasifp/vaspNestAgent.git
   cd vaspNestAgent
   ```

2. Set up Python environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   ```

3. Set up frontend:
   ```bash
   cd frontend
   npm install
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

5. Run tests:
   ```bash
   pytest tests/ -v
   cd frontend && npm test
   ```

6. Start development servers:
   ```bash
   # Backend
   python -m src.main
   
   # Frontend (in another terminal)
   cd frontend && npm run dev
   ```

### AWS Deployment

1. Configure AWS credentials:
   ```bash
   aws configure
   ```

2. Initialize Terraform:
   ```bash
   cd terraform
   terraform init
   ```

3. Deploy infrastructure:
   ```bash
   terraform plan
   terraform apply
   ```

4. Build and push Docker images:
   ```bash
   # Get ECR login
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
   
   # Build and push backend
   docker build -t vaspnestagent-backend .
   docker tag vaspnestagent-backend:latest <ecr-url>/backend:latest
   docker push <ecr-url>/backend:latest
   
   # Build and push frontend
   docker build -t vaspnestagent-frontend ./frontend
   docker tag vaspnestagent-frontend:latest <ecr-url>/frontend:latest
   docker push <ecr-url>/frontend:latest
   ```

5. Deploy to EKS:
   ```bash
   aws eks update-kubeconfig --name vaspnestagent-cluster --region us-east-1
   kubectl apply -f terraform/modules/kubernetes/
   ```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POLLING_INTERVAL` | Temperature polling interval (seconds) | 60 |
| `COOLDOWN_PERIOD` | Adjustment cooldown (seconds) | 1800 |
| `TEMPERATURE_THRESHOLD` | Adjustment trigger threshold (°F) | 5.0 |
| `TEMPERATURE_ADJUSTMENT` | Amount to adjust (°F) | 5.0 |
| `AWS_REGION` | AWS region | us-east-1 |
| `CLOUDWATCH_LOG_GROUP` | CloudWatch log group | /vaspNestAgent/logs |

### AWS Secrets Manager

The following secrets are stored in AWS Secrets Manager:
- `vaspnestagent/nest-credentials`: Google Nest API OAuth credentials
- `vaspnestagent/google-voice`: Google Voice credentials and phone number (480-442-0574)

## Monitoring

### CloudWatch Dashboard

Access the "vaspNestAgent" dashboard in CloudWatch to view:
- Temperature readings over time
- Adjustment counts and frequency
- Notification success/failure rates
- API call latencies
- Error counts and agent health

### Health Endpoints

- `GET /health` - Returns 200 if healthy, 503 if degraded
- `GET /ready` - Returns 200 when ready to process
- `GET /metrics` - Prometheus-compatible metrics

## Testing

```bash
# Run all backend tests
pytest tests/ -v

# Run property-based tests with more examples
pytest tests/property/ -v --hypothesis-profile=ci

# Run frontend tests
cd frontend && npm test

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## Correctness Properties

The system is designed around 14 correctness properties verified by 102 property-based tests:

| Property | Description |
|----------|-------------|
| Temperature Adjustment | Adjusts when differential < 5°F threshold |
| Cooldown Enforcement | 30-minute cooldown between adjustments |
| Retry Compliance | Max 5 retries for reads, 3 for writes |
| Notification Content | Messages contain all temperature values |
| Rate Limiting | Max 1 notification per hour |
| Error Recovery | Continues operation after errors |

See [Architecture](docs/architecture.md) for the complete list.

## License

MIT License - See [LICENSE](LICENSE) for details.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Run the test suite (`pytest tests/ -v`)
5. Commit your changes (`git commit -m 'feat: Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

See [Development Guide](docs/development.md) for detailed instructions.

## Support

- 📖 [Documentation](docs/index.md)
- 🐛 [Issue Tracker](https://github.com/vasifp/vaspNestAgent/issues)
- 💬 [Discussions](https://github.com/vasifp/vaspNestAgent/discussions)
