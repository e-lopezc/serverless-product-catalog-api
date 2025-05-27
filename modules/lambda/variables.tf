variable "function_name" {
  description = "Name of the lambda function"
  type        = string
}

variable "execution_role_arn" {
  description = "IAM Role arn for the lambda to asume to access the dynamo table"
  type        = string
}

variable "runtime" {
  description = "programming language version for lambda runtime"
  type        = string
}

variable "timeout" {
  description = "Max time of execution for lambda function"
  type        = int

}

variable "dynamodb_table_name" {
  description = "The name of the dynamodb table for lambda to interact with"
  type        = string
}
