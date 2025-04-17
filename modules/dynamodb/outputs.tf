output "dynamodb_table_id" {
  description = "ID of the DynamoDB table"
  value       = aws_dynamodb_table.mycv_website_visitors.id
}

output "dynamodb_table_name" {
  value = aws_dynamodb_table.products_catalog_table.name
}

output "dynamodb_table_arn" {
  description = "arn of the DynamoDB table"
  value       = aws_dynamodb_table.products_catalog_table.arn
}
