resource "aws_lambda_function" "api_function" {
  for_each = toset(var.function_names)

  function_name = "${var.environment}-${each.value}"
  role          = var.lambda_execution_role_arn
  handler       = var.handler
  runtime       = var.runtime
  timeout       = var.timeout

  filename         = var.deployment_package_path
  source_code_hash = filebase64sha256(var.deployment_package_path)

  environment {
    variables = merge(var.environment_variables, {
      DYNAMODB_TABLE = var.dynamodb_table_name
    })
  }

  depends_on = [var.iam_role]
}
