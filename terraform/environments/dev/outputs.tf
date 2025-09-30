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

output "lambda_function_arns" {
  description = "ARNs of all Lambda functions"
  value       = module.lambda_functions.lambda_function_arns
}

output "lambda_function_names" {
  description = "Names of all Lambda functions"
  value       = module.lambda_functions.lambda_function_names
}

output "lambda_function_invoke_arns" {
  description = "Invoke ARNs for API Gateway integration"
  value       = module.lambda_functions.lambda_function_invoke_arns
}
