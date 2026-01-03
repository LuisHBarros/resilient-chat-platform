# Infrastructure as Code

This directory contains Terraform configuration to deploy the AI Chat Platform on AWS.

## 📁 Structure

```
infra/
└── terraform/
    ├── main.tf                    # Provider configuration
    ├── variables.tf               # Variable definitions
    ├── terraform.tfvars.example    # Example configuration
    ├── vpc.tf                     # VPC and networking
    ├── security-groups.tf         # Security groups
    ├── iam.tf                     # IAM roles and policies
    ├── dynamodb.tf                # DynamoDB table
    ├── ecr.tf                     # ECR repository
    ├── ecs.tf                     # ECS cluster and service
    ├── alb.tf                     # Application Load Balancer
    ├── outputs.tf                # Output values
    ├── deploy.sh                  # Deployment script
    ├── build-and-push.sh          # Docker build/push script
    └── README.md                  # Detailed documentation
```

## 🚀 Quick Start

### 1. Prerequisites

- AWS CLI configured (`aws configure`)
- Terraform >= 1.0 installed
- Docker installed
- Bedrock model access enabled in AWS Console

### 2. Configure

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
```

### 3. Deploy Infrastructure

```bash
terraform init
terraform plan
terraform apply
```

Or use the deployment script:

```bash
./deploy.sh
```

### 4. Build and Push Docker Image

```bash
./build-and-push.sh
```

Or manually:

```bash
# Get ECR login
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $(terraform output -raw ecr_repository_url | cut -d'/' -f1)

# Build and push
docker build -t ia-proj-app:latest ../../
docker tag ia-proj-app:latest $(terraform output -raw ecr_repository_url):latest
docker push $(terraform output -raw ecr_repository_url):latest
```

### 5. Update ECS Service

```bash
aws ecs update-service \
  --cluster $(terraform output -raw ecs_cluster_name) \
  --service $(terraform output -raw ecs_service_name) \
  --force-new-deployment
```

### 6. Get Application URL

```bash
terraform output alb_url
```

## 🏗️ What Gets Created

- **VPC** with public and private subnets
- **ECS Fargate Cluster** for containerized application
- **ECR Repository** for Docker images
- **DynamoDB Table** for conversation storage
- **Application Load Balancer** for traffic distribution
- **IAM Roles** with permissions for Bedrock, DynamoDB, CloudWatch
- **Security Groups** with proper network isolation
- **CloudWatch Log Groups** for application logs
- **Auto Scaling** configuration (optional)

## 📚 Documentation

See [terraform/README.md](./terraform/README.md) for detailed documentation.

## 🔧 Configuration

Key configuration is in `terraform.tfvars`:

- `aws_region`: AWS region (default: us-east-1)
- `environment`: Environment name (dev/staging/prod)
- `bedrock_model_id`: Bedrock model to use
- `container_cpu`: CPU units for ECS tasks
- `container_memory`: Memory for ECS tasks
- `desired_count`: Initial number of tasks
- `dynamodb_billing_mode`: PAY_PER_REQUEST or PROVISIONED

## 🔍 Monitoring

- **CloudWatch Logs**: `/ecs/{project}-{environment}-app`
- **ECS Metrics**: Available in AWS Console
- **ALB Metrics**: Target group health checks

## 🧹 Cleanup

To destroy all resources:

```bash
terraform destroy
```

**Warning**: This will delete all resources including DynamoDB data!

