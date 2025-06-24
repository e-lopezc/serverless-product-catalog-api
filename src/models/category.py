import uuid
import re
from datetime import datetime
from typing import Optional, Dict, Any

from utils.db_operations import db_client
from utils.exceptions import ValidationError, NotFoundError, DuplicateError
from config.settings import (
    CATEGORY_PREFIX,
    create_category_item,
    get_category_pk,
    get_category_sk
)


class Category:
    """Category model for the single table design"""

    ENTITY_PREFIX = CATEGORY_PREFIX
    LIST_PREFIX = "CATEGORY_LIST"

    @staticmethod
    def create(name: str, description: str) -> Dict[str, Any]:
        """
        Create a new category item

        Args:
            name: Category name (required, must be unique case-insensitive)
            description: Category description (required)


        Returns:
            Created Category item

        Raises:
            ValidationError: If validation fails
            DuplicateError: If category name already exists
        """
        # Validate input data
        Category._validate_data(name, description)

        # Check if category name already exists (case-insensitive)
        if Category._name_exists(name):
            raise DuplicateError(f"Category name '{name}' already exists")

        # Generate unique brand ID
        category_id = Category._generate_id()

        # Create category item
        category_item = create_category_item(category_id, name, description)

        # Save to database
        db_client.put_item(category_item)

        return category_item

    @staticmethod
    def get(category_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a category by ID

        Args:
            category_id: Category ID

        Returns:
            Category item or None if not found
        """
        if not category_id:
            return None

        pk = get_category_pk(category_id)
        sk = get_category_pk(category_id)

        return db_client.get_item(pk, sk)

    @staticmethod
    def update(category_id: str, **updates) -> Dict[str, Any]:
        """
        Update a category item

        Args:
            category_id: Category ID
            **updates: Fields to update (name, description)

        Returns:
            Updated category item

        Raises:
            NotFoundError: If category doesn't exist
            ValidationError: If validation fails
            DuplicateError: If trying to update to existing name
        """
        # Check if the category exists
        if not Category.exists(category_id):
            raise NotFoundError(f"Category with ID '{category_id}' not found")

        # Validate updates
        allowed_fields = {'name', 'description'}
        invalid_fields = set(updates.keys()) - allowed_fields
        if invalid_fields:
            raise ValidationError(f"Invalid fields: {', '.join(invalid_fields)}")

        # Validate individual fields
        if 'name' in updates:
            Category._validate_name(updates['name'])
            # Check if new name already exists (case-insensitive)
            if Category._name_exists(updates['name'], exclude_brand_id=category_id):
                raise DuplicateError(f"Category name '{updates['name']}' already exists")

        if 'description' in updates:
            Category._validate_description(updates['description'])


        # Add updated_at timestamp
        updates['updated_at'] = datetime.utcnow().isoformat()

        # If name is being updated, also update GSI3SK for sorting
        if 'name' in updates:
            updates['GSI3SK'] = updates['name'].upper()

        pk = get_category_pk(category_id)
        sk = get_category_sk(category_id)

        return db_client.update_item(pk, sk, updates)

    @staticmethod
    def delete(category_id: str) -> bool:
        """
        Delete a category item

        Args:
            category_id: Category ID

        Returns:
            True if deleted, False if not found
        """
        if not Category.exists(category_id):
            return False

        pk = get_category_pk(category_id)
        sk = get_category_sk(category_id)

        deleted_item = db_client.delete_item(pk, sk)
        return deleted_item is not None

    @staticmethod
    def exists(category_id: str) -> bool:
        """
        Check if a category exists

        Args:
            category_id: Category ID

        Returns:
            True if exists, False otherwise
        """
        if not category_id:
            return False

        pk = get_category_pk(category_id)
        sk = get_category_sk(category_id)

        return db_client.check_item_exists(pk, sk)

    @staticmethod
    def list_all(limit: int = 50, last_evaluated_key: Optional[Dict] = None) -> Dict[str, Any]:
        """
        List all categories sorted by name

        Args:
            limit: Maximum number of categories to return
            last_evaluated_key: Pagination key

        Returns:
            Dict with 'items' and 'last_evaluated_key'
        """
        return db_client.list_categories_by_name(limit, last_evaluated_key)

    # Helper methods
    @staticmethod
    def _generate_id() -> str:
        """Generate a unique category ID"""
        return str(uuid.uuid4())

    @staticmethod
    def _validate_data(name: str, description: str) -> None:
        """
        Validate category data

        Args:
            name: Category name
            description: Brand description
            website: Brand website URL

        Raises:
            ValidationError: If validation fails
        """
        Category._validate_name(name)
        Category._validate_description(description)


    @staticmethod
    def _validate_name(name: str) -> None:
        """Validate category name"""
        if not name:
            raise ValidationError("Category name is required")

        if not isinstance(name, str):
            raise ValidationError("Category name must be a string")

        name = name.strip()
        if not name:
            raise ValidationError("Cagegory name cannot be empty or whitespace")

        if len(name) < 2:
            raise ValidationError("Category name must be at least 2 characters long")

        if len(name) > 100:
            raise ValidationError("Category name cannot exceed 100 characters")

        # Check for valid characters (letters, numbers, spaces, hyphens, underscores)
        if not re.match(r'^[a-zA-Z0-9\s\-_&.]+$', name):
            raise ValidationError("Category name contains invalid characters")

    @staticmethod
    def _validate_description(description: str) -> None:
        """Validate category description"""
        if not description:
            raise ValidationError("Category description is required")

        if not isinstance(description, str):
            raise ValidationError("Category description must be a string")

        description = description.strip()
        if not description:
            raise ValidationError("Category description cannot be empty or whitespace")

        if len(description) < 10:
            raise ValidationError("Category description must be at least 10 characters long")

        if len(description) > 500:
            raise ValidationError("Category description cannot exceed 500 characters")


    @staticmethod
    def _name_exists(name: str, exclude_category_id: Optional[str] = None) -> bool:
        """
        Check if a Category name already exists (case-insensitive)

        Args:
            name: Category name to check
            exclude_brand_id: Category ID to exclude from check (for updates)

        Returns:
            True if name exists, False otherwise
        """
        if not name:
            return False

        # Query GSI-3 to find categories with similar names
        # We'll check case-insensitive by querying and then comparing
        try:
            result = db_client.query_gsi3(Category.LIST_PREFIX, limit=100)  # Get all categories

            name_upper = name.strip().upper()

            for item in result.get('items', []):
                existing_name = item.get('name', '').strip().upper()
                existing_category_id = item.get('category_id')

                # Skip if this is the category being updated
                if exclude_category_id and existing_category_id == exclude_category_id:
                    continue

                if existing_name == name_upper:
                    return True

            return False

        except Exception:
            # If query fails, assume name doesn't exist to avoid blocking creation
            return False
