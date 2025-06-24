import uuid
import re
from datetime import datetime
from typing import Optional, Dict, Any
import validators

from utils.db_operations import db_client
from utils.exceptions import ValidationError, NotFoundError, DuplicateError
from config.settings import (
    BRAND_PREFIX,
    create_brand_item,
    get_brand_pk,
    get_brand_sk
)


class Brand:
    """Brand model for single table design"""

    ENTITY_PREFIX = BRAND_PREFIX
    LIST_PREFIX = "BRAND_LIST"

    @staticmethod
    def create(name: str, description: str, website: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new brand item

        Args:
            name: Brand name (required, must be unique case-insensitive)
            description: Brand description (required)
            website: Brand website URL (optional)

        Returns:
            Created brand item

        Raises:
            ValidationError: If validation fails
            DuplicateError: If brand name already exists
        """
        # Validate input data
        Brand._validate_data(name, description, website)

        # Check if brand name already exists (case-insensitive)
        if Brand._name_exists(name):
            raise DuplicateError(f"Brand name '{name}' already exists")

        # Generate unique brand ID
        brand_id = Brand._generate_id()

        # Create brand item
        brand_item = create_brand_item(brand_id, name, description, website)

        # Save to database
        db_client.put_item(brand_item)

        return brand_item

    @staticmethod
    def get(brand_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a brand by ID

        Args:
            brand_id: Brand ID

        Returns:
            Brand item or None if not found
        """
        if not brand_id:
            return None

        pk = get_brand_pk(brand_id)
        sk = get_brand_sk(brand_id)

        return db_client.get_item(pk, sk)

    @staticmethod
    def update(brand_id: str, **updates) -> Dict[str, Any]:
        """
        Update a brand item

        Args:
            brand_id: Brand ID
            **updates: Fields to update (name, description, website)

        Returns:
            Updated brand item

        Raises:
            NotFoundError: If brand doesn't exist
            ValidationError: If validation fails
            DuplicateError: If trying to update to existing name
        """
        # Check if brand exists
        if not Brand.exists(brand_id):
            raise NotFoundError(f"Brand with ID '{brand_id}' not found")

        # Validate updates
        allowed_fields = {'name', 'description', 'website'}
        invalid_fields = set(updates.keys()) - allowed_fields
        if invalid_fields:
            raise ValidationError(f"Invalid fields: {', '.join(invalid_fields)}")

        # Validate individual fields
        if 'name' in updates:
            Brand._validate_name(updates['name'])
            # Check if new name already exists (case-insensitive)
            if Brand._name_exists(updates['name'], exclude_brand_id=brand_id):
                raise DuplicateError(f"Brand name '{updates['name']}' already exists")

        if 'description' in updates:
            Brand._validate_description(updates['description'])

        if 'website' in updates:
            Brand._validate_website(updates['website'])

        # Add updated_at timestamp
        updates['updated_at'] = datetime.utcnow().isoformat()

        # If name is being updated, also update GSI3SK for sorting
        if 'name' in updates:
            updates['GSI3SK'] = updates['name'].upper()

        pk = get_brand_pk(brand_id)
        sk = get_brand_sk(brand_id)

        return db_client.update_item(pk, sk, updates)

    @staticmethod
    def delete(brand_id: str) -> bool:
        """
        Delete a brand iem

        Args:
            brand_id: Brand ID

        Returns:
            True if deleted, False if not found
        """
        if not Brand.exists(brand_id):
            return False

        pk = get_brand_pk(brand_id)
        sk = get_brand_sk(brand_id)

        deleted_item = db_client.delete_item(pk, sk)
        return deleted_item is not None

    @staticmethod
    def exists(brand_id: str) -> bool:
        """
        Check if a brand exists

        Args:
            brand_id: Brand ID

        Returns:
            True if exists, False otherwise
        """
        if not brand_id:
            return False

        pk = get_brand_pk(brand_id)
        sk = get_brand_sk(brand_id)

        return db_client.check_item_exists(pk, sk)

    @staticmethod
    def list_all(limit: int = 50, last_evaluated_key: Optional[Dict] = None) -> Dict[str, Any]:
        """
        List all brands sorted by name

        Args:
            limit: Maximum number of brands to return
            last_evaluated_key: Pagination key

        Returns:
            Dict with 'items' and 'last_evaluated_key'
        """
        return db_client.list_brands_by_name(limit, last_evaluated_key)

    # Helper methods
    @staticmethod
    def _generate_id() -> str:
        """Generate a unique brand ID"""
        return str(uuid.uuid4())

    @staticmethod
    def _validate_data(name: str, description: str, website: Optional[str] = None) -> None:
        """
        Validate brand data

        Args:
            name: Brand name
            description: Brand description
            website: Brand website URL

        Raises:
            ValidationError: If validation fails
        """
        Brand._validate_name(name)
        Brand._validate_description(description)
        if website is not None:
            Brand._validate_website(website)

    @staticmethod
    def _validate_name(name: str) -> None:
        """Validate brand name"""
        if not name:
            raise ValidationError("Brand name is required")

        if not isinstance(name, str):
            raise ValidationError("Brand name must be a string")

        name = name.strip()
        if not name:
            raise ValidationError("Brand name cannot be empty or whitespace")

        if len(name) < 2:
            raise ValidationError("Brand name must be at least 2 characters long")

        if len(name) > 100:
            raise ValidationError("Brand name cannot exceed 100 characters")

        # Check for valid characters (letters, numbers, spaces, hyphens, underscores)
        if not re.match(r'^[a-zA-Z0-9\s\-_&.]+$', name):
            raise ValidationError("Brand name contains invalid characters")

    @staticmethod
    def _validate_description(description: str) -> None:
        """Validate brand description"""
        if not description:
            raise ValidationError("Brand description is required")

        if not isinstance(description, str):
            raise ValidationError("Brand description must be a string")

        description = description.strip()
        if not description:
            raise ValidationError("Brand description cannot be empty or whitespace")

        if len(description) < 10:
            raise ValidationError("Brand description must be at least 10 characters long")

        if len(description) > 500:
            raise ValidationError("Brand description cannot exceed 500 characters")

    @staticmethod
    def _validate_website(website: str) -> None:
        """Validate brand website URL"""
        if not website:
            return  # Website is optional

        if not isinstance(website, str):
            raise ValidationError("Website must be a string")

        website = website.strip()
        if not website:
            return  # Empty string is acceptable for optional field

        # Use validators library for robust URL validation
        if not validators.url(website):
            raise ValidationError("Invalid website URL format")

        # Additional check for http/https protocol
        if not website.lower().startswith(('http://', 'https://')):
            raise ValidationError("Website URL must use http or https protocol")

    @staticmethod
    def _name_exists(name: str, exclude_brand_id: Optional[str] = None) -> bool:
        """
        Check if a brand name already exists (case-insensitive)

        Args:
            name: Brand name to check
            exclude_brand_id: Brand ID to exclude from check (for updates)

        Returns:
            True if name exists, False otherwise
        """
        if not name:
            return False

        # Query GSI-3 to find brands with similar names
        # We'll check case-insensitive by querying and then comparing
        try:
            result = db_client.query_gsi3(Brand.LIST_PREFIX, limit=100)  # Get all brands

            name_upper = name.strip().upper()

            for item in result.get('items', []):
                existing_name = item.get('name', '').strip().upper()
                existing_brand_id = item.get('brand_id')

                # Skip if this is the brand being updated
                if exclude_brand_id and existing_brand_id == exclude_brand_id:
                    continue

                if existing_name == name_upper:
                    return True

            return False

        except Exception:
            # If query fails, assume name doesn't exist to avoid blocking creation
            return False
