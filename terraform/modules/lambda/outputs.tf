output "lambda_function_arns" {
  description = "ARNs of the Lambda functions"
  value       = { for k, v in aws_lambda_function.api_function : k => v.arn }
}

output "lambda_function_names" {
  description = "Names of the Lambda functions"
  value       = { for k, v in aws_lambda_function.api_function : k => v.function_name }
}

output "lambda_function_invoke_arns" {
  description = "Invoke ARNs of the Lambda functions (for API Gateway)"
  value       = { for k, v in aws_lambda_function.api_function : k => v.invoke_arn }
}

output "lambda_function_qualified_arns" {
  description = "Qualified ARNs of the Lambda functions"
  value       = { for k, v in aws_lambda_function.api_function : k => v.qualified_arn }
}

output "lambda_function_versions" {
  description = "Latest published versions of the Lambda functions"
  value       = { for k, v in aws_lambda_function.api_function : k => v.version }
}

output "lambda_function_last_modified" {
  description = "Date Lambda functions were last modified"
  value       = { for k, v in aws_lambda_function.api_function : k => v.last_modified }
}

output "lambda_function_source_code_hashes" {
  description = "Base64-encoded representation of raw SHA-256 sum of the zip file"
  value       = { for k, v in aws_lambda_function.api_function : k => v.source_code_hash }
}

output "lambda_function_source_code_sizes" {
  description = "Size in bytes of the function .zip file"
  value       = { for k, v in aws_lambda_function.api_function : k => v.source_code_size }
}
