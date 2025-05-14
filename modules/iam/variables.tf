variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
}

variable "lambda_function_names" {
  description = "List of Lambda function names requiring IAM roles"
  type        = list(string)
  default     = []
}

variable "dynamodb_table_arns" {
  description = "ARNs of DynamoDB tables to be accessed"
  type        = list(string)
}
