# Tests

This directory contains tests for the serverless product catalog API.

## Directory Structure

```
tests/
├── README.md                    # This file
├── integration/                 # Integration tests requiring DynamoDB
│   ├── test_brand_integration.py
│   ├── test_category_integration.py
│   └── test_product_integration.py
├── e2e/                        # End-to-end tests calling API endpoints
│   ├── README.md               # E2E tests documentation
│   ├── run_all_e2e_tests.py    # Comprehensive E2E test runner
│   ├── test_brands_e2e.py      # Brands API E2E tests
│   ├── test_categories_e2e.py  # Categories API E2E tests
│   └── test_products_e2e.py    # Products API E2E tests
└── unit/                       # Unit tests (future)
```

## Integration Tests

The integration tests in the `integration/` directory test the complete functionality of the API models and services against a real DynamoDB instance. These tests:

- Test CRUD operations for brands, categories, and products
- Validate business logic and data validation
- Test relationships between entities
- Require DynamoDB Local or AWS DynamoDB to run

## End-to-End Tests

The end-to-end tests in the `e2e/` directory test the complete deployed system by making HTTP requests to the actual API Gateway endpoints. These tests:

- Test the full request/response cycle
- Verify API Gateway routing and Lambda execution
- Test against the deployed DynamoDB table
- Validate complete system integration
- Test error handling at the API level
- Require a deployed API instance to run

### Prerequisites

1. **DynamoDB Local** (recommended for local development):
   ```bash
   # Download and run DynamoDB Local
   java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -sharedDb
   ```

2. **Create the table** (if using DynamoDB Local):
   ```bash
   # Use the Terraform configuration or AWS CLI to create the table
   ```

3. **Environment Variables**:
   The tests automatically set these environment variables:
   - `DYNAMODB_TABLE=products_catalog`
   - `AWS_REGION=us-east-1` 
   - `DYNAMODB_ENDPOINT=http://localhost:8000` (for local testing)

### Running Integration Tests

```bash
# Run individual test files
python tests/integration/test_brand_integration.py
python tests/integration/test_category_integration.py
python tests/integration/test_product_integration.py

# Or run all integration tests
python -m pytest tests/integration/ -v
```

### Running End-to-End Tests

**Prerequisites:**
- Deployed API instance
- API Gateway URL

**Setup:**
```bash
# Set your deployed API URL
export API_BASE_URL=https://your-api-id.execute-api.region.amazonaws.com/stage

# Install requests library
pip install requests
```

**Run all E2E tests:**
```bash
python tests/e2e/run_all_e2e_tests.py
```

**Run individual E2E test suites:**
```bash
python tests/e2e/test_brands_e2e.py
python tests/e2e/test_categories_e2e.py
python tests/e2e/test_products_e2e.py
```

### Test Coverage

**Brand Integration Tests:**
- Create brand with validation
- Get brand by ID
- Update brand (name, description, website)
- List brands with pagination
- Delete brand
- Duplicate name validation
- Input validation (empty names, invalid URLs)

**Category Integration Tests:**
- Create category with validation
- Get category by ID
- Update category (name, description)
- List categories with pagination
- Delete category
- Duplicate name validation
- Input validation (empty names, short descriptions)

**Product Integration Tests:**
- Create product with brand and category relationships
- Get product by ID
- Update product details
- Stock management (absolute updates and relative adjustments)
- List products (all, by brand, by category)
- Delete product
- Validation for prices, stock quantities, images
- Foreign key validation (brand_id, category_id must exist)

## E2E Test Coverage

**Brands E2E Tests:**
- Full CRUD operations via HTTP API
- GET/POST /brands, GET/PUT/DELETE /brands/{id}
- Pagination testing with query parameters
- API-level validation and error responses
- Response format validation

**Categories E2E Tests:**
- Full CRUD operations via HTTP API  
- GET/POST /categories, GET/PUT/DELETE /categories/{id}
- Pagination testing with query parameters
- API-level validation and error responses
- Response format validation

**Products E2E Tests:**
- Full CRUD operations via HTTP API
- GET/POST /products, GET/PUT/DELETE /products/{id}
- Specialized endpoints (by-brand, by-category, stock updates)
- PATCH /products/{id}/stock for inventory management
- Cross-entity relationship testing
- API-level validation and error responses

## Running Tests in CI/CD

For automated testing in CI/CD pipelines, consider:

1. **Using DynamoDB Local in Docker**:
   ```bash
   docker run -p 8000:8000 amazon/dynamodb-local
   ```

2. **Using AWS DynamoDB with test tables**:
   - Create temporary test tables
   - Clean up after tests complete

3. **Environment Variables for CI**:
   ```bash
   export DYNAMODB_TABLE=test_products_catalog
   export AWS_REGION=us-east-1
   export DYNAMODB_ENDPOINT=http://localhost:8000  # For local DynamoDB
   ```

## Future Enhancements

- **Unit Tests**: Add unit tests for individual functions without external dependencies
- **API Tests**: Add tests for the Lambda handlers and API Gateway integration
- **Performance Tests**: Add tests for performance under load
- **Test Fixtures**: Create reusable test data fixtures
- **Test Cleanup**: Automatic cleanup of test data
- **Mocking**: Mock DynamoDB for faster unit tests

## Notes

### Integration Tests
- Create and delete real data in DynamoDB
- Include their own cleanup logic
- Are designed to be idempotent (can be run multiple times)
- Each test file can be run independently
- Validate both success and error scenarios

### End-to-End Tests
- Test against deployed API endpoints
- Create and delete real data via API calls
- Include automatic cleanup of test data
- Require network connectivity to deployed API
- Test the complete request/response cycle
- Can be used for deployment validation

## Test Types Comparison

| Feature | Integration Tests | E2E Tests |
|---------|------------------|-----------|
| **Target** | Models & Services | HTTP API Endpoints |
| **Requirements** | DynamoDB Local/AWS | Deployed API |
| **Speed** | Fast | Slower (network calls) |
| **Scope** | Business logic | Full system |
| **Best for** | Development | Deployment validation |
| **Data access** | Direct DB calls | HTTP requests |