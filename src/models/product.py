import uuid
import re
from datetime import datetime
from typing import Optional, Dict, Any, List, cast
from decimal import Decimal

from utils.db_operations import db_client
from utils.exceptions import ValidationError, NotFoundError
from config.settings import (
    PRODUCT_PREFIX,
    create_product_item,
    get_product_pk,
    get_product_sk
)


class Product:
    """Product model for single table design"""

    ENTITY_PREFIX = PRODUCT_PREFIX

    @staticmethod
    def create(name: str, brand_id: str, category_id: str, price: float,
               description: Optional[str] = None, stock_quantity: int = 0, images: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create a new product item

        Args:
            name: Product name (required)
            brand_id: Brand ID (required, must exist)
            category_id: Category ID (required, must exist)
            price: Product price (required, must be positive)
            description: Product description (optional)
            stock_quantity: Stock quantity (default: 0)
            images: List of image URLs (optional)

        Returns:
            Created product item

        Raises:
            ValidationError: If validation fails
            NotFoundError: If brand_id or category_id don't exist
        """
        Product._validate_data(name, brand_id, category_id, price, description,
            stock_quantity, images
        )

        if not Product._brand_exists(brand_id):
            raise NotFoundError(f"Brand with ID '{brand_id}' not found")

        if not Product._category_exists(category_id):
            raise NotFoundError(f"Category with ID '{category_id}' not found")

        product_id = Product._generate_id()

        product_item = create_product_item(
            product_id, name, brand_id, category_id, price,
            description, stock_quantity, images
        )

        from config.settings import create_product_list_item
        product_list_item = create_product_list_item(
            product_id, name, brand_id, category_id, price,
            description, stock_quantity, images
        )

        # Save both items to database
        db_client.put_item(product_item)
        db_client.put_item(product_list_item)

        return product_item

    @staticmethod
    def get(product_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a product by ID

        Args:
            product_id: Product ID

        Returns:
            Product item or None if not found
        """
        if not product_id:
            return None

        pk = get_product_pk(product_id)
        sk = get_product_sk(product_id)

        result = db_client.get_item(pk, sk)
        return cast(Optional[Dict[str, Any]], result)

    @staticmethod
    def update(product_id: str, **updates) -> Dict[str, Any]:
        """
        Update a product item

        Args:
            product_id: Product ID
            **updates: Fields to update (name, brand_id, category_id, price, description, stock_quantity, images)

        Returns:
            Updated product item

        Raises:
            NotFoundError: If product doesn't exist
            ValidationError: If validation fails
        """
        if not Product.exists(product_id):
            raise NotFoundError(f"Product with ID '{product_id}' not found")

        allowed_fields = {'name', 'brand_id', 'category_id', 'price', 'description', 'stock_quantity', 'images'}
        invalid_fields = set(updates.keys()) - allowed_fields
        if invalid_fields:
            raise ValidationError(f"Invalid fields: {', '.join(invalid_fields)}")

        if 'name' in updates:
            Product._validate_name(updates['name'])

        if 'brand_id' in updates:
            Product._validate_brand_id(updates['brand_id'])
            if not Product._brand_exists(updates['brand_id']):
                raise NotFoundError(f"Brand with ID '{updates['brand_id']}' not found")

        if 'category_id' in updates:
            Product._validate_category_id(updates['category_id'])
            if not Product._category_exists(updates['category_id']):
                raise NotFoundError(f"Category with ID '{updates['category_id']}' not found")

        if 'price' in updates:
            Product._validate_price(updates['price'])

        if 'description' in updates:
            Product._validate_description(updates['description'])

        if 'stock_quantity' in updates:
            Product._validate_stock_quantity(updates['stock_quantity'])

        if 'images' in updates:
            Product._validate_images(updates['images'])

        # Add updated_at timestamp
        updates['updated_at'] = datetime.utcnow().isoformat()

        # If category_id is being updated, also update GSI3PK for category queries
        if 'category_id' in updates:
            updates['GSI3PK'] = f"CATEGORY#{updates['category_id']}"

        pk = get_product_pk(product_id)
        sk = get_product_sk(product_id)

        result = db_client.update_item(pk, sk, updates)
        if result is None:
            raise NotFoundError(f"Product with ID '{product_id}' not found")

        # Also update the product list item
        list_pk = f"PRODUCT_LIST#{product_id}"
        list_sk = f"PRODUCT_LIST#{product_id}"
        list_updates = updates.copy()

        if 'name' in updates:
            list_updates['GSI3SK'] = updates['name'].upper()
        
        # Ensure product_list_item keeps GSI3PK = "PRODUCT_LIST" for list queries
        # (Don't copy the category-based GSI3PK from the main product item)
        if 'GSI3PK' in list_updates:
            del list_updates['GSI3PK']

        db_client.update_item(list_pk, list_sk, list_updates)

        return cast(Dict[str, Any], result)

    @staticmethod
    def delete(product_id: str) -> bool:
        """
        Delete a product item

        Args:
            product_id: Product ID

        Returns:
            True if deleted, False if not found
        """
        if not Product.exists(product_id):
            return False

        pk = get_product_pk(product_id)
        sk = get_product_sk(product_id)

        deleted_item = db_client.delete_item(pk, sk)

        list_pk = f"PRODUCT_LIST#{product_id}"
        list_sk = f"PRODUCT_LIST#{product_id}"
        db_client.delete_item(list_pk, list_sk)

        return deleted_item is not None

    @staticmethod
    def exists(product_id: str) -> bool:
        """
        Check if a product exists

        Args:
            product_id: Product ID

        Returns:
            True if exists, False otherwise
        """
        if not product_id:
            return False

        pk = get_product_pk(product_id)
        sk = get_product_sk(product_id)

        return db_client.check_item_exists(pk, sk)

    @staticmethod
    def list_all(limit: int = 50, last_evaluated_key: Optional[Dict] = None) -> Dict[str, Any]:
        """
        List all products using GSI-3 PRODUCT_LIST

        Args:
            limit: Maximum number of products to return
            last_evaluated_key: Pagination key

        Returns:
            Dict with 'items' and 'last_evaluated_key'
        """
        return db_client.list_products_by_name(limit, last_evaluated_key)

    @staticmethod
    def list_by_brand(brand_id: str, limit: int = 50, last_evaluated_key: Optional[Dict] = None) -> Dict[str, Any]:
        """
        List products by brand using GSI-2

        Args:
            brand_id: Brand ID
            limit: Maximum number of products to return
            last_evaluated_key: Pagination key

        Returns:
            Dict with 'items' and 'last_evaluated_key'
        """
        return db_client.get_products_by_brand(brand_id, limit, last_evaluated_key)

    @staticmethod
    def list_by_category(category_id: str, limit: int = 50, last_evaluated_key: Optional[Dict] = None) -> Dict[str, Any]:
        """
        List products by category using GSI-3

        Args:
            category_id: Category ID
            limit: Maximum number of products to return
            last_evaluated_key: Pagination key

        Returns:
            Dict with 'items' and 'last_evaluated_key'
        """
        return db_client.get_products_by_category(category_id, limit, last_evaluated_key)


    # Helper methods
    @staticmethod
    def _generate_id() -> str:
        """Generate a unique product ID"""
        return str(uuid.uuid4())

    @staticmethod
    def _validate_data(name: str, brand_id: str, category_id: str, price: float,
                      description: Optional[str] = None,
                      stock_quantity: int = 0, images: Optional[List[str]] = None) -> None:
        """
        Validate product data

        Args:
            name: Product name
            brand_id: Brand ID
            category_id: Category ID
            price: Product price
            description: Product description
            stock_quantity: Stock quantity
            images: List of image URLs

        Raises:
            ValidationError: If validation fails
        """
        Product._validate_name(name)
        Product._validate_brand_id(brand_id)
        Product._validate_category_id(category_id)
        Product._validate_price(price)

        if description is not None:
            Product._validate_description(description)

        Product._validate_stock_quantity(stock_quantity)

        if images is not None:
            Product._validate_images(images)

    @staticmethod
    def _validate_name(name: str) -> None:
        """Validate product name"""
        if not name:
            raise ValidationError("Product name is required")

        if not isinstance(name, str):
            raise ValidationError("Product name must be a string")

        name = name.strip()
        if not name:
            raise ValidationError("Product name cannot be empty or whitespace")

        if len(name) < 2:
            raise ValidationError("Product name must be at least 2 characters long")

        if len(name) > 200:
            raise ValidationError("Product name cannot exceed 200 characters")

        # Check for valid characters (letters, numbers, spaces, common punctuation)
        if not re.match(r'^[a-zA-Z0-9\s\-_&.,()\'"/!+]+$', name):
            raise ValidationError("Product name contains invalid characters")

    @staticmethod
    def _validate_brand_id(brand_id: str) -> None:
        """Validate brand ID"""
        if not brand_id:
            raise ValidationError("Brand ID is required")

        if not isinstance(brand_id, str):
            raise ValidationError("Brand ID must be a string")

        brand_id = brand_id.strip()
        if not brand_id:
            raise ValidationError("Brand ID cannot be empty or whitespace")

        # Basic UUID format validation
        try:
            uuid.UUID(brand_id)
        except ValueError:
            raise ValidationError("Brand ID must be a valid UUID")

    @staticmethod
    def _validate_category_id(category_id: str) -> None:
        """Validate category ID"""
        if not category_id:
            raise ValidationError("Category ID is required")

        if not isinstance(category_id, str):
            raise ValidationError("Category ID must be a string")

        category_id = category_id.strip()
        if not category_id:
            raise ValidationError("Category ID cannot be empty or whitespace")

        # Basic UUID format validation
        try:
            uuid.UUID(category_id)
        except ValueError:
            raise ValidationError("Category ID must be a valid UUID")

    @staticmethod
    def _validate_price(price: float) -> None:
        """Validate product price"""
        if price is None:
            raise ValidationError("Price is required")

        if not isinstance(price, (int, float, Decimal)):
            raise ValidationError("Price must be a number")

        if float(price) < 0:
            raise ValidationError("Price cannot be negative")

        if float(price) > 999999.99:
            raise ValidationError("Price cannot exceed 999,999.99")

        # Check for reasonable decimal places (max 2)
        if isinstance(price, float):
            decimal_places = len(str(price).split('.')[-1]) if '.' in str(price) else 0
            if decimal_places > 2:
                raise ValidationError("Price cannot have more than 2 decimal places")

    @staticmethod
    def _validate_description(description: str) -> None:
        """Validate product description"""
        if description is None:
            return  # Description is optional

        if not isinstance(description, str):
            raise ValidationError("Product description must be a string")

        description = description.strip()
        if not description:
            return  # Empty string is acceptable for optional field

        if len(description) < 10:
            raise ValidationError("Product description must be at least 10 characters long")

        if len(description) > 1000:
            raise ValidationError("Product description cannot exceed 1000 characters")


    @staticmethod
    def _validate_stock_quantity(stock_quantity: int) -> None:
        """Validate stock quantity"""
        if stock_quantity is None:
            raise ValidationError("Stock quantity is required")

        if isinstance(stock_quantity, float):
            if not stock_quantity.is_integer():
                raise ValidationError("Stock quantity must be a whole number")
            stock_quantity = int(stock_quantity)

        if not isinstance(stock_quantity, int):
            raise ValidationError("Stock quantity must be an integer")

        if stock_quantity < 0:
            raise ValidationError("Stock quantity cannot be negative")

        if stock_quantity > 999999:
            raise ValidationError("Stock quantity cannot exceed 999,999")

    @staticmethod
    def _validate_images(images: List[str]) -> None:
        """Validate product images list"""
        if images is None:
            return  # Images are optional

        if not isinstance(images, list):
            raise ValidationError("Images must be a list")

        if len(images) > 10:
            raise ValidationError("Cannot have more than 10 images")

        for i, image_url in enumerate(images):
            if not isinstance(image_url, str):
                raise ValidationError(f"Image {i+1} must be a string URL")

            image_url = image_url.strip()
            if not image_url:
                raise ValidationError(f"Image {i+1} URL cannot be empty")

            # Basic URL validation
            if not re.match(r'^https?://.+\.(jpg|jpeg|png|gif|webp)(\?.*)?$', image_url, re.IGNORECASE):
                raise ValidationError(f"Image {i+1} must be a valid image URL (jpg, jpeg, png, gif, webp)")

    @staticmethod
    def _brand_exists(brand_id: str) -> bool:
        """Check if a brand exists"""
        try:
            from config.settings import get_brand_pk, get_brand_sk
            pk = get_brand_pk(brand_id)
            sk = get_brand_sk(brand_id)
            return db_client.check_item_exists(pk, sk)
        except Exception:
            return False

    @staticmethod
    def _category_exists(category_id: str) -> bool:
        """Check if a category exists"""
        try:
            from config.settings import get_category_pk, get_category_sk
            pk = get_category_pk(category_id)
            sk = get_category_sk(category_id)
            return db_client.check_item_exists(pk, sk)
        except Exception:
            return False
