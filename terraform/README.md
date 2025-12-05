# vaspNestAgent Terraform Infrastructure

This directory contains Terraform configurations for deploying vaspNestAgent on AWS EKS.

## Architecture

- **VPC**: Custom VPC with public and private subnets across 2 availability zones
- **EKS**: Managed Kubernetes cluster (v1.28) with auto-scaling node group
- **ECR**: Container registries for backend and frontend images
- **Secrets Manager**: Secure storage for Nest API and Google Voice credentials
- **CloudWatch**: Logging, metrics, and dashboard for monitoring

## Prerequisites

1. AWS CLI configured with appropriate credentials
2. Terraform >= 1.0
3. kubectl
4. Docker

## Quick Start

### 1. Initialize Terraform

```bash
cd terraform
terraform init
```

### 2. Create terraform.tfvars

Create a `terraform.tfvars` file with your sensitive values:

```hcl
nest_client_id            = "your-nest-client-id"
nest_client_secret        = "your-nest-client-secret"
nest_refresh_token        = "your-nest-refresh-token"
nest_project_id           = "your-nest-project-id"
google_voice_credentials  = "your-google-voice-credentials"
google_voice_phone_number = "480-442-0574"
```

### 3. Plan and Apply

```bash
terraform plan
terraform apply
```

### 4. Configure kubectl

```bash
aws eks update-kubeconfig --region us-east-1 --name vaspnestagent-cluster
```

### 5. Build and Push Docker Images

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build and push backend
docker build -t <backend-repo-url>:latest .
docker push <backend-repo-url>:latest

# Build and push frontend
docker build -t <frontend-repo-url>:latest ./frontend
docker push <frontend-repo-url>:latest
```

## Module Structure

```
terraform/
├── main.tf              # Root module composition
├── variables.tf         # Input variables
├── outputs.tf           # Output values
├── backend.tf           # Remote state configuration
├── README.md            # This file
└── modules/
    ├── vpc/             # VPC, subnets, NAT gateways
    ├── eks/             # EKS cluster and node groups
    ├── ecr/             # Container registries
    ├── secrets/         # Secrets Manager
    ├── cloudwatch/      # Logging and monitoring
    └── kubernetes/      # K8s deployments and services
```

## Configuration Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `aws_region` | AWS region | `us-east-1` |
| `cluster_name` | EKS cluster name | `vaspnestagent-cluster` |
| `cluster_version` | Kubernetes version | `1.28` |
| `node_instance_types` | EC2 instance types | `["t3.medium"]` |
| `node_desired_size` | Desired node count | `2` |
| `polling_interval` | Temperature polling interval (s) | `60` |
| `temperature_threshold` | Adjustment threshold (°F) | `5` |

## Outputs

After applying, Terraform outputs useful information:

- `eks_cluster_endpoint`: EKS API endpoint
- `eks_kubeconfig_command`: Command to configure kubectl
- `ecr_backend_repository_url`: Backend image repository
- `ecr_frontend_repository_url`: Frontend image repository
- `cloudwatch_dashboard_name`: CloudWatch dashboard name

## Remote State (Optional)

To enable remote state storage:

1. Uncomment the backend configuration in `backend.tf`
2. Create the S3 bucket and DynamoDB table
3. Run `terraform init` to migrate state

## Cleanup

```bash
terraform destroy
```

**Warning**: This will delete all resources including the EKS cluster and data.

## Troubleshooting

### EKS Connection Issues

```bash
# Verify cluster status
aws eks describe-cluster --name vaspnestagent-cluster --query "cluster.status"

# Update kubeconfig
aws eks update-kubeconfig --region us-east-1 --name vaspnestagent-cluster
```

### Pod Issues

```bash
# Check pod status
kubectl get pods -n vaspnestagent

# View pod logs
kubectl logs -n vaspnestagent deployment/vaspnestagent-backend

# Describe pod for events
kubectl describe pod -n vaspnestagent <pod-name>
```

### CloudWatch Dashboard

Access the dashboard at:
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=vaspNestAgent
