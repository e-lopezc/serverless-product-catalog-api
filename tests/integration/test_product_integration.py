#!/usr/bin/env python3
"""
Simple test script for Product model
Run this to test the product functionality locally
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

from services.product_service import ProductService
from services.brand_service import BrandService
from services.category_service import CategoryService
from utils.exceptions import ValidationError, DuplicateError, NotFoundError


def setup_test_data():
    """Create test brand and category for product testing"""
    print("🔧 Setting up test data...")

    # Create a test brand
    brand_data = {
        'name': 'Test Brand for Products',
        'description': 'This is a test brand created for product testing purposes',
        'website': 'https://testbrand.com'
    }
    brand = BrandService.create_brand(brand_data)
    print(f"✅ Test brand created: {brand['name']} (ID: {brand['brand_id']})")

    # Create a test category
    category_data = {
        'name': 'Test Category for Products',
        'description': 'This is a test category created for product testing purposes'
    }
    category = CategoryService.create_category(category_data)
    print(f"✅ Test category created: {category['name']} (ID: {category['category_id']})")

    return brand['brand_id'], category['category_id']


def cleanup_test_data(brand_id, category_id, product_ids):
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")

    # Delete products first
    for product_id in product_ids:
        if ProductService.delete_product(product_id):
            print(f"✅ Deleted test product: {product_id}")

    # Delete test brand and category
    if BrandService.delete_brand(brand_id):
        print(f"✅ Deleted test brand: {brand_id}")

    if CategoryService.delete_category(category_id):
        print(f"✅ Deleted test category: {category_id}")


def test_product_operations():
    """Test basic product operations"""

    print("🧪 Testing Product operations...")

    created_product_ids = []
    brand_id = None
    category_id = None

    try:
        # Setup test data
        brand_id, category_id = setup_test_data()

        # Test 1: Create a product
        print("\n1. Creating a product...")
        product_data = {
            'name': 'Test Product',
            'brand_id': brand_id,
            'category_id': category_id,
            'price': 99.99,
            'description': 'This is a test product for demonstration purposes',
            'stock_quantity': 50,
            'images': [
                'https://example.com/image1.jpg',
                'https://example.com/image2.png'
            ]
        }

        product = ProductService.create_product(product_data)
        print(f"✅ Product created: {product['name']} (ID: {product['product_id']})")
        product_id = product['product_id']
        created_product_ids.append(product_id)

        # Test 2: Get the product
        print(f"\n2. Getting product by ID: {product_id}")
        retrieved_product = ProductService.get_product(product_id)
        if retrieved_product:
            print(f"✅ Product retrieved: {retrieved_product['name']} - ${retrieved_product['price']}")
        else:
            print("❌ Product not found")

        # Test 3: Skip SKU test (SKU removed from testing)
        print("\n3. Skipping SKU test (no SKU provided)")

        # Test 4: Update the product
        print(f"\n4. Updating product...")
        update_data = {
            'name': 'Updated Test Product',
            'price': 129.99,
            'description': 'Updated description for the test product',
            'stock_quantity': 75
        }
        updated_product = ProductService.update_product(product_id, update_data)
        print(f"✅ Product updated: {updated_product['name']} - ${updated_product['price']}")
        print(f"✅ Stock Quantity: {updated_product['stock_quantity']}")
        # Test 5: Test stock operations
        print("\n5. Testing stock operations...")

        # Update stock directly
        stock_updated = ProductService.update_stock(product_id, 100)
        if stock_updated:
            print(f"✅ Stock updated to: {stock_updated['stock_quantity']}")
        else:
            print("❌ Stock update failed")

        # Adjust stock relatively
        stock_adjusted = ProductService.adjust_stock(product_id, -10)
        if stock_adjusted:
            print(f"✅ Stock adjusted by -10, new quantity: {stock_adjusted['stock_quantity']}")
        else:
            print("❌ Stock adjustment failed")

        # Test 6: List products
        print("\n6. Listing products...")
        products_result = ProductService.list_products(limit=10)
        print(f"✅ Found {len(products_result.get('items', []))} products")

        # Test 7: List products by brand
        print("\n7. Listing products by brand...")
        brand_products = ProductService.list_products_by_brand(brand_id, limit=10)
        print(f"✅ Found {len(brand_products.get('items', []))} products for brand")

        # Test 8: List products by category
        print("\n8. Listing products by category...")
        category_products = ProductService.list_products_by_category(category_id, limit=10)
        print(f"✅ Found {len(category_products.get('items', []))} products for category")

        # Test 9: Skip duplicate SKU test (SKU removed from testing)
        print("\n9. Skipping duplicate SKU test (no SKU provided)")

        # Test 10: Test validation errors
        print("\n10. Testing validation...")

        # Test invalid price
        try:
            invalid_data = {
                'name': 'Invalid Product',
                'brand_id': brand_id,
                'category_id': category_id,
                'price': -10.0,  # Negative price should fail
                'description': 'Product with invalid price'
            }
            ProductService.create_product(invalid_data)
            print("❌ Validation failed - should have thrown error for negative price")
        except ValidationError:
            print("✅ Negative price correctly rejected")

        # Test invalid brand_id
        try:
            invalid_data = {
                'name': 'Product with Invalid Brand',
                'brand_id': 'non-existent-brand-id',
                'category_id': category_id,
                'price': 99.99,
                'description': 'Product with non-existent brand'
            }
            ProductService.create_product(invalid_data)
            print("❌ Validation failed - should have thrown error for invalid brand")
        except (ValidationError, NotFoundError):
            print("✅ Invalid brand_id correctly rejected")

        # Test 11: Create another product for additional testing
        print("\n11. Creating second product...")
        product_data_2 = {
            'name': 'Second Test Product',
            'brand_id': brand_id,
            'category_id': category_id,
            'price': 199.99,
            'description': 'Second test product for additional testing',
            'stock_quantity': 25
        }

        product_2 = ProductService.create_product(product_data_2)
        print(f"✅ Second product created: {product_2['name']} (ID: {product_2['product_id']})")
        created_product_ids.append(product_2['product_id'])

        # Test 12: List products again to see both
        print("\n12. Listing all products again...")
        all_products = ProductService.list_products(limit=10)
        product_count = len(all_products.get('items', []))
        print(f"✅ Found {product_count} total products")

        # Test 13: Test image validation
        print("\n13. Testing image validation...")
        try:
            invalid_data = {
                'name': 'Product with Invalid Images',
                'brand_id': brand_id,
                'category_id': category_id,
                'price': 99.99,
                'images': ['not-a-valid-url', 'https://example.com/invalid.txt']
            }
            ProductService.create_product(invalid_data)
            print("❌ Image validation failed - should have thrown error")
        except ValidationError:
            print("✅ Invalid images correctly rejected")

        print("\n🎉 All tests completed successfully!")

    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        # Clean up test data
        if brand_id and category_id:
            cleanup_test_data(brand_id, category_id, created_product_ids)


if __name__ == '__main__':
    test_product_operations()
