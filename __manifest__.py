# -*- coding: utf-8 -*-
{
    'name': "Odoo Serializer",
    'version': '1.0',
    'summary': "Django-like serializer and API response helper for Odoo modules",
    'description': """
The **Odoo Serializer** module provides a Django-style serializer system and a reusable Base API controller class for Odoo.

**Features**

- Validate and clean incoming API payloads

- Convert request data into typed, validated Python datatypes

- Simple field definitions with serializer custom field structure (example: required/default values)

- Date and datetime format handling per serializer

- Built-in JSON response formatting for controllers

- Safe serialization of date/datetime values


Perfect for developers building structured, consistent, and secure Odoo REST APIs.
    """,
    'author': "Awab Khalid",
    'website': "https://github.com/Awabkhaled/odoo_api_serializer",
    'category': 'Tools',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
