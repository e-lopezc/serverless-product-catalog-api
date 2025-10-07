# main dev
module "dynamodb_backend_table" {
  source                   = "../../modules/dynamodb"
  table_name               = var.dynamodb_table_name
  attribute_definitions    = var.dynamodb_attribute_definitions
  global_secondary_indexes = var.dynamodb_global_secondary_indexes
  hash_key                 = var.dynamodb_table_hash_key
  range_key                = var.dynamodb_table_range_key
}

module "iam_roles_and_policies" {
  source                = "../../modules/iam"
  environment           = var.environment
  lambda_function_names = var.lambda_functions_names
  dynamodb_table_arns   = ["${module.dynamodb_backend_table.dynamodb_table_arn}"]
  depends_on            = [module.dynamodb_backend_table]
}

module "lambda_functions" {
  source = "../../modules/lambda"

  environment               = var.environment
  function_names            = var.lambda_functions_names
  lambda_execution_role_arn = module.iam_roles_and_policies.lambda_execution_role_arn
  dynamodb_table_name       = module.dynamodb_backend_table.dynamodb_table_name

  # Separate deployment packages per function
  deployment_packages = var.lambda_deployment_packages

  # Performance (recommended)
  memory_size = 256 # Good for API functions
  timeout     = 30  # Generous for DynamoDB operations

  # Monitoring (recommended)
  tracing_config = {
    mode = "Active" # Enable X-Ray tracing
  }

  # Environment variables
  environment_variables = {
    LOG_LEVEL = "INFO"
  }

  # Skip these for your use case:
  # vpc_config = null                    # Not needed for DynamoDB
  # dead_letter_config = null            # Not needed for sync API
  # reserved_concurrent_executions = -1  # Default is fine
  # layers = []                          # Not needed for your dependencies
}

module "api_gateway" {
  source = "../../modules/api_gateway"

  environment = var.environment
  api_name    = var.api_gateway_name

  # Convert list to map for API Gateway module
  lambda_function_names = {
    for name in var.lambda_functions_names :
    name => "${var.environment}-${name}"
  }

  lambda_invoke_arns = module.lambda_functions.lambda_function_invoke_arns

  # Optional: override defaults if needed
  stage_name         = var.api_gateway_stage_name
  enable_auto_deploy = var.api_gateway_auto_deploy
  enable_access_logs = var.api_gateway_enable_logs
  log_retention_days = var.api_gateway_log_retention_days

  cors_configuration = var.api_gateway_cors_config
  throttle_settings  = var.api_gateway_throttle_settings

  depends_on = [module.lambda_functions]
}
