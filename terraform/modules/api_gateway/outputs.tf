output "api_id" {
  description = "ID of the API Gateway"
  value       = aws_apigatewayv2_api.api.id
}

output "api_endpoint" {
  description = "Base endpoint URL for the API Gateway"
  value       = aws_apigatewayv2_api.api.api_endpoint
}

output "api_invoke_url" {
  description = "Full invoke URL for the API (includes stage)"
  value       = aws_apigatewayv2_stage.default.invoke_url
}

output "api_arn" {
  description = "ARN of the API Gateway"
  value       = aws_apigatewayv2_api.api.arn
}

output "api_execution_arn" {
  description = "Execution ARN of the API Gateway"
  value       = aws_apigatewayv2_api.api.execution_arn
}

output "stage_name" {
  description = "Name of the API Gateway stage"
  value       = aws_apigatewayv2_stage.default.name
}

output "stage_id" {
  description = "ID of the API Gateway stage"
  value       = aws_apigatewayv2_stage.default.id
}

output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch Log Group for API Gateway"
  value       = var.enable_access_logs ? aws_cloudwatch_log_group.api_gateway[0].name : null
}

output "cloudwatch_log_group_arn" {
  description = "ARN of the CloudWatch Log Group for API Gateway"
  value       = var.enable_access_logs ? aws_cloudwatch_log_group.api_gateway[0].arn : null
}
