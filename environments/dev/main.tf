# main dev
module "dynamodb_backend_table" {
  source                   = "../../modules/dynamodb"
  table_name               = var.dynamodb_table_name
  attribute_definitions    = var.dynamodb_attribute_definitions
  global_secondary_indexes = var.dynamodb_global_secondary_indexes
  hash_key                 = var.dynamodb_table_hash_key
  range_key                = var.dynamodb_table_range_key
}
