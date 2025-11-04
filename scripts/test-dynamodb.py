#!/usr/bin/env python3
"""
DynamoDB Local Connectivity Test Script
This script tests the connection to DynamoDB Local and verifies table setup
"""

import boto3
import json
import sys
import os
from botocore.exceptions import ClientError, EndpointConnectionError, NoCredentialsError

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_success(text: str) -> None:
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text: str) -> None:
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_warning(text: str) -> None:
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_info(text: str) -> None:
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")

def print_header(text: str) -> None:
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*50}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(50)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*50}{Colors.END}")

def test_dynamodb_connection(endpoint_url: str = "http://localhost:8000",
                           region: str = "us-east-1") -> bool:
    """Test basic DynamoDB connection"""
    print_header("DYNAMODB CONNECTION TEST")

    try:
        # Create DynamoDB client
        dynamodb = boto3.client(
            'dynamodb',
            endpoint_url=endpoint_url,
            region_name=region,
            aws_access_key_id='local',
            aws_secret_access_key='local'
        )

        print_info(f"Testing connection to {endpoint_url}...")

        # Try to list tables
        response = dynamodb.list_tables()
        print_success("Successfully connected to DynamoDB Local")

        table_names = response.get('TableNames', [])
        if table_names:
            print_success(f"Found {len(table_names)} table(s):")
            for table_name in table_names:
                print(f"  - {table_name}")
        else:
            print_warning("No tables found")

        return True

    except EndpointConnectionError:
        print_error("Could not connect to DynamoDB Local")
        print_info("Make sure DynamoDB Local is running:")
        print_info("  docker-compose -f docker-compose.dev.yml up -d")
        return False

    except NoCredentialsError:
        print_error("AWS credentials not configured")
        print_info("For local development, we use dummy credentials")
        return False

    except ClientError as e:
        print_error(f"DynamoDB API error: {e}")
        return False

    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False

def test_table_structure(table_name: str = "products_catalog",
                        endpoint_url: str = "http://localhost:8000",
                        region: str = "us-east-1") -> bool:
    """Test specific table structure"""
    print_header(f"TABLE STRUCTURE TEST: {table_name}")

    try:
        dynamodb = boto3.client(
            'dynamodb',
            endpoint_url=endpoint_url,
            region_name=region,
            aws_access_key_id='local',
            aws_secret_access_key='local'
        )

        # Describe the table
        response = dynamodb.describe_table(TableName=table_name)
        table_info = response['Table']

        print_success(f"Table '{table_name}' found")
        print_info(f"Table Status: {table_info['TableStatus']}")
        print_info(f"Billing Mode: {table_info.get('BillingModeSummary', {}).get('BillingMode', 'PROVISIONED')}")

        # Check key schema
        key_schema = table_info['KeySchema']
        print_info("Key Schema:")
        for key in key_schema:
            print(f"  - {key['AttributeName']} ({key['KeyType']})")

        # Check GSIs
        gsis = table_info.get('GlobalSecondaryIndexes', [])
        if gsis:
            print_info(f"Global Secondary Indexes ({len(gsis)}):")
            for gsi in gsis:
                print(f"  - {gsi['IndexName']}")
                for key in gsi['KeySchema']:
                    print(f"    {key['AttributeName']} ({key['KeyType']})")
        else:
            print_warning("No Global Secondary Indexes found")

        return True

    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ResourceNotFoundException':
            print_error(f"Table '{table_name}' does not exist")
            print_info("Create the table by running:")
            print_info("  ./scripts/local-dev-setup.sh")
        else:
            print_error(f"Error describing table: {e}")
        return False

    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False

def test_basic_operations(table_name: str = "products_catalog",
                         endpoint_url: str = "http://localhost:8000",
                         region: str = "us-east-1") -> bool:
    """Test basic CRUD operations"""
    print_header("BASIC OPERATIONS TEST")

    try:
        dynamodb = boto3.resource(
            'dynamodb',
            endpoint_url=endpoint_url,
            region_name=region,
            aws_access_key_id='local',
            aws_secret_access_key='local'
        )

        table = dynamodb.Table(table_name)

        # Test item to insert/update/delete
        test_item = {
            'PK': 'TEST#connectivity-test',
            'SK': 'TEST#connectivity-test',
            'entity_type': 'test',
            'test_data': 'DynamoDB connectivity test',
            'timestamp': '2024-01-01T00:00:00Z'
        }

        print_info("Testing PUT operation...")
        table.put_item(Item=test_item)
        print_success("PUT operation successful")

        print_info("Testing GET operation...")
        response = table.get_item(
            Key={
                'PK': test_item['PK'],
                'SK': test_item['SK']
            }
        )

        if 'Item' in response:
            print_success("GET operation successful")
            retrieved_item = response['Item']
            if retrieved_item['test_data'] == test_item['test_data']:
                print_success("Data integrity verified")
            else:
                print_warning("Data integrity issue detected")
        else:
            print_error("GET operation failed - item not found")
            return False

        print_info("Testing UPDATE operation...")
        table.update_item(
            Key={
                'PK': test_item['PK'],
                'SK': test_item['SK']
            },
            UpdateExpression='SET test_data = :val',
            ExpressionAttributeValues={
                ':val': 'Updated test data'
            }
        )
        print_success("UPDATE operation successful")

        print_info("Testing DELETE operation...")
        table.delete_item(
            Key={
                'PK': test_item['PK'],
                'SK': test_item['SK']
            }
        )
        print_success("DELETE operation successful")

        # Verify deletion
        response = table.get_item(
            Key={
                'PK': test_item['PK'],
                'SK': test_item['SK']
            }
        )

        if 'Item' not in response:
            print_success("DELETE verification successful")
        else:
            print_warning("DELETE verification failed - item still exists")

        return True

    except Exception as e:
        print_error(f"Basic operations test failed: {e}")
        return False

def test_gsi_queries(table_name: str = "products_catalog",
                    endpoint_url: str = "http://localhost:8000",
                    region: str = "us-east-1") -> bool:
    """Test Global Secondary Index queries"""
    print_header("GSI QUERY TEST")

    try:
        dynamodb = boto3.resource(
            'dynamodb',
            endpoint_url=endpoint_url,
            region_name=region,
            aws_access_key_id='local',
            aws_secret_access_key='local'
        )

        table = dynamodb.Table(table_name)

        print_info("Testing GSI-1 query (inverted index)...")
        response = table.query(
            IndexName='GSI-1',
            KeyConditionExpression='SK = :sk',
            ExpressionAttributeValues={
                ':sk': 'BRAND#test'
            },
            Limit=1
        )
        print_success("GSI-1 query successful")

        print_info("Testing GSI-3 query (brand list)...")
        response = table.query(
            IndexName='GSI-3',
            KeyConditionExpression='GSI3PK = :pk',
            ExpressionAttributeValues={
                ':pk': 'BRAND_LIST'
            },
            Limit=1
        )
        print_success("GSI-3 query successful")

        return True

    except Exception as e:
        print_error(f"GSI query test failed: {e}")
        return False

def run_comprehensive_test(endpoint_url: str = "http://localhost:8000",
                          region: str = "us-east-1",
                          table_name: str = "products_catalog") -> bool:
    """Run comprehensive DynamoDB test suite"""
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("╔══════════════════════════════════════════════════════╗")
    print("║           DYNAMODB LOCAL TEST SUITE                 ║")
    print("╚══════════════════════════════════════════════════════╝")
    print(f"{Colors.END}")

    print_info(f"Endpoint: {endpoint_url}")
    print_info(f"Region: {region}")
    print_info(f"Table: {table_name}")

    tests = [
        ("Connection Test", lambda: test_dynamodb_connection(endpoint_url, region)),
        ("Table Structure Test", lambda: test_table_structure(table_name, endpoint_url, region)),
        ("Basic Operations Test", lambda: test_basic_operations(table_name, endpoint_url, region)),
        ("GSI Query Test", lambda: test_gsi_queries(table_name, endpoint_url, region))
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"{test_name} failed with exception: {e}")
            results.append((test_name, False))

    # Print summary
    print_header("TEST SUMMARY")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.END}\n")

    for test_name, result in results:
        status = "✓" if result else "✗"
        color = Colors.GREEN if result else Colors.RED
        print(f"{color}{status} {test_name}{Colors.END}")

    if passed == total:
        print_success("\n🎉 All tests passed! DynamoDB Local is working correctly.")
        return True
    else:
        print_warning(f"\n⚠️  {total - passed} test(s) failed. Please check your setup.")

        if not results[0][1]:  # Connection test failed
            print_info("\nTroubleshooting steps:")
            print_info("1. Start DynamoDB Local:")
            print_info("   docker-compose -f docker-compose.dev.yml up -d")
            print_info("2. Wait a few seconds for startup")
            print_info("3. Re-run this test")

        elif not results[1][1]:  # Table structure test failed
            print_info("\nTable setup required:")
            print_info("1. Run the setup script:")
            print_info("   ./scripts/local-dev-setup.sh")
            print_info("2. Re-run this test")

        return False

def main():
    """Main function"""
    # Default configuration
    endpoint_url = os.getenv('DYNAMODB_ENDPOINT', 'http://localhost:8000')
    region = os.getenv('AWS_REGION', 'us-east-1')
    table_name = os.getenv('DYNAMODB_TABLE', 'products_catalog')

    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help']:
            print("DynamoDB Local Test Script")
            print("\nUsage:")
            print("  python scripts/test-dynamodb.py [options]")
            print("\nOptions:")
            print("  -h, --help    Show this help message")
            print("  --quick       Run quick connection test only")
            print("\nEnvironment Variables:")
            print("  DYNAMODB_ENDPOINT  DynamoDB endpoint (default: http://localhost:8000)")
            print("  AWS_REGION         AWS region (default: us-east-1)")
            print("  DYNAMODB_TABLE     Table name (default: products_catalog)")
            print("\nExamples:")
            print("  python scripts/test-dynamodb.py")
            print("  python scripts/test-dynamodb.py --quick")
            print("  DYNAMODB_ENDPOINT=http://localhost:8001 python scripts/test-dynamodb.py")
            sys.exit(0)
        elif sys.argv[1] == '--quick':
            # Quick test - connection only
            success = test_dynamodb_connection(endpoint_url, region)
            sys.exit(0 if success else 1)

    # Run comprehensive test
    success = run_comprehensive_test(endpoint_url, region, table_name)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
