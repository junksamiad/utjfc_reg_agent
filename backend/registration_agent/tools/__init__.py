# backend/tools/__init__.py
# Main tools package
# This will eventually contain imports and registration of all available tools

from .registration_tools import (
    validate_person_name,
    PERSON_NAME_VALIDATION_TOOL,
    handle_person_name_validation
)

__all__ = [
    'validate_person_name',
    'PERSON_NAME_VALIDATION_TOOL', 
    'handle_person_name_validation'
] 