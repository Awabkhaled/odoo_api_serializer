from datetime import datetime, date
FIELD_TYPES = [
    'char',
    'text',
    'integer',
    'float',
    'boolean',
    'date',
    'datetime',
    'selection',
    'list',
    'dict'
]

FIELD_TYPES_SET = set(FIELD_TYPES)


class Field:
    """
    Defines a field used for validating and cleaning input dictionaries.
    Similar to DRF's basic Field, without model mapping.
    """

    def __init__(self, *, type, required=False, default=None, selection=None):
        if not type:
            raise ValueError("`type` is required when defining a Field.")
        if type not in FIELD_TYPES_SET:
            raise ValueError(
                f"Invalid field type '{type}'. Must be one of: {', '.join(FIELD_TYPES)}"
            )

        # If the type is 'selection', ensure valid selection list
        if type == 'selection':
            if not selection or not isinstance(selection, (list, tuple)):
                raise ValueError("`selection` must be provided as a list or tuple when type='selection'.")
            if not all(isinstance(choice, str) for choice in selection):
                raise ValueError("All selection values must be strings.")
            self.selection = selection
        else:
            if selection:
                raise ValueError(f"`selection` parameter is not valid for type `{type}`.")
            else:
                self.selection = None

        self.type = type
        self.required = required
        self.default = default

    def to_internal_value(self, value):
        """Convert input JSON value into the correct Python type."""
        if value is None:
            return self.default

        try:
            if self.type in ('char', 'text'):
                # Strictly ensure it's a non-numeric string nor a boolean value
                if isinstance(value, (int, float)):
                    raise ValueError("Expected string, got number")
                if isinstance(value, bool):
                    raise ValueError("Expected string, got boolean")
                return str(value)
            elif self.type == 'integer':
                if type(value) is int:
                    return int(value)
                elif isinstance(value, float) and value.is_integer():
                    return int(value)
                raise ValueError("Expected integer")
            elif self.type == 'float':
                if not isinstance(value, (int, float)):
                    raise ValueError("Expected float or integer")
                return float(value)
            elif self.type == 'boolean':
                if not isinstance(value, bool):
                    raise ValueError("Expected boolean")
                return value
            elif self.type == 'date':
                if isinstance(value, date):
                    return value
                if not isinstance(value, str):
                    raise ValueError(f"Expected date string ({getattr(self, '_date_format', '%Y-%m-%d')})")
                fmt = getattr(self, '_date_format', '%Y-%m-%d')
                return datetime.strptime(value, fmt).date()
            elif self.type == 'datetime':
                if isinstance(value, datetime):
                    return value
                if not isinstance(value, str):
                    raise ValueError(
                        f"Expected datetime string ({getattr(self, '_datetime_format', '%Y-%m-%d %H:%M:%S')})")
                fmt = getattr(self, '_datetime_format', '%Y-%m-%d %H:%M:%S')
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    # fallback: try date-only format (also uses serializer’s date_format)
                    fmt_date = getattr(self, '_date_format', '%Y-%m-%d')
                    try:
                        dt = datetime.strptime(value, fmt_date)
                        return datetime.combine(dt.date(), datetime.min.time())
                    except ValueError:
                        raise ValueError(f"Invalid datetime format. Expected '{fmt}' or '{fmt_date}'")
            elif self.type == 'selection':
                if not isinstance(value, str):
                    raise ValueError("Expected string for selection field.")
                if value not in self.selection:
                    raise ValueError(f"Invalid selection value '{value}'. Must be one of: ({', '.join(self.selection)})")
                return value
            elif self.type == 'list':
                if not isinstance(value, list):
                    raise ValueError("Expected list (ex. [1, 2, 3]).")
                return value
            elif self.type == 'dict':
                if not isinstance(value, dict):
                    raise ValueError("Expected dict (JSON object).")
                return value

        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid value for {self.type}: {e}")


class BaseSerializer:
    """
    Base serializer that validates and cleans input data (dict).
    It removes unwanted keys and ensures correct types/defaults.
    """
    date_format = "%Y-%m-%d"
    datetime_format = "%Y-%m-%d %H:%M:%S"

    def __init__(self, data=None, *, mode):
        if not mode:
            raise ValueError("`mode` is required when defining a serializer.")
        if mode not in ('create', 'write'):
            raise ValueError(
                f"Invalid serializer mode '{mode}'. Must be one of: create, write"
            )

        self.mode = mode
        self.initial_data = data or {}
        self.validated_data = {}
        self.errors = {}
        self.fields = self._collect_fields()

        # Assign serializer formats to all Field instances
        for field in self.fields.values():
            field._date_format = self.date_format
            field._datetime_format = self.datetime_format

    def __init_subclass__(cls, **kwargs):
        """Validate formats when subclass is defined"""
        super().__init_subclass__(**kwargs)

        sample_date = datetime(2025, 10, 28, 12, 0, 0)

        # --- Validate date_format ---
        try:
            _ = sample_date.strftime(cls.date_format)
        except Exception as e:
            raise ValueError(
                f"[{cls.__name__}] Invalid date_format '{cls.date_format}'.\n"
                f"Expected a valid Python strftime pattern.\n"
                f"Example of correct date format: '%Y-%m-%d' → 2025-10-27\n"
                f"Full error: {e}"
            )

        # --- Validate datetime_format ---
        try:
            _ = sample_date.strftime(cls.datetime_format)
        except Exception as e:
            raise ValueError(
                f"[{cls.__name__}] Invalid datetime_format '{cls.datetime_format}'.\n"
                f"Expected a valid Python strftime pattern.\n"
                f"Example of correct datetime format: '%Y-%m-%d %H:%M:%S' → 2025-10-27 12:00:00\n"
                f"Full error: {e}"
            )

    def _collect_fields(self):
        """Collect all declared Field attributes."""
        fields = {}
        for name, attr in self.__class__.__dict__.items():
            if isinstance(attr, Field):
                fields[name] = attr
        return fields

    def is_valid(self):
        """Validate input data against declared fields."""
        self.validated_data = {}
        self.errors = {}

        for name, field in self.fields.items():
            in_data = name in self.initial_data
            has_default = field.default is not None
            is_required = field.required
            is_create = self.mode == 'create'
            if not in_data and is_create and is_required:
                self.errors[name] = "This field is required."
                continue
            if not in_data and (not has_default or not is_create):
                continue
            raw_value = self.initial_data.get(name, field.default) if is_create else self.initial_data.get(name)

            try:
                # Get internal value
                value = field.to_internal_value(raw_value)

                # -- Attribute specific validation --
                validator_method = getattr(self, f'validate_{name}', None)
                if callable(validator_method):
                    try:
                        value = validator_method(value)
                    except ValueError as e:
                        self.errors[name] = str(e)
                        continue

                self.validated_data[name] = value
            except ValueError as e:
                self.errors[name] = str(e)

        return len(self.errors) == 0

    def cleaned_data(self):
        """Return the validated and cleaned dictionary."""
        return self.validated_data
