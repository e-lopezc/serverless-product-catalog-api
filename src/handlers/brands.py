import json
from typing import Dict, Any

from services.brand_service import BrandService
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
    Main Lambda handler for brands API

    Routes:
    - GET /brands - List all brands
    - POST /brands - Create a new brand
    - GET /brands/{brand_id} - Get a specific brand
    - PUT /brands/{brand_id} - Update a brand
    - DELETE /brands/{brand_id} - Delete a brand
    """

    # Log request information
    log_request_info(logger, event)

    http_method = event.get('httpMethod')
    path_parameters = event.get('pathParameters') or {}
    brand_id = path_parameters.get('id')  # Note: SAM template uses {id} not {brand_id}

    logger.debug(f"Brand ID extracted: {brand_id}")

    try:
        if http_method == 'GET':
            if brand_id:
                # Get specific brand
                brand = BrandService.get_brand(brand_id)
                if not brand:
                    return not_found_response("Brand not found")
                return success_response(brand)
            else:
                # List all brands
                limit = int(get_query_parameter(event, 'limit', 50))
                last_key = get_query_parameter(event, 'last_key')

                # Parse last_key if provided
                last_evaluated_key = None
                if last_key:
                    try:
                        last_evaluated_key = json.loads(last_key)
                    except json.JSONDecodeError:
                        return bad_request_response("Invalid last_key format")

                brands_data = BrandService.list_brands(limit, last_evaluated_key)
                return success_response(brands_data)

        elif http_method == 'POST':
            # Create new brand
            data = parse_json_body(event)
            brand = BrandService.create_brand(data)
            return created_response(brand, "Brand created successfully")

        elif http_method == 'PUT':
            if not brand_id:
                return bad_request_response("Brand ID is required")

            # Update brand
            data = parse_json_body(event)
            brand = BrandService.update_brand(brand_id, data)
            if not brand:
                return not_found_response("Brand not found")
            return success_response(brand, "Brand updated successfully")

        elif http_method == 'DELETE':
            if not brand_id:
                return bad_request_response("Brand ID is required")

            # Delete brand
            deleted = BrandService.delete_brand(brand_id)
            if not deleted:
                return not_found_response("Brand not found")
            return success_response(None, "Brand deleted successfully")

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
        logger.error(f"Unexpected error in brands handler: {str(e)}", exc_info=True)
        return server_error_response("An unexpected error occurred")
