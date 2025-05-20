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

output "lambda_execution_role_arn" {
  description = "Lambda Execution role arn"
  value       = module.iam_roles_and_policies.lambda_execution_role_arn
}

output "api_gateway_execution_role_arn" {
  description = "Api Gateway Execution role arn"
  value       = module.iam_roles_and_policies.api_gateway_role_arn
}
