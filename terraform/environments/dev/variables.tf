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
