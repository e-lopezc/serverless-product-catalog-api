from typing import Dict, Any, Optional
from models.category import Category
from utils.exceptions import ValidationError, NotFoundError, DuplicateError


class CategoryService:
    """Service layer for category operations"""

    @staticmethod
    def create_category(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new category

        Args:
            data: Category data dict with name, description
        Returns:
            Created category

        Raises:
            ValidationError: If validation fails
            DuplicateError: If category name already exists
        """
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()


        return Category.create(name, description)

    @staticmethod
    def get_category(category_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a category by ID

        Args:
            category_id: Category ID

        Returns:
            Category data or None if not found
        """
        return Category.get(category_id)

    @staticmethod
    def update_category(category_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a category

        Args:
            category_id: Category ID
            data: Update data

        Returns:
            Updated category data or None if not found

        Raises:
            ValidationError: If validation fails
            DuplicateError: If trying to update to existing name
        """
        # Prepare updates dict
        updates = {}

        if 'name' in data:
            updates['name'] = data['name'].strip()

        if 'description' in data:
            updates['description'] = data['description'].strip()

        if not updates:
            raise ValidationError("No valid fields to update")

        return Category.update(category_id, **updates)

    @staticmethod
    def delete_category(category_id: str) -> bool:
        """
        Delete a category

        Args:
            category_id: Category ID

        Returns:
            True if deleted, False if not found
        """
        return Category.delete(category_id)

    @staticmethod
    def list_categories(limit: int = 50, last_evaluated_key: Optional[Dict] = None) -> Dict[str, Any]:
        """
        List all categories

        Args:
            limit: Maximum number of categories to return
            last_evaluated_key: Pagination key

        Returns:
            Dict with categories list and pagination info
        """
        return Category.list_all(limit, last_evaluated_key)
