#!/bin/bash
# Script to build and push Docker image to ECR

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if Terraform has been applied
if [ ! -f "terraform.tfstate" ]; then
    echo -e "${YELLOW}Error: terraform.tfstate not found.${NC}"
    echo "Please run 'terraform apply' first to create the infrastructure."
    exit 1
fi

# Get ECR repository URL
ECR_REPO=$(terraform output -raw ecr_repository_url 2>/dev/null || echo "")
if [ -z "$ECR_REPO" ]; then
    echo -e "${YELLOW}Error: Could not get ECR repository URL.${NC}"
    echo "Make sure Terraform has been applied successfully."
    exit 1
fi

# Get AWS region
AWS_REGION=$(terraform output -raw aws_region 2>/dev/null || terraform output aws_region 2>/dev/null | tr -d '"' || echo "us-east-1")
ECR_REGISTRY=$(echo $ECR_REPO | cut -d'/' -f1)

echo -e "${GREEN}Building and pushing Docker image...${NC}"
echo "ECR Repository: $ECR_REPO"
echo "Region: $AWS_REGION"
echo ""

# Login to ECR
echo "Logging in to ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

# Build image
echo "Building Docker image..."
cd ../..  # Go to project root
docker build -t ia-proj-app:latest .

# Tag image
echo "Tagging image..."
docker tag ia-proj-app:latest $ECR_REPO:latest

# Push image
echo "Pushing image to ECR..."
docker push $ECR_REPO:latest

echo ""
echo -e "${GREEN}Image pushed successfully!${NC}"
echo ""
echo "Next step: Update ECS service to use the new image:"
echo "  aws ecs update-service \\"
echo "    --cluster \$(cd infra/terraform && terraform output -raw ecs_cluster_name) \\"
echo "    --service \$(cd infra/terraform && terraform output -raw ecs_service_name) \\"
echo "    --force-new-deployment \\"
echo "    --region $AWS_REGION"

