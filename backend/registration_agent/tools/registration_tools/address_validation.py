# backend/registration_agent/tools/registration_tools/address_validation.py
# Address validation using Google Places API for UTJFC registration

import os
import requests
from typing import Dict, Optional
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def validate_address(address: str, google_api_key: Optional[str] = None) -> Dict:
    """
    Validate and format address using Google Places API.
    
    Args:
        address (str): The address to validate
        google_api_key (str, optional): Google Places API key. If not provided, will try to get from env
        
    Returns:
        dict: Validation result with:
            - valid (bool): Whether the address is valid
            - message (str): Success message or error description
            - formatted_address (str): Formatted address from Google if valid
            - address_components (dict): Structured address components if valid
            - original_address (str): The original address provided
            - confidence_level (str): High/Medium/Low based on API response
    """
    
    # Handle empty address
    if not address or not address.strip():
        return {
            "valid": False,
            "message": "Address cannot be empty. Please provide a full address.",
            "formatted_address": "",
            "address_components": {},
            "original_address": address or "",
            "confidence_level": "None"
        }
    
    # Get API key
    if not google_api_key:
        google_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    
    if not google_api_key:
        return {
            "valid": False,
            "message": "Google Places API key not configured. Address validation unavailable.",
            "formatted_address": address.strip(),
            "address_components": {},
            "original_address": address,
            "confidence_level": "None"
        }
    
    try:
        # Use Google Places API Text Search to find and validate the address
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            "query": address.strip(),
            "key": google_api_key,
            "region": "uk",  # Bias towards UK results
            "language": "en"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("status") != "OK" or not data.get("results"):
            return {
                "valid": False,
                "message": f"Address not found or unclear. Please provide a more complete address including postcode.",
                "formatted_address": "",
                "address_components": {},
                "original_address": address,
                "confidence_level": "None"
            }
        
        # Get the first (best) result
        result = data["results"][0]
        formatted_address = result.get("formatted_address", "")
        
        # Check if this looks like a UK address
        if not any(keyword in formatted_address.upper() for keyword in ["UK", "UNITED KINGDOM", "ENGLAND", "SCOTLAND", "WALES"]):
            return {
                "valid": False,
                "message": "Please provide a UK address. Address appears to be outside the UK.",
                "formatted_address": formatted_address,
                "address_components": {},
                "original_address": address,
                "confidence_level": "Low"
            }
        
        # Determine confidence level based on how well the search matched
        confidence_level = "High"
        if len(data["results"]) > 3:
            confidence_level = "Medium"
        
        # Extract address components for structured data
        address_components = extract_address_components(result)
        
        return {
            "valid": True,
            "message": f"Address validated successfully with {confidence_level.lower()} confidence",
            "formatted_address": formatted_address,
            "address_components": address_components,
            "original_address": address,
            "confidence_level": confidence_level
        }
        
    except requests.RequestException as e:
        return {
            "valid": False,
            "message": f"Address validation service temporarily unavailable. Please try again.",
            "formatted_address": "",
            "address_components": {},
            "original_address": address,
            "confidence_level": "None"
        }
    except Exception as e:
        return {
            "valid": False,
            "message": f"Address validation error. Please provide a complete address with postcode.",
            "formatted_address": "",
            "address_components": {},
            "original_address": address,
            "confidence_level": "None"
        }


def extract_address_components(place_result: Dict) -> Dict:
    """
    Extract structured address components from Google Places API result.
    
    Args:
        place_result: Single result from Google Places API
        
    Returns:
        dict: Structured address components
    """
    components = {
        "street_number": "",
        "street_name": "",
        "locality": "",
        "postal_code": "",
        "administrative_area": "",
        "country": ""
    }
    
    # Google Places doesn't always return address_components in text search
    # So we'll try to parse from formatted_address as fallback
    formatted = place_result.get("formatted_address", "")
    
    if formatted:
        # Simple parsing - in a real implementation you might want more sophisticated parsing
        parts = [part.strip() for part in formatted.split(",")]
        if len(parts) >= 2:
            components["street_name"] = parts[0]
            if len(parts) >= 3:
                components["locality"] = parts[1] 
                components["administrative_area"] = parts[2]
            if len(parts) >= 4:
                components["country"] = parts[-1]
    
    return components


# Test cases for development/debugging
if __name__ == "__main__":
    test_addresses = [
        "10 Downing Street, London",
        "Manchester United, Old Trafford, Manchester",
        "1 Main Street, Urmston, Manchester M41 9JJ",
        "Invalid address xyz123",
        "",
        "Some random text that is not an address"
    ]
    
    print("Testing Address Validation:")
    print("-" * 60)
    
    for addr in test_addresses:
        print(f"\nTesting: '{addr}'")
        result = validate_address(addr)
        print(f"Valid: {result['valid']}")
        print(f"Message: {result['message']}")
        if result['valid']:
            print(f"Formatted: {result['formatted_address']}")
            print(f"Confidence: {result['confidence_level']}") 