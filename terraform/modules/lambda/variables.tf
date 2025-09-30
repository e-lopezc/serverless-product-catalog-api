variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
}

variable "function_names" {
  description = "List of Lambda function names to create"
  type        = list(string)
}

variable "lambda_execution_role_arn" {
  description = "ARN of the Lambda execution role"
  type        = string
}

variable "handler" {
  description = "Lambda function handler"
  type        = string
  default     = "lambda_handler"
}

variable "runtime" {
  description = "Lambda runtime"
  type        = string
  default     = "python3.13"
}

variable "timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 29
}

variable "deployment_packages" {
  description = "Map of function names to their deployment package paths (for separate packages per function)"
  type        = map(string)
  default     = {}
}

variable "dynamodb_table_name" {
  description = "Name of the DynamoDB table"
  type        = string
}

variable "environment_variables" {
  description = "Additional environment variables for Lambda functions"
  type        = map(string)
  default     = {}
}

variable "iam_role" {
  description = "IAM role dependency (for depends_on)"
  type        = any
  default     = null
}

variable "memory_size" {
  description = "Amount of memory in MB your Lambda Function can use at runtime"
  type        = number
  default     = 128
}

variable "reserved_concurrent_executions" {
  description = "Amount of reserved concurrent executions for Lambda function"
  type        = number
  default     = -1
}

variable "layers" {
  description = "List of Lambda Layer ARNs"
  type        = list(string)
  default     = []
}

variable "vpc_config" {
  description = "VPC configuration for Lambda function"
  type = object({
    subnet_ids         = list(string)
    security_group_ids = list(string)
  })
  default = null
}

variable "dead_letter_config" {
  description = "Dead letter queue configuration"
  type = object({
    target_arn = string
  })
  default = null
}

variable "tracing_config" {
  description = "Tracing configuration"
  type = object({
    mode = string
  })
  default = {
    mode = "PassThrough"
  }
}
