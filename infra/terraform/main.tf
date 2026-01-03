terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Optional: Configure remote state backend
  # backend "s3" {
  #   bucket = "your-terraform-state-bucket"
  #   key    = "ia-proj/terraform.tfstate"
  #   region = "us-east-1"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = merge(
      var.tags,
      {
        Environment = var.environment
        Project     = var.project_name
      }
    )
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Local values for common naming
locals {
  name_prefix = "${var.project_name}-${var.environment}"
  
  common_tags = merge(
    var.tags,
    {
      Environment = var.environment
      Project     = var.project_name
    }
  )
}

