# End-to-End Tests

This directory contains end-to-end tests for the serverless product catalog API that test the complete deployed system by making HTTP requests to the actual API Gateway endpoints.

## Overview

The E2E tests verify the entire system functionality including:
- API Gateway routing
- Lambda function execution
- DynamoDB operations
- Error handling and validation
- Response formatting
- Cross-entity relationships

## Directory Structure

```
tests/e2e/
├── README.md                    # This file
├── __init__.py                  
├── run_all_e2e_tests.py        # Comprehensive test runner
├── test_brands_e2e.py          # Brands API E2E tests
├── test_categories_e2e.py      # Categories API E2E tests
└── test_products_e2e.py        # Products API E2E tests
```

## Prerequisites

### 1. Deployed API

You need a deployed instance of the serverless product catalog API. Deploy using:

```bash
# Using SAM
sam build
sam deploy --guided

# Or using your preferred deployment method
```

### 2. API Base URL

Get your API Gateway URL from the deployment output or AWS Console:
```
https://your-api-id.execute-api.region.amazonaws.com/stage
```

### 3. Python Dependencies

Install required dependencies:
```bash
pip install requests
```

## Running E2E Tests

### Environment Setup

Set the API base URL:
```bash
export API_BASE_URL=https://your-api-id.execute-api.region.amazonaws.com/dev
```

### Run All Tests

Use the comprehensive test runner:
```bash
python tests/e2e/run_all_e2e_tests.py
```

This will:
1. Perform API health checks
2. Run a smoke test
3. Execute all E2E test suites in order
4. Provide detailed results and summary

### Run Individual Test Suites

Run specific test suites:
```bash
# Test brands API
python tests/e2e/test_brands_e2e.py

# Test categories API  
python tests/e2e/test_categories_e2e.py

# Test products API
python tests/e2e/test_products_e2e.py
```

## Test Coverage

### Brands API Tests (`test_brands_e2e.py`)

**CRUD Operations:**
- ✅ CREATE brand (POST /brands)
- ✅ GET brand by ID (GET /brands/{id})
- ✅ LIST all brands (GET /brands)
- ✅ UPDATE brand (PUT /brands/{id})
- ✅ DELETE brand (DELETE /brands/{id})

**Additional Features:**
- ✅ Pagination support
- ✅ Input validation (empty names, invalid URLs)
- ✅ Duplicate name prevention
- ✅ Error handling (404, 400, 409)

### Categories API Tests (`test_categories_e2e.py`)

**CRUD Operations:**
- ✅ CREATE category (POST /categories)
- ✅ GET category by ID (GET /categories/{id})
- ✅ LIST all categories (GET /categories)
- ✅ UPDATE category (PUT /categories/{id})
- ✅ DELETE category (DELETE /categories/{id})

**Additional Features:**
- ✅ Pagination support
- ✅ Input validation (empty names, short descriptions)
- ✅ Duplicate name prevention
- ✅ Error handling (404, 400, 409)

### Products API Tests (`test_products_e2e.py`)

**CRUD Operations:**
- ✅ CREATE product (POST /products)
- ✅ GET product by ID (GET /products/{id})
- ✅ LIST all products (GET /products)
- ✅ UPDATE product (PUT /products/{id})
- ✅ DELETE product (DELETE /products/{id})

**Specialized Endpoints:**
- ✅ LIST products by brand (GET /products/by-brand/{brand_id})
- ✅ LIST products by category (GET /products/by-category/{category_id})
- ✅ UPDATE stock (PATCH /products/{id}/stock)
  - Absolute stock updates
  - Relative stock adjustments

**Additional Features:**
- ✅ Pagination support
- ✅ Input validation (prices, stock, images, foreign keys)
- ✅ Relationship validation (brand_id and category_id must exist)
- ✅ Error handling (404, 400)

## Test Data Management

### Automatic Cleanup
- All tests include automatic cleanup of created data
- Tests track created resources and delete them after completion
- Cleanup runs even if tests fail or are interrupted

### Test Isolation
- Each test file can run independently
- Tests create their own test data
- No dependencies between test files
- Products tests create their own brands and categories

## Sample Test Output

```
🧪 Starting Comprehensive End-to-End Test Suite
================================================================================
🔗 API Base URL: https://abc123.execute-api.us-east-1.amazonaws.com/dev
📝 Test Files: test_brands_e2e.py, test_categories_e2e.py, test_products_e2e.py

🔍 Checking API health...
   https://abc123.execute-api.us-east-1.amazonaws.com/dev/brands: 200
   https://abc123.execute-api.us-east-1.amazonaws.com/dev/categories: 200
   https://abc123.execute-api.us-east-1.amazonaws.com/dev/products: 200
✅ API is accessible

🚀 Running smoke test...
✅ Smoke test passed

🚀 Running 3 test suites...

================================================================================
🧪 Running BRANDS E2E Tests
📁 File: test_brands_e2e.py
================================================================================

1. Testing CREATE brand (POST /brands)
   Status Code: 201
✅ Brand created successfully: abc-123-def

[... detailed test output ...]

✅ BRANDS tests PASSED (15.23s)

================================================================================
📊 END-TO-END TEST SUMMARY
================================================================================
📈 Overall Results:
   Total test suites: 3
   ✅ Passed: 3
   ❌ Failed: 0
   ⏱️  Total duration: 45.67 seconds
   🎯 Success rate: 100.0%

🎉 ALL END-TO-END TESTS PASSED!
```

## Troubleshooting

### Common Issues

**1. API_BASE_URL not set**
```bash
❌ API_BASE_URL environment variable not set
```
Solution: Export the correct API Gateway URL

**2. API not accessible**
```bash
❌ Failed to reach https://your-api.com/brands: Connection error
```
Solutions:
- Verify the API is deployed
- Check the URL is correct
- Ensure the API is publicly accessible
- Check AWS region settings

**3. Authentication errors**
```bash
❌ Failed to create brand: 403
```
Solution: If your API requires authentication, add auth headers to the test sessions

**4. Timeout errors**
```bash
⏰ PRODUCTS tests TIMED OUT (> 5 minutes)
```
Solutions:
- Check for cold start delays
- Verify DynamoDB performance
- Increase timeout in test configuration

### Test Debugging

Enable verbose output:
```bash
# Add debug prints to individual test files
python tests/e2e/test_brands_e2e.py
```

Check API logs:
```bash
# View CloudWatch logs for your Lambda functions
sam logs -n BrandsFunction --tail
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: E2E Tests
on: [push, pull_request]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v3
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install requests
      
      - name: Deploy API (if needed)
        run: |
          # Your deployment commands here
          sam build && sam deploy --no-confirm-changeset
      
      - name: Run E2E Tests
        env:
          API_BASE_URL: ${{ secrets.API_BASE_URL }}
        run: python tests/e2e/run_all_e2e_tests.py
```

## Performance Considerations

- Tests may be slower than unit tests due to network calls
- Cold starts can affect initial test performance
- Consider running tests against a warm API
- Database operations may have eventual consistency delays

## Security Notes

- Tests create and delete real data in your DynamoDB table
- Ensure your test environment is isolated from production
- Be aware of API rate limits
- Consider using separate AWS accounts for testing

## Contributing

When adding new E2E tests:

1. **Follow the existing pattern**: Use the same structure as existing test files
2. **Include cleanup**: Always clean up created test data
3. **Test error cases**: Include validation and error scenarios
4. **Add to runner**: Update `run_all_e2e_tests.py` if adding new test files
5. **Document coverage**: Update this README with new test coverage

## Future Enhancements

- **Authentication tests**: Add tests for API authentication if implemented
- **Performance tests**: Add load testing and performance validation
- **Data validation**: More comprehensive data integrity checks
- **Edge cases**: Additional boundary condition testing
- **Monitoring integration**: Integration with application monitoring