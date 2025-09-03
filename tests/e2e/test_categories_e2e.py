#!/usr/bin/env python3
"""
End-to-End Tests for Categories API
Tests the deployed API endpoints for category operations
"""

import os
import sys
import requests
import json
import time
from typing import Dict, Any, Optional, List

# Configuration
API_BASE_URL = os.getenv('API_BASE_URL')
API_TIMEOUT = 30  # seconds


class CategoriesE2ETest:
    """End-to-end test class for Categories API"""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.categories_url = f"{self.base_url}/categories"
        self.created_category_ids: List[str] = []
        self.session = requests.Session()

        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def cleanup(self):
        """Clean up any created test data"""
        print(f"\n🧹 Cleaning up {len(self.created_category_ids)} test categories...")

        for category_id in self.created_category_ids:
            try:
                response = self.session.delete(f"{self.categories_url}/{category_id}", timeout=API_TIMEOUT)
                if response.status_code == 200:
                    print(f"✅ Deleted category: {category_id}")
                else:
                    print(f"⚠️  Failed to delete category {category_id}: {response.status_code}")
            except Exception as e:
                print(f"❌ Error deleting category {category_id}: {str(e)}")

        self.created_category_ids.clear()

    def test_create_category(self) -> Optional[str]:
        """Test POST /categories - Create a new category"""
        print("\n1. Testing CREATE category (POST /categories)")

        category_data = {
            "name": "E2E Test Category",
            "description": "This is a test category created during end-to-end testing"
        }

        try:
            response = self.session.post(self.categories_url, json=category_data, timeout=API_TIMEOUT)

            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")

            if response.status_code == 201:
                response_data = response.json()
                category_id = response_data['data']['category_id']
                self.created_category_ids.append(category_id)
                print(f"✅ Category created successfully: {category_id}")
                return category_id
            else:
                print(f"❌ Failed to create category: {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ Error creating category: {str(e)}")
            return None

    def test_get_category(self, category_id: str) -> bool:
        """Test GET /categories/{id} - Get a specific category"""
        print(f"\n2. Testing GET category (GET /categories/{category_id})")

        try:
            response = self.session.get(f"{self.categories_url}/{category_id}", timeout=API_TIMEOUT)

            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")

            if response.status_code == 200:
                response_data = response.json()
                category = response_data['data']

                # Validate response structure
                required_fields = ['category_id', 'name', 'description', 'created_at', 'updated_at']
                for field in required_fields:
                    if field not in category:
                        print(f"❌ Missing field in response: {field}")
                        return False

                if category['category_id'] == category_id:
                    print(f"✅ Category retrieved successfully: {category['name']}")
                    return True
                else:
                    print(f"❌ Category ID mismatch: expected {category_id}, got {category['category_id']}")
                    return False
            else:
                print(f"❌ Failed to get category: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error getting category: {str(e)}")
            return False

    def test_list_categories(self) -> bool:
        """Test GET /categories - List all categories"""
        print("\n3. Testing LIST categories (GET /categories)")

        try:
            response = self.session.get(self.categories_url, timeout=API_TIMEOUT)

            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")

            if response.status_code == 200:
                response_data = response.json()

                # Check response structure
                if 'data' in response_data and 'items' in response_data['data']:
                    categories = response_data['data']['items']
                    print(f"✅ Listed {len(categories)} categories successfully")

                    # Validate that our test category is in the list
                    if self.created_category_ids:
                        test_category_found = any(
                            category.get('category_id') in self.created_category_ids
                            for category in categories
                        )
                        if test_category_found:
                            print("✅ Test category found in list")
                        else:
                            print("⚠️  Test category not found in list (might be pagination)")

                    return True
                else:
                    print("❌ Invalid response structure for list categories")
                    return False
            else:
                print(f"❌ Failed to list categories: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error listing categories: {str(e)}")
            return False

    def test_update_category(self, category_id: str) -> bool:
        """Test PUT /categories/{id} - Update a category"""
        print(f"\n4. Testing UPDATE category (PUT /categories/{category_id})")

        update_data = {
            "name": "Updated E2E Test Category",
            "description": "This category has been updated during end-to-end testing"
        }

        try:
            response = self.session.put(f"{self.categories_url}/{category_id}", json=update_data, timeout=API_TIMEOUT)

            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")

            if response.status_code == 200:
                response_data = response.json()
                updated_category = response_data['data']

                # Verify the updates were applied
                if (updated_category['name'] == update_data['name'] and
                    updated_category['description'] == update_data['description']):
                    print("✅ Category updated successfully")
                    return True
                else:
                    print("❌ Category update did not apply correctly")
                    return False
            else:
                print(f"❌ Failed to update category: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error updating category: {str(e)}")
            return False

    def test_list_categories_with_pagination(self) -> bool:
        """Test GET /categories with pagination parameters"""
        print("\n5. Testing LIST categories with pagination (GET /categories?limit=1)")

        try:
            response = self.session.get(f"{self.categories_url}?limit=1", timeout=API_TIMEOUT)

            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")

            if response.status_code == 200:
                response_data = response.json()

                if 'data' in response_data and 'items' in response_data['data']:
                    categories = response_data['data']['items']

                    if len(categories) <= 1:
                        print(f"✅ Pagination working: returned {len(categories)} category(s)")

                        # Check if last_evaluated_key is present when there are more items
                        if 'last_evaluated_key' in response_data['data']:
                            print("✅ Pagination key present for next page")

                        return True
                    else:
                        print(f"❌ Pagination failed: returned {len(categories)} categories (expected <= 1)")
                        return False
                else:
                    print("❌ Invalid response structure")
                    return False
            else:
                print(f"❌ Failed to list categories with pagination: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error testing pagination: {str(e)}")
            return False

    def test_create_category_validation_errors(self) -> bool:
        """Test POST /categories with invalid data to verify validation"""
        print("\n6. Testing category validation errors")

        test_cases = [
            {
                "name": "Empty name test",
                "data": {"name": "", "description": "Valid description for testing"},
                "expected_status": 400
            },
            {
                "name": "Missing description test",
                "data": {"name": "Valid Name"},
                "expected_status": 400
            },
            {
                "name": "Short description test",
                "data": {
                    "name": "Valid Name",
                    "description": "Short"  # Too short
                },
                "expected_status": 400
            },
            {
                "name": "Invalid characters in name",
                "data": {
                    "name": "Category@#$%^&*()",
                    "description": "Valid description for testing purposes"
                },
                "expected_status": 400
            }
        ]

        all_passed = True

        for test_case in test_cases:
            print(f"\n   Testing: {test_case['name']}")

            try:
                response = self.session.post(self.categories_url, json=test_case['data'], timeout=API_TIMEOUT)

                print(f"   Status Code: {response.status_code}")

                if response.status_code == test_case['expected_status']:
                    print(f"   ✅ Validation working correctly")
                else:
                    print(f"   ❌ Expected {test_case['expected_status']}, got {response.status_code}")
                    all_passed = False

            except Exception as e:
                print(f"   ❌ Error testing validation: {str(e)}")
                all_passed = False

        return all_passed

    def test_get_nonexistent_category(self) -> bool:
        """Test GET /categories/{id} with non-existent ID"""
        print("\n7. Testing GET non-existent category")

        fake_id = "00000000-0000-0000-0000-000000000000"

        try:
            response = self.session.get(f"{self.categories_url}/{fake_id}", timeout=API_TIMEOUT)

            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")

            if response.status_code == 404:
                print("✅ Correctly returned 404 for non-existent category")
                return True
            else:
                print(f"❌ Expected 404, got {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error testing non-existent category: {str(e)}")
            return False

    def test_update_nonexistent_category(self) -> bool:
        """Test PUT /categories/{id} with non-existent ID"""
        print("\n8. Testing UPDATE non-existent category")

        fake_id = "00000000-0000-0000-0000-000000000000"
        update_data = {
            "name": "Non-existent Category",
            "description": "This should fail because the category doesn't exist"
        }

        try:
            response = self.session.put(f"{self.categories_url}/{fake_id}", json=update_data, timeout=API_TIMEOUT)

            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")

            if response.status_code == 404:
                print("✅ Correctly returned 404 for updating non-existent category")
                return True
            else:
                print(f"❌ Expected 404, got {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error testing update non-existent category: {str(e)}")
            return False

    def test_delete_category(self, category_id: str) -> bool:
        """Test DELETE /categories/{id} - Delete a category"""
        print(f"\n9. Testing DELETE category (DELETE /categories/{category_id})")

        try:
            response = self.session.delete(f"{self.categories_url}/{category_id}", timeout=API_TIMEOUT)

            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")

            if response.status_code == 200:
                # Remove from our tracking list since it's now deleted
                if category_id in self.created_category_ids:
                    self.created_category_ids.remove(category_id)

                print("✅ Category deleted successfully")

                # Verify it's actually deleted by trying to get it
                get_response = self.session.get(f"{self.categories_url}/{category_id}", timeout=API_TIMEOUT)
                if get_response.status_code == 404:
                    print("✅ Verified category was deleted (GET returns 404)")
                    return True
                else:
                    print(f"❌ Category still exists after deletion (GET returns {get_response.status_code})")
                    return False
            else:
                print(f"❌ Failed to delete category: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error deleting category: {str(e)}")
            return False

    def test_duplicate_category_name(self) -> bool:
        """Test creating a category with duplicate name"""
        print("\n10. Testing duplicate category name validation")

        # First, create a category
        category_data = {
            "name": "Duplicate Test Category",
            "description": "First category with this name for testing purposes"
        }

        try:
            response1 = self.session.post(self.categories_url, json=category_data, timeout=API_TIMEOUT)

            if response1.status_code == 201:
                category_id = response1.json()['data']['category_id']
                self.created_category_ids.append(category_id)
                print("✅ First category created successfully")

                # Now try to create another with the same name
                duplicate_data = {
                    "name": "Duplicate Test Category",  # Same name
                    "description": "Second category with same name (should fail) for testing"
                }

                response2 = self.session.post(self.categories_url, json=duplicate_data, timeout=API_TIMEOUT)

                print(f"   Duplicate attempt status: {response2.status_code}")

                if response2.status_code == 409:  # Conflict
                    print("✅ Duplicate name correctly rejected")
                    return True
                else:
                    print(f"❌ Expected 409 for duplicate, got {response2.status_code}")
                    return False
            else:
                print(f"❌ Failed to create first category: {response1.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error testing duplicate names: {str(e)}")
            return False

    def run_all_tests(self) -> bool:
        """Run all category API tests"""
        print("🧪 Starting Categories API End-to-End Tests")
        print("=" * 60)

        try:
            # Test basic CRUD operations
            category_id = self.test_create_category()
            if not category_id:
                return False

            if not self.test_get_category(category_id):
                return False

            if not self.test_list_categories():
                return False

            if not self.test_update_category(category_id):
                return False

            if not self.test_list_categories_with_pagination():
                return False

            # Test validation and error cases
            if not self.test_create_category_validation_errors():
                return False

            if not self.test_get_nonexistent_category():
                return False

            if not self.test_update_nonexistent_category():
                return False

            if not self.test_duplicate_category_name():
                return False

            # Test delete (this should be last for the main test category)
            if not self.test_delete_category(category_id):
                return False

            print("\n🎉 All Categories API tests passed!")
            return True

        except Exception as e:
            print(f"\n💥 Test suite failed with error: {str(e)}")
            return False

        finally:
            self.cleanup()


def main():
    """Main function to run categories E2E tests"""

    # Get API base URL from environment or use default
    api_url = os.getenv('API_BASE_URL')

    if not api_url:
        print("❌ API_BASE_URL environment variable not set")
        print("   Set it to your deployed API Gateway URL:")
        print("   export API_BASE_URL=https://your-api-id.execute-api.region.amazonaws.com/stage")
        sys.exit(1)

    print(f"🔗 Testing API at: {api_url}")

    # Run tests
    test_runner = CategoriesE2ETest(api_url)

    try:
        success = test_runner.run_all_tests()

        if success:
            print(f"\n✅ All categories E2E tests completed successfully!")
            sys.exit(0)
        else:
            print(f"\n❌ Some categories E2E tests failed!")
            sys.exit(1)

    except KeyboardInterrupt:
        print(f"\n⚠️  Tests interrupted by user")
        test_runner.cleanup()
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        test_runner.cleanup()
        sys.exit(1)


if __name__ == '__main__':
    main()
