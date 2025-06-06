# backend/registration_agent/tools/registration_tools/address_lookup_tool.py
# OpenAI tool definition for address lookup using Google Places API

from .address_lookup import lookup_address_by_postcode_and_number

# OpenAI tool definition - CORRECTED for Responses API
ADDRESS_LOOKUP_TOOL = {
    "type": "function",
    "name": "address_lookup",
    "description": "Look up a full address using UK postcode and house number via Google Places API. Returns the complete formatted address for user confirmation.",
    "parameters": {
        "type": "object",
        "properties": {
            "postcode": {
                "type": "string",
                "description": "UK postcode (e.g., 'M41 9JJ', 'SW1A 2AA'). Will be cleaned and validated."
            },
            "house_number": {
                "type": "string", 
                "description": "House number or name (e.g., '12', '12a', 'Flat 2', 'The Cottage'). Can include letters and descriptions."
            }
        },
        "required": ["postcode", "house_number"]
    }
}

def handle_address_lookup(postcode: str, house_number: str) -> dict:
    """
    Handle address lookup tool calls from OpenAI.
    
    Args:
        postcode (str): UK postcode to search within
        house_number (str): House number/name to find
        
    Returns:
        dict: Lookup result containing success status, message, formatted address, etc.
    """
    return lookup_address_by_postcode_and_number(postcode, house_number) 