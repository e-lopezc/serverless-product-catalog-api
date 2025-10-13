import json
from typing import Dict, Any

from services.product_service import ProductService
from utils.response import (
    success_response, created_response, bad_request_response,
    not_found_response, conflict_response, server_error_response,
    parse_json_body, get_query_parameter
)
from utils.exceptions import ValidationError, NotFoundError, DuplicateError
from utils.logger import setup_logger, log_request_info

# Set up logger
logger = setup_logger(__name__)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for products API

    Routes:
    - GET /products - List all products
    - POST /products - Create a new product
    - GET /products/{product_id} - Get a specific product
    - PUT /products/{product_id} - Update a product
    - DELETE /products/{product_id} - Delete a product
    - GET /products/by-brand/{brand_id} - List products by brand
    - GET /products/by-category/{category_id} - List products by category
    - PATCH /products/{product_id}/stock - Update product stock
    """

    # Support both API Gateway v1 (REST API) and v2 (HTTP API) event formats
    http_method = event.get('httpMethod') or event.get('requestContext', {}).get('http', {}).get('method')
    path_parameters = event.get('pathParameters') or {}
    product_id = path_parameters.get('id')
    brand_id = path_parameters.get('brand_id')
    category_id = path_parameters.get('category_id')
    # For HTTP API v2, use rawPath or routeKey; for REST API use resource
    resource_path = event.get('resource') or event.get('rawPath', '')

    # Log request information
    log_request_info(logger, event)

    logger.debug(f"Product ID: {product_id}, Brand ID: {brand_id}, Category ID: {category_id}")

    try:
        # Handle different resource paths
        if '/by-brand/' in resource_path:
            # GET /products/by-brand/{brand_id}
            if not brand_id:
                return bad_request_response("Brand ID is required")
            return handle_products_by_brand(event, brand_id)

        elif '/by-category/' in resource_path:
            # GET /products/by-category/{category_id}
            if not category_id:
                return bad_request_response("Category ID is required")
            return handle_products_by_category(event, category_id)


        elif '/stock' in resource_path:
            # PATCH /products/{product_id}/stock
            if not product_id:
                return bad_request_response("Product ID is required")
            return handle_stock_update(event, product_id)

        else:
            # Standard CRUD operations
            if http_method == 'GET':
                if product_id:
                    # Get specific product
                    product = ProductService.get_product(product_id)
                    if not product:
                        return not_found_response("Product not found")
                    return success_response(product)
                else:
                    # List all products
                    limit = int(get_query_parameter(event, 'limit', 50))
                    last_key = get_query_parameter(event, 'last_key')

                    # Parse last_key if provided
                    last_evaluated_key = None
                    if last_key:
                        try:
                            last_evaluated_key = json.loads(last_key)
                        except json.JSONDecodeError:
                            return bad_request_response("Invalid last_key format")

                    products_data = ProductService.list_products(limit, last_evaluated_key)
                    return success_response(products_data)

            elif http_method == 'POST':
                # Create new product
                data = parse_json_body(event)
                product = ProductService.create_product(data)
                return created_response(product, "Product created successfully")

            elif http_method == 'PUT':
                if not product_id:
                    return bad_request_response("Product ID is required")

                # Update product
                data = parse_json_body(event)
                product = ProductService.update_product(product_id, data)
                if not product:
                    return not_found_response("Product not found")
                return success_response(product, "Product updated successfully")

            elif http_method == 'DELETE':
                if not product_id:
                    return bad_request_response("Product ID is required")

                # Delete product
                deleted = ProductService.delete_product(product_id)
                if not deleted:
                    return not_found_response("Product not found")
                return success_response(None, "Product deleted successfully")

            else:
                return bad_request_response(f"Method {http_method} not allowed")

    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        return bad_request_response(str(e))
    except DuplicateError as e:
        logger.warning(f"Duplicate error: {str(e)}")
        return conflict_response(str(e))
    except NotFoundError as e:
        logger.info(f"Not found: {str(e)}")
        return not_found_response(str(e))
    except ValueError as e:
        logger.warning(f"Value error: {str(e)}")
        return bad_request_response(str(e))
    except Exception as e:
        logger.error(f"Unexpected error in products handler: {str(e)}", exc_info=True)
        return server_error_response("An unexpected error occurred")


def handle_products_by_brand(event: Dict[str, Any], brand_id: str) -> Dict[str, Any]:
    """Handle GET /products/by-brand/{brand_id}"""

    limit = int(get_query_parameter(event, 'limit', 50))
    last_key = get_query_parameter(event, 'last_key')

    # Parse last_key if provided
    last_evaluated_key = None
    if last_key:
        try:
            last_evaluated_key = json.loads(last_key)
        except json.JSONDecodeError:
            return bad_request_response("Invalid last_key format")

    products_data = ProductService.list_products_by_brand(brand_id, limit, last_evaluated_key)
    return success_response(products_data)


def handle_products_by_category(event: Dict[str, Any], category_id: str) -> Dict[str, Any]:
    """Handle GET /products/by-category/{category_id}"""

    limit = int(get_query_parameter(event, 'limit', 50))
    last_key = get_query_parameter(event, 'last_key')

    # Parse last_key if provided
    last_evaluated_key = None
    if last_key:
        try:
            last_evaluated_key = json.loads(last_key)
        except json.JSONDecodeError:
            return bad_request_response("Invalid last_key format")

    products_data = ProductService.list_products_by_category(category_id, limit, last_evaluated_key)
    return success_response(products_data)


def handle_stock_update(event: Dict[str, Any], product_id: str) -> Dict[str, Any]:
    """Handle PATCH /products/{product_id}/stock"""

    data = parse_json_body(event)

    # Support two types of stock updates:
    # 1. Absolute: {"stock_quantity": 100}
    # 2. Relative: {"quantity_change": -5}

    if 'stock_quantity' in data:
        # Absolute stock update
        stock_quantity = data['stock_quantity']
        if not isinstance(stock_quantity, int):
            return bad_request_response("stock_quantity must be an integer")

        product = ProductService.update_stock(product_id, stock_quantity)
        if not product:
            return not_found_response("Product not found")

        return success_response(product, "Stock updated successfully")

    elif 'quantity_change' in data:
        # Relative stock adjustment
        quantity_change = data['quantity_change']
        if not isinstance(quantity_change, int):
            return bad_request_response("quantity_change must be an integer")

        product = ProductService.adjust_stock(product_id, quantity_change)
        if not product:
            return not_found_response("Product not found")

        return success_response(product, "Stock adjusted successfully")

    else:
        return bad_request_response("Either stock_quantity or quantity_change is required")
