import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Import the handler function and related modules
from handlers.brands import lambda_handler
from utils.exceptions import ValidationError, NotFoundError, DuplicateError


class TestBrandsHandler:
    """Test class for brands Lambda handler"""

    def setup_method(self):
        """Setup method run before each test"""
        self.mock_context = Mock()
        self.mock_context.function_name = "brands-handler"
        self.mock_context.function_version = "1"
        self.mock_context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:brands-handler"

    def create_api_gateway_event(
        self,
        http_method: str,
        path_parameters: Dict[str, str] = None,
        query_string_parameters: Dict[str, str] = None,
        body: str = None
    ) -> Dict[str, Any]:
        """Helper method to create API Gateway event"""
        return {
            'httpMethod': http_method,
            'pathParameters': path_parameters,
            'queryStringParameters': query_string_parameters,
            'body': body,
            'headers': {
                'Content-Type': 'application/json'
            }
        }

    @patch('handlers.brands.BrandService')
    def test_get_brands_list_success(self, mock_brand_service):
        """Test successful GET /brands request"""
        # Arrange
        mock_brands_data = {
            'items': [
                {
                    'brand_id': 'test-brand-1',
                    'name': 'Test Brand 1',
                    'description': 'First test brand',
                    'website': 'https://testbrand1.com'
                },
                {
                    'brand_id': 'test-brand-2',
                    'name': 'Test Brand 2',
                    'description': 'Second test brand',
                    'website': 'https://testbrand2.com'
                }
            ],
            'last_evaluated_key': None
        }
        mock_brand_service.list_brands.return_value = mock_brands_data

        event = self.create_api_gateway_event('GET')

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 200
        assert 'application/json' in response['headers']['Content-Type']

        body = json.loads(response['body'])
        assert body['message'] == 'Success'
        assert body['data'] == mock_brands_data

        mock_brand_service.list_brands.assert_called_once_with(50, None)

    @patch('handlers.brands.BrandService')
    def test_get_brands_list_with_pagination(self, mock_brand_service):
        """Test GET /brands with pagination parameters"""
        # Arrange
        mock_brands_data = {
            'items': [{'brand_id': 'test-brand-1', 'name': 'Test Brand 1'}],
            'last_evaluated_key': {'PK': 'BRAND#test-brand-1', 'SK': 'BRAND#test-brand-1'}
        }
        mock_brand_service.list_brands.return_value = mock_brands_data

        last_key = json.dumps({'PK': 'BRAND#prev', 'SK': 'BRAND#prev'})
        event = self.create_api_gateway_event(
            'GET',
            query_string_parameters={'limit': '25', 'last_key': last_key}
        )

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 200
        mock_brand_service.list_brands.assert_called_once_with(
            25, {'PK': 'BRAND#prev', 'SK': 'BRAND#prev'}
        )

    @patch('handlers.brands.BrandService')
    def test_get_brands_list_invalid_last_key(self, mock_brand_service):
        """Test GET /brands with invalid last_key format"""
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
        mock_brand_service.list_brands.assert_not_called()

    @patch('handlers.brands.BrandService')
    def test_get_brand_by_id_success(self, mock_brand_service):
        """Test successful GET /brands/{id} request"""
        # Arrange
        brand_id = 'test-brand-123'
        mock_brand = {
            'brand_id': brand_id,
            'name': 'Test Brand',
            'description': 'A test brand',
            'website': 'https://testbrand.com'
        }
        mock_brand_service.get_brand.return_value = mock_brand

        event = self.create_api_gateway_event('GET', path_parameters={'id': brand_id})

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['data'] == mock_brand
        mock_brand_service.get_brand.assert_called_once_with(brand_id)

    @patch('handlers.brands.BrandService')
    def test_get_brand_by_id_not_found(self, mock_brand_service):
        """Test GET /brands/{id} when brand doesn't exist"""
        # Arrange
        brand_id = 'non-existent-brand'
        mock_brand_service.get_brand.return_value = None

        event = self.create_api_gateway_event('GET', path_parameters={'id': brand_id})

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert body['message'] == 'Brand not found'
        mock_brand_service.get_brand.assert_called_once_with(brand_id)

    @patch('handlers.brands.BrandService')
    def test_create_brand_success(self, mock_brand_service):
        """Test successful POST /brands request"""
        # Arrange
        brand_data = {
            'name': 'New Test Brand',
            'description': 'A new test brand description',
            'website': 'https://newtestbrand.com'
        }
        created_brand = {
            'brand_id': 'new-brand-123',
            **brand_data,
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-01T00:00:00Z'
        }
        mock_brand_service.create_brand.return_value = created_brand

        event = self.create_api_gateway_event('POST', body=json.dumps(brand_data))

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 201
        body = json.loads(response['body'])
        assert body['message'] == 'Brand created successfully'
        assert body['data'] == created_brand
        mock_brand_service.create_brand.assert_called_once_with(brand_data)

    @patch('handlers.brands.BrandService')
    def test_create_brand_validation_error(self, mock_brand_service):
        """Test POST /brands with validation error"""
        # Arrange
        invalid_brand_data = {
            'name': '',  # Empty name should fail validation
            'description': 'Valid description'
        }
        mock_brand_service.create_brand.side_effect = ValidationError("Brand name is required")

        event = self.create_api_gateway_event('POST', body=json.dumps(invalid_brand_data))

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['message'] == 'Brand name is required'
        mock_brand_service.create_brand.assert_called_once_with(invalid_brand_data)

    @patch('handlers.brands.BrandService')
    def test_create_brand_duplicate_error(self, mock_brand_service):
        """Test POST /brands with duplicate name error"""
        # Arrange
        brand_data = {
            'name': 'Existing Brand',
            'description': 'Valid description'
        }
        mock_brand_service.create_brand.side_effect = DuplicateError("Brand name 'Existing Brand' already exists")

        event = self.create_api_gateway_event('POST', body=json.dumps(brand_data))

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 409
        body = json.loads(response['body'])
        assert "already exists" in body['message']
        mock_brand_service.create_brand.assert_called_once_with(brand_data)

    @patch('handlers.brands.BrandService')
    def test_create_brand_invalid_json(self, mock_brand_service):
        """Test POST /brands with invalid JSON body"""
        # Arrange
        event = self.create_api_gateway_event('POST', body='invalid-json{')

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'Invalid JSON' in body['message']
        mock_brand_service.create_brand.assert_not_called()

    @patch('handlers.brands.BrandService')
    def test_update_brand_success(self, mock_brand_service):
        """Test successful PUT /brands/{id} request"""
        # Arrange
        brand_id = 'test-brand-123'
        update_data = {
            'name': 'Updated Brand Name',
            'description': 'Updated description'
        }
        updated_brand = {
            'brand_id': brand_id,
            **update_data,
            'website': 'https://original-website.com',
            'updated_at': '2024-01-01T12:00:00Z'
        }
        mock_brand_service.update_brand.return_value = updated_brand

        event = self.create_api_gateway_event(
            'PUT',
            path_parameters={'id': brand_id},
            body=json.dumps(update_data)
        )

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['message'] == 'Brand updated successfully'
        assert body['data'] == updated_brand
        mock_brand_service.update_brand.assert_called_once_with(brand_id, update_data)

    @patch('handlers.brands.BrandService')
    def test_update_brand_not_found(self, mock_brand_service):
        """Test PUT /brands/{id} when brand doesn't exist"""
        # Arrange
        brand_id = 'non-existent-brand'
        update_data = {'name': 'Updated Name'}
        mock_brand_service.update_brand.return_value = None

        event = self.create_api_gateway_event(
            'PUT',
            path_parameters={'id': brand_id},
            body=json.dumps(update_data)
        )

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert body['message'] == 'Brand not found'
        mock_brand_service.update_brand.assert_called_once_with(brand_id, update_data)

    @patch('handlers.brands.BrandService')
    def test_update_brand_missing_id(self, mock_brand_service):
        """Test PUT /brands/{id} without brand ID"""
        # Arrange
        update_data = {'name': 'Updated Name'}
        event = self.create_api_gateway_event('PUT', body=json.dumps(update_data))

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['message'] == 'Brand ID is required'
        mock_brand_service.update_brand.assert_not_called()

    @patch('handlers.brands.BrandService')
    def test_delete_brand_success(self, mock_brand_service):
        """Test successful DELETE /brands/{id} request"""
        # Arrange
        brand_id = 'test-brand-123'
        mock_brand_service.delete_brand.return_value = True

        event = self.create_api_gateway_event('DELETE', path_parameters={'id': brand_id})

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['message'] == 'Brand deleted successfully'
        mock_brand_service.delete_brand.assert_called_once_with(brand_id)

    @patch('handlers.brands.BrandService')
    def test_delete_brand_not_found(self, mock_brand_service):
        """Test DELETE /brands/{id} when brand doesn't exist"""
        # Arrange
        brand_id = 'non-existent-brand'
        mock_brand_service.delete_brand.return_value = False

        event = self.create_api_gateway_event('DELETE', path_parameters={'id': brand_id})

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert body['message'] == 'Brand not found'
        mock_brand_service.delete_brand.assert_called_once_with(brand_id)

    @patch('handlers.brands.BrandService')
    def test_delete_brand_missing_id(self, mock_brand_service):
        """Test DELETE /brands/{id} without brand ID"""
        # Arrange
        event = self.create_api_gateway_event('DELETE')

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['message'] == 'Brand ID is required'
        mock_brand_service.delete_brand.assert_not_called()

    @patch('handlers.brands.BrandService')
    def test_unsupported_http_method(self, mock_brand_service):
        """Test unsupported HTTP method"""
        # Arrange
        event = self.create_api_gateway_event('PATCH')

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'Method PATCH not allowed' in body['message']

    @patch('handlers.brands.BrandService')
    def test_unexpected_exception(self, mock_brand_service):
        """Test handling of unexpected exceptions"""
        # Arrange
        mock_brand_service.list_brands.side_effect = Exception("Unexpected database error")
        event = self.create_api_gateway_event('GET')

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert body['message'] == 'An unexpected error occurred'

    @patch('handlers.brands.BrandService')
    def test_not_found_error_exception(self, mock_brand_service):
        """Test handling of NotFoundError exception"""
        # Arrange
        mock_brand_service.get_brand.side_effect = NotFoundError("Brand not found in database")
        event = self.create_api_gateway_event('GET', path_parameters={'id': 'test-brand'})

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert body['message'] == 'Brand not found in database'

    @patch('handlers.brands.BrandService')
    def test_value_error_exception(self, mock_brand_service):
        """Test handling of ValueError exception"""
        # Arrange
        mock_brand_service.create_brand.side_effect = ValueError("Invalid input value")
        event = self.create_api_gateway_event('POST', body='{"name": "Test"}')

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
        with patch('handlers.brands.BrandService'):
            response = lambda_handler(event, self.mock_context)

        # Assert
        headers = response['headers']
        assert 'Access-Control-Allow-Origin' in headers
        assert 'Access-Control-Allow-Methods' in headers
        assert 'Access-Control-Allow-Headers' in headers
        assert headers['Access-Control-Allow-Origin'] == '*'

    @patch('handlers.brands.BrandService')
    def test_empty_path_parameters(self, mock_brand_service):
        """Test handling when pathParameters is None"""
        # Arrange
        event = {
            'httpMethod': 'GET',
            'pathParameters': None,
            'queryStringParameters': None,
            'body': None
        }
        mock_brand_service.list_brands.return_value = {'items': [], 'last_evaluated_key': None}

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 200
        mock_brand_service.list_brands.assert_called_once()

    @patch('handlers.brands.BrandService')
    def test_empty_query_parameters(self, mock_brand_service):
        """Test handling when queryStringParameters is None"""
        # Arrange
        event = self.create_api_gateway_event('GET')
        event['queryStringParameters'] = None
        mock_brand_service.list_brands.return_value = {'items': [], 'last_evaluated_key': None}

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 200
        # Should use default limit (50) and None for last_key
        mock_brand_service.list_brands.assert_called_once_with(50, None)

    @patch('handlers.brands.BrandService')
    def test_empty_body_handling(self, mock_brand_service):
        """Test handling when body is None or empty"""
        # Arrange
        event = self.create_api_gateway_event('POST')
        event['body'] = None
        mock_brand_service.create_brand.return_value = {'brand_id': 'test', 'name': 'Test Brand'}

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 201
        # Should pass empty dict when body is None
        mock_brand_service.create_brand.assert_called_once_with({})


# Integration-style tests (still unit tests but testing more end-to-end flow)
class TestBrandsHandlerIntegration:
    """Integration-style tests for brands handler"""

    def setup_method(self):
        """Setup method run before each test"""
        self.mock_context = Mock()

    def create_api_gateway_event(
        self,
        http_method: str,
        path_parameters: Dict[str, str] = None,
        query_string_parameters: Dict[str, str] = None,
        body: str = None
    ) -> Dict[str, Any]:
        """Helper method to create API Gateway event"""
        return {
            'httpMethod': http_method,
            'pathParameters': path_parameters,
            'queryStringParameters': query_string_parameters,
            'body': body,
            'headers': {
                'Content-Type': 'application/json'
            }
        }

    @patch('handlers.brands.BrandService.create_brand')
    @patch('handlers.brands.BrandService.get_brand')
    @patch('handlers.brands.BrandService.update_brand')
    @patch('handlers.brands.BrandService.delete_brand')
    def test_full_crud_workflow(self, mock_delete, mock_update, mock_get, mock_create):
        """Test a complete CRUD workflow"""
        brand_id = 'workflow-test-brand'

        # 1. Create brand
        brand_data = {
            'name': 'Workflow Test Brand',
            'description': 'A brand for testing the complete workflow',
            'website': 'https://workflowtest.com'
        }
        created_brand = {
            'brand_id': brand_id,
            **brand_data,
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-01T00:00:00Z'
        }
        mock_create.return_value = created_brand

        create_event = self.create_api_gateway_event('POST', body=json.dumps(brand_data))
        create_response = lambda_handler(create_event, self.mock_context)

        assert create_response['statusCode'] == 201
        body = json.loads(create_response['body'])
        assert body['data']['brand_id'] == brand_id

        # 2. Get brand
        mock_get.return_value = created_brand
        get_event = self.create_api_gateway_event('GET', path_parameters={'id': brand_id})
        get_response = lambda_handler(get_event, self.mock_context)

        assert get_response['statusCode'] == 200
        body = json.loads(get_response['body'])
        assert body['data']['brand_id'] == brand_id

        # 3. Update brand
        update_data = {'description': 'Updated workflow test brand description'}
        updated_brand = {**created_brand, 'description': update_data['description'], 'updated_at': '2024-01-01T12:00:00Z'}
        mock_update.return_value = updated_brand

        update_event = self.create_api_gateway_event(
            'PUT',
            path_parameters={'id': brand_id},
            body=json.dumps(update_data)
        )
        update_response = lambda_handler(update_event, self.mock_context)

        assert update_response['statusCode'] == 200
        body = json.loads(update_response['body'])
        assert body['data']['description'] == update_data['description']

        # 4. Delete brand
        mock_delete.return_value = True
        delete_event = self.create_api_gateway_event('DELETE', path_parameters={'id': brand_id})
        delete_response = lambda_handler(delete_event, self.mock_context)

        assert delete_response['statusCode'] == 200
        body = json.loads(delete_response['body'])
        assert body['message'] == 'Brand deleted successfully'

        # Verify all service methods were called
        mock_create.assert_called_once()
        mock_get.assert_called_once()
        mock_update.assert_called_once()
        mock_delete.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__])
