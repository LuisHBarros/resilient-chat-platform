# Terraform Infrastructure for IA Proj

This directory contains Terraform configuration to deploy the AI Chat Platform on AWS using:
- **ECS Fargate** for containerized application hosting
- **AWS Bedrock** for LLM capabilities
- **DynamoDB** for conversation storage
- **Application Load Balancer** for traffic distribution
- **CloudWatch** for logging and monitoring

## 📋 Prerequisites

1. **AWS CLI** installed and configured
   ```bash
   aws configure
   ```

2. **Terraform** installed (>= 1.0)
   ```bash
   terraform version
   ```

3. **Docker** installed (for building container images)

4. **AWS Permissions**: Your AWS credentials need permissions to create:
   - VPC, Subnets, Internet Gateway, NAT Gateway
   - ECS Cluster, Service, Task Definition
   - ECR Repository
   - DynamoDB Tables
   - IAM Roles and Policies
   - Application Load Balancer
   - CloudWatch Log Groups
   - Security Groups

5. **Bedrock Model Access**: Ensure you have access to the Bedrock model in AWS Console:
   - Go to [AWS Bedrock Console](https://console.aws.amazon.com/bedrock/)
   - Navigate to **Model access**
   - Request access for your desired model (e.g., Claude 3 Sonnet)

## 🚀 Quick Start

### 1. Configure Variables

Copy the example variables file and customize:

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
```

### 2. Initialize Terraform

```bash
terraform init
```

### 3. Review Plan

```bash
terraform plan
```

### 4. Apply Infrastructure

```bash
terraform apply
```

This will create:
- VPC with public and private subnets
- ECS Fargate cluster
- ECR repository for Docker images
- DynamoDB table for conversations
- Application Load Balancer
- IAM roles and policies
- Security groups
- CloudWatch log groups

### 5. Build and Push Docker Image

After infrastructure is created, build and push your Docker image:

```bash
# Get ECR login token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $(terraform output -raw ecr_repository_url | cut -d'/' -f1)

# Build image
docker build -t ia-proj-app:latest ../../

# Tag image
docker tag ia-proj-app:latest $(terraform output -raw ecr_repository_url):latest

# Push image
docker push $(terraform output -raw ecr_repository_url):latest
```

### 6. Update ECS Service

After pushing the image, update the ECS service to use the new image:

```bash
aws ecs update-service \
  --cluster $(terraform output -raw ecs_cluster_name) \
  --service $(terraform output -raw ecs_service_name) \
  --force-new-deployment \
  --region us-east-1
```

### 7. Get Application URL

```bash
terraform output alb_url
# Example: http://ia-proj-dev-alb-123456789.us-east-1.elb.amazonaws.com
```

## 📁 File Structure

```
infra/terraform/
├── main.tf                 # Provider and main configuration
├── variables.tf             # Variable definitions
├── terraform.tfvars.example # Example variable values
├── vpc.tf                  # VPC, subnets, routing
├── security-groups.tf      # Security group rules
├── iam.tf                  # IAM roles and policies
├── dynamodb.tf             # DynamoDB table
├── ecr.tf                  # ECR repository
├── ecs.tf                  # ECS cluster, service, task definition
├── alb.tf                  # Application Load Balancer
├── outputs.tf              # Output values
└── README.md              # This file
```

## 🏗️ Architecture Overview

```
Internet
   │
   ▼
Application Load Balancer (Public Subnets)
   │
   ▼
ECS Fargate Tasks (Private Subnets)
   │
   ├──► AWS Bedrock (LLM)
   │
   └──► DynamoDB (Conversations)
```

### Network Architecture

- **Public Subnets**: ALB, NAT Gateway
- **Private Subnets**: ECS Tasks (no direct internet access)
- **NAT Gateway**: Allows ECS tasks to pull images and access AWS services

### Security

- **Security Groups**: Restrict traffic to necessary ports only
- **IAM Roles**: Least privilege access (Bedrock, DynamoDB, CloudWatch)
- **Private Subnets**: ECS tasks not directly accessible from internet
- **Encryption**: DynamoDB encryption at rest enabled

## 🔧 Configuration

### Key Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `aws_region` | AWS region | `us-east-1` |
| `environment` | Environment name | `dev` |
| `bedrock_model_id` | Bedrock model to use | `anthropic.claude-3-sonnet-20240229-v1:0` |
| `container_cpu` | CPU units (1024 = 1 vCPU) | `512` |
| `container_memory` | Memory in MB | `1024` |
| `desired_count` | Initial ECS task count | `2` |
| `dynamodb_billing_mode` | `PAY_PER_REQUEST` or `PROVISIONED` | `PAY_PER_REQUEST` |

### DynamoDB Table Structure

**Table**: `{project}-{environment}-conversations`

**Primary Key**:
- Partition Key: `conversation_id` (String)

**Global Secondary Index**: `user-id-index`
- Partition Key: `user_id` (String)
- Sort Key: `updated_at` (String)

**Attributes**:
- `conversation_id`: String (PK)
- `user_id`: String (GSI PK)
- `updated_at`: String (GSI SK, ISO format)
- `messages`: List/JSON (messages array)
- `created_at`: String (ISO format)

## 🐳 Docker Image Requirements

Your application needs a `Dockerfile` in the project root. Example:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📝 Environment Variables

The ECS task definition sets these environment variables:

- `LLM_PROVIDER=bedrock`
- `AWS_REGION={aws_region}`
- `BEDROCK_MODEL_ID={bedrock_model_id}`
- `DYNAMODB_TABLE_NAME={table_name}`
- `API_PREFIX=/api/v1`
- `ENVIRONMENT={environment}`
- `CORS_ORIGINS={allowed_origins}`

## 🔍 Monitoring

### CloudWatch Logs

Logs are automatically sent to CloudWatch:
- Log Group: `/ecs/{project}-{environment}-app`
- Retention: Configurable (default: 7 days)

### View Logs

```bash
aws logs tail /ecs/ia-proj-dev-app --follow --region us-east-1
```

### ECS Metrics

ECS Container Insights is enabled. View metrics in:
- AWS Console → ECS → Clusters → Your Cluster → Metrics

## 🔄 Updating Infrastructure

### Update Application Code

1. Build and push new Docker image
2. Force new deployment:
   ```bash
   aws ecs update-service \
     --cluster $(terraform output -raw ecs_cluster_name) \
     --service $(terraform output -raw ecs_service_name) \
     --force-new-deployment
   ```

### Update Infrastructure

```bash
terraform plan
terraform apply
```

## 🧹 Cleanup

To destroy all resources:

```bash
terraform destroy
```

**Warning**: This will delete all resources including DynamoDB data!

## 🔐 Security Best Practices

1. **Production**: 
   - Use HTTPS (configure ACM certificate in `alb.tf`)
   - Restrict CORS origins to specific domains
   - Enable deletion protection on ALB
   - Use `PROVISIONED` billing for DynamoDB with proper capacity planning
   - Enable point-in-time recovery for DynamoDB

2. **Secrets Management**:
   - Use AWS Secrets Manager or Parameter Store for sensitive config
   - Don't hardcode credentials in task definitions

3. **Network**:
   - Consider VPC endpoints for AWS services (reduce NAT costs)
   - Use security groups with least privilege

## 📚 Additional Resources

- [ECS Fargate Documentation](https://docs.aws.amazon.com/ecs/latest/developerguide/AWS_Fargate.html)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)

## 🐛 Troubleshooting

### ECS Tasks Not Starting

1. Check CloudWatch logs:
   ```bash
   aws logs tail /ecs/ia-proj-dev-app --follow
   ```

2. Check task status:
   ```bash
   aws ecs describe-tasks \
     --cluster $(terraform output -raw ecs_cluster_name) \
     --tasks $(aws ecs list-tasks --cluster $(terraform output -raw ecs_cluster_name) --query 'taskArns[0]' --output text)
   ```

3. Verify IAM permissions (Bedrock, DynamoDB, CloudWatch)

### Cannot Access Application

1. Check ALB health checks:
   - AWS Console → EC2 → Load Balancers → Target Groups → Health checks

2. Verify security groups allow traffic

3. Check if tasks are running:
   ```bash
   aws ecs describe-services \
     --cluster $(terraform output -raw ecs_cluster_name) \
     --services $(terraform output -raw ecs_service_name)
   ```

### DynamoDB Access Issues

1. Verify IAM policy allows DynamoDB access
2. Check table name matches environment variable
3. Verify table exists:
   ```bash
   aws dynamodb describe-table --table-name $(terraform output -raw dynamodb_table_name)
   ```

