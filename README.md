# Odoo API Serializer

A lightweight validation and serialization framework for building clean, maintainable REST APIs in Odoo.

## Overview

The `odoo_api_serializer` module provides a structured approach to handling API requests in Odoo, offering:

- **Field-level validation** with type checking and custom validators
- **Consistent JSON responses** with automatic datetime serialization
- **DRF-inspired API** that's familiar to Django developers

## Installation

1. Copy the module to your Odoo addons directory
2. Update the apps list in Odoo
3. Install the `odoo_api_serializer` module

## Components

### BaseSerializer

A validation class that ensures incoming data meets your requirements before processing.

**Key Features:**
- Type validation for common data types
- Required field enforcement
- Default value support
- Custom field-level validators
- Configurable date/datetime formats

### Field Types

The module supports the following field types:

| Type | Description | Example |
|------|-------------|---------|
| `char` | Short text strings | `"John Doe"` |
| `text` | Long text content | `"Description..."` |
| `integer` | Whole numbers | `42` |
| `float` | Decimal numbers | `3.14` |
| `boolean` | True/False values | `true` |
| `date` | Date values | `"2025-01-15"` |
| `datetime` | Date and time values | `"2025-01-15 14:30:00"` |
| `selection` | Predefined choices | `"draft"` |
| `list` | Array values | `[1, 2, 3]` |
| `dict` | JSON objects | `{"key": "value"}` |

### BaseApiController

A base controller class providing consistent JSON response formatting with automatic datetime handling.

## Usage Examples

### Basic Serializer

```python
from odoo_api_serializer.serializers import BaseSerializer, Field

class ProductSerializer(BaseSerializer):
    name = Field(type='char', required=True)
    price = Field(type='float', required=True)
    quantity = Field(type='integer', default=0)
    active = Field(type='boolean', default=True)
    
    def validate_price(self, value):
        """Custom validator for price field"""
        if value < 0:
            raise ValueError("Price cannot be negative")
        return value
```

### Using Selection Fields

```python
class OrderSerializer(BaseSerializer):
    status = Field(
        type='selection',
        required=True,
        selection=['draft', 'confirmed', 'done', 'cancelled']
    )
    order_date = Field(type='date', required=True)
```

### Custom Date Formats

```python
class CustomSerializer(BaseSerializer):
    date_format = "%d/%m/%Y"  # DD/MM/YYYY
    datetime_format = "%d/%m/%Y %H:%M"  # DD/MM/YYYY HH:MM
    
    created_date = Field(type='date', required=True)
    updated_at = Field(type='datetime')
```

### API Controller Example

```python
from odoo_api_serializer.controllers import BaseApiController
from odoo_api_serializer.serializers import BaseSerializer, Field

class ProductApiController(BaseApiController):
    
    @http.route('/api/products', type='http', auth='user', methods=['POST'], csrf=False)
    def create_product(self):
        self._ensure_user_env()
        
        # Parse JSON data
        try:
            data = json.loads(request.httprequest.data)
        except json.JSONDecodeError:
            return self._json_response('error', 'Invalid JSON', http_status=400)
        
        # Validate with serializer
        serializer = ProductSerializer(data=data, mode='create')
        if not serializer.is_valid():
            return self._json_response(
                'error',
                'Validation failed',
                data={'errors': serializer.errors},
                http_status=400
            )
        
        # Create record with validated data
        product = request.env['product.product'].create(serializer.cleaned_data())
        
        return self._json_response(
            'success',
            'Product created successfully',
            data={'id': product.id, 'name': product.name}
        )
```

### Update Operations

```python
@http.route('/api/products/<int:product_id>', type='http', auth='user', methods=['PUT'], csrf=False)
def update_product(self, product_id):
    self._ensure_user_env()
    
    product = request.env['product.product'].browse(product_id)
    if not product.exists():
        return self._json_response('error', 'Product not found', http_status=404)
    
    data = json.loads(request.httprequest.data)
    serializer = ProductSerializer(data=data, mode='write')
    
    if not serializer.is_valid():
        return self._json_response('error', 'Validation failed', 
                                  data={'errors': serializer.errors}, http_status=400)
    
    product.write(serializer.cleaned_data())
    return self._json_response('success', 'Product updated')
```

## Validation Modes

The serializer supports two modes:

- **`create` mode**: All required fields must be present, defaults are applied
- **`write` mode**: Only provided fields are validated, partial updates allowed

## Custom Field Validators

Add custom validation logic by defining `validate_<field_name>` methods:

```python
class UserSerializer(BaseSerializer):
    email = Field(type='char', required=True)
    age = Field(type='integer', required=True)
    
    def validate_email(self, value):
        if '@' not in value:
            raise ValueError("Invalid email format")
        return value.lower()
    
    def validate_age(self, value):
        if value < 18:
            raise ValueError("User must be at least 18 years old")
        return value
```

## Response Format

All responses from `BaseApiController` follow this structure:

```json
{
    "status": "success|error",
    "message": "Optional message",
    "data": {
        "key": "value"
    }
}
```

Datetime objects are automatically formatted as strings using the configured formats.

## Error Handling

Validation errors are collected and returned in a dictionary:

```python
{
    "status": "error",
    "message": "Validation failed",
    "data": {
        "errors": {
            "name": "This field is required.",
            "price": "Invalid value for float: Expected float or integer"
        }
    }
}
```

## Requirements

- Odoo 18.0

## License

LGPL-3

## Contributing

Contributions are welcome! Please ensure all code follows Odoo coding standards and includes appropriate validation tests.

## Support

For issues and questions, please refer to the module documentation or contact the development team 'https://github.com/Awabkhaled'.