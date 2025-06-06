# backend/registration_agent/tools/registration_tools/medical_issues_validation_tool.py
# OpenAI function tool definition for medical issues validation

import json
from .medical_issues_validation import validate_medical_issues

# Tool definition for OpenAI Responses API
MEDICAL_ISSUES_VALIDATION_TOOL = {
    "type": "function",
    "name": "medical_issues_validation",
    "description": """Validate and structure medical issues information according to UTJFC registration standards.
    
    This tool validates and structures medical issues by:
    - Normalizing Yes/No responses (accepts variations like 'yeah', 'nope', etc.)
    - If Yes, structuring medical issues details into a clean list
    - Handling multiple issues separated by commas, semicolons, 'and', etc.
    - Cleaning up common prefixes and formatting
    
    Use this tool to validate and structure any medical issues information during registration.
    
    Examples of valid responses:
    - has_issues: "No" -> No medical issues
    - has_issues: "Yes", details: "Asthma" -> Single issue
    - has_issues: "y", details: "diabetes, allergies to nuts" -> Multiple issues
    - has_issues: "yeah", details: "has ADHD and wears glasses" -> Multiple issues with cleanup
    
    Examples that require clarification:
    - has_issues: "maybe" (unclear yes/no)
    - has_issues: "yes", details: "" (missing required details)
    """,
    "parameters": {
        "type": "object",
        "properties": {
            "has_issues": {
                "type": "string",
                "description": "Response to whether child has medical issues (Yes/No and variations)"
            },
            "issues_details": {
                "type": "string",
                "description": "Details of medical issues if has_issues is Yes (optional if No)",
                "default": ""
            }
        },
        "required": ["has_issues"]
    }
}

def handle_medical_issues_validation(has_issues: str, issues_details: str = "") -> str:
    """
    Handle the medical issues validation tool call from agents.
    
    Args:
        has_issues (str): Response to whether child has medical issues
        issues_details (str): Details of medical issues if applicable
        
    Returns:
        str: JSON string with validation results
    """
    try:
        # Perform validation
        validation_result = validate_medical_issues(has_issues, issues_details)
        
        # Add usage guidance based on result
        if validation_result["valid"]:
            normalizations = validation_result.get("normalizations_applied", [])
            if normalizations:
                normalization_details = []
                if "whitespace_normalized" in normalizations:
                    normalization_details.append("whitespace was cleaned")
                if "yes_response_normalized" in normalizations:
                    normalization_details.append("yes response was normalized")
                if "no_response_normalized" in normalizations:
                    normalization_details.append("no response was normalized")
                if "medical_issues_structured" in normalizations:
                    normalization_details.append("medical issues were structured into a list")
                
                validation_result["usage_note"] = f"Medical issues information is valid and ready for registration use. Note: {' and '.join(normalization_details)} during processing."
            else:
                validation_result["usage_note"] = "Medical issues information is valid and ready for registration use (no normalization needed)"
        else:
            validation_result["usage_note"] = "Medical issues validation failed - please ask parent to provide clearer information"
        
        return json.dumps(validation_result, indent=2)
        
    except Exception as e:
        error_result = {
            "valid": False,
            "message": f"Validation error: {str(e)}",
            "has_medical_issues": None,
            "medical_issues_list": [],
            "original_response": has_issues,
            "original_details": issues_details,
            "normalizations_applied": [],
            "usage_note": "Tool error occurred - please try again or handle manually"
        }
        return json.dumps(error_result, indent=2) 