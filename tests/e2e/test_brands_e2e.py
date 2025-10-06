#!/usr/bin/env python3
"""
End-to-End Tests for Brands API
Tests the deployed API endpoints for brand operations
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


class BrandsE2ETest:
    """End-to-end test class for Brands API"""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.brands_url = f"{self.base_url}/brands"
        self.created_brand_ids: List[str] = []
        self.session = requests.Session()

        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def cleanup(self):
        """Clean up any created test data"""
        print(f"\n🧹 Cleaning up {len(self.created_brand_ids)} test brands...")

        for brand_id in self.created_brand_ids:
            try:
                response = self.session.delete(f"{self.brands_url}/{brand_id}", timeout=API_TIMEOUT)
                if response.status_code == 200:
                    print(f"✅ Deleted brand: {brand_id}")
                else:
                    print(f"⚠️  Failed to delete brand {brand_id}: {response.status_code}")
            except Exception as e:
                print(f"❌ Error deleting brand {brand_id}: {str(e)}")

        self.created_brand_ids.clear()

    def test_create_brand(self) -> Optional[str]:
        """Test POST /brands - Create a new brand"""
        print("\n1. Testing CREATE brand (POST /brands)")

        brand_data = {
            "name": "E2E Test Brand",
            "description": "This is a test brand created during end-to-end testing",
            "website": "https://e2etest.com"
        }

        try:
            response = self.session.post(self.brands_url, json=brand_data, timeout=API_TIMEOUT)

            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")

            if response.status_code == 201:
                response_data = response.json()
                brand_id = response_data['data']['brand_id']
                self.created_brand_ids.append(brand_id)
                print(f"✅ Brand created successfully: {brand_id}")
                return brand_id
            else:
                print(f"❌ Failed to create brand: {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ Error creating brand: {str(e)}")
            return None

    def test_get_brand(self, brand_id: str) -> bool:
        """Test GET /brands/{id} - Get a specific brand"""
        print(f"\n2. Testing GET brand (GET /brands/{brand_id})")

        try:
            response = self.session.get(f"{self.brands_url}/{brand_id}", timeout=API_TIMEOUT)

            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")

            if response.status_code == 200:
                response_data = response.json()
                brand = response_data['data']

                # Validate response structure
                required_fields = ['brand_id', 'name', 'description', 'created_at', 'updated_at']
                for field in required_fields:
                    if field not in brand:
                        print(f"❌ Missing field in response: {field}")
                        return False

                if brand['brand_id'] == brand_id:
                    print(f"✅ Brand retrieved successfully: {brand['name']}")
                    return True
                else:
                    print(f"❌ Brand ID mismatch: expected {brand_id}, got {brand['brand_id']}")
                    return False
            else:
                print(f"❌ Failed to get brand: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error getting brand: {str(e)}")
            return False

    def test_list_brands(self) -> bool:
        """Test GET /brands - List all brands"""
        print("\n3. Testing LIST brands (GET /brands)")

        try:
            response = self.session.get(self.brands_url, timeout=API_TIMEOUT)

            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")

            if response.status_code == 200:
                response_data = response.json()

                # Check response structure
                if 'data' in response_data and 'items' in response_data['data']:
                    brands = response_data['data']['items']
                    print(f"✅ Listed {len(brands)} brands successfully")

                    # Validate that our test brand is in the list
                    if self.created_brand_ids:
                        test_brand_found = any(
                            brand.get('brand_id') in self.created_brand_ids
                            for brand in brands
                        )
                        if test_brand_found:
                            print("✅ Test brand found in list")
                        else:
                            print("⚠️  Test brand not found in list (might be pagination)")

                    return True
                else:
                    print("❌ Invalid response structure for list brands")
                    return False
            else:
                print(f"❌ Failed to list brands: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error listing brands: {str(e)}")
            return False

    def test_update_brand(self, brand_id: str) -> bool:
        """Test PUT /brands/{id} - Update a brand"""
        print(f"\n4. Testing UPDATE brand (PUT /brands/{brand_id})")

        update_data = {
            "name": "Updated E2E Test Brand",
            "description": "This brand has been updated during end-to-end testing",
            "website": "https://updated-e2etest.com"
        }

        try:
            response = self.session.put(f"{self.brands_url}/{brand_id}", json=update_data, timeout=API_TIMEOUT)

            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")

            if response.status_code == 200:
                response_data = response.json()
                updated_brand = response_data['data']

                # Verify the updates were applied
                if (updated_brand['name'] == update_data['name'] and
                    updated_brand['description'] == update_data['description'] and
                    updated_brand['website'] == update_data['website']):
                    print("✅ Brand updated successfully")
                    return True
                else:
                    print("❌ Brand update did not apply correctly")
                    return False
            else:
                print(f"❌ Failed to update brand: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error updating brand: {str(e)}")
            return False

    def test_list_brands_with_pagination(self) -> bool:
        """Test GET /brands with pagination parameters"""
        print("\n5. Testing LIST brands with pagination (GET /brands?limit=1)")

        try:
            response = self.session.get(f"{self.brands_url}?limit=1", timeout=API_TIMEOUT)

            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")

            if response.status_code == 200:
                response_data = response.json()

                if 'data' in response_data and 'items' in response_data['data']:
                    brands = response_data['data']['items']

                    if len(brands) <= 1:
                        print(f"✅ Pagination working: returned {len(brands)} brand(s)")

                        # Check if last_evaluated_key is present when there are more items
                        if 'last_evaluated_key' in response_data['data']:
                            print("✅ Pagination key present for next page")

                        return True
                    else:
                        print(f"❌ Pagination failed: returned {len(brands)} brands (expected <= 1)")
                        return False
                else:
                    print("❌ Invalid response structure")
                    return False
            else:
                print(f"❌ Failed to list brands with pagination: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error testing pagination: {str(e)}")
            return False

    def test_create_brand_validation_errors(self) -> bool:
        """Test POST /brands with invalid data to verify validation"""
        print("\n6. Testing brand validation errors")

        test_cases = [
            {
                "name": "Empty name test",
                "data": {"name": "", "description": "Valid description"},
                "expected_status": 400
            },
            {
                "name": "Missing description test",
                "data": {"name": "Valid Name"},
                "expected_status": 400
            },
            {
                "name": "Invalid website test",
                "data": {
                    "name": "Valid Name",
                    "description": "Valid description",
                    "website": "not-a-url"
                },
                "expected_status": 400
            }
        ]

        all_passed = True

        for test_case in test_cases:
            print(f"\n   Testing: {test_case['name']}")

            try:
                response = self.session.post(self.brands_url, json=test_case['data'], timeout=API_TIMEOUT)

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

    def test_get_nonexistent_brand(self) -> bool:
        """Test GET /brands/{id} with non-existent ID"""
        print("\n7. Testing GET non-existent brand")

        fake_id = "00000000-0000-0000-0000-000000000000"

        try:
            response = self.session.get(f"{self.brands_url}/{fake_id}", timeout=API_TIMEOUT)

            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")

            if response.status_code == 404:
                print("✅ Correctly returned 404 for non-existent brand")
                return True
            else:
                print(f"❌ Expected 404, got {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error testing non-existent brand: {str(e)}")
            return False

    def test_delete_brand(self, brand_id: str) -> bool:
        """Test DELETE /brands/{id} - Delete a brand"""
        print(f"\n8. Testing DELETE brand (DELETE /brands/{brand_id})")

        try:
            response = self.session.delete(f"{self.brands_url}/{brand_id}", timeout=API_TIMEOUT)

            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")

            if response.status_code == 200:
                # Remove from our tracking list since it's now deleted
                if brand_id in self.created_brand_ids:
                    self.created_brand_ids.remove(brand_id)

                print("✅ Brand deleted successfully")

                # Verify it's actually deleted by trying to get it
                get_response = self.session.get(f"{self.brands_url}/{brand_id}", timeout=API_TIMEOUT)
                if get_response.status_code == 404:
                    print("✅ Verified brand was deleted (GET returns 404)")
                    return True
                else:
                    print(f"❌ Brand still exists after deletion (GET returns {get_response.status_code})")
                    return False
            else:
                print(f"❌ Failed to delete brand: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error deleting brand: {str(e)}")
            return False

    def test_duplicate_brand_name(self) -> bool:
        """Test creating a brand with duplicate name"""
        print("\n9. Testing duplicate brand name validation")

        # First, create a brand
        brand_data = {
            "name": "Duplicate Test Brand",
            "description": "First brand with this name"
        }

        try:
            response1 = self.session.post(self.brands_url, json=brand_data, timeout=API_TIMEOUT)

            if response1.status_code == 201:
                brand_id = response1.json()['data']['brand_id']
                self.created_brand_ids.append(brand_id)
                print("✅ First brand created successfully")

                # Now try to create another with the same name
                duplicate_data = {
                    "name": "Duplicate Test Brand",  # Same name
                    "description": "Second brand with same name (should fail)"
                }

                response2 = self.session.post(self.brands_url, json=duplicate_data, timeout=API_TIMEOUT)

                print(f"   Duplicate attempt status: {response2.status_code}")

                if response2.status_code == 409:  # Conflict
                    print("✅ Duplicate name correctly rejected")
                    return True
                else:
                    print(f"❌ Expected 409 for duplicate, got {response2.status_code}")
                    return False
            else:
                print(f"❌ Failed to create first brand: {response1.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error testing duplicate names: {str(e)}")
            return False

    def run_all_tests(self) -> bool:
        """Run all brand API tests"""
        print("🧪 Starting Brands API End-to-End Tests")
        print("=" * 60)

        try:
            # Test basic CRUD operations
            brand_id = self.test_create_brand()
            if not brand_id:
                return False

            if not self.test_get_brand(brand_id):
                return False

            if not self.test_list_brands():
                return False

            if not self.test_update_brand(brand_id):
                return False

            if not self.test_list_brands_with_pagination():
                return False

            # Test validation and error cases
            if not self.test_create_brand_validation_errors():
                return False

            if not self.test_get_nonexistent_brand():
                return False

            if not self.test_duplicate_brand_name():
                return False

            # Test delete (this should be last for the main test brand)
            if not self.test_delete_brand(brand_id):
                return False

            print("\n🎉 All Brands API tests passed!")
            return True

        except Exception as e:
            print(f"\n💥 Test suite failed with error: {str(e)}")
            return False

        finally:
            self.cleanup()


def main():
    """Main function to run brands E2E tests"""

    # Get API base URL from environment or use default
    api_url = os.getenv('API_BASE_URL')

    if not api_url:
        print("❌ API_BASE_URL environment variable not set")
        print("   Set it to your deployed API Gateway URL:")
        print("   export API_BASE_URL=https://your-api-id.execute-api.region.amazonaws.com/stage")
        sys.exit(1)

    print(f"🔗 Testing API at: {api_url}")

    # Run tests
    test_runner = BrandsE2ETest(api_url)

    try:
        success = test_runner.run_all_tests()

        if success:
            print(f"\n✅ All brands E2E tests completed successfully!")
            sys.exit(0)
        else:
            print(f"\n❌ Some brands E2E tests failed!")
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
