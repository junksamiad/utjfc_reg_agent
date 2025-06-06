# backend/registration_agent/tools/registration_tools/postcode_validation_tool.py
# OpenAI function tool definition for UK postcode validation

import json
from .postcode_validation import validate_uk_postcode

# Tool definition for OpenAI Responses API
POSTCODE_VALIDATION_TOOL = {
    "type": "function",
    "name": "postcode_validation",
    "description": """Validate and normalize a UK postcode according to UTJFC registration standards.
    
    This tool validates postcodes by:
    - Checking the postcode matches UK format (e.g., M32 8JL, SW1A 2AA, B33 8TH)
    - Normalizing case (converting to uppercase)
    - Standardizing spacing format
    - Cleaning whitespace
    
    Use this tool specifically for postcode validation during address collection.
    
    Examples of valid postcodes:
    - "M32 8JL" (Manchester area)
    - "SW1A 2AA" (London)
    - "B33 8TH" (Birmingham)
    - "m32 8jl" (will be normalized to M32 8JL)
    - "M328JL" (will be formatted with proper spacing)
    
    Examples of invalid postcodes:
    - "M32" (incomplete)
    - "12345" (numbers only)
    - "INVALID" (not postcode format)
    """,
    "parameters": {
        "type": "object",
        "properties": {
            "postcode": {
                "type": "string",
                "description": "The UK postcode to validate and normalize (e.g., 'M32 8JL', 'm32 8jl', 'M328JL')"
            }
        },
        "required": ["postcode"]
    }
}

def handle_postcode_validation(postcode: str) -> str:
    """
    Handle the postcode validation tool call from agents.
    
    Args:
        postcode (str): The postcode to validate
        
    Returns:
        str: JSON string with validation results
    """
    try:
        # Perform validation
        validation_result = validate_uk_postcode(postcode)
        
        # Add usage guidance based on result
        if validation_result["valid"]:
            normalizations = validation_result.get("normalizations_applied", [])
            if normalizations:
                normalization_details = []
                if "whitespace_and_case_normalized" in normalizations:
                    normalization_details.append("converted to uppercase and cleaned whitespace")
                if "spacing_standardized" in normalizations:
                    normalization_details.append("spacing was standardized")
                
                validation_result["usage_note"] = f"Postcode is valid and ready for registration use. Note: {' and '.join(normalization_details)} during processing."
            else:
                validation_result["usage_note"] = "Postcode is valid and ready for registration use (no normalization needed)"
        else:
            validation_result["usage_note"] = "Postcode validation failed - please ask parent to provide a corrected UK postcode"
        
        return json.dumps(validation_result, indent=2)
        
    except Exception as e:
        error_result = {
            "valid": False,
            "message": f"Validation error: {str(e)}",
            "formatted_postcode": "",
            "original_input": postcode,
            "normalizations_applied": [],
            "usage_note": "Tool error occurred - please try again or handle manually"
        }
        return json.dumps(error_result, indent=2) 