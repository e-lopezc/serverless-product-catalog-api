#!/usr/bin/env python3
"""
End-to-End Tests for Products API
Tests the deployed API endpoints for product operations
"""

import os
import sys
import requests
import json
import time
from typing import Dict, Any, Optional, List

# Configuration
API_TIMEOUT = 30  # seconds


class ProductsE2ETest:
    """End-to-end test class for Products API"""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.products_url = f"{self.base_url}/products"
        self.brands_url = f"{self.base_url}/brands"
        self.categories_url = f"{self.base_url}/categories"

        self.created_product_ids: List[str] = []
        self.created_brand_ids: List[str] = []
        self.created_category_ids: List[str] = []

        self.session = requests.Session()

        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def setup_test_data(self) -> tuple[Optional[str], Optional[str]]:
        """Set up test brand and category for product testing"""
        print("\n🔧 Setting up test data (brand and category)...")

        # Create test brand
        brand_data = {
            "name": "E2E Test Product Brand",
            "description": "Test brand created for product end-to-end testing"
        }

        try:
            brand_response = self.session.post(self.brands_url, json=brand_data, timeout=API_TIMEOUT)
            if brand_response.status_code == 201:
                brand_id = brand_response.json()['data']['brand_id']
                self.created_brand_ids.append(brand_id)
                print(f"✅ Test brand created: {brand_id}")
            else:
                print(f"❌ Failed to create test brand: {brand_response.status_code}")
                return None, None
        except Exception as e:
            print(f"❌ Error creating test brand: {str(e)}")
            return None, None

        # Create test category
        category_data = {
            "name": "E2E Test Product Category",
            "description": "Test category created for product end-to-end testing"
        }

        try:
            category_response = self.session.post(self.categories_url, json=category_data, timeout=API_TIMEOUT)
            if category_response.status_code == 201:
                category_id = category_response.json()['data']['category_id']
                self.created_category_ids.append(category_id)
                print(f"✅ Test category created: {category_id}")
                return brand_id, category_id
            else:
                print(f"❌ Failed to create test category: {category_response.status_code}")
                return None, None
        except Exception as e:
            print(f"❌ Error creating test category: {str(e)}")
            return None, None

    def cleanup(self):
        """Clean up any created test data"""
        print(f"\n🧹 Cleaning up test data...")

        # Delete products first (they depend on brands and categories)
        for product_id in self.created_product_ids:
            try:
                response = self.session.delete(f"{self.products_url}/{product_id}", timeout=API_TIMEOUT)
                if response.status_code == 200:
                    print(f"✅ Deleted product: {product_id}")
                else:
                    print(f"⚠️  Failed to delete product {product_id}: {response.status_code}")
            except Exception as e:
                print(f"❌ Error deleting product {product_id}: {str(e)}")

        # Delete brands
        for brand_id in self.created_brand_ids:
            try:
                response = self.session.delete(f"{self.brands_url}/{brand_id}", timeout=API_TIMEOUT)
                if response.status_code == 200:
                    print(f"✅ Deleted brand: {brand_id}")
                else:
                    print(f"⚠️  Failed to delete brand {brand_id}: {response.status_code}")
            except Exception as e:
                print(f"❌ Error deleting brand {brand_id}: {str(e)}")

        # Delete categories
        for category_id in self.created_category_ids:
            try:
                response = self.session.delete(f"{self.categories_url}/{category_id}", timeout=API_TIMEOUT)
                if response.status_code == 200:
                    print(f"✅ Deleted category: {category_id}")
                else:
                    print(f"⚠️  Failed to delete category {category_id}: {response.status_code}")
            except Exception as e:
                print(f"❌ Error deleting category {category_id}: {str(e)}")

        # Clear tracking lists
        self.created_product_ids.clear()
        self.created_brand_ids.clear()
        self.created_category_ids.clear()

    def test_create_product(self, brand_id: str, category_id: str) -> Optional[str]:
        """Test POST /products - Create a new product"""
        print("\n1. Testing CREATE product (POST /products)")

        product_data = {
            "name": "E2E Test Product",
            "brand_id": brand_id,
            "category_id": category_id,
            "price": 99.99,
            "description": "This is a test product created during end-to-end testing",
            "stock_quantity": 50,
            "images": [
                "https://example.com/test-image1.jpg",
                "https://example.com/test-image2.png"
            ]
        }

        try:
            response = self.session.post(self.products_url, json=product_data, timeout=API_TIMEOUT)

            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")

            if response.status_code == 201:
                response_data = response.json()
                product_id = response_data['data']['product_id']
                self.created_product_ids.append(product_id)
                print(f"✅ Product created successfully: {product_id}")
                return product_id
            else:
                print(f"❌ Failed to create product: {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ Error creating product: {str(e)}")
            return None

    def test_get_product(self, product_id: str) -> bool:
        """Test GET /products/{id} - Get a specific product"""
        print(f"\n2. Testing GET product (GET /products/{product_id})")

        try:
            response = self.session.get(f"{self.products_url}/{product_id}", timeout=API_TIMEOUT)

            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")

            if response.status_code == 200:
                response_data = response.json()
                product = response_data['data']

                # Validate response structure
                required_fields = ['product_id', 'name', 'brand_id', 'category_id', 'price', 'stock_quantity', 'created_at', 'updated_at']
                for field in required_fields:
                    if field not in product:
                        print(f"❌ Missing field in response: {field}")
                        return False

                if product['product_id'] == product_id:
                    print(f"✅ Product retrieved successfully: {product['name']} - ${product['price']}")
                    return True
                else:
                    print(f"❌ Product ID mismatch: expected {product_id}, got {product['product_id']}")
                    return False
            else:
                print(f"❌ Failed to get product: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error getting product: {str(e)}")
            return False

    def test_list_products(self) -> bool:
        """Test GET /products - List all products"""
        print("\n3. Testing LIST products (GET /products)")

        try:
            response = self.session.get(self.products_url, timeout=API_TIMEOUT)

            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")

            if response.status_code == 200:
                response_data = response.json()

                # Check response structure
                if 'data' in response_data and 'items' in response_data['data']:
                    products = response_data['data']['items']
                    print(f"✅ Listed {len(products)} products successfully")

                    # Validate that our test product is in the list
                    if self.created_product_ids:
                        test_product_found = any(
                            product.get('product_id') in self.created_product_ids
                            for product in products
                        )
                        if test_product_found:
                            print("✅ Test product found in list")
                        else:
                            print("⚠️  Test product not found in list (might be pagination)")

                    return True
                else:
                    print("❌ Invalid response structure for list products")
                    return False
            else:
                print(f"❌ Failed to list products: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error listing products: {str(e)}")
            return False

    def test_update_product(self, product_id: str) -> bool:
        """Test PUT /products/{id} - Update a product"""
        print(f"\n4. Testing UPDATE product (PUT /products/{product_id})")

        update_data = {
            "name": "Updated E2E Test Product",
            "price": 129.99,
            "description": "This product has been updated during end-to-end testing",
            "stock_quantity": 75
        }

        try:
            response = self.session.put(f"{self.products_url}/{product_id}", json=update_data, timeout=API_TIMEOUT)

            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")

            if response.status_code == 200:
                response_data = response.json()
                updated_product = response_data['data']

                # Verify the updates were applied
                if (updated_product['name'] == update_data['name'] and
                    updated_product['price'] == update_data['price'] and
                    updated_product['description'] == update_data['description'] and
                    updated_product['stock_quantity'] == update_data['stock_quantity']):
                    print("✅ Product updated successfully")
                    return True
                else:
                    print("❌ Product update did not apply correctly")
                    return False
            else:
                print(f"❌ Failed to update product: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error updating product: {str(e)}")
            return False

    def test_list_products_by_brand(self, brand_id: str) -> bool:
        """Test GET /products/by-brand/{brand_id} - List products by brand"""
        print(f"\n5. Testing LIST products by brand (GET /products/by-brand/{brand_id})")

        try:
            response = self.session.get(f"{self.products_url}/by-brand/{brand_id}", timeout=API_TIMEOUT)

            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")

            if response.status_code == 200:
                response_data = response.json()

                if 'data' in response_data and 'items' in response_data['data']:
                    products = response_data['data']['items']
                    print(f"✅ Listed {len(products)} products for brand")

                    # Verify all products belong to the specified brand
                    for product in products:
                        if product.get('brand_id') != brand_id:
                            print(f"❌ Product {product.get('product_id')} has wrong brand_id")
                            return False

                    print("✅ All products belong to correct brand")
                    return True
                else:
                    print("❌ Invalid response structure")
                    return False
            else:
                print(f"❌ Failed to list products by brand: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error listing products by brand: {str(e)}")
            return False

    def test_list_products_by_category(self, category_id: str) -> bool:
        """Test GET /products/by-category/{category_id} - List products by category"""
        print(f"\n6. Testing LIST products by category (GET /products/by-category/{category_id})")

        try:
            response = self.session.get(f"{self.products_url}/by-category/{category_id}", timeout=API_TIMEOUT)

            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")

            if response.status_code == 200:
                response_data = response.json()

                if 'data' in response_data and 'items' in response_data['data']:
                    products = response_data['data']['items']
                    print(f"✅ Listed {len(products)} products for category")

                    # Verify all products belong to the specified category
                    for product in products:
                        if product.get('category_id') != category_id:
                            print(f"❌ Product {product.get('product_id')} has wrong category_id")
                            return False

                    print("✅ All products belong to correct category")
                    return True
                else:
                    print("❌ Invalid response structure")
                    return False
            else:
                print(f"❌ Failed to list products by category: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error listing products by category: {str(e)}")
            return False

    def test_stock_operations(self, product_id: str) -> bool:
        """Test PATCH /products/{id}/stock - Update product stock"""
        print(f"\n7. Testing stock operations (PATCH /products/{product_id}/stock)")

        # Test absolute stock update
        print("   Testing absolute stock update...")
        stock_data = {"stock_quantity": 100}

        try:
            response = self.session.patch(f"{self.products_url}/{product_id}/stock", json=stock_data, timeout=API_TIMEOUT)

            print(f"   Status Code: {response.status_code}")

            if response.status_code == 200:
                response_data = response.json()
                updated_product = response_data['data']

                if updated_product['stock_quantity'] == 100:
                    print("✅ Absolute stock update successful")
                else:
                    print(f"❌ Stock not updated correctly: expected 100, got {updated_product['stock_quantity']}")
                    return False
            else:
                print(f"❌ Failed absolute stock update: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error in absolute stock update: {str(e)}")
            return False

        # Test relative stock adjustment
        print("   Testing relative stock adjustment...")
        adjustment_data = {"quantity_change": -10}

        try:
            response = self.session.patch(f"{self.products_url}/{product_id}/stock", json=adjustment_data, timeout=API_TIMEOUT)

            print(f"   Status Code: {response.status_code}")

            if response.status_code == 200:
                response_data = response.json()
                updated_product = response_data['data']

                if updated_product['stock_quantity'] == 90:  # 100 - 10
                    print("✅ Relative stock adjustment successful")
                    return True
                else:
                    print(f"❌ Stock not adjusted correctly: expected 90, got {updated_product['stock_quantity']}")
                    return False
            else:
                print(f"❌ Failed relative stock adjustment: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error in relative stock adjustment: {str(e)}")
            return False

    def test_product_validation_errors(self, brand_id: str, category_id: str) -> bool:
        """Test POST /products with invalid data to verify validation"""
        print("\n8. Testing product validation errors")

        test_cases = [
            {
                "name": "Missing name test",
                "data": {
                    "brand_id": brand_id,
                    "category_id": category_id,
                    "price": 99.99
                },
                "expected_status": 400
            },
            {
                "name": "Invalid price test",
                "data": {
                    "name": "Test Product",
                    "brand_id": brand_id,
                    "category_id": category_id,
                    "price": -10.00
                },
                "expected_status": 400
            },
            {
                "name": "Invalid brand_id test",
                "data": {
                    "name": "Test Product",
                    "brand_id": "invalid-brand-id",
                    "category_id": category_id,
                    "price": 99.99
                },
                "expected_status": [400, 404]  # Could be either validation or not found
            },
            {
                "name": "Invalid stock quantity test",
                "data": {
                    "name": "Test Product",
                    "brand_id": brand_id,
                    "category_id": category_id,
                    "price": 99.99,
                    "stock_quantity": -5
                },
                "expected_status": 400
            }
        ]

        all_passed = True

        for test_case in test_cases:
            print(f"\n   Testing: {test_case['name']}")

            try:
                response = self.session.post(self.products_url, json=test_case['data'], timeout=API_TIMEOUT)

                print(f"   Status Code: {response.status_code}")

                expected_statuses = test_case['expected_status']
                if not isinstance(expected_statuses, list):
                    expected_statuses = [expected_statuses]

                if response.status_code in expected_statuses:
                    print(f"   ✅ Validation working correctly")
                else:
                    print(f"   ❌ Expected {expected_statuses}, got {response.status_code}")
                    all_passed = False

            except Exception as e:
                print(f"   ❌ Error testing validation: {str(e)}")
                all_passed = False

        return all_passed

    def test_get_nonexistent_product(self) -> bool:
        """Test GET /products/{id} with non-existent ID"""
        print("\n9. Testing GET non-existent product")

        fake_id = "00000000-0000-0000-0000-000000000000"

        try:
            response = self.session.get(f"{self.products_url}/{fake_id}", timeout=API_TIMEOUT)

            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")

            if response.status_code == 404:
                print("✅ Correctly returned 404 for non-existent product")
                return True
            else:
                print(f"❌ Expected 404, got {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error testing non-existent product: {str(e)}")
            return False

    def test_pagination(self) -> bool:
        """Test product listing with pagination"""
        print("\n10. Testing products pagination (GET /products?limit=1)")

        try:
            response = self.session.get(f"{self.products_url}?limit=1", timeout=API_TIMEOUT)

            print(f"   Status Code: {response.status_code}")

            if response.status_code == 200:
                response_data = response.json()

                if 'data' in response_data and 'items' in response_data['data']:
                    products = response_data['data']['items']

                    if len(products) <= 1:
                        print(f"✅ Pagination working: returned {len(products)} product(s)")

                        # Check if last_evaluated_key is present when there are more items
                        if 'last_evaluated_key' in response_data['data']:
                            print("✅ Pagination key present for next page")

                        return True
                    else:
                        print(f"❌ Pagination failed: returned {len(products)} products (expected <= 1)")
                        return False
                else:
                    print("❌ Invalid response structure")
                    return False
            else:
                print(f"❌ Failed to test pagination: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error testing pagination: {str(e)}")
            return False

    def test_delete_product(self, product_id: str) -> bool:
        """Test DELETE /products/{id} - Delete a product"""
        print(f"\n11. Testing DELETE product (DELETE /products/{product_id})")

        try:
            response = self.session.delete(f"{self.products_url}/{product_id}", timeout=API_TIMEOUT)

            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")

            if response.status_code == 200:
                # Remove from our tracking list since it's now deleted
                if product_id in self.created_product_ids:
                    self.created_product_ids.remove(product_id)

                print("✅ Product deleted successfully")

                # Verify it's actually deleted by trying to get it
                get_response = self.session.get(f"{self.products_url}/{product_id}", timeout=API_TIMEOUT)
                if get_response.status_code == 404:
                    print("✅ Verified product was deleted (GET returns 404)")
                    return True
                else:
                    print(f"❌ Product still exists after deletion (GET returns {get_response.status_code})")
                    return False
            else:
                print(f"❌ Failed to delete product: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error deleting product: {str(e)}")
            return False

    def run_all_tests(self) -> bool:
        """Run all product API tests"""
        print("🧪 Starting Products API End-to-End Tests")
        print("=" * 60)

        try:
            # Setup test data
            brand_id, category_id = self.setup_test_data()
            if not brand_id or not category_id:
                print("❌ Failed to setup test data")
                return False

            # Test basic CRUD operations
            product_id = self.test_create_product(brand_id, category_id)
            if not product_id:
                return False

            if not self.test_get_product(product_id):
                return False

            if not self.test_list_products():
                return False

            if not self.test_update_product(product_id):
                return False

            # Test specialized endpoints
            if not self.test_list_products_by_brand(brand_id):
                return False

            if not self.test_list_products_by_category(category_id):
                return False

            if not self.test_stock_operations(product_id):
                return False

            # Test validation and error cases
            if not self.test_product_validation_errors(brand_id, category_id):
                return False

            if not self.test_get_nonexistent_product():
                return False

            if not self.test_pagination():
                return False

            # Test delete (this should be last for the main test product)
            if not self.test_delete_product(product_id):
                return False

            print("\n🎉 All Products API tests passed!")
            return True

        except Exception as e:
            print(f"\n💥 Test suite failed with error: {str(e)}")
            return False

        finally:
            self.cleanup()


def main():
    """Main function to run products E2E tests"""

    # Get API base URL from environment or use default
    api_url = os.getenv('API_BASE_URL')

    if not api_url:
        print("❌ API_BASE_URL environment variable not set")
        print("   Set it to your deployed API Gateway URL:")
        print("   export API_BASE_URL=https://your-api-id.execute-api.region.amazonaws.com/stage")
        sys.exit(1)

    print(f"🔗 Testing API at: {api_url}")

    # Run tests
    test_runner = ProductsE2ETest(api_url)

    try:
        success = test_runner.run_all_tests()

        if success:
            print(f"\n✅ All products E2E tests completed successfully!")
            sys.exit(0)
        else:
            print(f"\n❌ Some products E2E tests failed!")
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
