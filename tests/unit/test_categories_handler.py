import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Import the handler function and related modules


from handlers.categories import lambda_handler
from utils.exceptions import ValidationError, NotFoundError, DuplicateError


class TestCategoriesHandler:
    """Test class for categories Lambda handler"""

    def setup_method(self):
        """Setup method run before each test"""
        self.mock_context = Mock()
        self.mock_context.function_name = "categories-handler"
        self.mock_context.function_version = "1"
        self.mock_context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:categories-handler"

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

    @patch('handlers.categories.CategoryService')
    def test_get_categories_list_success(self, mock_category_service):
        """Test successful GET /categories request"""
        # Arrange
        mock_categories_data = {
            'items': [
                {
                    'category_id': 'test-category-1',
                    'name': 'Test Category 1',
                    'description': 'First test category'
                },
                {
                    'category_id': 'test-category-2',
                    'name': 'Test Category 2',
                    'description': 'Second test category'
                }
            ],
            'last_evaluated_key': None
        }
        mock_category_service.list_categories.return_value = mock_categories_data

        event = self.create_api_gateway_event('GET')

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 200
        assert 'application/json' in response['headers']['Content-Type']

        body = json.loads(response['body'])
        assert body['message'] == 'Success'
        assert body['data'] == mock_categories_data

        mock_category_service.list_categories.assert_called_once_with(50, None)

    @patch('handlers.categories.CategoryService')
    def test_get_categories_list_with_pagination(self, mock_category_service):
        """Test GET /categories with pagination parameters"""
        # Arrange
        mock_categories_data = {
            'items': [{'category_id': 'test-category-1', 'name': 'Test Category 1'}],
            'last_evaluated_key': {'PK': 'CATEGORY#test-category-1', 'SK': 'CATEGORY#test-category-1'}
        }
        mock_category_service.list_categories.return_value = mock_categories_data

        last_key = json.dumps({'PK': 'CATEGORY#prev', 'SK': 'CATEGORY#prev'})
        event = self.create_api_gateway_event(
            'GET',
            query_string_parameters={'limit': '25', 'last_key': last_key}
        )

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 200
        mock_category_service.list_categories.assert_called_once_with(
            25, {'PK': 'CATEGORY#prev', 'SK': 'CATEGORY#prev'}
        )

    @patch('handlers.categories.CategoryService')
    def test_get_categories_list_invalid_last_key(self, mock_category_service):
        """Test GET /categories with invalid last_key format"""
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
        mock_category_service.list_categories.assert_not_called()

    @patch('handlers.categories.CategoryService')
    def test_get_category_by_id_success(self, mock_category_service):
        """Test successful GET /categories/{id} request"""
        # Arrange
        category_id = 'test-category-123'
        mock_category = {
            'category_id': category_id,
            'name': 'Test Category',
            'description': 'A test category for testing purposes'
        }
        mock_category_service.get_category.return_value = mock_category

        event = self.create_api_gateway_event('GET', path_parameters={'id': category_id})

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['data'] == mock_category
        mock_category_service.get_category.assert_called_once_with(category_id)

    @patch('handlers.categories.CategoryService')
    def test_get_category_by_id_not_found(self, mock_category_service):
        """Test GET /categories/{id} when category doesn't exist"""
        # Arrange
        category_id = 'non-existent-category'
        mock_category_service.get_category.return_value = None

        event = self.create_api_gateway_event('GET', path_parameters={'id': category_id})

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert body['message'] == 'Category not found'
        mock_category_service.get_category.assert_called_once_with(category_id)

    @patch('handlers.categories.CategoryService')
    def test_create_category_success(self, mock_category_service):
        """Test successful POST /categories request"""
        # Arrange
        category_data = {
            'name': 'New Test Category',
            'description': 'A new test category description for testing purposes'
        }
        created_category = {
            'category_id': 'new-category-123',
            **category_data,
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-01T00:00:00Z'
        }
        mock_category_service.create_category.return_value = created_category

        event = self.create_api_gateway_event('POST', body=json.dumps(category_data))

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 201
        body = json.loads(response['body'])
        assert body['message'] == 'Category created successfully'
        assert body['data'] == created_category
        mock_category_service.create_category.assert_called_once_with(category_data)

    @patch('handlers.categories.CategoryService')
    def test_create_category_validation_error(self, mock_category_service):
        """Test POST /categories with validation error"""
        # Arrange
        invalid_category_data = {
            'name': '',  # Empty name should fail validation
            'description': 'Valid description for testing purposes'
        }
        mock_category_service.create_category.side_effect = ValidationError("Category name is required")

        event = self.create_api_gateway_event('POST', body=json.dumps(invalid_category_data))

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['message'] == 'Category name is required'
        mock_category_service.create_category.assert_called_once_with(invalid_category_data)

    @patch('handlers.categories.CategoryService')
    def test_create_category_duplicate_error(self, mock_category_service):
        """Test POST /categories with duplicate name error"""
        # Arrange
        category_data = {
            'name': 'Existing Category',
            'description': 'Valid description for testing purposes'
        }
        mock_category_service.create_category.side_effect = DuplicateError("Category name 'Existing Category' already exists")

        event = self.create_api_gateway_event('POST', body=json.dumps(category_data))

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 409
        body = json.loads(response['body'])
        assert "already exists" in body['message']
        mock_category_service.create_category.assert_called_once_with(category_data)

    @patch('handlers.categories.CategoryService')
    def test_create_category_invalid_json(self, mock_category_service):
        """Test POST /categories with invalid JSON body"""
        # Arrange
        event = self.create_api_gateway_event('POST', body='invalid-json{')

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'Invalid JSON' in body['message']
        mock_category_service.create_category.assert_not_called()

    @patch('handlers.categories.CategoryService')
    def test_update_category_success(self, mock_category_service):
        """Test successful PUT /categories/{id} request"""
        # Arrange
        category_id = 'test-category-123'
        update_data = {
            'name': 'Updated Category Name',
            'description': 'Updated category description for testing purposes'
        }
        updated_category = {
            'category_id': category_id,
            **update_data,
            'updated_at': '2024-01-01T12:00:00Z'
        }
        mock_category_service.update_category.return_value = updated_category

        event = self.create_api_gateway_event(
            'PUT',
            path_parameters={'id': category_id},
            body=json.dumps(update_data)
        )

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['message'] == 'Category updated successfully'
        assert body['data'] == updated_category
        mock_category_service.update_category.assert_called_once_with(category_id, update_data)

    @patch('handlers.categories.CategoryService')
    def test_update_category_not_found(self, mock_category_service):
        """Test PUT /categories/{id} when category doesn't exist"""
        # Arrange
        category_id = 'non-existent-category'
        update_data = {'name': 'Updated Name'}
        mock_category_service.update_category.return_value = None

        event = self.create_api_gateway_event(
            'PUT',
            path_parameters={'id': category_id},
            body=json.dumps(update_data)
        )

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert body['message'] == 'Category not found'
        mock_category_service.update_category.assert_called_once_with(category_id, update_data)

    @patch('handlers.categories.CategoryService')
    def test_update_category_missing_id(self, mock_category_service):
        """Test PUT /categories/{id} without category ID"""
        # Arrange
        update_data = {'name': 'Updated Name'}
        event = self.create_api_gateway_event('PUT', body=json.dumps(update_data))

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['message'] == 'Category ID is required'
        mock_category_service.update_category.assert_not_called()

    @patch('handlers.categories.CategoryService')
    def test_delete_category_success(self, mock_category_service):
        """Test successful DELETE /categories/{id} request"""
        # Arrange
        category_id = 'test-category-123'
        mock_category_service.delete_category.return_value = True

        event = self.create_api_gateway_event('DELETE', path_parameters={'id': category_id})

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['message'] == 'Category deleted successfully'
        mock_category_service.delete_category.assert_called_once_with(category_id)

    @patch('handlers.categories.CategoryService')
    def test_delete_category_not_found(self, mock_category_service):
        """Test DELETE /categories/{id} when category doesn't exist"""
        # Arrange
        category_id = 'non-existent-category'
        mock_category_service.delete_category.return_value = False

        event = self.create_api_gateway_event('DELETE', path_parameters={'id': category_id})

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert body['message'] == 'Category not found'
        mock_category_service.delete_category.assert_called_once_with(category_id)

    @patch('handlers.categories.CategoryService')
    def test_delete_category_missing_id(self, mock_category_service):
        """Test DELETE /categories/{id} without category ID"""
        # Arrange
        event = self.create_api_gateway_event('DELETE')

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['message'] == 'Category ID is required'
        mock_category_service.delete_category.assert_not_called()

    @patch('handlers.categories.CategoryService')
    def test_unsupported_http_method(self, mock_category_service):
        """Test unsupported HTTP method"""
        # Arrange
        event = self.create_api_gateway_event('PATCH')

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'Method PATCH not allowed' in body['message']

    @patch('handlers.categories.CategoryService')
    def test_unexpected_exception(self, mock_category_service):
        """Test handling of unexpected exceptions"""
        # Arrange
        mock_category_service.list_categories.side_effect = Exception("Unexpected database error")
        event = self.create_api_gateway_event('GET')

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert body['message'] == 'An unexpected error occurred'

    @patch('handlers.categories.CategoryService')
    def test_not_found_error_exception(self, mock_category_service):
        """Test handling of NotFoundError exception"""
        # Arrange
        mock_category_service.get_category.side_effect = NotFoundError("Category not found in database")
        event = self.create_api_gateway_event('GET', path_parameters={'id': 'test-category'})

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert body['message'] == 'Category not found in database'

    @patch('handlers.categories.CategoryService')
    def test_value_error_exception(self, mock_category_service):
        """Test handling of ValueError exception"""
        # Arrange
        mock_category_service.create_category.side_effect = ValueError("Invalid input value")
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
        with patch('handlers.categories.CategoryService'):
            response = lambda_handler(event, self.mock_context)

        # Assert
        headers = response['headers']
        assert 'Access-Control-Allow-Origin' in headers
        assert 'Access-Control-Allow-Methods' in headers
        assert 'Access-Control-Allow-Headers' in headers
        assert headers['Access-Control-Allow-Origin'] == '*'

    @patch('handlers.categories.CategoryService')
    def test_empty_path_parameters(self, mock_category_service):
        """Test handling when pathParameters is None"""
        # Arrange
        event = {
            'httpMethod': 'GET',
            'pathParameters': None,
            'queryStringParameters': None,
            'body': None
        }
        mock_category_service.list_categories.return_value = {'items': [], 'last_evaluated_key': None}

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 200
        mock_category_service.list_categories.assert_called_once()

    @patch('handlers.categories.CategoryService')
    def test_empty_query_parameters(self, mock_category_service):
        """Test handling when queryStringParameters is None"""
        # Arrange
        event = self.create_api_gateway_event('GET')
        event['queryStringParameters'] = None
        mock_category_service.list_categories.return_value = {'items': [], 'last_evaluated_key': None}

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 200
        # Should use default limit (50) and None for last_key
        mock_category_service.list_categories.assert_called_once_with(50, None)

    @patch('handlers.categories.CategoryService')
    def test_empty_body_handling(self, mock_category_service):
        """Test handling when body is None or empty"""
        # Arrange
        event = self.create_api_gateway_event('POST')
        event['body'] = None
        mock_category_service.create_category.return_value = {'category_id': 'test', 'name': 'Test Category'}

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 201
        # Should pass empty dict when body is None
        mock_category_service.create_category.assert_called_once_with({})

    @patch('handlers.categories.CategoryService')
    def test_create_category_with_short_description_validation(self, mock_category_service):
        """Test POST /categories with too short description"""
        # Arrange
        invalid_category_data = {
            'name': 'Valid Category Name',
            'description': 'Short'  # Too short according to validation rules
        }
        mock_category_service.create_category.side_effect = ValidationError("Category description must be at least 10 characters long")

        event = self.create_api_gateway_event('POST', body=json.dumps(invalid_category_data))

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'must be at least 10 characters long' in body['message']
        mock_category_service.create_category.assert_called_once_with(invalid_category_data)

    @patch('handlers.categories.CategoryService')
    def test_create_category_with_invalid_characters(self, mock_category_service):
        """Test POST /categories with invalid characters in name"""
        # Arrange
        invalid_category_data = {
            'name': 'Invalid@Category!Name',  # Contains invalid characters
            'description': 'Valid description for testing purposes'
        }
        mock_category_service.create_category.side_effect = ValidationError("Category name contains invalid characters")

        event = self.create_api_gateway_event('POST', body=json.dumps(invalid_category_data))

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'invalid characters' in body['message']
        mock_category_service.create_category.assert_called_once_with(invalid_category_data)

    @patch('handlers.categories.CategoryService')
    def test_update_category_validation_error(self, mock_category_service):
        """Test PUT /categories/{id} with validation error"""
        # Arrange
        category_id = 'test-category-123'
        update_data = {
            'description': 'Short'  # Too short description
        }
        mock_category_service.update_category.side_effect = ValidationError("Category description must be at least 10 characters long")

        event = self.create_api_gateway_event(
            'PUT',
            path_parameters={'id': category_id},
            body=json.dumps(update_data)
        )

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'must be at least 10 characters long' in body['message']
        mock_category_service.update_category.assert_called_once_with(category_id, update_data)

    @patch('handlers.categories.CategoryService')
    def test_update_category_duplicate_name_error(self, mock_category_service):
        """Test PUT /categories/{id} with duplicate name error"""
        # Arrange
        category_id = 'test-category-123'
        update_data = {
            'name': 'Existing Category Name'
        }
        mock_category_service.update_category.side_effect = DuplicateError("Category name 'Existing Category Name' already exists")

        event = self.create_api_gateway_event(
            'PUT',
            path_parameters={'id': category_id},
            body=json.dumps(update_data)
        )

        # Act
        response = lambda_handler(event, self.mock_context)

        # Assert
        assert response['statusCode'] == 409
        body = json.loads(response['body'])
        assert 'already exists' in body['message']
        mock_category_service.update_category.assert_called_once_with(category_id, update_data)


# Integration-style tests (still unit tests but testing more end-to-end flow)
class TestCategoriesHandlerIntegration:
    """Integration-style tests for categories handler"""

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

    @patch('handlers.categories.CategoryService.create_category')
    @patch('handlers.categories.CategoryService.get_category')
    @patch('handlers.categories.CategoryService.update_category')
    @patch('handlers.categories.CategoryService.delete_category')
    def test_full_crud_workflow(self, mock_delete, mock_update, mock_get, mock_create):
        """Test a complete CRUD workflow"""
        category_id = 'workflow-test-category'

        # 1. Create category
        category_data = {
            'name': 'Workflow Test Category',
            'description': 'A category for testing the complete workflow functionality'
        }
        created_category = {
            'category_id': category_id,
            **category_data,
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-01T00:00:00Z'
        }
        mock_create.return_value = created_category

        create_event = self.create_api_gateway_event('POST', body=json.dumps(category_data))
        create_response = lambda_handler(create_event, self.mock_context)

        assert create_response['statusCode'] == 201
        body = json.loads(create_response['body'])
        assert body['data']['category_id'] == category_id

        # 2. Get category
        mock_get.return_value = created_category
        get_event = self.create_api_gateway_event('GET', path_parameters={'id': category_id})
        get_response = lambda_handler(get_event, self.mock_context)

        assert get_response['statusCode'] == 200
        body = json.loads(get_response['body'])
        assert body['data']['category_id'] == category_id

        # 3. Update category
        update_data = {'description': 'Updated workflow test category description for testing'}
        updated_category = {**created_category, 'description': update_data['description'], 'updated_at': '2024-01-01T12:00:00Z'}
        mock_update.return_value = updated_category

        update_event = self.create_api_gateway_event(
            'PUT',
            path_parameters={'id': category_id},
            body=json.dumps(update_data)
        )
        update_response = lambda_handler(update_event, self.mock_context)

        assert update_response['statusCode'] == 200
        body = json.loads(update_response['body'])
        assert body['data']['description'] == update_data['description']

        # 4. Delete category
        mock_delete.return_value = True
        delete_event = self.create_api_gateway_event('DELETE', path_parameters={'id': category_id})
        delete_response = lambda_handler(delete_event, self.mock_context)

        assert delete_response['statusCode'] == 200
        body = json.loads(delete_response['body'])
        assert body['message'] == 'Category deleted successfully'

        # Verify all service methods were called
        mock_create.assert_called_once()
        mock_get.assert_called_once()
        mock_update.assert_called_once()
        mock_delete.assert_called_once()

    @patch('handlers.categories.CategoryService.list_categories')
    def test_list_categories_with_multiple_pages(self, mock_list_categories):
        """Test listing categories with pagination across multiple pages"""
        # First page
        first_page_response = {
            'items': [
                {'category_id': 'cat-1', 'name': 'Category 1', 'description': 'First category'},
                {'category_id': 'cat-2', 'name': 'Category 2', 'description': 'Second category'}
            ],
            'last_evaluated_key': {'PK': 'CATEGORY#cat-2', 'SK': 'CATEGORY#cat-2'}
        }
        mock_list_categories.return_value = first_page_response

        event = self.create_api_gateway_event('GET', query_string_parameters={'limit': '2'})
        response = lambda_handler(event, self.mock_context)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert len(body['data']['items']) == 2
        assert body['data']['last_evaluated_key'] is not None

        # Second page
        second_page_response = {
            'items': [
                {'category_id': 'cat-3', 'name': 'Category 3', 'description': 'Third category'}
            ],
            'last_evaluated_key': None
        }
        mock_list_categories.return_value = second_page_response

        last_key = json.dumps({'PK': 'CATEGORY#cat-2', 'SK': 'CATEGORY#cat-2'})
        event = self.create_api_gateway_event(
            'GET',
            query_string_parameters={'limit': '2', 'last_key': last_key}
        )
        response = lambda_handler(event, self.mock_context)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert len(body['data']['items']) == 1
        assert body['data']['last_evaluated_key'] is None

    @patch('handlers.categories.CategoryService')
    def test_error_handling_chain(self, mock_category_service):
        """Test error handling chain for different exception types"""
        category_id = 'error-test-category'

        # Test ValidationError
        mock_category_service.create_category.side_effect = ValidationError("Invalid category data")
        event = self.create_api_gateway_event('POST', body='{"name": "Test"}')
        response = lambda_handler(event, self.mock_context)
        assert response['statusCode'] == 400

        # Test DuplicateError
        mock_category_service.create_category.side_effect = DuplicateError("Category already exists")
        response = lambda_handler(event, self.mock_context)
        assert response['statusCode'] == 409

        # Test NotFoundError
        mock_category_service.get_category.side_effect = NotFoundError("Category not found")
        event = self.create_api_gateway_event('GET', path_parameters={'id': category_id})
        response = lambda_handler(event, self.mock_context)
        assert response['statusCode'] == 404

        # Test ValueError
        mock_category_service.create_category.side_effect = ValueError("Invalid value")
        event = self.create_api_gateway_event('POST', body='{"name": "Test"}')
        response = lambda_handler(event, self.mock_context)
        assert response['statusCode'] == 400

        # Test generic Exception
        mock_category_service.list_categories.side_effect = Exception("Unexpected error")
        event = self.create_api_gateway_event('GET')
        response = lambda_handler(event, self.mock_context)
        assert response['statusCode'] == 500


if __name__ == '__main__':
    pytest.main([__file__])
