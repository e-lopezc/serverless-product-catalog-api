from typing import Dict, Any, Optional
from models.brand import Brand
from utils.exceptions import ValidationError, NotFoundError, DuplicateError


class BrandService:
    """Service layer for brand operations"""

    @staticmethod
    def create_brand(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new brand

        Args:
            data: Brand data dict with name, description, and optional website

        Returns:
            Created brand

        Raises:
            ValidationError: If validation fails
            DuplicateError: If brand name already exists
        """
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        website = data.get('website')

        if website:
            website = website.strip()
            if not website:
                website = None

        return Brand.create(name, description, website)

    @staticmethod
    def get_brand(brand_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a brand by ID

        Args:
            brand_id: Brand ID

        Returns:
            Brand data or None if not found
        """
        return Brand.get(brand_id)

    @staticmethod
    def update_brand(brand_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a brand

        Args:
            brand_id: Brand ID
            data: Update data

        Returns:
            Updated brand data or None if not found

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

        if 'website' in data:
            website = data['website']
            if website:
                website = website.strip()
                if not website:
                    website = None
            updates['website'] = website

        if not updates:
            raise ValidationError("No valid fields to update")

        return Brand.update(brand_id, **updates)

    @staticmethod
    def delete_brand(brand_id: str) -> bool:
        """
        Delete a brand

        Args:
            brand_id: Brand ID

        Returns:
            True if deleted, False if not found
        """
        return Brand.delete(brand_id)

    @staticmethod
    def list_brands(limit: int = 50, last_evaluated_key: Optional[Dict] = None) -> Dict[str, Any]:
        """
        List all brands

        Args:
            limit: Maximum number of brands to return
            last_evaluated_key: Pagination key

        Returns:
            Dict with brands list and pagination info
        """
        return Brand.list_all(limit, last_evaluated_key)
