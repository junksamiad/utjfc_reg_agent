from typing import Dict, Any, get_origin, get_args, Union
from pydantic import BaseModel
from pydantic.fields import FieldInfo
from typing_extensions import Literal
import inspect

def pydantic_to_openai_schema(pydantic_model: BaseModel, function_name: str, function_description: str) -> Dict[str, Any]:
    """
    Convert a Pydantic model to an OpenAI function calling schema.
    
    This allows the AI to see all individual fields with their descriptions,
    validation rules, and examples - just like the old OpenAI function calling approach.
    
    Args:
        pydantic_model: The Pydantic model class
        function_name: Name of the function for OpenAI
        function_description: Description of what the function does
        
    Returns:
        dict: Complete OpenAI function schema with detailed property descriptions
    """
    
    properties = {}
    required_fields = []
    
    # Get all fields from the Pydantic model (v2 syntax)
    for field_name, field_info in pydantic_model.model_fields.items():
        
        # Build the property definition
        property_def = _convert_pydantic_field_to_openai_property(field_name, field_info)
        
        properties[field_name] = property_def
        
        # Check if field is required (no default value)
        if field_info.default is ... or (field_info.default is None and not _is_optional_v2(field_info)):
            required_fields.append(field_name)
    
    return {
        "type": "function",
        "name": function_name,
        "description": function_description,
        "parameters": {
            "type": "object",
            "properties": properties,
            "required": required_fields
        }
    }


def _convert_pydantic_field_to_openai_property(field_name: str, field_info: FieldInfo) -> Dict[str, Any]:
    """Convert a single Pydantic field to OpenAI property definition."""
    
    property_def = {}
    
    # Get the annotation (type) from field_info
    field_type = field_info.annotation
    
    # Handle Literal types first (most important for enum detection)
    if _is_literal_type(field_type):
        enum_values = get_args(field_type)
        property_def["type"] = "string"
        property_def["enum"] = list(enum_values)
        
        # Add special descriptions for key enum fields to help AI normalize
        if field_name == "player_gender":
            property_def["description"] = (field_info.description or "") + \
                " IMPORTANT: Normalize user input - 'boy/man/male' → 'Male', 'girl/woman/female' → 'Female', 'prefer not to say/not disclosed' → 'Not Disclosed'"
        elif field_name == "parent_relationship_to_player":
            property_def["description"] = (field_info.description or "") + \
                " IMPORTANT: Normalize user input - 'mum/mom/mother' → 'Mother', 'dad/daddy/father' → 'Father', 'gran/grandma/grandfather/grandad' → 'Other'"
        elif field_name in ["player_has_any_medical_issues", "communication_consent", "played_elsewhere_last_season"]:
            property_def["description"] = (field_info.description or "") + \
                " IMPORTANT: Normalize user input - 'yes/yeah/yep/y' → 'Y', 'no/nope/n' → 'N'"
        else:
            property_def["description"] = field_info.description
            
    # Handle Union types (like Optional)
    elif _is_union_type(field_type):
        union_args = get_args(field_type)
        # Filter out NoneType for Optional handling
        non_none_types = [arg for arg in union_args if arg is not type(None)]
        
        if len(non_none_types) == 1:
            # This is Optional[SomeType]
            inner_type = non_none_types[0]
            if _is_literal_type(inner_type):
                enum_values = get_args(inner_type)
                property_def["type"] = "string"
                property_def["enum"] = list(enum_values)
            else:
                property_def["type"] = _get_simple_type(inner_type)
        else:
            property_def["type"] = "string"  # Default for complex unions
            
    # Handle basic types
    elif field_type == str:
        property_def["type"] = "string"
    elif field_type == int:
        property_def["type"] = "integer"
    elif field_type == float:
        property_def["type"] = "number"
    elif field_type == bool:
        property_def["type"] = "boolean"
    elif field_type == list:
        property_def["type"] = "array"
    elif field_type == dict:
        property_def["type"] = "object"
    else:
        property_def["type"] = "string"  # Default fallback
    
    # Add description from Pydantic field (if not already set above)
    if "description" not in property_def and field_info.description:
        property_def["description"] = field_info.description
    
    # Add validation constraints
    if hasattr(field_info, 'pattern') and field_info.pattern:
        property_def["pattern"] = field_info.pattern
        property_def["description"] = property_def.get("description", "") + f" (Format: {field_info.pattern})"
    
    if hasattr(field_info, 'min_length') and field_info.min_length:
        property_def["minLength"] = field_info.min_length
    
    if hasattr(field_info, 'max_length') and field_info.max_length:
        property_def["maxLength"] = field_info.max_length
    
    if hasattr(field_info, 'ge') and field_info.ge is not None:
        property_def["minimum"] = field_info.ge
    
    if hasattr(field_info, 'le') and field_info.le is not None:
        property_def["maximum"] = field_info.le
    
    # Add examples if available
    if hasattr(field_info, 'examples') and field_info.examples:
        property_def["examples"] = field_info.examples
    
    return property_def


def _is_literal_type(field_type) -> bool:
    """Check if a type is a Literal type."""
    origin = get_origin(field_type)
    return origin is Literal


def _is_union_type(field_type) -> bool:
    """Check if a type is a Union type (including Optional)."""
    origin = get_origin(field_type)
    return origin is Union


def _get_simple_type(field_type) -> str:
    """Get simple type string for basic Python types."""
    if field_type == str:
        return "string"
    elif field_type == int:
        return "integer"
    elif field_type == float:
        return "number"
    elif field_type == bool:
        return "boolean"
    elif field_type == list:
        return "array"
    elif field_type == dict:
        return "object"
    else:
        return "string"


def _is_optional_v2(field_info) -> bool:
    """Check if a field is Optional in Pydantic v2."""
    # In v2, check if the field has a default or is explicitly optional
    if hasattr(field_info, 'default') and field_info.default is not ...:
        return True
    
    # Check the annotation for Optional type
    field_type = field_info.annotation
    origin = get_origin(field_type)
    if origin is type(None):
        return True
    
    args = get_args(field_type)
    if origin and args:
        return type(None) in args
    
    return False


# Example usage function
def generate_registration_schema():
    """Generate the OpenAI schema for our registration data contract."""
    from .registration_data_models import RegistrationDataContract
    
    return pydantic_to_openai_schema(
        pydantic_model=RegistrationDataContract,
        function_name="update_reg_details_to_db",
        function_description="""
        Save complete registration data to the registrations_2526 database.
        
        Extract each piece of information from the conversation history and provide it
        in the exact format specified for each field. The AI should use its intelligence
        to parse the conversation and extract data in the precise format required.
        
        Call this function AFTER create_payment_token succeeds in routine 29.
        """
    ) 