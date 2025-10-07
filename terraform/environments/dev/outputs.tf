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

# API Gateway outputs
output "api_gateway_id" {
  description = "API Gateway ID"
  value       = module.api_gateway.api_id
}

output "api_gateway_endpoint" {
  description = "API Gateway base endpoint"
  value       = module.api_gateway.api_endpoint
}

output "api_gateway_invoke_url" {
  description = "API Gateway invoke URL (use this to call your API)"
  value       = module.api_gateway.api_invoke_url
}

output "api_gateway_arn" {
  description = "API Gateway ARN"
  value       = module.api_gateway.api_arn
}

output "api_gateway_stage_name" {
  description = "API Gateway stage name"
  value       = module.api_gateway.stage_name
}
