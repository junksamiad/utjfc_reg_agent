# backend/registration_agent/tools/registration_tools/child_dob_validation_tool.py
# OpenAI function tool definition for child date of birth validation

import json
from .child_dob_validation import validate_child_dob, calculate_age

# Tool definition for OpenAI Responses API
CHILD_DOB_VALIDATION_TOOL = {
    "type": "function",
    "name": "child_dob_validation",
    "description": """Validate a child's date of birth according to UTJFC registration standards.
    
    This tool validates that a date of birth:
    - Can be parsed and converted to DD-MM-YYYY format
    - Has a birth year of 2007 or later (club requirement)
    - Is not a future date
    - Handles multiple input formats and normalizes them
    
    Use this tool to validate any child's date of birth during registration.
    
    Examples of valid dates:
    - "15-03-2015" (DD-MM-YYYY)
    - "31/12/2010" (DD/MM/YYYY)
    - "15.06.2007" (DD.MM.YYYY)
    - "2018-12-25" (YYYY-MM-DD)
    
    Examples of invalid dates:
    - "15-03-2006" (year too early)
    - "32-01-2015" (invalid day)
    - "15-03-2030" (future date)
    """,
    "parameters": {
        "type": "object",
        "properties": {
            "date_of_birth": {
                "type": "string",
                "description": "The child's date of birth in any common format (e.g., '15-03-2015', '31/12/2010', '2018-12-25')"
            },
            "calculate_age": {
                "type": "boolean",
                "description": "Whether to calculate the child's current age (default: false)",
                "default": False
            }
        },
        "required": ["date_of_birth"]
    }
}

def handle_child_dob_validation(date_of_birth: str, calculate_age_flag: bool = False) -> str:
    """
    Handle the child DOB validation tool call from agents.
    
    Args:
        date_of_birth (str): The date of birth to validate
        calculate_age_flag (bool): Whether to calculate current age
        
    Returns:
        str: JSON string with validation results
    """
    try:
        # Perform validation
        validation_result = validate_child_dob(date_of_birth)
        
        # Add age calculation if requested and validation passed
        if calculate_age_flag and validation_result["valid"]:
            age = calculate_age(validation_result["formatted_date"])
            validation_result["current_age"] = age
        
        # Add usage guidance based on result
        if validation_result["valid"]:
            normalizations = validation_result.get("normalizations_applied", [])
            if normalizations:
                normalization_details = []
                if "whitespace_normalized" in normalizations:
                    normalization_details.append("whitespace was cleaned")
                if "date_format_normalized" in normalizations:
                    normalization_details.append("date format was converted to DD-MM-YYYY")
                if "flexible_date_parsing" in normalizations:
                    normalization_details.append("date was parsed from flexible format")
                
                validation_result["usage_note"] = f"Date is valid and ready for registration use. Note: {' and '.join(normalization_details)} during processing."
            else:
                validation_result["usage_note"] = "Date is valid and ready for registration use (no normalization needed)"
        else:
            validation_result["usage_note"] = "Date validation failed - please ask parent to provide a corrected date"
        
        return json.dumps(validation_result, indent=2)
        
    except Exception as e:
        error_result = {
            "valid": False,
            "message": f"Validation error: {str(e)}",
            "formatted_date": "",
            "original_input": date_of_birth,
            "birth_year": None,
            "normalizations_applied": [],
            "usage_note": "Tool error occurred - please try again or handle manually"
        }
        return json.dumps(error_result, indent=2) 