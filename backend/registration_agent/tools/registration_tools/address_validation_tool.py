# backend/registration_agent/tools/registration_tools/address_validation_tool.py
# OpenAI function tool definition for address validation using Google Places API

import json
from .address_validation import validate_address

# Tool definition for OpenAI Responses API - CORRECTED format
ADDRESS_VALIDATION_TOOL = {
    "type": "function",
    "name": "address_validation",
    "description": """Validate a UK address using Google Places API to ensure it's a real, complete address.
    
    This tool validates addresses by:
    - Checking the address exists in Google Places database
    - Ensuring it's a UK address
    - Formatting the address consistently
    - Providing structured address components
    
    Use this tool to validate any address provided during registration to ensure it's complete and accurate.
    
    Examples of valid addresses:
    - "10 Downing Street, London SW1A 2AA"
    - "1 Main Street, Urmston, Manchester M41 9JJ"
    - "Old Trafford, Manchester M16 0RA"
    
    Examples that need clarification:
    - "123 Main St" (incomplete - needs area/postcode)
    - "Random text xyz" (not a real address)
    - "" (empty address)
    """,
    "parameters": {
        "type": "object",
        "properties": {
            "address": {
                "type": "string",
                "description": "The full address to validate including street, area, and postcode if available"
            }
        },
        "required": ["address"]
    }
}

def handle_address_validation(address: str) -> str:
    """
    Handle the address validation tool call from agents.
    
    Args:
        address (str): The address to validate
        
    Returns:
        str: JSON string with validation results
    """
    try:
        # Perform validation
        validation_result = validate_address(address)
        
        # Add usage guidance based on result
        if validation_result["valid"]:
            confidence = validation_result.get("confidence_level", "Unknown")
            validation_result["usage_note"] = f"Address validated successfully with {confidence.lower()} confidence. Use the formatted_address for consistent storage."
        else:
            validation_result["usage_note"] = "Address validation failed - please ask parent to provide a more complete address including postcode"
        
        return json.dumps(validation_result, indent=2)
        
    except Exception as e:
        error_result = {
            "valid": False,
            "message": f"Address validation error: {str(e)}",
            "formatted_address": "",
            "address_components": {},
            "original_address": address,
            "confidence_level": "None",
            "usage_note": "Tool error occurred - please try again or handle manually"
        }
        return json.dumps(error_result, indent=2) 