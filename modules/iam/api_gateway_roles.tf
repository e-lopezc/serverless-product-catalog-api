resource "aws_iam_role" "api_gateway_role" {
  name = "${var.environment}-api-gateway-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "apigateway.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_policy" "api_gateway_lambda_invoke" {
  name        = "${var.environment}-api-gateway-lambda-invoke"
  description = "Allow API Gateway to invoke Lambda functions"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action   = "lambda:InvokeFunction"
      Effect   = "Allow"
      Resource = [for name in var.lambda_function_names : "arn:aws:lambda:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:function:${var.environment}-${name}"]
    }]
  })
}

resource "aws_iam_role_policy_attachment" "api_gateway_lambda" {
  role       = aws_iam_role.api_gateway_role.name
  policy_arn = aws_iam_policy.api_gateway_lambda_invoke.arn
}
