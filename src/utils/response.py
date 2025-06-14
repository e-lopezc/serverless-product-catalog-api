import json
from typing import Any, Dict, Optional
from decimal import Decimal


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal types"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def create_response(
    status_code: int,
    body: Any = None,
    message: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Create a standardized API response

    Args:
        status_code: HTTP status code
        body: Response body data
        message: Optional message
        headers: Optional headers

    Returns:
        API Gateway response dict
    """
    default_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Amz-Date, X-Api-Key, X-Amz-Security-Token'
    }

    if headers:
        default_headers.update(headers)

    response_body = {}

    if message:
        response_body['message'] = message

    if body is not None:
        if isinstance(body, dict) and 'data' not in body:
            response_body['data'] = body
        else:
            response_body.update(body if isinstance(body, dict) else {'data': body})

    return {
        'statusCode': status_code,
        'headers': default_headers,
        'body': json.dumps(response_body, cls=DecimalEncoder)
    }


def success_response(data: Any = None, message: str = "Success") -> Dict[str, Any]:
    """Create a success response (200)"""
    return create_response(200, data, message)


def created_response(data: Any = None, message: str = "Created successfully") -> Dict[str, Any]:
    """Create a created response (201)"""
    return create_response(201, data, message)


def bad_request_response(message: str = "Bad request") -> Dict[str, Any]:
    """Create a bad request response (400)"""
    return create_response(400, message=message)


def not_found_response(message: str = "Not found") -> Dict[str, Any]:
    """Create a not found response (404)"""
    return create_response(404, message=message)


def conflict_response(message: str = "Conflict") -> Dict[str, Any]:
    """Create a conflict response (409)"""
    return create_response(409, message=message)


def server_error_response(message: str = "Internal server error") -> Dict[str, Any]:
    """Create a server error response (500)"""
    return create_response(500, message=message)


def parse_json_body(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse JSON body from API Gateway event

    Args:
        event: API Gateway event

    Returns:
        Parsed JSON data

    Raises:
        ValueError: If JSON is invalid
    """
    body = event.get('body', '{}')

    if not body:
        return {}

    try:
        return json.loads(body)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {str(e)}")


def get_query_parameter(event: Dict[str, Any], param_name: str, default_value: Any = None) -> Any:
    """
    Get query parameter from API Gateway event

    Args:
        event: API Gateway event
        param_name: Parameter name
        default_value: Default value if parameter not found

    Returns:
        Parameter value or default
    """
    query_params = event.get('queryStringParameters') or {}
    return query_params.get(param_name, default_value)
