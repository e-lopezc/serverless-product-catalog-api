output "dynamodb_table_id" {
  description = "DynamoDB table id"
  value       = module.dynamodb_backend_table.dynamodb_table_id
}

output "dynamodb_table_arn" {
  description = "DynamoDB table arn"
  value       = module.dynamodb_backend_table.dynamodb_table_arn
}

output "dynamodb_table_name" {
  description = "DynamoDB table name"
  value       = module.dynamodb_backend_table.dynamodb_table_name
}
