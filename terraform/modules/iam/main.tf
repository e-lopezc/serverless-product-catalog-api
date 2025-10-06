# Get current AWS region and account ID
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}
