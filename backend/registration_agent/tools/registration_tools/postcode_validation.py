# backend/registration_agent/tools/registration_tools/postcode_validation.py
# Core validation function for UK postcodes used in registration

import re

def validate_uk_postcode(postcode_input: str) -> dict:
    """
    Validate and normalize a UK postcode according to UTJFC registration standards.
    
    Rules:
    - Must match UK postcode format (e.g., M32 8JL, SW1A 2AA, B33 8TH)
    - Will be normalized to uppercase with proper spacing
    - Accepts various input formats and cleans them
    
    Args:
        postcode_input (str): The postcode to validate
        
    Returns:
        dict: Validation result with:
            - valid (bool): Whether the postcode passes validation
            - message (str): Success message or specific error description
            - formatted_postcode (str): Cleaned postcode in standard format if valid
            - original_input (str): The original input before normalization
            - normalizations_applied (list): List of normalizations that were performed
    """
    
    # Handle empty or None input
    if not postcode_input or not postcode_input.strip():
        return {
            "valid": False,
            "message": "Postcode cannot be empty",
            "formatted_postcode": "",
            "original_input": postcode_input or "",
            "normalizations_applied": []
        }
    
    # Track original input and normalizations applied
    original_input = postcode_input
    normalizations_applied = []
    
    # Normalize whitespace and convert to uppercase
    cleaned_postcode = postcode_input.strip().upper()
    if cleaned_postcode != postcode_input:
        normalizations_applied.append("whitespace_and_case_normalized")
    
    # Remove all spaces to work with the raw characters
    postcode_no_spaces = cleaned_postcode.replace(" ", "")
    
    # UK postcode regex patterns
    # Format: 1-2 letters, 1-2 digits, optional letter, space, 1 digit, 2 letters
    uk_postcode_patterns = [
        r'^[A-Z]{1,2}[0-9]{1,2}[A-Z]?[0-9][A-Z]{2}$',  # Full format without spaces
    ]
    
    # Check if it matches UK postcode pattern
    postcode_valid = False
    for pattern in uk_postcode_patterns:
        if re.match(pattern, postcode_no_spaces):
            postcode_valid = True
            break
    
    if not postcode_valid:
        return {
            "valid": False,
            "message": f"'{postcode_input}' is not a valid UK postcode format. Please provide a UK postcode (e.g., M32 8JL, SW1A 2AA)",
            "formatted_postcode": "",
            "original_input": original_input,
            "normalizations_applied": normalizations_applied
        }
    
    # Format with proper spacing: insert space before the last 3 characters
    if len(postcode_no_spaces) >= 5:
        formatted_postcode = postcode_no_spaces[:-3] + " " + postcode_no_spaces[-3:]
        if formatted_postcode != cleaned_postcode:
            normalizations_applied.append("spacing_standardized")
    else:
        formatted_postcode = postcode_no_spaces
    
    # All validations passed
    return {
        "valid": True,
        "message": f"Valid UK postcode: {formatted_postcode}",
        "formatted_postcode": formatted_postcode,
        "original_input": original_input,
        "normalizations_applied": normalizations_applied
    }


# Test cases for development/debugging
if __name__ == "__main__":
    test_cases = [
        # Valid postcodes
        ("M32 8JL", True),
        ("m32 8jl", True),  # Should normalize to M32 8JL
        ("M328JL", True),   # Should add space
        ("SW1A 2AA", True),
        ("sw1a2aa", True),  # Should normalize
        ("B33 8TH", True),
        ("E1 6AN", True),
        
        # Invalid postcodes
        ("", False),
        ("   ", False),
        ("M32", False),          # Incomplete
        ("12345", False),        # Numbers only
        ("INVALID", False),      # Not postcode format
        ("M32 8JLL", False),     # Too many letters at end
        ("MM32 8JL", False),     # Too many letters at start
        
        # Edge cases
        ("  m32   8jl  ", True), # Extra whitespace
    ]
    
    print("Running UK postcode validation tests:")
    print("-" * 60)
    
    for postcode, expected_valid in test_cases:
        result = validate_uk_postcode(postcode)
        passed = result["valid"] == expected_valid
        status = "✅ PASS" if passed else "❌ FAIL"
        
        print(f"{status} '{postcode}' -> {result['valid']} ({result['message']})")
        if result["valid"]:
            print(f"    Formatted: '{result['formatted_postcode']}'")
            if result["normalizations_applied"]:
                print(f"    Normalizations: {result['normalizations_applied']}")
        print() 