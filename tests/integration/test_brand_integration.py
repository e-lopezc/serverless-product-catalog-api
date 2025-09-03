#!/usr/bin/env python3
"""
Simple test script for Brand model
Run this to test the brand functionality locally
"""

import os
import sys

# Add src to path so we can import our modules
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'src')
sys.path.insert(0, src_path)

# Set environment variables for local testing
os.environ['DYNAMODB_TABLE'] = 'products_catalog'
os.environ['AWS_REGION'] = 'us-east-1'
os.environ['DYNAMODB_ENDPOINT'] = 'http://localhost:8000'

from services.brand_service import BrandService
from utils.exceptions import ValidationError, DuplicateError


def test_brand_operations():
    """Test basic brand operations"""

    print("🧪 Testing Brand operations...")

    try:
        # Test 1: Create a brand
        print("\n1. Creating a brand...")
        brand_data = {
            'name': 'Test Brand',
            'description': 'This is a test brand for demonstration purposes',
            'website': 'https://testbrand.com'
        }

        brand = BrandService.create_brand(brand_data)
        print(f"✅ Brand created: {brand['name']} (ID: {brand['brand_id']})")
        brand_id = brand['brand_id']

        # Test 2: Get the brand
        print(f"\n2. Getting brand by ID: {brand_id}")
        retrieved_brand = BrandService.get_brand(brand_id)
        if retrieved_brand:
            print(f"✅ Brand retrieved: {retrieved_brand['name']}")
        else:
            print("❌ Brand not found")

        # Test 3: Update the brand
        print(f"\n3. Updating brand...")
        update_data = {
            'description': 'Updated description for the test brand',
            'website': 'https://updated-testbrand.com'
        }
        updated_brand = BrandService.update_brand(brand_id, update_data)
        print(f"✅ Brand updated: {updated_brand['description']}")

        # Test 4: List brands
        print(f"\n4. Listing brands...")
        brands_result = BrandService.list_brands(limit=10)
        print(f"✅ Found {len(brands_result.get('items', []))} brands")

        # Test 5: Try to create duplicate name (should fail)
        print(f"\n5. Testing duplicate name validation...")
        try:
            duplicate_data = {
                'name': 'Test Brand',  # Same name as before
                'description': 'This should fail due to duplicate name'
            }
            BrandService.create_brand(duplicate_data)
            print("❌ Duplicate validation failed - should have thrown error")
        except DuplicateError:
            print("✅ Duplicate name correctly rejected")

        # Test 6: Test validation errors
        print(f"\n6. Testing validation...")
        try:
            invalid_data = {
                'name': '',  # Empty name should fail
                'description': 'Valid description'
            }
            BrandService.create_brand(invalid_data)
            print("❌ Validation failed - should have thrown error")
        except ValidationError:
            print("✅ Empty name correctly rejected")

        # Test 7: Delete the brand
        print(f"\n7. Deleting brand...")
        deleted = BrandService.delete_brand(brand_id)
        if deleted:
            print("✅ Brand deleted successfully")
        else:
            print("❌ Brand deletion failed")

        print("\n🎉 All tests completed!")

    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_brand_operations()
