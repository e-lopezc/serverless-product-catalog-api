#!/usr/bin/env python3
"""
Integration Test Runner
Run all integration tests for the serverless product catalog API
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_dynamodb_local():
    """Check if DynamoDB Local is running"""
    try:
        import requests
        response = requests.get('http://localhost:8000')
        return response.status_code == 400  # DynamoDB Local returns 400 for GET requests
    except:
        return False

def run_test_file(test_file):
    """Run a single test file"""
    print(f"\n{'='*60}")
    print(f"Running: {test_file}")
    print(f"{'='*60}")

    try:
        result = subprocess.run([sys.executable, test_file],
                              capture_output=True,
                              text=True,
                              timeout=120)

        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        if result.returncode == 0:
            print(f"✅ {test_file} PASSED")
            return True
        else:
            print(f"❌ {test_file} FAILED (exit code: {result.returncode})")
            return False

    except subprocess.TimeoutExpired:
        print(f"⏰ {test_file} TIMED OUT (> 120 seconds)")
        return False
    except Exception as e:
        print(f"💥 {test_file} ERROR: {str(e)}")
        return False

def main():
    """Main test runner"""
    print("🧪 Integration Test Runner for Serverless Product Catalog API")
    print("="*60)

    # Get the tests directory
    tests_dir = Path(__file__).parent
    integration_dir = tests_dir / 'integration'

    # Check if integration directory exists
    if not integration_dir.exists():
        print("❌ Integration tests directory not found")
        sys.exit(1)

    # Find all integration test files
    test_files = list(integration_dir.glob('test_*_integration.py'))

    if not test_files:
        print("❌ No integration test files found")
        sys.exit(1)

    print(f"Found {len(test_files)} integration test files:")
    for test_file in test_files:
        print(f"  • {test_file.name}")

    # Check if DynamoDB Local is running
    print(f"\n🔍 Checking DynamoDB Local connection...")
    if check_dynamodb_local():
        print("✅ DynamoDB Local is running on http://localhost:8000")
    else:
        print("⚠️  DynamoDB Local not detected on http://localhost:8000")
        print("   Make sure DynamoDB Local is running or set DYNAMODB_ENDPOINT for AWS")

        user_input = input("\nContinue anyway? (y/N): ").strip().lower()
        if user_input != 'y':
            print("Exiting...")
            sys.exit(1)

    # Set environment variables for testing
    os.environ['DYNAMODB_TABLE'] = 'products_catalog'
    os.environ['AWS_REGION'] = 'us-east-1'
    if not os.getenv('DYNAMODB_ENDPOINT'):
        os.environ['DYNAMODB_ENDPOINT'] = 'http://localhost:8000'

    print(f"\n📋 Test Environment:")
    print(f"   DYNAMODB_TABLE: {os.environ.get('DYNAMODB_TABLE')}")
    print(f"   AWS_REGION: {os.environ.get('AWS_REGION')}")
    print(f"   DYNAMODB_ENDPOINT: {os.environ.get('DYNAMODB_ENDPOINT')}")

    # Run tests
    print(f"\n🚀 Starting integration tests...")
    start_time = time.time()

    passed = 0
    failed = 0

    # Sort test files for consistent order
    test_files.sort()

    for test_file in test_files:
        if run_test_file(str(test_file)):
            passed += 1
        else:
            failed += 1

        # Small delay between tests
        time.sleep(1)

    # Summary
    end_time = time.time()
    duration = end_time - start_time

    print(f"\n{'='*60}")
    print(f"TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Total tests: {passed + failed}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⏱️  Duration: {duration:.2f} seconds")

    if failed == 0:
        print(f"\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"\n💥 {failed} test(s) failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()
