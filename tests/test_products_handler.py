import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Import the handler function and related modules
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from handlers.products import lambda_handler
from utils.exceptions import ValidationError, NotFoundError, DuplicateError


class TestProductsHandler:
    """Test class for products Lambda handler"""

    def setup_method(self):
        """Setup method run before each test"""
        self.mock_context = Mock()
        self.mock_context.function_name = "products-handler"
        self.mock_context.function_version = "1"
        self.mock_context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:products-handler"

    def create_api_gateway_event(
        self,
        http_method: str,
        path_parameters: Dict[str, str] = None,
        query_string_parameters: Dict[str, str] = None,
        body: str = None,
        resource_path: str = "/products"
    ) -> Dict[str, Any]:
        """Helper method to create API Gateway event"""
        return {
            'httpMethod': http_method,
            'pathParameters': path_parameters,
            'queryStringParameters': query_string_parameters,
            'body': body,
            'resource': resource_path,
            'headers': {
                'Content-Type': 'application/json'
            }
        }

    @patch('handlers.products.ProductService')
    def test_get_products_list_success(self, mock_product_service):
        """Test successful GET /products request"""
        # Arrange
        mock_products_data = {
            'items': [
                {
                    'product_id': 'test-product-1',
                    'name': 'Test Product 1',
                    'brand_id': 'brand-1',
                    'category_id': 'category-1',
                    'price': 99.99,
                    'description': 'First test product',
                    'stock_quantity': 10,
                    'images': ['https://example.com/image1.jpg']
                },
                {
                    'product_id': 'test-product-2',
                    'name': 'Test Product 2',
                    'brand_id': 'brand-2',
                    'category_id': 'category-2',
                    'price': 149.99,
                    'description': 'Second test product',
                    'stock_quantity': 5,
                    'images': []
                }
            ],
            'last_evaluated_key': None
        }
        mock_product_service.list_products.return_value = mock_products_data

        event = self.create_api_gateway_event('GET')

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 200
        assert 'application/json' in response['headers']['Content-Type']

        body = json.loads(response['body'])
        assert body['message'] == 'Success'
        assert body['data'] == mock_products_data

        mock_product_service.list_products.assert_called_once_with(50, None)

    @patch('handlers.products.ProductService')
    def test_get_products_list_with_pagination(self, mock_product_service):
        """Test GET /products with pagination parameters"""
        # Arrange
        mock_products_data = {
            'items': [{'product_id': 'test-product-1', 'name': 'Test Product 1', 'stock_quantity': 15}],
            'last_evaluated_key': {'PK': 'PRODUCT#test-product-1', 'SK': 'PRODUCT#test-product-1'}
        }
        mock_product_service.list_products.return_value = mock_products_data

        last_key = json.dumps({'PK': 'PRODUCT#prev', 'SK': 'PRODUCT#prev'})
        event = self.create_api_gateway_event(
            'GET',
            query_string_parameters={'limit': '25', 'last_key': last_key}
        )

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 200
        mock_product_service.list_products.assert_called_once_with(
            25, {'PK': 'PRODUCT#prev', 'SK': 'PRODUCT#prev'}
        )

    @patch('handlers.products.ProductService')
    def test_get_products_list_invalid_last_key(self, mock_product_service):
        """Test GET /products with invalid last_key format"""
        # Arrange
        event = self.create_api_gateway_event(
            'GET',
            query_string_parameters={'last_key': 'invalid-json'}
        )

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'Invalid last_key format' in body['message']
        mock_product_service.list_products.assert_not_called()

    @patch('handlers.products.ProductService')
    def test_get_product_by_id_success(self, mock_product_service):
        """Test successful GET /products/{id} request"""
        # Arrange
        product_id = 'test-product-123'
        mock_product = {
            'product_id': product_id,
            'name': 'Test Product',
            'brand_id': 'brand-123',
            'category_id': 'category-123',
            'price': 199.99,
            'description': 'A test product for testing',
            'stock_quantity': 20,
            'images': ['https://example.com/test.jpg']
        }
        mock_product_service.get_product.return_value = mock_product

        event = self.create_api_gateway_event('GET', path_parameters={'id': product_id})

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['data'] == mock_product
        mock_product_service.get_product.assert_called_once_with(product_id)

    @patch('handlers.products.ProductService')
    def test_get_product_by_id_not_found(self, mock_product_service):
        """Test GET /products/{id} when product doesn't exist"""
        # Arrange
        product_id = 'non-existent-product'
        mock_product_service.get_product.return_value = None

        event = self.create_api_gateway_event('GET', path_parameters={'id': product_id})

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert body['message'] == 'Product not found'
        mock_product_service.get_product.assert_called_once_with(product_id)

    @patch('handlers.products.ProductService')
    def test_create_product_success(self, mock_product_service):
        """Test successful POST /products request"""
        # Arrange
        product_data = {
            'name': 'New Test Product',
            'brand_id': 'brand-123',
            'category_id': 'category-123',
            'price': 299.99,
            'description': 'A new test product description',
            'stock_quantity': 25,
            'images': ['https://example.com/new-product.jpg']
        }
        created_product = {
            'product_id': 'new-product-123',
            **product_data,
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-01T00:00:00Z'
        }
        mock_product_service.create_product.return_value = created_product

        event = self.create_api_gateway_event('POST', body=json.dumps(product_data))

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 201
        body = json.loads(response['body'])
        assert body['message'] == 'Product created successfully'
        assert body['data'] == created_product
        mock_product_service.create_product.assert_called_once_with(product_data)

    @patch('handlers.products.ProductService')
    def test_create_product_validation_error(self, mock_product_service):
        """Test POST /products with validation error"""
        # Arrange
        invalid_product_data = {
            'name': '',  # Empty name should fail validation
            'brand_id': 'brand-123',
            'category_id': 'category-123',
            'price': 99.99,
            'stock_quantity': 10
        }
        mock_product_service.create_product.side_effect = ValidationError("Product name is required")

        event = self.create_api_gateway_event('POST', body=json.dumps(invalid_product_data))

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['message'] == 'Product name is required'
        mock_product_service.create_product.assert_called_once_with(invalid_product_data)

    @patch('handlers.products.ProductService')
    def test_create_product_not_found_error(self, mock_product_service):
        """Test POST /products with brand/category not found error"""
        # Arrange
        product_data = {
            'name': 'Test Product',
            'brand_id': 'non-existent-brand',
            'category_id': 'category-123',
            'price': 99.99,
            'stock_quantity': 5
        }
        mock_product_service.create_product.side_effect = NotFoundError("Brand with ID 'non-existent-brand' not found")

        event = self.create_api_gateway_event('POST', body=json.dumps(product_data))

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert "Brand with ID 'non-existent-brand' not found" in body['message']
        mock_product_service.create_product.assert_called_once_with(product_data)

    @patch('handlers.products.ProductService')
    def test_create_product_invalid_json(self, mock_product_service):
        """Test POST /products with invalid JSON body"""
        # Arrange
        event = self.create_api_gateway_event('POST', body='invalid-json{')

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'Invalid JSON' in body['message']
        mock_product_service.create_product.assert_not_called()

    @patch('handlers.products.ProductService')
    def test_update_product_success(self, mock_product_service):
        """Test successful PUT /products/{id} request"""
        # Arrange
        product_id = 'test-product-123'
        update_data = {
            'name': 'Updated Product Name',
            'price': 199.99,
            'stock_quantity': 30
        }
        updated_product = {
            'product_id': product_id,
            **update_data,
            'brand_id': 'brand-123',
            'category_id': 'category-123',
            'description': 'Original description',
            'updated_at': '2024-01-01T12:00:00Z'
        }
        mock_product_service.update_product.return_value = updated_product

        event = self.create_api_gateway_event(
            'PUT',
            path_parameters={'id': product_id},
            body=json.dumps(update_data)
        )

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['message'] == 'Product updated successfully'
        assert body['data'] == updated_product
        mock_product_service.update_product.assert_called_once_with(product_id, update_data)

    @patch('handlers.products.ProductService')
    def test_update_product_not_found(self, mock_product_service):
        """Test PUT /products/{id} when product doesn't exist"""
        # Arrange
        product_id = 'non-existent-product'
        update_data = {'name': 'Updated Name', 'stock_quantity': 15}
        mock_product_service.update_product.return_value = None

        event = self.create_api_gateway_event(
            'PUT',
            path_parameters={'id': product_id},
            body=json.dumps(update_data)
        )

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert body['message'] == 'Product not found'
        mock_product_service.update_product.assert_called_once_with(product_id, update_data)

    @patch('handlers.products.ProductService')
    def test_update_product_missing_id(self, mock_product_service):
        """Test PUT /products/{id} without product ID"""
        # Arrange
        update_data = {'name': 'Updated Name', 'stock_quantity': 8}
        event = self.create_api_gateway_event('PUT', body=json.dumps(update_data))

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['message'] == 'Product ID is required'
        mock_product_service.update_product.assert_not_called()

    @patch('handlers.products.ProductService')
    def test_delete_product_success(self, mock_product_service):
        """Test successful DELETE /products/{id} request"""
        # Arrange
        product_id = 'test-product-123'
        mock_product_service.delete_product.return_value = True

        event = self.create_api_gateway_event('DELETE', path_parameters={'id': product_id})

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['message'] == 'Product deleted successfully'
        mock_product_service.delete_product.assert_called_once_with(product_id)

    @patch('handlers.products.ProductService')
    def test_delete_product_not_found(self, mock_product_service):
        """Test DELETE /products/{id} when product doesn't exist"""
        # Arrange
        product_id = 'non-existent-product'
        mock_product_service.delete_product.return_value = False

        event = self.create_api_gateway_event('DELETE', path_parameters={'id': product_id})

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert body['message'] == 'Product not found'
        mock_product_service.delete_product.assert_called_once_with(product_id)

    @patch('handlers.products.ProductService')
    def test_delete_product_missing_id(self, mock_product_service):
        """Test DELETE /products/{id} without product ID"""
        # Arrange
        event = self.create_api_gateway_event('DELETE')

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['message'] == 'Product ID is required'
        mock_product_service.delete_product.assert_not_called()

    @patch('handlers.products.ProductService')
    def test_get_products_by_brand_success(self, mock_product_service):
        """Test successful GET /products/by-brand/{brand_id} request"""
        # Arrange
        brand_id = 'test-brand-123'
        mock_products_data = {
            'items': [
                {
                    'product_id': 'product-1',
                    'name': 'Brand Product 1',
                    'brand_id': brand_id,
                    'stock_quantity': 12
                },
                {
                    'product_id': 'product-2',
                    'name': 'Brand Product 2',
                    'brand_id': brand_id,
                    'stock_quantity': 8
                }
            ],
            'last_evaluated_key': None
        }
        mock_product_service.list_products_by_brand.return_value = mock_products_data

        event = self.create_api_gateway_event(
            'GET',
            path_parameters={'brand_id': brand_id},
            resource_path='/products/by-brand/{brand_id}'
        )

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['data'] == mock_products_data
        mock_product_service.list_products_by_brand.assert_called_once_with(brand_id, 50, None)

    @patch('handlers.products.ProductService')
    def test_get_products_by_brand_missing_id(self, mock_product_service):
        """Test GET /products/by-brand/{brand_id} without brand ID"""
        # Arrange
        event = self.create_api_gateway_event(
            'GET',
            resource_path='/products/by-brand/{brand_id}'
        )

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['message'] == 'Brand ID is required'
        mock_product_service.list_products_by_brand.assert_not_called()

    @patch('handlers.products.ProductService')
    def test_get_products_by_category_success(self, mock_product_service):
        """Test successful GET /products/by-category/{category_id} request"""
        # Arrange
        category_id = 'test-category-123'
        mock_products_data = {
            'items': [
                {
                    'product_id': 'product-1',
                    'name': 'Category Product 1',
                    'category_id': category_id,
                    'stock_quantity': 18
                },
                {
                    'product_id': 'product-2',
                    'name': 'Category Product 2',
                    'category_id': category_id,
                    'stock_quantity': 22
                }
            ],
            'last_evaluated_key': None
        }
        mock_product_service.list_products_by_category.return_value = mock_products_data

        event = self.create_api_gateway_event(
            'GET',
            path_parameters={'category_id': category_id},
            resource_path='/products/by-category/{category_id}'
        )

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['data'] == mock_products_data
        mock_product_service.list_products_by_category.assert_called_once_with(category_id, 50, None)

    @patch('handlers.products.ProductService')
    def test_get_products_by_category_missing_id(self, mock_product_service):
        """Test GET /products/by-category/{category_id} without category ID"""
        # Arrange
        event = self.create_api_gateway_event(
            'GET',
            resource_path='/products/by-category/{category_id}'
        )

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['message'] == 'Category ID is required'
        mock_product_service.list_products_by_category.assert_not_called()

    @patch('handlers.products.ProductService')
    def test_update_stock_absolute_success(self, mock_product_service):
        """Test successful PATCH /products/{id}/stock with absolute stock quantity"""
        # Arrange
        product_id = 'test-product-123'
        stock_data = {'stock_quantity': 50}
        updated_product = {
            'product_id': product_id,
            'name': 'Test Product',
            'stock_quantity': 50,
            'updated_at': '2024-01-01T12:00:00Z'
        }
        mock_product_service.update_stock.return_value = updated_product

        event = self.create_api_gateway_event(
            'PATCH',
            path_parameters={'id': product_id},
            body=json.dumps(stock_data),
            resource_path='/products/{id}/stock'
        )

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['message'] == 'Stock updated successfully'
        assert body['data'] == updated_product
        mock_product_service.update_stock.assert_called_once_with(product_id, 50)

    @patch('handlers.products.ProductService')
    def test_update_stock_relative_success(self, mock_product_service):
        """Test successful PATCH /products/{id}/stock with relative stock adjustment"""
        # Arrange
        product_id = 'test-product-123'
        stock_data = {'quantity_change': -5}
        updated_product = {
            'product_id': product_id,
            'name': 'Test Product',
            'stock_quantity': 15,  # Assuming it was 20, now 15
            'updated_at': '2024-01-01T12:00:00Z'
        }
        mock_product_service.adjust_stock.return_value = updated_product

        event = self.create_api_gateway_event(
            'PATCH',
            path_parameters={'id': product_id},
            body=json.dumps(stock_data),
            resource_path='/products/{id}/stock'
        )

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['message'] == 'Stock adjusted successfully'
        assert body['data'] == updated_product
        mock_product_service.adjust_stock.assert_called_once_with(product_id, -5)

    @patch('handlers.products.ProductService')
    def test_update_stock_missing_product_id(self, mock_product_service):
        """Test PATCH /products/{id}/stock without product ID"""
        # Arrange
        stock_data = {'stock_quantity': 10}
        event = self.create_api_gateway_event(
            'PATCH',
            body=json.dumps(stock_data),
            resource_path='/products/{id}/stock'
        )

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['message'] == 'Product ID is required'
        mock_product_service.update_stock.assert_not_called()
        mock_product_service.adjust_stock.assert_not_called()

    @patch('handlers.products.ProductService')
    def test_update_stock_missing_data(self, mock_product_service):
        """Test PATCH /products/{id}/stock without stock data"""
        # Arrange
        product_id = 'test-product-123'
        event = self.create_api_gateway_event(
            'PATCH',
            path_parameters={'id': product_id},
            body='{}',
            resource_path='/products/{id}/stock'
        )

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['message'] == 'Either stock_quantity or quantity_change is required'
        mock_product_service.update_stock.assert_not_called()
        mock_product_service.adjust_stock.assert_not_called()

    @patch('handlers.products.ProductService')
    def test_update_stock_invalid_data_type(self, mock_product_service):
        """Test PATCH /products/{id}/stock with invalid data types"""
        # Arrange
        product_id = 'test-product-123'
        stock_data = {'stock_quantity': 'not-a-number'}
        event = self.create_api_gateway_event(
            'PATCH',
            path_parameters={'id': product_id},
            body=json.dumps(stock_data),
            resource_path='/products/{id}/stock'
        )

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['message'] == 'stock_quantity must be an integer'
        mock_product_service.update_stock.assert_not_called()

    @patch('handlers.products.ProductService')
    def test_update_stock_product_not_found(self, mock_product_service):
        """Test PATCH /products/{id}/stock when product doesn't exist"""
        # Arrange
        product_id = 'non-existent-product'
        stock_data = {'stock_quantity': 25}
        mock_product_service.update_stock.return_value = None

        event = self.create_api_gateway_event(
            'PATCH',
            path_parameters={'id': product_id},
            body=json.dumps(stock_data),
            resource_path='/products/{id}/stock'
        )

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert body['message'] == 'Product not found'
        mock_product_service.update_stock.assert_called_once_with(product_id, 25)

    @patch('handlers.products.ProductService')
    def test_unsupported_http_method(self, mock_product_service):
        """Test unsupported HTTP method"""
        # Arrange
        event = self.create_api_gateway_event('PATCH')  # PATCH without /stock path

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'Method PATCH not allowed' in body['message']

    @patch('handlers.products.ProductService')
    def test_unexpected_exception(self, mock_product_service):
        """Test handling of unexpected exceptions"""
        # Arrange
        mock_product_service.list_products.side_effect = Exception("Unexpected database error")
        event = self.create_api_gateway_event('GET')

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert body['message'] == 'An unexpected error occurred'

    @patch('handlers.products.ProductService')
    def test_not_found_error_exception(self, mock_product_service):
        """Test handling of NotFoundError exception"""
        # Arrange
        mock_product_service.get_product.side_effect = NotFoundError("Product not found in database")
        event = self.create_api_gateway_event('GET', path_parameters={'id': 'test-product'})

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert body['message'] == 'Product not found in database'

    @patch('handlers.products.ProductService')
    def test_value_error_exception(self, mock_product_service):
        """Test handling of ValueError exception"""
        # Arrange
        mock_product_service.create_product.side_effect = ValueError("Invalid input value")
        event = self.create_api_gateway_event('POST', body='{"name": "Test", "stock_quantity": 5}')

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['message'] == 'Invalid input value'

    def test_cors_headers_present(self):
        """Test that CORS headers are present in all responses"""
        # Arrange
        event = self.create_api_gateway_event('OPTIONS')

        # Act
        with patch('handlers.products.ProductService'):
            response = lambda_handler(event, self.mock_context)

        # Assert
        headers = response['headers']
        assert 'Access-Control-Allow-Origin' in headers
        assert 'Access-Control-Allow-Methods' in headers
        assert 'Access-Control-Allow-Headers' in headers
        assert headers['Access-Control-Allow-Origin'] == '*'

    @patch('handlers.products.ProductService')
    def test_empty_path_parameters(self, mock_product_service):
        """Test handling when pathParameters is None"""
        # Arrange
        event = {
            'httpMethod': 'GET',
            'pathParameters': None,
            'queryStringParameters': None,
            'body': None,
            'resource': '/products'
        }
        mock_product_service.list_products.return_value = {'items': [], 'last_evaluated_key': None}

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 200
        mock_product_service.list_products.assert_called_once()

    @patch('handlers.products.ProductService')
    def test_empty_query_parameters(self, mock_product_service):
        """Test handling when queryStringParameters is None"""
        # Arrange
        event = self.create_api_gateway_event('GET')
        event['queryStringParameters'] = None
        mock_product_service.list_products.return_value = {'items': [], 'last_evaluated_key': None}

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 200
        # Should use default limit (50) and None for last_key
        mock_product_service.list_products.assert_called_once_with(50, None)

    @patch('handlers.products.ProductService')
    def test_empty_body_handling(self, mock_product_service):
        """Test handling when body is None or empty"""
        # Arrange
        event = self.create_api_gateway_event('POST')
        event['body'] = None
        mock_product_service.create_product.return_value = {
            'product_id': 'test',
            'name': 'Test Product',
            'stock_quantity': 0
        }

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 201
        # Should pass empty dict when body is None
        mock_product_service.create_product.assert_called_once_with({})

    @patch('handlers.products.ProductService')
    def test_create_product_with_zero_stock(self, mock_product_service):
        """Test creating product with zero stock quantity"""
        # Arrange
        product_data = {
            'name': 'Out of Stock Product',
            'brand_id': 'brand-123',
            'category_id': 'category-123',
            'price': 99.99,
            'stock_quantity': 0
        }
        created_product = {
            'product_id': 'zero-stock-product',
            **product_data,
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-01T00:00:00Z'
        }
        mock_product_service.create_product.return_value = created_product

        event = self.create_api_gateway_event('POST', body=json.dumps(product_data))

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 201
        body = json.loads(response['body'])
        assert body['data']['stock_quantity'] == 0
        mock_product_service.create_product.assert_called_once_with(product_data)

    @patch('handlers.products.ProductService')
    def test_update_product_stock_only(self, mock_product_service):
        """Test updating only stock quantity of a product"""
        # Arrange
        product_id = 'test-product-123'
        update_data = {'stock_quantity': 100}
        updated_product = {
            'product_id': product_id,
            'name': 'Existing Product',
            'stock_quantity': 100,
            'updated_at': '2024-01-01T12:00:00Z'
        }
        mock_product_service.update_product.return_value = updated_product

        event = self.create_api_gateway_event(
            'PUT',
            path_parameters={'id': product_id},
            body=json.dumps(update_data)
        )

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['data']['stock_quantity'] == 100
        mock_product_service.update_product.assert_called_once_with(product_id, update_data)


# Integration-style tests (still unit tests but testing more end-to-end flow)
class TestProductsHandlerIntegration:
    """Integration-style tests for products handler"""

    def setup_method(self):
        """Setup method run before each test"""
        self.mock_context = Mock()

    def create_api_gateway_event(
        self,
        http_method: str,
        path_parameters: Dict[str, str] = None,
        query_string_parameters: Dict[str, str] = None,
        body: str = None,
        resource_path: str = "/products"
    ) -> Dict[str, Any]:
        """Helper method to create API Gateway event"""
        return {
            'httpMethod': http_method,
            'pathParameters': path_parameters,
            'queryStringParameters': query_string_parameters,
            'body': body,
            'resource': resource_path,
            'headers': {
                'Content-Type': 'application/json'
            }
        }

    @patch('handlers.products.ProductService.create_product')
    @patch('handlers.products.ProductService.get_product')
    @patch('handlers.products.ProductService.update_product')
    @patch('handlers.products.ProductService.delete_product')
    @patch('handlers.products.ProductService.update_stock')
    def test_full_crud_workflow_with_stock_management(self, mock_update_stock, mock_delete, mock_update, mock_get, mock_create):
        """Test a complete CRUD workflow including stock management"""
        product_id = 'workflow-test-product'

        # 1. Create product
        product_data = {
            'name': 'Workflow Test Product',
            'brand_id': 'test-brand-123',
            'category_id': 'test-category-123',
            'price': 99.99,
            'description': 'A product for testing the complete workflow',
            'stock_quantity': 20
        }
        created_product = {
            'product_id': product_id,
            **product_data,
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-01T00:00:00Z'
        }
        mock_create.return_value = created_product

        create_event = self.create_api_gateway_event('POST', body=json.dumps(product_data))
        create_response = lambda_handler(create_event, self.mock_context)

        assert create_response['statusCode'] == 201
        body = json.loads(create_response['body'])
        assert body['data']['product_id'] == product_id
        assert body['data']['stock_quantity'] == 20

        # 2. Get product
        mock_get.return_value = created_product
        get_event = self.create_api_gateway_event('GET', path_parameters={'id': product_id})
        get_response = lambda_handler(get_event, self.mock_context)

        assert get_response['statusCode'] == 200
        body = json.loads(get_response['body'])
        assert body['data']['product_id'] == product_id
        assert body['data']['stock_quantity'] == 20

        # 3. Update product
        update_data = {
            'description': 'Updated workflow test product description',
            'stock_quantity': 25
        }
        updated_product = {
            **created_product,
            'description': update_data['description'],
            'stock_quantity': 25,
            'updated_at': '2024-01-01T12:00:00Z'
        }
        mock_update.return_value = updated_product

        update_event = self.create_api_gateway_event(
            'PUT',
            path_parameters={'id': product_id},
            body=json.dumps(update_data)
        )
        update_response = lambda_handler(update_event, self.mock_context)

        assert update_response['statusCode'] == 200
        body = json.loads(update_response['body'])
        assert body['data']['description'] == update_data['description']
        assert body['data']['stock_quantity'] == 25

        # 4. Update stock using PATCH
        stock_updated_product = {**updated_product, 'stock_quantity': 50}
        mock_update_stock.return_value = stock_updated_product

        stock_event = self.create_api_gateway_event(
            'PATCH',
            path_parameters={'id': product_id},
            body=json.dumps({'stock_quantity': 50}),
            resource_path='/products/{id}/stock'
        )
        stock_response = lambda_handler(stock_event, self.mock_context)

        assert stock_response['statusCode'] == 200
        body = json.loads(stock_response['body'])
        assert body['data']['stock_quantity'] == 50

        # 5. Delete product
        mock_delete.return_value = True
        delete_event = self.create_api_gateway_event('DELETE', path_parameters={'id': product_id})
        delete_response = lambda_handler(delete_event, self.mock_context)

        assert delete_response['statusCode'] == 200
        body = json.loads(delete_response['body'])
        assert body['message'] == 'Product deleted successfully'

        # Verify all service methods were called
        mock_create.assert_called_once()
        mock_get.assert_called_once()
        mock_update.assert_called_once()
        mock_update_stock.assert_called_once()
        mock_delete.assert_called_once()

    @patch('handlers.products.ProductService.list_products_by_brand')
    @patch('handlers.products.ProductService.list_products_by_category')
    def test_filtering_workflow(self, mock_list_by_category, mock_list_by_brand):
        """Test product filtering by brand and category"""
        brand_id = 'test-brand-123'
        category_id = 'test-category-123'

        # Test filtering by brand
        brand_products = {
            'items': [
                {'product_id': 'p1', 'name': 'Brand Product 1', 'brand_id': brand_id, 'stock_quantity': 10},
                {'product_id': 'p2', 'name': 'Brand Product 2', 'brand_id': brand_id, 'stock_quantity': 15}
            ],
            'last_evaluated_key': None
        }
        mock_list_by_brand.return_value = brand_products

        brand_event = self.create_api_gateway_event(
            'GET',
            path_parameters={'brand_id': brand_id},
            resource_path='/products/by-brand/{brand_id}'
        )
        brand_response = lambda_handler(brand_event, self.mock_context)

        assert brand_response['statusCode'] == 200
        body = json.loads(brand_response['body'])
        assert len(body['data']['items']) == 2
        assert all(item['brand_id'] == brand_id for item in body['data']['items'])

        # Test filtering by category
        category_products = {
            'items': [
                {'product_id': 'p3', 'name': 'Category Product 1', 'category_id': category_id, 'stock_quantity': 5},
                {'product_id': 'p4', 'name': 'Category Product 2', 'category_id': category_id, 'stock_quantity': 12}
            ],
            'last_evaluated_key': None
        }
        mock_list_by_category.return_value = category_products

        category_event = self.create_api_gateway_event(
            'GET',
            path_parameters={'category_id': category_id},
            resource_path='/products/by-category/{category_id}'
        )
        category_response = lambda_handler(category_event, self.mock_context)

        assert category_response['statusCode'] == 200
        body = json.loads(category_response['body'])
        assert len(body['data']['items']) == 2
        assert all(item['category_id'] == category_id for item in body['data']['items'])

        # Verify service methods were called
        mock_list_by_brand.assert_called_once_with(brand_id, 50, None)
        mock_list_by_category.assert_called_once_with(category_id, 50, None)

    @patch('handlers.products.ProductService.update_stock')
    @patch('handlers.products.ProductService.adjust_stock')
    def test_stock_management_workflow(self, mock_adjust_stock, mock_update_stock):
        """Test different stock management operations"""
        product_id = 'stock-test-product'

        # Test absolute stock update
        updated_product_abs = {
            'product_id': product_id,
            'name': 'Stock Test Product',
            'stock_quantity': 100
        }
        mock_update_stock.return_value = updated_product_abs

        abs_event = self.create_api_gateway_event(
            'PATCH',
            path_parameters={'id': product_id},
            body=json.dumps({'stock_quantity': 100}),
            resource_path='/products/{id}/stock'
        )
        abs_response = lambda_handler(abs_event, self.mock_context)

        assert abs_response['statusCode'] == 200
        body = json.loads(abs_response['body'])
        assert body['data']['stock_quantity'] == 100
        assert 'Stock updated successfully' in body['message']

        # Test relative stock adjustment
        updated_product_rel = {
            'product_id': product_id,
            'name': 'Stock Test Product',
            'stock_quantity': 85  # Assuming it was reduced by 15
        }
        mock_adjust_stock.return_value = updated_product_rel

        rel_event = self.create_api_gateway_event(
            'PATCH',
            path_parameters={'id': product_id},
            body=json.dumps({'quantity_change': -15}),
            resource_path='/products/{id}/stock'
        )
        rel_response = lambda_handler(rel_event, self.mock_context)

        assert rel_response['statusCode'] == 200
        body = json.loads(rel_response['body'])
        assert body['data']['stock_quantity'] == 85
        assert 'Stock adjusted successfully' in body['message']

        # Verify service methods were called
        mock_update_stock.assert_called_once_with(product_id, 100)
        mock_adjust_stock.assert_called_once_with(product_id, -15)

    @patch('handlers.products.ProductService')
    def test_error_handling_chain(self, mock_product_service):
        """Test error handling chain for different exception types"""
        product_id = 'error-test-product'

        # Test ValidationError
        mock_product_service.create_product.side_effect = ValidationError("Invalid product data")
        event = self.create_api_gateway_event('POST', body='{"name": "Test", "stock_quantity": 0}')
        response = lambda_handler(event, self.mock_context)
        assert response['statusCode'] == 400

        # Test NotFoundError
        mock_product_service.get_product.side_effect = NotFoundError("Product not found")
        event = self.create_api_gateway_event('GET', path_parameters={'id': product_id})
        response = lambda_handler(event, self.mock_context)
        assert response['statusCode'] == 404

        # Test ValueError
        mock_product_service.create_product.side_effect = ValueError("Invalid value")
        event = self.create_api_gateway_event('POST', body='{"name": "Test", "stock_quantity": 5}')
        response = lambda_handler(event, self.mock_context)
        assert response['statusCode'] == 400

        # Test generic Exception
        mock_product_service.list_products.side_effect = Exception("Unexpected error")
        event = self.create_api_gateway_event('GET')
        response = lambda_handler(event, self.mock_context)
        assert response['statusCode'] == 500


if __name__ == '__main__':
    pytest.main([__file__])
