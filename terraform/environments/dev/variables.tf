variable "environment" {
  description = "environment (dev, staging, prod)"
  type        = string
}

variable "dynamodb_table_name" {
  description = "The name for the table that will hold product catalog data"
  type        = string
}

variable "dynamodb_table_hash_key" {
  description = "The name of the hash key attribute"
  type        = string
}

variable "dynamodb_table_range_key" {
  description = "The name of the range or sort key attribute"
  type        = string
}

variable "dynamodb_attribute_definitions" {
  description = "All the attribute definitions for the table"
  type = list(object({
    name = string
    type = string
  }))
}

variable "dynamodb_global_secondary_indexes" {
  description = "List of global secondary indexes for the DynamoDB table"
  type = list(object({
    name            = string
    hash_key        = string
    range_key       = string
    projection_type = string
    read_capacity   = optional(number)
    write_capacity  = optional(number)
  }))
}

variable "lambda_functions_names" {
  description = "Lambda functions names"
  type        = list(string)
}

variable "lambda_deployment_packages" {
  description = "Map of Lambda function names to their deployment package paths"
  type        = map(string)
  default     = {}
}

# API Gateway variables
variable "api_gateway_name" {
  description = "Name of the API Gateway"
  type        = string
}

variable "api_gateway_stage_name" {
  description = "Stage name for API Gateway"
  type        = string
  default     = "$default"
}

variable "api_gateway_auto_deploy" {
  description = "Enable automatic deployment of API changes"
  type        = bool
  default     = true
}

variable "api_gateway_enable_logs" {
  description = "Enable CloudWatch access logs"
  type        = bool
  default     = true
}

variable "api_gateway_log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7
}

variable "api_gateway_cors_config" {
  description = "CORS configuration for API Gateway"
  type = object({
    allow_origins = list(string)
    allow_methods = list(string)
    allow_headers = list(string)
    max_age       = number
  })
  default = {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    allow_headers = ["Content-Type", "Authorization", "X-Amz-Date", "X-Api-Key", "X-Amz-Security-Token"]
    max_age       = 300
  }
}

variable "api_gateway_throttle_settings" {
  description = "Throttle settings for API Gateway"
  type = object({
    burst_limit = number
    rate_limit  = number
  })
  default = {
    burst_limit = 100
    rate_limit  = 50
  }
}
