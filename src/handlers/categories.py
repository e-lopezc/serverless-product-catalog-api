import json
from typing import Dict, Any


from services.category_service import CategoryService
from utils.response import (
    success_response, created_response, bad_request_response,
    not_found_response, conflict_response, server_error_response,
    parse_json_body, get_query_parameter
)
from utils.exceptions import ValidationError, NotFoundError, DuplicateError


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for Categories API

    Routes:
    - GET /categories - List all categories
    - POST /categories - Create a new category
    - GET /categories/{category_id} - Get a specific category
    - PUT /categories/{category_id} - Update a category
    - DELETE /categories/{category_id} - Delete a category
    """

    http_method = event.get('httpMethod')
    path_parameters = event.get('pathParameters') or {}
    category_id = path_parameters.get('id')

    print(f"Processing {http_method} request for categories")
    print(f"Path parameters: {path_parameters}")
    print(f"Category ID: {category_id}")

    try:
        if http_method == 'GET':
            if category_id:
                # Get new category
                category = CategoryService.get_category(category_id)
                if not category:
                    return not_found_response("Category not found")
                return success_response(category)
            else:
                # List all categories
                limit = int(get_query_parameter(event, 'limit', 50))
                last_key = get_query_parameter(event, 'last_key')

                # Parse last_key if provided
                last_evaluated_key = None
                if last_key:
                    try:
                        last_evaluated_key = json.loads(last_key)
                    except json.JSONDecodeError:
                        return bad_request_response("Invalid last_key format")

                categories_data = CategoryService.list_categories(limit, last_evaluated_key)
                return success_response(categories_data)

        elif http_method == 'POST':
            # Create new category
            data = parse_json_body(event)
            category = CategoryService.create_category(data)
            return created_response(category, "Category created successfully")

        elif http_method == 'PUT':
            if not category_id:
                return bad_request_response("Category ID is required")

            # Update category
            data = parse_json_body(event)
            category = CategoryService.update_category(category_id, data)
            if not category:
                return not_found_response("Category not found")
            return success_response(category, "Category updated successfully")

        elif http_method == 'DELETE':
            if not category_id:
                return bad_request_response("Category ID is required")

            # Delete category
            deleted = CategoryService.delete_category(category_id)
            if not deleted:
                return not_found_response("Category not found")
            return success_response(None, "Category deleted successfully")

        else:
            return bad_request_response(f"Method {http_method} not allowed")

    except ValidationError as e:
        return bad_request_response(str(e))
    except DuplicateError as e:
        return conflict_response(str(e))
    except NotFoundError as e:
        return not_found_response(str(e))
    except ValueError as e:
        return bad_request_response(str(e))
    except Exception as e:
        print(f"Unexpected error in categories handler: {str(e)}")
        import traceback
        traceback.print_exc()
        return server_error_response("An unexpected error occurred")
