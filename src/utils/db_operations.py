import boto3
import json
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from config.settings import (
    TABLE_NAME, PK_FIELD, SK_FIELD,
    GSI1_NAME, GSI1_PK, GSI1_SK,
    GSI2_NAME, GSI2_PK, GSI2_SK,
    GSI3_NAME, GSI3_PK, GSI3_SK,
    AWS_REGION
)
from utils.exceptions import NotFoundError, DuplicateError, DatabaseError


class DynamoDbClient:
    def __init__(self):
        # Support for local development with DynamoDB Local
        import os
        endpoint_url = os.getenv('DYNAMODB_ENDPOINT')

        if endpoint_url:
            # Local development
            self.dynamodb = boto3.resource(
                'dynamodb',
                region_name=AWS_REGION,
                endpoint_url=endpoint_url
            )
        else:
            # Production
            self.dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)

        self.table = self.dynamodb.Table(TABLE_NAME)

    def get_item(self, pk, sk):
        """Get a single item by partition key and sort key"""
        try:
            response = self.table.get_item(
                Key={
                    PK_FIELD: pk,
                    SK_FIELD: sk
                }
            )
            item = response.get('Item')
            if item:
                return self._convert_decimal_to_float(item)
            return None
        except ClientError as e:
            raise DatabaseError(f"Failed to get item: {str(e)}")

    def put_item(self, item, condition_expression=None):
        """Create or update an item"""
        try:
            # Convert any float values to Decimal for DynamoDB
            item = self._convert_floats_to_decimal(item)

            kwargs = {'Item': item}
            if condition_expression:
                kwargs['ConditionExpression'] = condition_expression

            response = self.table.put_item(**kwargs)
            return response
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise DuplicateError("Item already exists or condition not met")
            raise DatabaseError(f"Failed to put item: {str(e)}")

    def update_item(self, pk, sk, updates, condition_expression=None):
        """Update an existing item"""
        try:
            # Build update expression
            update_expression = "SET "
            expression_attribute_names = {}
            expression_attribute_values = {}

            for i, (key, value) in enumerate(updates.items()):
                if i > 0:
                    update_expression += ", "

                attr_name = f"#attr{i}"
                attr_value = f":val{i}"

                update_expression += f"{attr_name} = {attr_value}"
                expression_attribute_names[attr_name] = key
                expression_attribute_values[attr_value] = self._convert_floats_to_decimal(value)

            kwargs = {
                'Key': {PK_FIELD: pk, SK_FIELD: sk},
                'UpdateExpression': update_expression,
                'ExpressionAttributeNames': expression_attribute_names,
                'ExpressionAttributeValues': expression_attribute_values,
                'ReturnValues': 'ALL_NEW'
            }

            if condition_expression:
                kwargs['ConditionExpression'] = condition_expression

            response = self.table.update_item(**kwargs)
            updated_item = response.get('Attributes')
            if updated_item:
                return self._convert_decimal_to_float(updated_item)
            return None

        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise NotFoundError("Item not found or condition not met")
            raise DatabaseError(f"Failed to update item: {str(e)}")

    def delete_item(self, pk, sk, condition_expression=None):
        """Delete an item"""
        try:
            kwargs = {
                'Key': {PK_FIELD: pk, SK_FIELD: sk},
                'ReturnValues': 'ALL_OLD'
            }

            if condition_expression:
                kwargs['ConditionExpression'] = condition_expression

            response = self.table.delete_item(**kwargs)
            deleted_item = response.get('Attributes')
            if deleted_item:
                return self._convert_decimal_to_float(deleted_item)
            return None

        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise NotFoundError("Item not found")
            raise DatabaseError(f"Failed to delete item: {str(e)}")

    # Query Methods for the GSI structure

    def list_entities_by_type(self, entity_type, limit=50, last_evaluated_key=None):
        """
        List all entities of a specific type using GSI-1 (inverted index)
        Query where SK begins_with entity_type
        """
        try:
            key_condition = Key(GSI1_PK).begins_with(f"{entity_type}#")

            kwargs = {
                'IndexName': GSI1_NAME,
                'KeyConditionExpression': key_condition,
                'Limit': limit
            }

            if last_evaluated_key:
                kwargs['ExclusiveStartKey'] = last_evaluated_key

            response = self.table.query(**kwargs)
            return {
                'items': [self._convert_decimal_to_float(item) for item in response.get('Items', [])],
                'last_evaluated_key': response.get('LastEvaluatedKey')
            }

        except ClientError as e:
            raise DatabaseError(f"Failed to list entities: {str(e)}")

    def get_products_by_brand(self, brand_id, limit=50, last_evaluated_key=None):
        """
        Get products by brand using GSI-2
        Query where brand_id = brand_id
        """
        try:
            key_condition = Key(GSI2_PK).eq(brand_id)

            kwargs = {
                'IndexName': GSI2_NAME,
                'KeyConditionExpression': key_condition,
                'Limit': limit
            }

            if last_evaluated_key:
                kwargs['ExclusiveStartKey'] = last_evaluated_key

            response = self.table.query(**kwargs)
            return {
                'items': [self._convert_decimal_to_float(item) for item in response.get('Items', [])],
                'last_evaluated_key': response.get('LastEvaluatedKey')
            }

        except ClientError as e:
            raise DatabaseError(f"Failed to get products by brand: {str(e)}")

    def query_gsi3(self, gsi3_pk, gsi3_sk_begins_with=None, limit=50, last_evaluated_key=None):
        """
        Flexible query using GSI-3
        Can be used for:
        - List brands by name: GSI3PK="BRAND_LIST"
        - List categories by name: GSI3PK="CATEGORY_LIST"
        - Get products by category: GSI3PK="CATEGORY#{id}"
        """
        try:
            key_condition = Key(GSI3_PK).eq(gsi3_pk)

            if gsi3_sk_begins_with:
                key_condition = key_condition & Key(GSI3_SK).begins_with(gsi3_sk_begins_with)

            kwargs = {
                'IndexName': GSI3_NAME,
                'KeyConditionExpression': key_condition,
                'Limit': limit
            }

            if last_evaluated_key:
                kwargs['ExclusiveStartKey'] = last_evaluated_key

            response = self.table.query(**kwargs)
            return {
                'items': [self._convert_decimal_to_float(item) for item in response.get('Items', [])],
                'last_evaluated_key': response.get('LastEvaluatedKey')
            }

        except ClientError as e:
            raise DatabaseError(f"Failed to query GSI3: {str(e)}")

    def get_products_by_category(self, category_id, limit=50, last_evaluated_key=None):
        """
        Get products by category using GSI-3
        Query where GSI3PK = "CATEGORY#{category_id}"
        """
        return self.query_gsi3(
            gsi3_pk=f"CATEGORY#{category_id}",
            limit=limit,
            last_evaluated_key=last_evaluated_key
        )

    def list_brands_by_name(self, limit=50, last_evaluated_key=None):
        """
        List brands sorted by name using GSI-3
        Query where GSI3PK = "BRAND_LIST"
        """
        return self.query_gsi3(
            gsi3_pk="BRAND_LIST",
            limit=limit,
            last_evaluated_key=last_evaluated_key
        )

    def list_categories_by_name(self, limit=50, last_evaluated_key=None):
        """
        List categories sorted by name using GSI-3
        Query where GSI3PK = "CATEGORY_LIST"
        """
        return self.query_gsi3(
            gsi3_pk="CATEGORY_LIST",
            limit=limit,
            last_evaluated_key=last_evaluated_key
        )

    def batch_get_items(self, keys):
        """Get multiple items in a single request"""
        try:
            # DynamoDB batch_get_item expects keys in a specific format
            request_items = {
                TABLE_NAME: {
                    'Keys': [
                        {PK_FIELD: key['pk'], SK_FIELD: key['sk']}
                        for key in keys
                    ]
                }
            }

            response = self.dynamodb.batch_get_item(RequestItems=request_items)
            items = response.get('Responses', {}).get(TABLE_NAME, [])
            return [self._convert_decimal_to_float(item) for item in items]

        except ClientError as e:
            raise DatabaseError(f"Failed to batch get items: {str(e)}")

    def batch_write_items(self, items_to_put=None, items_to_delete=None):
        """Batch write (put/delete) multiple items"""
        try:
            request_items = {TABLE_NAME: []}

            if items_to_put:
                for item in items_to_put:
                    request_items[TABLE_NAME].append({
                        'PutRequest': {
                            'Item': self._convert_floats_to_decimal(item)
                        }
                    })

            if items_to_delete:
                for key in items_to_delete:
                    request_items[TABLE_NAME].append({
                        'DeleteRequest': {
                            'Key': {PK_FIELD: key['pk'], SK_FIELD: key['sk']}
                        }
                    })

            response = self.dynamodb.batch_write_item(RequestItems=request_items)
            return response

        except ClientError as e:
            raise DatabaseError(f"Failed to batch write items: {str(e)}")

    def check_item_exists(self, pk, sk):
        """Check if an item exists without returning the full item"""
        try:
            response = self.table.get_item(
                Key={PK_FIELD: pk, SK_FIELD: sk},
                ProjectionExpression=PK_FIELD  # Only return PK to minimize data transfer
            )
            return 'Item' in response
        except ClientError as e:
            raise DatabaseError(f"Failed to check item existence: {str(e)}")

    def _convert_floats_to_decimal(self, obj):
        """Convert float values to Decimal for DynamoDB compatibility"""
        if isinstance(obj, dict):
            return {k: self._convert_floats_to_decimal(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_floats_to_decimal(item) for item in obj]
        elif isinstance(obj, float):
            return Decimal(str(obj))
        else:
            return obj

    def _convert_decimal_to_float(self, obj):
        """Convert Decimal values back to float for JSON serialization, preserving integers"""
        if isinstance(obj, dict):
            return {k: self._convert_decimal_to_float(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_decimal_to_float(item) for item in obj]
        elif isinstance(obj, Decimal):
            # Check if the Decimal represents a whole number
            if obj % 1 == 0:
                return int(obj)
            else:
                return float(obj)
        else:
            return obj


# Singleton instance
db_client = DynamoDbClient()
