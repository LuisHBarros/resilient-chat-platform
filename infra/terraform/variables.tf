variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "ia-proj"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "app_port" {
  description = "Port the application listens on"
  type        = number
  default     = 8000
}

variable "container_cpu" {
  description = "CPU units for ECS task (1024 = 1 vCPU)"
  type        = number
  default     = 512
}

variable "container_memory" {
  description = "Memory for ECS task in MB"
  type        = number
  default     = 1024
}

variable "desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 2
}

variable "min_capacity" {
  description = "Minimum number of ECS tasks for autoscaling"
  type        = number
  default     = 1
}

variable "max_capacity" {
  description = "Maximum number of ECS tasks for autoscaling"
  type        = number
  default     = 10
}

variable "bedrock_model_id" {
  description = "AWS Bedrock model ID to use"
  type        = string
  default     = "anthropic.claude-3-sonnet-20240229-v1:0"
}

variable "allowed_cors_origins" {
  description = "Allowed CORS origins for the API"
  type        = list(string)
  default     = ["*"] # In production, specify exact origins
}

variable "enable_autoscaling" {
  description = "Enable ECS autoscaling"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7
}

variable "dynamodb_billing_mode" {
  description = "DynamoDB billing mode (PROVISIONED or PAY_PER_REQUEST)"
  type        = string
  default     = "PAY_PER_REQUEST"
}

variable "dynamodb_read_capacity" {
  description = "DynamoDB read capacity units (only for PROVISIONED mode)"
  type        = number
  default     = 5
}

variable "dynamodb_write_capacity" {
  description = "DynamoDB write capacity units (only for PROVISIONED mode)"
  type        = number
  default     = 5
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "ia-proj"
    ManagedBy   = "Terraform"
    Environment = "dev"
  }
}

