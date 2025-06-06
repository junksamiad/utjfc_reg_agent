# backend/registration_agent/tools/registration_tools/person_name_validation.py
# Core validation function for person names used in registration

import re

def validate_person_name(full_name: str) -> dict:
    """
    Validate a full name string according to UTJFC registration standards.
    
    Rules:
    - Must have at least two parts (first name + last name minimum)
    - Each part can only contain letters, apostrophes ('), and hyphens (-)
    - No other symbols, numbers, or special characters allowed
    - Hyphens are allowed between names (e.g., "Mary-Jane", "Jean-Pierre")
    - Curly apostrophes are automatically normalized to straight apostrophes
    
    Normalization:
    - Whitespace is normalized (extra spaces removed, trimmed)
    - Curly apostrophes (', ', etc.) are converted to straight apostrophes (')
    - This prevents common database issues with Unicode characters
    
    Args:
        full_name (str): The full name to validate
        
    Returns:
        dict: Validation result with:
            - valid (bool): Whether the name passes validation
            - message (str): Success message or specific error description
            - parts (list): List of name parts if valid
            - normalized_name (str): Cleaned/normalized version of the name
            - original_name (str): The original input before normalization
            - normalizations_applied (list): List of normalizations that were performed
    """
    
    # Handle empty or None input
    if not full_name or not full_name.strip():
        return {
            "valid": False,
            "message": "Name cannot be empty",
            "parts": [],
            "normalized_name": "",
            "original_name": full_name or "",
            "normalizations_applied": []
        }
    
    # Track original input and normalizations applied
    original_name = full_name
    normalizations_applied = []
    
    # Normalize whitespace - remove extra spaces and trim
    normalized_name = " ".join(full_name.strip().split())
    if normalized_name != full_name:
        normalizations_applied.append("whitespace_normalized")
    
    # Normalize curly apostrophes to straight apostrophes
    # Common curly apostrophes that cause issues in databases
    curly_apostrophes = {
        '\u2018': "'",  # Left single quotation mark
        '\u2019': "'",  # Right single quotation mark  
        '\u201A': "'",  # Single low-9 quotation mark
        '\u201B': "'",  # Single high-reversed-9 quotation mark
        '\u2039': "'",  # Single left-pointing angle quotation mark
        '\u203A': "'",  # Single right-pointing angle quotation mark
    }
    
    pre_apostrophe_name = normalized_name
    for curly, straight in curly_apostrophes.items():
        normalized_name = normalized_name.replace(curly, straight)
    
    if normalized_name != pre_apostrophe_name:
        normalizations_applied.append("curly_apostrophes_normalized")
    
    # Split into parts by spaces
    name_parts = normalized_name.split()
    
    # Check minimum parts requirement
    if len(name_parts) < 2:
        return {
            "valid": False,
            "message": "Name must contain at least two parts (first name and last name)",
            "parts": name_parts,
            "normalized_name": normalized_name,
            "original_name": original_name,
            "normalizations_applied": normalizations_applied
        }
    
    # Validate each part
    valid_name_pattern = re.compile(r"^[a-zA-Z'-]+$")
    
    for i, part in enumerate(name_parts):
        if not part:  # Empty part (shouldn't happen after normalization, but be safe)
            return {
                "valid": False,
                "message": f"Name part {i+1} is empty",
                "parts": name_parts,
                "normalized_name": normalized_name,
                "original_name": original_name,
                "normalizations_applied": normalizations_applied
            }
        
        if not valid_name_pattern.match(part):
            # Find the invalid character(s) for better error message
            invalid_chars = set(re.findall(r"[^a-zA-Z'-]", part))
            if invalid_chars:
                invalid_chars_str = ", ".join(sorted(invalid_chars))
                return {
                    "valid": False,
                    "message": f"Name part '{part}' contains invalid character(s): {invalid_chars_str}. Only letters, apostrophes ('), and hyphens (-) are allowed.",
                    "parts": name_parts,
                    "normalized_name": normalized_name,
                    "original_name": original_name,
                    "normalizations_applied": normalizations_applied
                }
            else:
                return {
                    "valid": False,
                    "message": f"Name part '{part}' is invalid",
                    "parts": name_parts,
                    "normalized_name": normalized_name,
                    "original_name": original_name,
                    "normalizations_applied": normalizations_applied
                }
    
    # All validations passed
    return {
        "valid": True,
        "message": f"Valid name with {len(name_parts)} parts",
        "parts": name_parts,
        "normalized_name": normalized_name,
        "original_name": original_name,
        "normalizations_applied": normalizations_applied
    }


def get_name_parts(full_name: str) -> tuple:
    """
    Extract first and last name from a validated full name.
    
    Args:
        full_name (str): The full name to parse
        
    Returns:
        tuple: (first_name, last_name) where last_name may contain multiple parts
    """
    validation_result = validate_person_name(full_name)
    
    if not validation_result["valid"]:
        return None, None
    
    parts = validation_result["parts"]
    
    if len(parts) == 2:
        return parts[0], parts[1]
    elif len(parts) > 2:
        # First part is first name, everything else is last name
        return parts[0], " ".join(parts[1:])
    else:
        return None, None


# Test cases for development/debugging
if __name__ == "__main__":
    test_cases = [
        # Valid names
        ("John Smith", True),
        ("Mary-Jane O'Connor", True),
        ("Jean-Pierre Van Der Berg", True),
        ("Sarah Jane Smith-Jones", True),
        ("Mike O'Brien", True),
        ("Anna-Maria Rodriguez", True),
        ("Patrick O'Boyle", True),  # Curly apostrophe (normalized)
        ("D'Angelo Martinez", True),  # Curly apostrophe (normalized)
        
        # Invalid names
        ("John", False),  # Only one part
        ("", False),  # Empty
        ("   ", False),  # Only whitespace
        ("John Smith123", False),  # Contains numbers
        ("John@Smith", False),  # Contains @
        ("John Smith!", False),  # Contains !
        ("John  Smith", True),  # Extra spaces (should be normalized)
        ("John_Smith", False),  # Contains underscore
        ("John.Smith", False),  # Contains period
    ]
    
    print("Running person name validation tests:")
    print("-" * 50)
    
    for name, expected_valid in test_cases:
        result = validate_person_name(name)
        passed = result["valid"] == expected_valid
        status = "✅ PASS" if passed else "❌ FAIL"
        
        print(f"{status} '{name}' -> {result['valid']} ({result['message']})")
        if result["valid"]:
            print(f"    Parts: {result['parts']}")
            print(f"    Normalized: '{result['normalized_name']}'")
        print() 