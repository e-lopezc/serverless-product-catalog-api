import json
import boto3
import os
import logging
from botocore.exceptions import ClientError

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')

# Lambda handler function
def lambda_handler(event, context):
    try:
        # Get table name from environment variable
        dynamodb_table_name = os.getenv('DYNAMO_TABLE_NAME')
        
        # Check if table name is provided
        if not dynamodb_table_name:
            logger.error("Environment variable DYNAMO_TABLE_NAME is not set")
            return {
                'statusCode': 500,
                'body': json.dumps('Configuration error: DynamoDB table name not specified')
            }
        
        # Get the table
        table = dynamodb.Table(dynamodb_table_name)
        
        # Try to get the item
        try:
            response = table.get_item(Key={
                'id': '1'
            })
            
            # Check if item exists
            if 'Item' not in response:
                logger.warning(f"Item with id '1' not found in table {dynamodb_table_name}")
                # Initialize with views = 1 if item doesn't exist
                views = 1
            else:
                views = response['Item']['views']
                views += 1
            
            logger.info(f"Updated view count: {views}")
            
            # Update the item
            table.put_item(Item={
                'id': '1',
                'views': views
            })
            
            return {
                'statusCode': 200,
                'body': json.dumps(views)
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            logger.error(f"DynamoDB operation failed: {error_code} - {error_message}")
            
            return {
                'statusCode': 500,
                'body': json.dumps(f'Database operation failed: {error_message}')
            }
            
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'An unexpected error occurred: {str(e)}')
        }
