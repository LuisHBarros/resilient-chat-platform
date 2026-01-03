# DynamoDB table for conversations
resource "aws_dynamodb_table" "conversations" {
  name         = "${local.name_prefix}-conversations"
  billing_mode = var.dynamodb_billing_mode

  # Provisioned capacity (only used if billing_mode = "PROVISIONED")
  read_capacity  = var.dynamodb_billing_mode == "PROVISIONED" ? var.dynamodb_read_capacity : null
  write_capacity = var.dynamodb_billing_mode == "PROVISIONED" ? var.dynamodb_write_capacity : null

  # Partition key: conversation_id
  hash_key = "conversation_id"

  attribute {
    name = "conversation_id"
    type = "S"
  }

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "updated_at"
    type = "S"
  }

  # Global Secondary Index for querying by user_id
  global_secondary_index {
    name            = "user-id-index"
    hash_key        = "user_id"
    range_key       = "updated_at"
    projection_type = "ALL"

    # Provisioned capacity for GSI (only if billing_mode = "PROVISIONED")
    read_capacity  = var.dynamodb_billing_mode == "PROVISIONED" ? var.dynamodb_read_capacity : null
    write_capacity = var.dynamodb_billing_mode == "PROVISIONED" ? var.dynamodb_write_capacity : null
  }

  # Point-in-time recovery
  point_in_time_recovery {
    enabled = var.environment == "prod" ? true : false
  }

  # Server-side encryption
  server_side_encryption {
    enabled = true
  }

  tags = {
    Name = "${local.name_prefix}-conversations"
  }
}

