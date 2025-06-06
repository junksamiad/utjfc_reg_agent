# backend/registration_agent/tools/registration_tools/child_dob_validation.py
# Core validation function for child date of birth used in registration

import re
from datetime import datetime, date

def validate_child_dob(dob_input: str) -> dict:
    """
    Validate a child's date of birth according to UTJFC registration standards.
    
    Rules:
    - Must be in DD-MM-YYYY format
    - Birth year must be 2007 or later (no children born before 2007)
    - Must be a valid date
    - Date normalization from various input formats
    
    Args:
        dob_input (str): The date of birth to validate
        
    Returns:
        dict: Validation result with:
            - valid (bool): Whether the date passes validation
            - message (str): Success message or specific error description
            - formatted_date (str): Date in DD-MM-YYYY format if valid
            - original_input (str): The original input before normalization
            - birth_year (int): The birth year if valid
            - normalizations_applied (list): List of normalizations that were performed
    """
    
    # Handle empty or None input
    if not dob_input or not dob_input.strip():
        return {
            "valid": False,
            "message": "Date of birth cannot be empty",
            "formatted_date": "",
            "original_input": dob_input or "",
            "birth_year": None,
            "normalizations_applied": []
        }
    
    # Track original input and normalizations applied
    original_input = dob_input
    normalizations_applied = []
    
    # Normalize whitespace
    dob_input = dob_input.strip()
    if dob_input != original_input.strip():
        normalizations_applied.append("whitespace_normalized")
    
    # Try to parse various date formats and convert to DD-MM-YYYY
    parsed_date = None
    input_format = None
    
    # Define common date formats to try
    date_formats = [
        ("%d-%m-%Y", "DD-MM-YYYY"),
        ("%d/%m/%Y", "DD/MM/YYYY"),
        ("%d.%m.%Y", "DD.MM.YYYY"),
        ("%d %m %Y", "DD MM YYYY"),
        ("%d-%m-%y", "DD-MM-YY"),
        ("%d/%m/%y", "DD/MM/YY"),
        ("%Y-%m-%d", "YYYY-MM-DD"),
        ("%m/%d/%Y", "MM/DD/YYYY"),
        ("%m-%d-%Y", "MM-DD-YYYY"),
    ]
    
    for fmt, description in date_formats:
        try:
            parsed_date = datetime.strptime(dob_input, fmt).date()
            input_format = description
            break
        except ValueError:
            continue
    
    # If no format worked, try some flexible parsing
    if not parsed_date:
        # Try to extract numbers and guess the format
        numbers = re.findall(r'\d+', dob_input)
        
        if len(numbers) == 3:
            try:
                # Try different interpretations of the three numbers
                day, month, year = map(int, numbers)
                
                # Handle 2-digit years
                if year < 100:
                    if year <= 30:  # Assume 2000s for years 00-30
                        year += 2000
                    else:  # Assume 1900s for years 31-99
                        year += 1900
                
                # Validate ranges
                if 1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2030:
                    parsed_date = date(year, month, day)
                    input_format = "flexible_parsing"
                    normalizations_applied.append("flexible_date_parsing")
                
            except (ValueError, TypeError):
                pass
    
    if not parsed_date:
        return {
            "valid": False,
            "message": f"Could not parse date '{dob_input}'. Please provide date in DD-MM-YYYY format (e.g., 15-03-2015)",
            "formatted_date": "",
            "original_input": original_input,
            "birth_year": None,
            "normalizations_applied": normalizations_applied
        }
    
    # Check if year is 2007 or later
    birth_year = parsed_date.year
    if birth_year < 2007:
        return {
            "valid": False,
            "message": f"Birth year {birth_year} is too early. Children must be born in 2007 or later for UTJFC registration.",
            "formatted_date": "",
            "original_input": original_input,
            "birth_year": birth_year,
            "normalizations_applied": normalizations_applied
        }
    
    # Check if date is not in the future
    today = date.today()
    if parsed_date > today:
        return {
            "valid": False,
            "message": f"Date of birth cannot be in the future. Please check the date provided.",
            "formatted_date": "",
            "original_input": original_input,
            "birth_year": birth_year,
            "normalizations_applied": normalizations_applied
        }
    
    # Format as DD-MM-YYYY
    formatted_date = parsed_date.strftime("%d-%m-%Y")
    
    # Check if format normalization was applied
    if input_format != "DD-MM-YYYY":
        normalizations_applied.append("date_format_normalized")
    
    # All validations passed
    return {
        "valid": True,
        "message": f"Valid date of birth for child born in {birth_year}",
        "formatted_date": formatted_date,
        "original_input": original_input,
        "birth_year": birth_year,
        "normalizations_applied": normalizations_applied
    }


def calculate_age(dob_string: str) -> int:
    """
    Calculate age from a validated date of birth string.
    
    Args:
        dob_string (str): Date in DD-MM-YYYY format
        
    Returns:
        int: Age in years, or None if invalid date
    """
    validation_result = validate_child_dob(dob_string)
    
    if not validation_result["valid"]:
        return None
    
    try:
        birth_date = datetime.strptime(validation_result["formatted_date"], "%d-%m-%Y").date()
        today = date.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return age
    except:
        return None


# Test cases for development/debugging
if __name__ == "__main__":
    test_cases = [
        # Valid dates
        ("15-03-2015", True),
        ("01-01-2020", True),
        ("31/12/2010", True),
        ("15.06.2007", True),
        ("25 11 2018", True),
        ("2018-12-25", True),
        
        # Valid with 2-digit years
        ("15-03-15", True),  # Should be 2015
        ("01/01/20", True),  # Should be 2020
        
        # Invalid - too early
        ("15-03-2006", False),
        ("01-01-2000", False),
        
        # Invalid formats
        ("", False),
        ("not-a-date", False),
        ("32-13-2015", False),  # Invalid day/month
        
        # Future dates
        ("15-03-2030", False),
    ]
    
    print("Running child DOB validation tests:")
    print("-" * 60)
    
    for dob, expected_valid in test_cases:
        result = validate_child_dob(dob)
        passed = result["valid"] == expected_valid
        status = "✅ PASS" if passed else "❌ FAIL"
        
        print(f"{status} '{dob}' -> {result['valid']} ({result['message']})")
        if result["valid"]:
            print(f"    Formatted: {result['formatted_date']}")
            print(f"    Birth Year: {result['birth_year']}")
            if result["normalizations_applied"]:
                print(f"    Normalizations: {result['normalizations_applied']}")
        print() 