from typing import Dict, Any, Optional
from models import Product
from utils.exceptions import ValidationError, NotFoundError


class ProductService:
    """Service layer for product operations"""

    @staticmethod
    def create_product(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new product

        Args:
            data: Product data dict with name, brand_id, category_id, price, and optional fields

        Returns:
            Created product

        Raises:
            ValidationError: If validation fails
            DuplicateError: If SKU already exists
            NotFoundError: If brand_id or category_id don't exist
        """
        name = data.get('name', '').strip()
        brand_id = data.get('brand_id', '').strip()
        category_id = data.get('category_id', '').strip()
        price = data.get('price')

        # Validate required fields
        if not name:
            raise ValidationError("Product name is required")
        if not brand_id:
            raise ValidationError("Brand ID is required")
        if not category_id:
            raise ValidationError("Category ID is required")
        if price is None:
            raise ValidationError("Price is required")

        # Optional fields
        description = data.get('description')
        if description:
            description = description.strip()
            if not description:
                description = None

        sku = data.get('sku')
        if sku:
            sku = sku.strip()
            if not sku:
                sku = None

        stock_quantity = data.get('stock_quantity', 0)
        images = data.get('images')

        return Product.create(
            name=name,
            brand_id=brand_id,
            category_id=category_id,
            price=price,
            description=description,
            sku=sku,
            stock_quantity=stock_quantity,
            images=images
        )

    @staticmethod
    def get_product(product_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a product by ID

        Args:
            product_id: Product ID

        Returns:
            Product data or None if not found
        """
        return Product.get(product_id)

    @staticmethod
    def get_product_by_sku(sku: str) -> Optional[Dict[str, Any]]:
        """
        Get a product by SKU

        Args:
            sku: Stock Keeping Unit

        Returns:
            Product data or None if not found
        """
        return Product.get_by_sku(sku)

    @staticmethod
    def update_product(product_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a product

        Args:
            product_id: Product ID
            data: Update data

        Returns:
            Updated product data or None if not found

        Raises:
            ValidationError: If validation fails
            DuplicateError: If trying to update to existing SKU
            NotFoundError: If brand_id or category_id don't exist
        """
        # Prepare updates dict
        updates = {}

        if 'name' in data:
            updates['name'] = data['name'].strip()

        if 'brand_id' in data:
            updates['brand_id'] = data['brand_id'].strip()

        if 'category_id' in data:
            updates['category_id'] = data['category_id'].strip()

        if 'price' in data:
            updates['price'] = data['price']

        if 'description' in data:
            description = data['description']
            if description:
                description = description.strip()
                if not description:
                    description = None
            updates['description'] = description

        if 'sku' in data:
            sku = data['sku']
            if sku:
                sku = sku.strip()
                if not sku:
                    sku = None
            updates['sku'] = sku

        if 'stock_quantity' in data:
            updates['stock_quantity'] = data['stock_quantity']

        if 'images' in data:
            updates['images'] = data['images']

        if not updates:
            raise ValidationError("No valid fields to update")

        return Product.update(product_id, **updates)

    @staticmethod
    def delete_product(product_id: str) -> bool:
        """
        Delete a product

        Args:
            product_id: Product ID

        Returns:
            True if deleted, False if not found
        """
        return Product.delete(product_id)

    @staticmethod
    def list_products(limit: int = 50, last_evaluated_key: Optional[Dict] = None) -> Dict[str, Any]:
        """
        List all products

        Args:
            limit: Maximum number of products to return
            last_evaluated_key: Pagination key

        Returns:
            Dict with products list and pagination info
        """
        return Product.list_all(limit, last_evaluated_key)

    @staticmethod
    def list_products_by_brand(brand_id: str, limit: int = 50, last_evaluated_key: Optional[Dict] = None) -> Dict[str, Any]:
        """
        List products by brand

        Args:
            brand_id: Brand ID
            limit: Maximum number of products to return
            last_evaluated_key: Pagination key

        Returns:
            Dict with products list and pagination info
        """
        return Product.list_by_brand(brand_id, limit, last_evaluated_key)

    @staticmethod
    def list_products_by_category(category_id: str, limit: int = 50, last_evaluated_key: Optional[Dict] = None) -> Dict[str, Any]:
        """
        List products by category

        Args:
            category_id: Category ID
            limit: Maximum number of products to return
            last_evaluated_key: Pagination key

        Returns:
            Dict with products list and pagination info
        """
        return Product.list_by_category(category_id, limit, last_evaluated_key)

    @staticmethod
    def update_stock(product_id: str, stock_quantity: int) -> Optional[Dict[str, Any]]:
        """
        Update product stock quantity

        Args:
            product_id: Product ID
            stock_quantity: New stock quantity

        Returns:
            Updated product data or None if not found

        Raises:
            ValidationError: If validation fails
        """
        updates = {'stock_quantity': stock_quantity}
        return Product.update(product_id, **updates)

    @staticmethod
    def adjust_stock(product_id: str, quantity_change: int) -> Optional[Dict[str, Any]]:
        """
        Adjust product stock by a relative amount (add/subtract)

        Args:
            product_id: Product ID
            quantity_change: Amount to add (positive) or subtract (negative)

        Returns:
            Updated product data or None if not found

        Raises:
            ValidationError: If validation fails
            NotFoundError: If product doesn't exist
        """
        # Get current product
        product = Product.get(product_id)
        if not product:
            raise NotFoundError(f"Product with ID '{product_id}' not found")

        current_stock = product.get('stock_quantity', 0)
        new_stock = current_stock + quantity_change

        if new_stock < 0:
            raise ValidationError("Stock quantity cannot be negative after adjustment")

        return ProductService.update_stock(product_id, new_stock)
