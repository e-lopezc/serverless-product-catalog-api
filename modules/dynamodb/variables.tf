variable "environment" {
  description = "environment (dev, staging, prod)"
  type        = string
}

variable "managed_by" {
  description = "managed by tag for the resource"
  type        = string
  default     = "terraform"
}

variable "table_name" {
  description = "The name of the DynamoDB table"
  type        = string
}

variable "billing_mode" {
  description = "Controls how we are charged for read and write throughput. Values are PROVISIONED or PAY_PER_REQUEST"
  type        = string
  default     = "PAY_PER_REQUEST"
}

variable "read_capacity_units" {
  description = "The number of read units for this table. If the billing_mode is PROVISIONED, this field is required"
  type        = number
  default     = null
}

variable "write_capacity_units" {
  description = "The number of write units for this table. If the billing_mode is PROVISIONED, this field is required"
  type        = number
  default     = null
}

variable "attribute_definitions" {
  description = "List of attribute definitions"
  type = list(object({
    name = string
    type = string
  }))
}

variable "global_secondary_indexes" {
  description = "List of global secondary indexes for the DynamoDB table"
  type = list(object({
    name            = string
    hash_key        = string
    range_key       = string
    projection_type = string
    read_capacity   = optional(number)
    write_capacity  = optional(number)
  }))
  default = []
}

variable "hash_key" {
  description = "The name of the hash key attribute"
  type        = string
  validation {
    condition     = var.has_key != null && var.kash_key != ""
    error_message = "hash_key must not be null or empty."
  }
}

variable "range_key" {
  description = "The name of the range key attribute (optional)"
  type        = string
  default     = null
}


variable "point_in_time_recovery" {
  description = "point in time recovery. Values true or false"
  type        = bool
  default     = false
}


variable "server_side_encryption" {
  description = "point in time recovery. Values true or false"
  type        = bool
  default     = false
}
