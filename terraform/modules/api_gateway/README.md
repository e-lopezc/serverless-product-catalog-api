# API Gateway HTTP API Module

## Overview
This module creates an AWS HTTP API Gateway (v2) for serverless applications. HTTP API is optimized for Lambda proxy integrations and is 70% cheaper than REST API.

## Features
- **HTTP API (v2)**: Cost-effective alternative to REST API
- **Lambda Proxy Integration**: Direct pass-through of requests to Lambda
- **Built-in CORS**: Simple CORS configuration
- **Auto-deployment**: Automatic deployment of API changes
- **CloudWatch Logging**: Access logs for monitoring and debugging
- **Throttling**: Rate limiting to prevent runaway costs
- **Multiple Routes**: Supports full CRUD operations (GET, POST, PUT, PATCH, DELETE)

## Usage

```hcl
module "api_gateway" {
  source = "../../modules/api_gateway"

  environment = "dev"
  api_name    = "product-catalog-api"

  lambda_function_names = {
    brands     = "dev-brands"
    categories = "dev-categories"
    products   = "dev-products"
  }

  lambda_invoke_arns = {
    brands     = module.lambda_functions.lambda_function_invoke_arns["brands"]
    categories = module.lambda_functions.lambda_function_invoke_arns["categories"]
    products   = module.lambda_functions.lambda_function_invoke_arns["products"]
  }

  # Optional: Override defaults
  stage_name          = "$default"
  enable_auto_deploy  = true
  enable_access_logs  = true
  log_retention_days  = 7

  cors_configuration = {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    allow_headers = ["Content-Type", "Authorization"]
    max_age       = 300
  }

  throttle_settings = {
    burst_limit = 100
    rate_limit  = 50
  }
}
```

## Routes Created

For each Lambda function, the module creates these routes:
- `GET /resource` - List all items
- `POST /resource` - Create new item
- `GET /resource/{id}` - Get item by ID
- `PUT /resource/{id}` - Update entire item
- `DELETE /resource/{id}` - Delete item
- `PATCH /resource/{id}` - Partial update

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| environment | Deployment environment | string | - | yes |
| api_name | Name of the API Gateway | string | - | yes |
| lambda_function_names | Map of Lambda function names | map(string) | - | yes |
| lambda_invoke_arns | Map of Lambda invoke ARNs | map(string) | - | yes |
| api_description | API description | string | "Product Catalog HTTP API" | no |
| stage_name | Stage name | string | "$default" | no |
| enable_auto_deploy | Auto-deploy changes | bool | true | no |
| enable_access_logs | Enable CloudWatch logs | bool | true | no |
| log_retention_days | Log retention in days | number | 7 | no |
| cors_configuration | CORS settings | object | See variables.tf | no |
| throttle_settings | Throttle limits | object | { burst_limit = 100, rate_limit = 50 } | no |

## Outputs

| Name | Description |
|------|-------------|
| api_id | API Gateway ID |
| api_endpoint | Base API endpoint URL |
| api_invoke_url | Full invoke URL (with stage) |
| api_arn | API Gateway ARN |
| stage_name | Stage name |
| cloudwatch_log_group_name | CloudWatch log group name |

## Cost Optimization

1. **HTTP API vs REST API**: 70% cheaper ($1.00 vs $3.50 per million requests)
2. **Short log retention**: 7 days default (adjustable)
3. **No caching**: Caching disabled (costs extra)
4. **Regional endpoint**: Cheaper than edge-optimized
5. **Throttling**: Prevents unexpected bills from API abuse

## Best Practices Implemented

1. **Resource-based permissions**: Uses `aws_lambda_permission` instead of IAM roles
2. **Auto-deployment**: Simplifies CI/CD workflows
3. **Structured logging**: JSON format for easy parsing
4. **CORS enabled**: Ready for web application integration
5. **Throttling**: Protection against cost overruns

## Example API Endpoints

After deployment, your API will have endpoints like:
```
https://abc123.execute-api.us-east-1.amazonaws.com/brands
https://abc123.execute-api.us-east-1.amazonaws.com/brands/123
https://abc123.execute-api.us-east-1.amazonaws.com/products
https://abc123.execute-api.us-east-1.amazonaws.com/products/456
```

## Notes

- HTTP API doesn't support API keys, request validation, or caching (use REST API if needed)
- The `$default` stage auto-deploys changes without manual deployment
- Lambda functions must handle HTTP method routing internally
- CORS is handled by API Gateway, not Lambda
