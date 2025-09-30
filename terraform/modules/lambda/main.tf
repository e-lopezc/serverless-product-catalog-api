resource "aws_lambda_function" "api_function" {
  for_each = toset(var.function_names)

  function_name                  = "${var.environment}-${each.value}"
  role                           = var.lambda_execution_role_arn
  handler                        = "handlers.${each.value}.${var.handler}" # Specific handler per function
  runtime                        = var.runtime
  timeout                        = var.timeout
  memory_size                    = var.memory_size
  reserved_concurrent_executions = var.reserved_concurrent_executions

  filename         = var.deployment_packages[each.value]
  source_code_hash = filebase64sha256(var.deployment_packages[each.value])

  layers = var.layers

  environment {
    variables = merge(var.environment_variables, {
      DYNAMODB_TABLE = var.dynamodb_table_name
      AWS_REGION     = data.aws_region.current.name
    })
  }

  # VPC configuration (optional)
  dynamic "vpc_config" {
    for_each = var.vpc_config != null ? [var.vpc_config] : []
    content {
      subnet_ids         = vpc_config.value.subnet_ids
      security_group_ids = vpc_config.value.security_group_ids
    }
  }

  # Dead letter queue (optional)
  dynamic "dead_letter_config" {
    for_each = var.dead_letter_config != null ? [var.dead_letter_config] : []
    content {
      target_arn = dead_letter_config.value.target_arn
    }
  }

  # X-Ray tracing
  tracing_config {
    mode = var.tracing_config.mode
  }

  depends_on = [var.iam_role]

  tags = {
    Environment = var.environment
    Function    = each.value
    ManagedBy   = "terraform"
  }
}

# CloudWatch Log Groups for Lambda functions
resource "aws_cloudwatch_log_group" "lambda_log_group" {
  for_each = toset(var.function_names)

  name              = "/aws/lambda/${var.environment}-${each.value}"
  retention_in_days = 14

  tags = {
    Environment = var.environment
    Function    = each.value
    ManagedBy   = "terraform"
  }
}

# Get current AWS region
data "aws_region" "current" {}
