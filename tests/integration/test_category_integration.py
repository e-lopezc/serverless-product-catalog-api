#!/usr/bin/env python3
"""
Simple test script for Category model
Run this to test the category functionality locally
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

from services.category_service import CategoryService
from utils.exceptions import ValidationError, DuplicateError


def test_category_operations():
    """Test basic category operations"""

    print("🧪 Testing Category operations...")

    try:
        # Test 1: Create a category
        print("\n1. Creating a category...")
        category_data = {
            'name': 'Test Category',
            'description': 'This is a test category for demonstration purposes'
        }

        category = CategoryService.create_category(category_data)
        print(f"✅ Category created: {category['name']} (ID: {category['category_id']})")
        category_id = category['category_id']

        # Test 2: Get the category
        print(f"\n2. Getting category by ID: {category_id}")
        retrieved_category = CategoryService.get_category(category_id)
        if retrieved_category:
            print(f"✅ Category retrieved: {retrieved_category['name']}")
        else:
            print("❌ Category not found")

        # Test 3: Update the category
        print(f"\n3. Updating category...")
        update_data = {
            'description': 'Updated description for the test category',
            'name': 'Updated Test Category'
        }
        updated_category = CategoryService.update_category(category_id, update_data)
        print(f"✅ Category updated: {updated_category['name']} - {updated_category['description']}")

        # Test 4: List categories
        print(f"\n4. Listing categories...")
        categories_result = CategoryService.list_categories(limit=10)
        print(f"✅ Found {len(categories_result.get('items', []))} categories")

        # Test 5: Try to create duplicate name (should fail)
        print(f"\n5. Testing duplicate name validation...")
        try:
            duplicate_data = {
                'name': 'Updated Test Category',  # Same name as the updated category
                'description': 'This should fail due to duplicate name'
            }
            CategoryService.create_category(duplicate_data)
            print("❌ Duplicate validation failed - should have thrown error")
        except DuplicateError:
            print("✅ Duplicate name correctly rejected")

        # Test 6: Test validation errors
        print(f"\n6. Testing validation...")

        # Test empty name
        try:
            invalid_data = {
                'name': '',  # Empty name should fail
                'description': 'Valid description for testing purposes'
            }
            CategoryService.create_category(invalid_data)
            print("❌ Validation failed - should have thrown error for empty name")
        except ValidationError:
            print("✅ Empty name correctly rejected")

        # Test short description
        try:
            invalid_data = {
                'name': 'Valid Category Name',
                'description': 'Short'  # Too short description should fail
            }
            CategoryService.create_category(invalid_data)
            print("❌ Validation failed - should have thrown error for short description")
        except ValidationError:
            print("✅ Short description correctly rejected")

        # Test 7: Delete the category
        print(f"\n7. Deleting category...")
        deleted = CategoryService.delete_category(category_id)
        if deleted:
            print("✅ Category deleted successfully")

            # Verify deletion
            deleted_category = CategoryService.get_category(category_id)
            if not deleted_category:
                print("✅ Category deletion verified - category no longer exists")
            else:
                print("❌ Category deletion verification failed - category still exists")
        else:
            print("❌ Category deletion failed")

        print("\n🎉 All tests completed!")

    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_category_operations()
