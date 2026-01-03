#!/bin/bash
# Deployment script for IA Proj infrastructure

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if terraform.tfvars exists
if [ ! -f "terraform.tfvars" ]; then
    echo -e "${YELLOW}Warning: terraform.tfvars not found. Using defaults.${NC}"
    echo "Copy terraform.tfvars.example to terraform.tfvars and customize it."
    read -p "Continue with defaults? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Initialize Terraform
echo -e "${GREEN}Initializing Terraform...${NC}"
terraform init

# Plan
echo -e "${GREEN}Planning infrastructure changes...${NC}"
terraform plan -out=tfplan

# Ask for confirmation
read -p "Apply these changes? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    rm -f tfplan
    exit 1
fi

# Apply
echo -e "${GREEN}Applying infrastructure changes...${NC}"
terraform apply tfplan
rm -f tfplan

# Get outputs
echo -e "${GREEN}Infrastructure deployed successfully!${NC}"
echo ""
echo "Outputs:"
echo "=========="
terraform output

# Get ECR repository URL
ECR_REPO=$(terraform output -raw ecr_repository_url 2>/dev/null || echo "")
if [ -n "$ECR_REPO" ]; then
    echo ""
    echo -e "${GREEN}Next steps:${NC}"
    echo "1. Build and push Docker image:"
    echo "   aws ecr get-login-password --region \$(terraform output -raw aws_region) | docker login --username AWS --password-stdin \$(echo $ECR_REPO | cut -d'/' -f1)"
    echo "   docker build -t ia-proj-app:latest ../../"
    echo "   docker tag ia-proj-app:latest $ECR_REPO:latest"
    echo "   docker push $ECR_REPO:latest"
    echo ""
    echo "2. Update ECS service:"
    echo "   aws ecs update-service --cluster \$(terraform output -raw ecs_cluster_name) --service \$(terraform output -raw ecs_service_name) --force-new-deployment"
    echo ""
    echo "3. Get application URL:"
    echo "   terraform output alb_url"
fi

