# Deployment Guide

This guide covers deploying vaspNestAgent to AWS EKS using Terraform.

## Prerequisites

- AWS CLI configured with appropriate credentials
- Terraform 1.6+
- kubectl
- Docker

## Infrastructure Overview

The Terraform configuration creates:

- **VPC** with public and private subnets across 2 AZs
- **EKS Cluster** with managed node groups
- **ECR Repositories** for backend and frontend images
- **Secrets Manager** secrets for API credentials
- **CloudWatch** log groups, dashboard, and alarms
- **Kubernetes** deployments, services, and ingress

## Step 1: Configure Terraform Backend

Edit `terraform/backend.tf` to configure your S3 backend:

```hcl
terraform {
  backend "s3" {
    bucket         = "your-terraform-state-bucket"
    key            = "vaspnestagent/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}
```

Create the S3 bucket and DynamoDB table:

```bash
# Create S3 bucket
aws s3 mb s3://your-terraform-state-bucket --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket your-terraform-state-bucket \
  --versioning-configuration Status=Enabled

# Create DynamoDB table for locking
aws dynamodb create-table \
  --table-name terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

## Step 2: Configure Variables

Create `terraform/terraform.tfvars`:

```hcl
# AWS Configuration
aws_region = "us-east-1"

# Project Configuration
project_name = "vaspnestagent"
environment  = "prod"

# EKS Configuration
eks_cluster_version = "1.31"
eks_node_instance_types = ["t3.medium"]
eks_node_desired_size   = 2
eks_node_min_size       = 1
eks_node_max_size       = 4

# Application Configuration
backend_image_tag  = "latest"
frontend_image_tag = "latest"
backend_replicas   = 2
frontend_replicas  = 2

# Tags
tags = {
  Project     = "vaspNestAgent"
  Environment = "prod"
  ManagedBy   = "terraform"
}
```

## Step 3: Initialize Terraform

```bash
cd terraform
terraform init
```

## Step 4: Create Secrets

Before applying Terraform, create the secrets in AWS Secrets Manager:

```bash
# Create Nest credentials secret
aws secretsmanager create-secret \
  --name vaspnestagent/nest-credentials \
  --secret-string '{
    "client_id": "YOUR_NEST_CLIENT_ID",
    "client_secret": "YOUR_NEST_CLIENT_SECRET",
    "refresh_token": "YOUR_NEST_REFRESH_TOKEN",
    "project_id": "YOUR_NEST_PROJECT_ID"
  }' \
  --region us-east-1

# Create Google Voice secret
aws secretsmanager create-secret \
  --name vaspnestagent/google-voice \
  --secret-string '{
    "credentials": "YOUR_GOOGLE_VOICE_CREDENTIALS",
    "phone_number": "480-442-0574"
  }' \
  --region us-east-1
```

## Step 5: Plan and Apply

```bash
# Review the plan
terraform plan -out=tfplan

# Apply the configuration
terraform apply tfplan
```

This will take 15-20 minutes to create all resources.

## Step 6: Build and Push Docker Images

```bash
# Get ECR login
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  $(terraform output -raw ecr_backend_url | cut -d'/' -f1)

# Build and push backend
docker build -t $(terraform output -raw ecr_backend_url):latest .
docker push $(terraform output -raw ecr_backend_url):latest

# Build and push frontend
docker build -t $(terraform output -raw ecr_frontend_url):latest ./frontend
docker push $(terraform output -raw ecr_frontend_url):latest
```

## Step 7: Configure kubectl

```bash
# Update kubeconfig
aws eks update-kubeconfig \
  --region us-east-1 \
  --name $(terraform output -raw eks_cluster_name)

# Verify connection
kubectl get nodes
```

## Step 8: Deploy Application

The Kubernetes resources are created by Terraform. Verify the deployment:

```bash
# Check pods
kubectl get pods -n vaspnestagent

# Check services
kubectl get services -n vaspnestagent

# Check ingress
kubectl get ingress -n vaspnestagent
```

## Step 9: Verify Deployment

```bash
# Get the ALB URL
export ALB_URL=$(kubectl get ingress -n vaspnestagent -o jsonpath='{.items[0].status.loadBalancer.ingress[0].hostname}')

# Check health endpoint
curl http://$ALB_URL/health

# Check GraphQL endpoint
curl -X POST http://$ALB_URL/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ currentTemperature { ambientTemperature targetTemperature } }"}'
```

## CI/CD with GitHub Actions

### Configure GitHub Secrets

Add these secrets to your GitHub repository:

| Secret | Description |
|--------|-------------|
| `AWS_ACCOUNT_ID` | Your AWS account ID |
| `AWS_DEPLOY_ROLE_ARN` | IAM role ARN for deployment |

### Create IAM Role for GitHub Actions

```bash
# Create trust policy
cat > trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:vasifp/vaspNestAgent:*"
        }
      }
    }
  ]
}
EOF

# Create role
aws iam create-role \
  --role-name vaspnestagent-github-actions \
  --assume-role-policy-document file://trust-policy.json

# Attach policies
aws iam attach-role-policy \
  --role-name vaspnestagent-github-actions \
  --policy-arn arn:aws:iam::aws:policy/AmazonEKSClusterPolicy

aws iam attach-role-policy \
  --role-name vaspnestagent-github-actions \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser
```

### Trigger Deployment

Push to the `main` branch to trigger the CI/CD pipeline:

```bash
git push origin main
```

## Monitoring

### CloudWatch Dashboard

Access the CloudWatch dashboard at:
```
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=vaspNestAgent
```

### Dashboard Widgets

- **Temperature Readings** - Ambient and target temperature over time
- **Adjustments** - Count of temperature adjustments
- **Notifications** - Success/failure counts
- **API Latency** - Nest API and Google Voice latency
- **Errors** - Error count and types

### Alarms

| Alarm | Threshold | Action |
|-------|-----------|--------|
| High Error Rate | >10 errors/5min | SNS notification |
| API Latency | >5s average | SNS notification |
| Pod Restart | >3 restarts/hour | SNS notification |

## Scaling

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: vaspnestagent-backend-hpa
  namespace: vaspnestagent
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: vaspnestagent-backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Node Scaling

The EKS node group is configured with:
- Minimum: 1 node
- Desired: 2 nodes
- Maximum: 4 nodes

Cluster Autoscaler will automatically adjust based on pod resource requests.

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl describe pod -n vaspnestagent <pod-name>

# Check logs
kubectl logs -n vaspnestagent <pod-name>
```

### Secrets Not Loading

```bash
# Verify IAM role
kubectl describe serviceaccount -n vaspnestagent vaspnestagent-backend

# Check Secrets Manager access
aws secretsmanager get-secret-value --secret-id vaspnestagent/nest-credentials
```

### ALB Not Creating

```bash
# Check ingress controller logs
kubectl logs -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller
```

## Cleanup

To destroy all resources:

```bash
cd terraform
terraform destroy
```

**Warning:** This will delete all data including CloudWatch logs and metrics.
