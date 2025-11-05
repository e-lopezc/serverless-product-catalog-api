# API Gateway Testing Guide

This guide provides realistic testing procedures for the Product Catalog API after Terraform deployment.

## Prerequisites

- Terraform deployed successfully
- AWS CLI configured with appropriate credentials
- `curl` and `jq` installed for API testing

## 1. Extract API Endpoint

```bash
cd terraform/environments/dev
export API_URL=$(terraform output -raw api_gateway_invoke_url)
echo "API URL: $API_URL"
```

## 2. Quick Smoke Test

Test that the API is responding:

```bash
# Should return empty list initially
curl -s -X GET "$API_URL/brands" | jq '.'
curl -s -X GET "$API_URL/categories" | jq '.'
curl -s -X GET "$API_URL/products" | jq '.'
```

## 3. Realistic Workflow Test

Products require brands and categories, so test in order:

### Step 1: Create a Brand

```bash
curl -s -X POST "$API_URL/brands" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Nike",
    "description": "Athletic apparel and footwear"
  }' | jq '.'
```

Save the `brand_id` from the response:
```bash
export BRAND_ID="<brand_id_from_response>"
```

### Step 2: Create a Category

```bash
curl -s -X POST "$API_URL/categories" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Shoes",
    "description": "Footwear category"
  }' | jq '.'
```

Save the `category_id` from the response:
```bash
export CATEGORY_ID="<category_id_from_response>"
```

### Step 3: Create a Product

Now create a product with the brand and category:

```bash
curl -s -X POST "$API_URL/products" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Air Max 90\",
    \"description\": \"Classic Nike sneakers\",
    \"price\": 129.99,
    \"brand_id\": \"$BRAND_ID\",
    \"category_id\": \"$CATEGORY_ID\",
    \"stock_quantity\": 100,
    \"sku\": \"NIKE-AM90-001\"
  }" | jq '.'
```

Save the `product_id`:
```bash
export PRODUCT_ID="<product_id_from_response>"
```

### Step 4: Test Product Operations

```bash
# Get product by ID
curl -s -X GET "$API_URL/products/$PRODUCT_ID" | jq '.'

# Update product price
curl -s -X PUT "$API_URL/products/$PRODUCT_ID" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Air Max 90\",
    \"description\": \"Classic Nike sneakers - Updated\",
    \"price\": 139.99,
    \"brand_id\": \"$BRAND_ID\",
    \"category_id\": \"$CATEGORY_ID\",
    \"stock_quantity\": 100,
    \"sku\": \"NIKE-AM90-001\"
  }" | jq '.'

# Update stock (PATCH)
curl -s -X PATCH "$API_URL/products/$PRODUCT_ID/stock" \
  -H "Content-Type: application/json" \
  -d '{"stock_quantity": 75}' | jq '.'

# List all products
curl -s -X GET "$API_URL/products" | jq '.'

# Get products by brand
curl -s -X GET "$API_URL/products/by-brand/$BRAND_ID" | jq '.'

# Get products by category
curl -s -X GET "$API_URL/products/by-category/$CATEGORY_ID" | jq '.'
```


### Step 5: Cleanup (Optional)

```bash
# Delete in reverse order
curl -s -X DELETE "$API_URL/products/$PRODUCT_ID" | jq '.'
curl -s -X DELETE "$API_URL/categories/$CATEGORY_ID" | jq '.'
curl -s -X DELETE "$API_URL/brands/$BRAND_ID" | jq '.'
```

## 4. Automated Test Script

Use the e2e test script:

```bash
# Set the API URL
export API_BASE_URL=$API_URL

# Run the test
python3 tests/e2e/run_all_e2e_tests.py
```

Or run tests individually:

```bash
python3 tests/e2e/test_brands_e2e.py
python3 tests/e2e/test_categories_e2e.py
python3 tests/e2e/test_products_e2e.py
```

## 5. Monitoring

### View API Gateway Logs

```bash
aws logs tail "/aws/apigateway/dev-product-catalog-api" --follow
```

### View Lambda Logs

```bash
# Products handler
aws logs tail "/aws/lambda/dev-products-handler" --follow

# Brands handler
aws logs tail "/aws/lambda/dev-brands-handler" --follow

# Categories handler
aws logs tail "/aws/lambda/dev-categories-handler" --follow
```

## 6. Common Issues

### 400 Bad Request: "Brand ID is required"
Products require a brand_id. Create a brand first (see Step 1 above).

### 400 Bad Request: "Category ID is required"
Products require a category_id. Create a category first (see Step 2 above).

### 403 Forbidden
Check Lambda permissions:
```bash
aws lambda get-policy --function-name dev-products-handler
```

### 502 Bad Gateway
Check Lambda function logs for errors:
```bash
aws logs tail "/aws/lambda/dev-products-handler" --since 5m
```

### CORS Errors (from browser)
CORS is configured for `*` in dev environment. Check preflight:
```bash
curl -X OPTIONS "$API_URL/products" \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -v
```

## 7. Quick Reference

### All Routes

**Brands:**
- `GET /brands` - List all brands
- `POST /brands` - Create brand
- `GET /brands/{id}` - Get brand
- `PUT /brands/{id}` - Update brand
- `DELETE /brands/{id}` - Delete brand

**Categories:**
- `GET /categories` - List all categories
- `POST /categories` - Create category
- `GET /categories/{id}` - Get category
- `PUT /categories/{id}` - Update category
- `DELETE /categories/{id}` - Delete category

**Products:**
- `GET /products` - List all products
- `POST /products` - Create product (requires brand_id & category_id)
- `GET /products/{id}` - Get product
- `PUT /products/{id}` - Update product
- `DELETE /products/{id}` - Delete product
- `PATCH /products/{id}/stock` - Update stock quantity
- `GET /products/by-brand/{brand_id}` - List products by brand
- `GET /products/by-category/{category_id}` - List products by category

### Required Fields

**Brand:**
```json
{
  "name": "string (required)",
  "description": "string (optional)"
}
```

**Category:**
```json
{
  "name": "string (required)",
  "description": "string (optional)"
}
```

**Product:**
```json
{
  "name": "string (required)",
  "description": "string (optional)",
  "price": "number (required)",
  "brand_id": "string (required)",
  "category_id": "string (required)",
  "stock_quantity": "number (required)",
  "sku": "string (required)"
}
```
