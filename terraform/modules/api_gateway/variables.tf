# Required variables
variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
}

variable "api_name" {
  description = "Name of the API Gateway"
  type        = string
}

variable "lambda_function_names" {
  description = "Map of Lambda function names (key = resource name like 'brands', value = full function name)"
  type        = map(string)
  # Example: { brands = "dev-brands", products = "dev-products" }
}

variable "lambda_invoke_arns" {
  description = "Map of Lambda function invoke ARNs (key must match lambda_function_names keys)"
  type        = map(string)
  # Example: { brands = "arn:aws:lambda:...:function:dev-brands" }
}

# Optional variables with sensible defaults
variable "api_description" {
  description = "Description of the API Gateway"
  type        = string
  default     = "Product Catalog HTTP API"
}

variable "stage_name" {
  description = "Stage name for API Gateway deployment"
  type        = string
  default     = "$default" # HTTP API uses $default for auto-deployment
}

variable "enable_auto_deploy" {
  description = "Whether to automatically deploy API changes"
  type        = bool
  default     = true # Simplifies deployment, good for dev environments
}

variable "cors_configuration" {
  description = "CORS configuration for the API"
  type = object({
    allow_origins = list(string)
    allow_methods = list(string)
    allow_headers = list(string)
    max_age       = number
  })
  default = {
    allow_origins = ["*"]                                                   # Allow all origins (restrict in production)
    allow_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]   # All CRUD methods
    allow_headers = ["Content-Type", "Authorization", "X-Amz-Date", "X-Api-Key", "X-Amz-Security-Token"]
    max_age       = 300 # Cache preflight requests for 5 minutes
  }
}

variable "throttle_settings" {
  description = "Default throttle settings for the API"
  type = object({
    burst_limit = number # Maximum concurrent requests
    rate_limit  = number # Requests per second
  })
  default = {
    burst_limit = 100 # Good for small projects
    rate_limit  = 50  # Prevents runaway costs
  }
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7 # Short retention for cost savings
}

variable "enable_access_logs" {
  description = "Enable CloudWatch access logs for API Gateway"
  type        = bool
  default     = true # Best practice for monitoring
}
