# Odoo API Serializer

A lightweight validation and serialization framework for building clean, maintainable REST APIs in Odoo.

## Overview

The `odoo_api_serializer` module provides a structured approach to handling API requests in Odoo, offering:

- **Field-level validation** with type checking and custom validators
- **DRF-inspired API** that's familiar to Django developers
- **Configurable date/datetime formats**
- **Clean separation of validation logic from controller code**

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

## How to Use

This section demonstrates how to build a complete REST API using the Film API example.

### Step 1: Define Your Serializer

Create a serializer class that defines the fields you want to validate:

```python
from odoo.addons.odoo_api_serializer.utils.serializers import BaseSerializer, Field

class FilmSerializer(BaseSerializer):
    # Configure custom date formats (optional)
    date_format = "%Y/%m/%d"
    datetime_format = "%Y/%m/%d %H:%M:%S"
    
    # Define fields with validation rules
    name = Field(type='char', required=True)
    genre = Field(
        type='selection',
        selection=('action', 'drama', 'comedy', 'animation', 
                   'romance', 'musical', 'documentary', 'thriller', 'horror')
    )
    release_date = Field(type='date')
    first_premier_datetime = Field(type='datetime')
    list_test = Field(type='list')
    dict_test = Field(type='dict')
    
    # Add custom field validator
    def validate_name(self, value):
        if value[0] == 'a':
            raise ValueError("Name cannot start with an 'a'")
        return value
```

### Step 2: Create Your API Controller

Build your controller with endpoints for CRUD operations:

```python
from odoo import http
from odoo.http import request
import json

class FilmsApiController(http.Controller):
    """
    APIs for Film Model (awab.film)
    Supports: Create, Read (all/single), Update, Delete
    """
        
    @http.route('/api/films', type='http', auth='none', 
                methods=['GET', 'POST'], csrf=False)
    def create_list_films(self, **kwargs):
        """
        GET  → List all films
        """
        # ------------------------------
        # The Rest Of Your Code Here
        # ------------------------------
        payload = request.get_json_data()
        serializer = FilmSerializer(payload, mode='create')    
        if not serializer.is_valid():
            return self._json_response( # A custom Function
                'error', 
                message='Validation failed', 
                data=serializer.errors,
                http_status=400
            )
            
        film = request.env['awab.film'].sudo().create(serializer.cleaned_data())
        return self._json_response( # A custom Function
            'success', 
            data=self._format_film(film), 
            message='Film created', 
            http_status=201
        )
            
    @http.route('/api/films/<int:film_id>', type='http', auth='none', 
                methods=['GET', 'PUT', 'DELETE'], csrf=False)
    def get_update_delete_film(self, film_id, **kwargs):
        """
        Handle GET, PUT, and DELETE requests for a film:
            - GET    /api/films/<id> → Fetch film info
            - PUT    /api/films/<id> → Update film info
            - DELETE /api/films/<id> → Delete film
        """
        # ------------------------------
        # The Rest Of Your Code Here
        # ------------------------------
        payload = request.get_json_data()
        if not payload:
            return self._json_response('error', message='Missing request body', http_status=400)
        
        serializer = FilmSerializer(payload, mode='write')
        
        if not serializer.is_valid():
            return self._json_response(
                'error', 
                message='Validation failed', 
                data=serializer.errors,
                http_status=400
            )
        
        film.write(serializer.cleaned_data())
        return self._json_response(
            'success', 
            message='Film updated successfully', 
            data=self._format_film(film)
        )
```

### Step 3: Test Your API

#### Create a Film (POST)

**Request:**
```bash
POST /api/films
Content-Type: application/json

{
    "name": "Inception",
    "genre": "thriller",
    "release_date": "2010/07/16",
    "first_premier_datetime": "2010/07/08 20:00:00"
}
```

**Response:**
```json
{
    "status": "success",
    "message": "Film created",
    "data": {
        "id": 1,
        "name": "Inception",
        "genre": "thriller",
        "release_date": "16-07-2010",
        "first_premier_datetime": "08-07-2010 20:00:00"
    }
}
```
#### Update Film (PUT)

**Request:**
```bash
PUT /api/films/1
Content-Type: application/json

{
    "genre": "action"
}
```

**Response:**
```json
{
    "status": "success",
    "message": "Film updated successfully",
    "data": {
        "id": 1,
        "name": "Inception",
        "genre": "action",
        "release_date": "16-07-2010",
        "first_premier_datetime": "08-07-2010 20:00:00"
    }
}
```

### Validation Examples

#### Invalid Selection Value

**Request:**
```json
{
    "name": "Test Film",
    "genre": "scifi"
}
```

**Response:**
```json
{
    "status": "error",
    "message": "Validation failed",
    "data": {
        "genre": "Invalid selection value 'scifi'. Must be one of: (action, drama, comedy, animation, romance, musical, documentary, thriller, horror)"
    }
}
```

#### Custom Validator Error

**Request:**
```json
{
    "name": "avatar"
}
```

**Response:**
```json
{
    "status": "error",
    "message": "Validation failed",
    "data": {
        "name": "Name cannot start with an 'a'"
    }
}
```

#### Missing Required Field

**Request:**
```json
{
    "genre": "action"
}
```

**Response:**
```json
{
    "status": "error",
    "message": "Validation failed",
    "data": {
        "name": "This field is required."
    }
}
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

## Custom Date Formats

Override the default date/datetime formats in your serializer:

```python
class CustomSerializer(BaseSerializer):
    date_format = "%d/%m/%Y"  # DD/MM/YYYY (e.g., 15/01/2025)
    datetime_format = "%d/%m/%Y %H:%M"  # DD/MM/YYYY HH:MM (e.g., 15/01/2025 14:30)
    
    created_date = Field(type='date', required=True)
    updated_at = Field(type='datetime')
```

## Response Format

All API responses should follow this consistent structure:

```json
{
    "status": "success|error",
    "message": "Optional message",
    "data": {
        "key": "value"
    }
}
```

Datetime objects are automatically formatted as strings when using the `_json_response` helper method.

## Requirements

- Odoo 18.0

## License

LGPL-3

## Contributing

Contributions are welcome! Please ensure all code follows Odoo, and python coding standards.

## Support

For issues and questions, please refer to the module documentation or contact the development team at https://github.com/Awabkhaled