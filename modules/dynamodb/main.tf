resource "aws_dynamodb_table" "products_catalog_table" {
  name           = var.table_name
  billing_mode   = var.billing_mode
  read_capacity  = var.billing_mode == "PROVISIONED" ? var.read_capacity_units : null
  write_capacity = var.billing_mode == "PROVISIONED" ? var.write_capacity_units : null
  hash_key       = var.hash_key
  range_key      = var.range_key

  dynamic "attribute" {
    for_each = var.attribute_definitions
    content {
      name = attribute.value.name
      type = attribute.value.type
    }
  }

  dynamic "global_secondary_index" {
    for_each = var.global_secondary_indexes
    content {
      name            = global_secondary_index.value.name
      hash_key        = global_secondary_index.value.hash_key
      range_key       = global_secondary_index.value.range_key
      projection_type = global_secondary_index.value.projection_type
      read_capacity   = var.billing_mode == "PROVISIONED" ? lookup(global_secondary_index.value, "read_capacity", null) : null
      write_capacity  = var.billing_mode == "PROVISIONED" ? lookup(global_secondary_index.value, "write_capacity", null) : null
    }
  }

  point_in_time_recovery {
    enabled = var.point_in_time_recovery # This will enable point-in-time recovery for data protection
  }

  server_side_encryption {
    enabled = var.server_side_encryption # For data security, we could enable encryption at rest
  }

  tags = {
    Name        = var.table_name
    Environment = var.environment
    ManagedBy   = var.managed_by
  }

}
