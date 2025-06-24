import os

# Using the single table design.
TABLE_NAME = os.getenv('DYNAMODB_TABLE', 'products_catalog')

# Primary Key Field Names
PK_FIELD = 'PK'
SK_FIELD = 'SK'

# Global Secondary Indexes (matching Terraform)
GSI1_NAME = 'GSI-1'
GSI1_PK = 'SK'    # Inverted index
GSI1_SK = 'PK'

GSI2_NAME = 'GSI-2'
GSI2_PK = 'brand_id'
GSI2_SK = 'product_id'

GSI3_NAME = 'GSI-3'
GSI3_PK = 'GSI3PK'
GSI3_SK = 'GSI3SK'

# Entity Type Prefixes
BRAND_PREFIX = 'BRAND'
CATEGORY_PREFIX = 'CATEGORY'
PRODUCT_PREFIX = 'PRODUCT'

# Key Generation Functions
def get_brand_pk(brand_id):
    """Generate brand partition key"""
    return f"{BRAND_PREFIX}#{brand_id}"

def get_brand_sk(brand_id):
    """Generate brand sort key"""
    return f"{BRAND_PREFIX}#{brand_id}"

def get_category_pk(category_id):
    """Generate category partition key"""
    return f"{CATEGORY_PREFIX}#{category_id}"

def get_category_sk(category_id):
    """Generate category sort key"""
    return f"{CATEGORY_PREFIX}#{category_id}"

def get_product_pk(product_id):
    """Generate product partition key"""
    return f"{PRODUCT_PREFIX}#{product_id}"

def get_product_sk(product_id):
    """Generate product sort key"""
    return f"{PRODUCT_PREFIX}#{product_id}"

# Access Pattern Helper Functions
def get_entity_list_keys(entity_type):
    """
    Generate keys for listing entities using GSI-1 (inverted index)
    Query where SK begins_with entity type
    """
    return {
        'gsi_name': GSI1_NAME,
        'pk_field': GSI1_PK,
        'sk_field': GSI1_SK,
        'pk_value': f"{entity_type}#",  # SK begins_with pattern
    }

def get_products_by_brand_keys(brand_id):
    """
    Generate keys for querying products by brand using GSI-2
    """
    return {
        'gsi_name': GSI2_NAME,
        'pk_field': GSI2_PK,
        'sk_field': GSI2_SK,
        'pk_value': brand_id,
    }

def get_gsi3_keys(gsi3_pk, gsi3_sk=None):
    """
    Generate keys for GSI-3 flexible queries
    Can be used for:
    - Categories by name: GSI3PK="CATEGORY_LIST", GSI3SK=category_name
    - Products by category: GSI3PK="CATEGORY#{id}", GSI3SK=product_id
    - Any other custom access pattern
    """
    return {
        'gsi_name': GSI3_NAME,
        'pk_field': GSI3_PK,
        'sk_field': GSI3_SK,
        'pk_value': gsi3_pk,
        'sk_value': gsi3_sk
    }

# Item Structure Helpers
def create_brand_item(brand_id, name, description=None, website=None):
    """Create a brand item structure"""
    from datetime import datetime

    item = {
        PK_FIELD: get_brand_pk(brand_id),
        SK_FIELD: get_brand_sk(brand_id),
        GSI3_PK: 'BRAND_LIST',  # For listing all brands
        GSI3_SK: name.upper(),  # For sorting brands by name
        'entity_type': 'brand',
        'brand_id': brand_id,
        'name': name,
        'description': description,
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }

    if website:
        item['website'] = website

    return item

def create_category_item(category_id, name, description=None, parent_category_id=None):
    """Create a category item structure"""
    from datetime import datetime

    item = {
        PK_FIELD: get_category_pk(category_id),
        SK_FIELD: get_category_sk(category_id),
        GSI3_PK: 'CATEGORY_LIST',  # For listing all categories
        GSI3_SK: name.upper(),     # For sorting categories by name
        'entity_type': 'category',
        'category_id': category_id,
        'name': name,
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }

    if description:
        item['description'] = description
    if parent_category_id:
        item['parent_category_id'] = parent_category_id

    return item

def create_product_item(product_id, name, brand_id, category_id, price,
                       description=None, sku=None, stock_quantity=0, images=None):
    """Create a product item structure"""
    from datetime import datetime

    item = {
        PK_FIELD: get_product_pk(product_id),
        SK_FIELD: get_product_sk(product_id),
        # GSI-2 fields for products by brand
        'brand_id': brand_id,
        'product_id': product_id,
        # GSI-3 for products by category
        GSI3_PK: f"CATEGORY#{category_id}",
        GSI3_SK: product_id,
        'entity_type': 'product',
        'name': name,
        'category_id': category_id,
        'price': price,
        'stock_quantity': stock_quantity,
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }

    if description:
        item['description'] = description
    if sku:
        item['sku'] = sku
    if images:
        item['images'] = images

    return item

# Access Pattern Documentation
ACCESS_PATTERNS = {
    'get_brand_by_id': {
        'operation': 'get_item',
        'keys': 'PK=BRAND#{id}, SK=BRAND#{id}'
    },
    'list_all_brands': {
        'operation': 'query',
        'index': 'GSI-1',
        'keys': 'SK begins_with BRAND#'
    },
    'list_brands_by_name': {
        'operation': 'query',
        'index': 'GSI-3',
        'keys': 'GSI3PK=BRAND_LIST, GSI3SK sorted by name'
    },
    'list_categories_by_name': {
        'operation': 'query',
        'index': 'GSI-3',
        'keys': 'GSI3PK=CATEGORY_LIST, GSI3SK sorted by name'
    },
    'get_products_by_brand': {
        'operation': 'query',
        'index': 'GSI-2',
        'keys': 'brand_id={brand_id}'
    },
    'get_products_by_category': {
        'operation': 'query',
        'index': 'GSI-3',
        'keys': 'GSI3PK=CATEGORY#{category_id}'
    }
}

# API Configuration
API_VERSION = 'v1'
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100

# Feature Flags
ENABLE_SOFT_DELETE = os.getenv('ENABLE_SOFT_DELETE', 'false').lower() == 'true'

# AWS Configuration
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

# CORS Configuration
CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
CORS_HEADERS = [
    'Content-Type',
    'X-Amz-Date',
    'Authorization',
    'X-Api-Key',
    'X-Amz-Security-Token'
]
