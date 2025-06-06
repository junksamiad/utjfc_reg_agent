# backend/registration_agent/tools/registration_tools/person_name_validation_tool.py
# OpenAI function tool definition for person name validation

import json
from .person_name_validation import validate_person_name, get_name_parts

# Tool definition for OpenAI Responses API
PERSON_NAME_VALIDATION_TOOL = {
    "type": "function",
    "name": "person_name_validation",
    "description": """Validate a full person name according to UTJFC registration standards.
    
    This tool validates that a name:
    - Has at least two parts (first name + last name minimum)
    - Contains only letters, apostrophes ('), and hyphens (-)
    - No numbers, symbols, or special characters (except ' and -)
    - Normalizes whitespace and formatting
    
    Use this tool to validate player names, parent names, or any person's name during registration.
    
    Examples of valid names:
    - "John Smith"
    - "Mary-Jane O'Connor" 
    - "Jean-Pierre Van Der Berg"
    
    Examples of invalid names:
    - "John" (only one part)
    - "John Smith123" (contains numbers)
    - "John@Smith" (contains symbols)
    """,
    "parameters": {
        "type": "object",
        "properties": {
            "full_name": {
                "type": "string",
                "description": "The full name to validate (e.g., 'John Smith', 'Mary-Jane O'Connor')"
            },
            "extract_parts": {
                "type": "boolean",
                "description": "Whether to extract first and last name parts from the validated name (default: false)",
                "default": False
            }
        },
        "required": ["full_name"]
    }
}

def handle_person_name_validation(full_name: str, extract_parts: bool = False) -> str:
    """
    Handle the person name validation tool call from agents.
    
    Args:
        full_name (str): The full name to validate
        extract_parts (bool): Whether to extract first/last name parts
        
    Returns:
        str: JSON string with validation results
    """
    try:
        # Perform validation
        validation_result = validate_person_name(full_name)
        
        # Add name part extraction if requested
        if extract_parts and validation_result["valid"]:
            first_name, last_name = get_name_parts(full_name)
            validation_result["first_name"] = first_name
            validation_result["last_name"] = last_name
        
        # Add usage guidance based on result
        if validation_result["valid"]:
            normalizations = validation_result.get("normalizations_applied", [])
            if normalizations:
                normalization_details = []
                if "whitespace_normalized" in normalizations:
                    normalization_details.append("extra spaces were removed")
                if "curly_apostrophes_normalized" in normalizations:
                    normalization_details.append("curly apostrophes were converted to straight apostrophes")
                
                validation_result["usage_note"] = f"Name is valid and ready for registration use. Note: {' and '.join(normalization_details)} during processing."
            else:
                validation_result["usage_note"] = "Name is valid and ready for registration use (no normalization needed)"
        else:
            validation_result["usage_note"] = "Name validation failed - please ask user to provide a corrected version"
        
        return json.dumps(validation_result, indent=2)
        
    except Exception as e:
        error_result = {
            "valid": False,
            "message": f"Validation error: {str(e)}",
            "parts": [],
            "normalized_name": "",
            "usage_note": "Tool error occurred - please try again or handle manually"
        }
        return json.dumps(error_result, indent=2) 