# backend/registration_agent/tools/registration_tools/address_lookup.py
# Address lookup using Google Places API Text Search for UTJFC registration

import os
import requests
from typing import Dict, Optional
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def construct_full_address(house_number: str, postcode_address: str, postcode: str) -> str:
    """
    Construct a full address by combining house number with street info from postcode lookup.
    
    Args:
        house_number: The house number (e.g., "11", "12a", "Flat 2")
        postcode_address: The address returned from postcode-only search
        postcode: The original postcode
        
    Returns:
        str: Full constructed address
    """
    if not postcode_address:
        return f"{house_number}, {postcode}"
    
    # Extract street name from the postcode address
    # Typical format: "Street Name, Area, City, Postcode"
    parts = [part.strip() for part in postcode_address.split(',')]
    
    if len(parts) >= 2:
        # Use first part as street name, keep the rest
        street_name = parts[0]
        area_parts = parts[1:]
        
        # Construct: "house_number street_name, area, city, postcode"
        full_address = f"{house_number} {street_name}, " + ", ".join(area_parts)
    else:
        # Fallback: just prepend house number
        full_address = f"{house_number}, {postcode_address}"
    
    return full_address


def lookup_address_by_postcode_and_number(postcode: str, house_number: str, google_api_key: Optional[str] = None) -> Dict:
    """
    Look up full address using postcode and house number via Google Places API Text Search.
    
    Args:
        postcode (str): UK postcode (e.g., "M41 9JJ")
        house_number (str): House number/name (e.g., "12", "12a", "Flat 2")
        google_api_key (str, optional): Google Places API key. If not provided, will try to get from env
        
    Returns:
        dict: Lookup result with:
            - success (bool): Whether the lookup was successful
            - message (str): Success message or error description
            - formatted_address (str): Full formatted address if found
            - address_components (dict): Structured address components if found
            - confidence_level (str): High/Medium/Low based on API response
            - original_postcode (str): The original postcode provided
            - original_house_number (str): The original house number provided
    """
    
    # Handle empty inputs
    if not postcode or not postcode.strip():
        return {
            "success": False,
            "message": "Postcode cannot be empty.",
            "formatted_address": "",
            "address_components": {},
            "confidence_level": "None",
            "original_postcode": postcode or "",
            "original_house_number": house_number or ""
        }
    
    if not house_number or not house_number.strip():
        return {
            "success": False,
            "message": "House number cannot be empty.",
            "formatted_address": "",
            "address_components": {},
            "confidence_level": "None",
            "original_postcode": postcode,
            "original_house_number": house_number or ""
        }
    
    # Get API key
    if not google_api_key:
        google_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    
    if not google_api_key:
        return {
            "success": False,
            "message": "Google Maps API key not configured. Address lookup unavailable.",
            "formatted_address": "",
            "address_components": {},
            "confidence_level": "None",
            "original_postcode": postcode,
            "original_house_number": house_number
        }
    
    try:
        # Clean and format inputs
        postcode_clean = postcode.strip().upper()
        house_number_clean = house_number.strip()
        
        # Construct search query - just the postcode to get street/area info
        search_query = postcode_clean
        
        # Use Google Places API Text Search
        url = "https://places.googleapis.com/v1/places:searchText"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": google_api_key,
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.addressComponents"
        }
        
        payload = {
            "textQuery": search_query,
            "regionCode": "GB",  # UK region
            "languageCode": "en"
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get("places") or len(data["places"]) == 0:
            return {
                "success": False,
                "message": f"Postcode {postcode_clean} not found. Please check the postcode.",
                "formatted_address": "",
                "address_components": {},
                "confidence_level": "None",
                "original_postcode": postcode,
                "original_house_number": house_number
            }

        # Get the first (best) result for the postcode
        place = data["places"][0]
        postcode_address = place.get("formattedAddress", "")
        
        # Extract street name and area from the postcode result
        # Then construct the full address with the house number
        formatted_address = construct_full_address(house_number_clean, postcode_address, postcode_clean)
        
        # Check if this looks like a UK address
        uk_indicators = ["UK", "UNITED KINGDOM", "ENGLAND", "SCOTLAND", "WALES", "LONDON", "MANCHESTER", "BIRMINGHAM", "LIVERPOOL", "LEEDS", "SHEFFIELD", "BRISTOL", "CARDIFF", "EDINBURGH", "GLASGOW"]
        if not any(keyword in formatted_address.upper() for keyword in uk_indicators):
            return {
                "success": False,
                "message": "Found address appears to be outside the UK. Please check postcode.",
                "formatted_address": formatted_address,
                "address_components": {},
                "confidence_level": "Low",
                "original_postcode": postcode,
                "original_house_number": house_number
            }
        
        # Determine confidence level
        confidence_level = "High"
        if len(data["places"]) > 3:
            confidence_level = "Medium"
        
        # Extract address components
        address_components = extract_address_components_v2(place)
        
        return {
            "success": True,
            "message": f"Address found with {confidence_level.lower()} confidence",
            "formatted_address": formatted_address,
            "address_components": address_components,
            "confidence_level": confidence_level,
            "original_postcode": postcode,
            "original_house_number": house_number
        }
        
    except requests.RequestException as e:
        return {
            "success": False,
            "message": f"Address lookup service temporarily unavailable. Please try again.",
            "formatted_address": "",
            "address_components": {},
            "confidence_level": "None",
            "original_postcode": postcode,
            "original_house_number": house_number
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Address lookup error. Please check postcode and house number format.",
            "formatted_address": "",
            "address_components": {},
            "confidence_level": "None",
            "original_postcode": postcode,
            "original_house_number": house_number
        }


def house_number_matches(house_number: str, formatted_address: str) -> bool:
    """
    Check if the house number appears to match what's in the formatted address.
    
    Args:
        house_number: The house number we're looking for
        formatted_address: The full formatted address from Google
        
    Returns:
        bool: Whether the house number seems to match
    """
    house_lower = house_number.lower().strip()
    address_lower = formatted_address.lower()
    
    # Direct match
    if house_lower in address_lower:
        return True
    
    # Handle common variations
    # e.g., "12a" might be formatted as "12A" or "12-A"
    house_alpha = ''.join(c for c in house_lower if c.isalnum())
    if house_alpha in address_lower.replace('-', '').replace(' ', ''):
        return True
    
    # Extract just the numeric part for partial matching
    house_numeric = ''.join(c for c in house_number if c.isdigit())
    if house_numeric and house_numeric in address_lower:
        return True
    
    return False


def extract_address_components_v2(place_data: Dict) -> Dict:
    """
    Extract structured address components from Google Places API v2 result.
    
    Args:
        place_data: Single place result from Google Places API
        
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
    
    # Try to extract from addressComponents if available
    if "addressComponents" in place_data:
        for component in place_data["addressComponents"]:
            types = component.get("types", [])
            text = component.get("longText", "")
            
            if "street_number" in types:
                components["street_number"] = text
            elif "route" in types:
                components["street_name"] = text
            elif "locality" in types:
                components["locality"] = text
            elif "postal_code" in types:
                components["postal_code"] = text
            elif "administrative_area_level_1" in types:
                components["administrative_area"] = text
            elif "country" in types:
                components["country"] = text
    
    # Fallback to parsing formatted address
    if not any(components.values()):
        formatted = place_data.get("formattedAddress", "")
        if formatted:
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
    test_cases = [
        ("M41 9JJ", "10"),
        ("SW1A 2AA", "10"),  # 10 Downing Street
        ("M16 0RA", "1"),    # Old Trafford
        ("INVALID", "123"),
        ("", ""),
    ]
    
    print("Testing Address Lookup by Postcode + House Number:")
    print("-" * 70)
    
    for postcode, house_num in test_cases:
        print(f"\nTesting: '{house_num}' in '{postcode}'")
        result = lookup_address_by_postcode_and_number(postcode, house_num)
        print(f"Success: {result['success']}")
        print(f"Message: {result['message']}")
        if result['success']:
            print(f"Address: {result['formatted_address']}")
            print(f"Confidence: {result['confidence_level']}") 