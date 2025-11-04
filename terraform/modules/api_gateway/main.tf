# HTTP API Gateway
resource "aws_apigatewayv2_api" "api" {
  name          = "${var.environment}-${var.api_name}"
  description   = var.api_description
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = var.cors_configuration.allow_origins
    allow_methods = var.cors_configuration.allow_methods
    allow_headers = var.cors_configuration.allow_headers
    max_age       = var.cors_configuration.max_age
  }
}

# Lambda Integrations
resource "aws_apigatewayv2_integration" "lambda" {
  for_each = var.lambda_function_names

  api_id                 = aws_apigatewayv2_api.api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = var.lambda_invoke_arns[each.key]
  integration_method     = "POST"
  payload_format_version = "2.0"
  timeout_milliseconds   = 30000
}

# Routes for CRUD operations
resource "aws_apigatewayv2_route" "get_all" {
  for_each = var.lambda_function_names

  api_id    = aws_apigatewayv2_api.api.id
  route_key = "GET /${each.key}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda[each.key].id}"
}

resource "aws_apigatewayv2_route" "post" {
  for_each = var.lambda_function_names

  api_id    = aws_apigatewayv2_api.api.id
  route_key = "POST /${each.key}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda[each.key].id}"
}

resource "aws_apigatewayv2_route" "get_by_id" {
  for_each = var.lambda_function_names

  api_id    = aws_apigatewayv2_api.api.id
  route_key = "GET /${each.key}/{id}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda[each.key].id}"
}

resource "aws_apigatewayv2_route" "put" {
  for_each = var.lambda_function_names

  api_id    = aws_apigatewayv2_api.api.id
  route_key = "PUT /${each.key}/{id}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda[each.key].id}"
}

resource "aws_apigatewayv2_route" "delete" {
  for_each = var.lambda_function_names

  api_id    = aws_apigatewayv2_api.api.id
  route_key = "DELETE /${each.key}/{id}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda[each.key].id}"
}

resource "aws_apigatewayv2_route" "patch" {
  for_each = var.lambda_function_names

  api_id    = aws_apigatewayv2_api.api.id
  route_key = "PATCH /${each.key}/{id}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda[each.key].id}"
}

# Special route for products stock management
resource "aws_apigatewayv2_route" "products_stock" {
  count = contains(keys(var.lambda_function_names), "products") ? 1 : 0

  api_id    = aws_apigatewayv2_api.api.id
  route_key = "PATCH /products/{id}/stock"
  target    = "integrations/${aws_apigatewayv2_integration.lambda["products"].id}"
}

# Special route for products by brand query
resource "aws_apigatewayv2_route" "products_by_brand" {
  count = contains(keys(var.lambda_function_names), "products") ? 1 : 0

  api_id    = aws_apigatewayv2_api.api.id
  route_key = "GET /products/by-brand/{brand_id}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda["products"].id}"
}

# Special route for products by category query
resource "aws_apigatewayv2_route" "products_by_category" {
  count = contains(keys(var.lambda_function_names), "products") ? 1 : 0

  api_id    = aws_apigatewayv2_api.api.id
  route_key = "GET /products/by-category/{category_id}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda["products"].id}"
}

# Lambda Permissions
resource "aws_lambda_permission" "api_gateway" {
  for_each = var.lambda_function_names

  statement_id  = "AllowExecutionFromAPIGateway-${each.key}"
  action        = "lambda:InvokeFunction"
  function_name = each.value
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*"
}

# API Stage
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.api.id
  name        = var.stage_name
  auto_deploy = var.enable_auto_deploy

  dynamic "access_log_settings" {
    for_each = var.enable_access_logs ? [1] : []
    content {
      destination_arn = aws_cloudwatch_log_group.api_gateway[0].arn
      format = jsonencode({
        requestId      = "$context.requestId"
        ip             = "$context.identity.sourceIp"
        requestTime    = "$context.requestTime"
        httpMethod     = "$context.httpMethod"
        routeKey       = "$context.routeKey"
        status         = "$context.status"
        protocol       = "$context.protocol"
        responseLength = "$context.responseLength"
        errorMessage   = "$context.error.message"
      })
    }
  }

  default_route_settings {
    throttling_burst_limit = var.throttle_settings.burst_limit
    throttling_rate_limit  = var.throttle_settings.rate_limit
  }

  depends_on = [aws_cloudwatch_log_group.api_gateway]
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "api_gateway" {
  count = var.enable_access_logs ? 1 : 0

  name              = "/aws/apigateway/${var.environment}-${var.api_name}"
  retention_in_days = var.log_retention_days
}
