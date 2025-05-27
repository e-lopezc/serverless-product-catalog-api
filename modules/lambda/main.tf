data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/src/${var.function_name}_crud"
  output_path = "${path.module}/src/${var.function_name}_crud/${var.function_name}_crud_function.zip"
}


resource "aws_lambda_function" "crud_function" {
  filename      = data.archive_file.lambda_zip.output_path
  handler       = "index.lambda_handler"
  function_name = var.function_name
  role          = var.execution_role_arn
  runtime       = var.runtime
  timeout       = var.timeout
  environment {
    variables = {
      DYNAMO_TABLE_NAME = "${var.dynamodb_table_name}"
    }
  }
}
