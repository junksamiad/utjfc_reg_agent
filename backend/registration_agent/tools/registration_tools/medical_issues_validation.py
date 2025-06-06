# backend/registration_agent/tools/registration_tools/medical_issues_validation.py
# Core validation function for child medical issues used in registration

import re

def validate_medical_issues(has_issues_response: str, issues_details: str = "") -> dict:
    """
    Validate and structure medical issues information according to UTJFC registration standards.
    
    Rules:
    - First response should indicate Yes/No for having medical issues
    - If Yes, details should be provided and structured into a list
    - Normalize common responses and provide clear structure
    
    Args:
        has_issues_response (str): Response to "does child have medical issues" (Yes/No)
        issues_details (str): Details of medical issues if has_issues_response is Yes
        
    Returns:
        dict: Validation result with:
            - valid (bool): Whether the response passes validation
            - message (str): Success message or specific error description
            - has_medical_issues (bool): Whether child has medical issues
            - medical_issues_list (list): Structured list of medical issues if any
            - original_response (str): The original response
            - original_details (str): The original details provided
            - normalizations_applied (list): List of normalizations that were performed
    """
    
    # Handle empty or None input for main response
    if not has_issues_response or not has_issues_response.strip():
        return {
            "valid": False,
            "message": "Medical issues response cannot be empty. Please provide Yes or No.",
            "has_medical_issues": None,
            "medical_issues_list": [],
            "original_response": has_issues_response or "",
            "original_details": issues_details or "",
            "normalizations_applied": []
        }
    
    # Track original inputs and normalizations applied
    original_response = has_issues_response
    original_details = issues_details or ""
    normalizations_applied = []
    
    # Normalize whitespace
    has_issues_response = has_issues_response.strip().lower()
    if has_issues_response != original_response.strip().lower():
        normalizations_applied.append("whitespace_normalized")
    
    # Define patterns for Yes/No responses
    yes_patterns = [
        'yes', 'y', 'yeah', 'yep', 'sure', 'definitely', 'absolutely', 
        'true', '1', 'correct', 'indeed', 'of course', 'certainly'
    ]
    
    no_patterns = [
        'no', 'n', 'nope', 'nah', 'never', 'not', 'none', 'negative',
        'false', '0', 'incorrect', 'nothing', 'nil', 'zero'
    ]
    
    # Determine if child has medical issues
    has_medical_issues = None
    
    if has_issues_response in yes_patterns:
        has_medical_issues = True
        if has_issues_response != 'yes':
            normalizations_applied.append("yes_response_normalized")
    elif has_issues_response in no_patterns:
        has_medical_issues = False
        if has_issues_response != 'no':
            normalizations_applied.append("no_response_normalized")
    else:
        # Try partial matching
        for pattern in yes_patterns:
            if pattern in has_issues_response:
                has_medical_issues = True
                normalizations_applied.append("yes_response_normalized")
                break
        
        if has_medical_issues is None:
            for pattern in no_patterns:
                if pattern in has_issues_response:
                    has_medical_issues = False
                    normalizations_applied.append("no_response_normalized")
                    break
    
    # If still unclear, return validation error
    if has_medical_issues is None:
        return {
            "valid": False,
            "message": f"Could not understand response '{original_response}'. Please answer with Yes or No.",
            "has_medical_issues": None,
            "medical_issues_list": [],
            "original_response": original_response,
            "original_details": original_details,
            "normalizations_applied": normalizations_applied
        }
    
    # If no medical issues, return successful response
    if not has_medical_issues:
        return {
            "valid": True,
            "message": "No medical issues recorded",
            "has_medical_issues": False,
            "medical_issues_list": [],
            "original_response": original_response,
            "original_details": original_details,
            "normalizations_applied": normalizations_applied
        }
    
    # If has medical issues, validate and structure the details
    if not issues_details or not issues_details.strip():
        return {
            "valid": False,
            "message": "Medical issues details are required when child has medical issues. Please provide details.",
            "has_medical_issues": True,
            "medical_issues_list": [],
            "original_response": original_response,
            "original_details": original_details,
            "normalizations_applied": normalizations_applied
        }
    
    # Structure the medical issues into a list
    medical_issues_list = structure_medical_issues(issues_details.strip())
    
    if len(medical_issues_list) > 0:
        normalizations_applied.append("medical_issues_structured")
    
    return {
        "valid": True,
        "message": f"Medical issues recorded: {len(medical_issues_list)} issue(s) identified",
        "has_medical_issues": True,
        "medical_issues_list": medical_issues_list,
        "original_response": original_response,
        "original_details": original_details,
        "normalizations_applied": normalizations_applied
    }


def structure_medical_issues(details: str) -> list:
    """
    Structure medical issues details into a clean list.
    
    Args:
        details (str): Raw medical issues details
        
    Returns:
        list: Structured list of medical issues
    """
    if not details or not details.strip():
        return []
    
    # Common separators for multiple issues
    separators = [',', ';', ' and ', ' & ', '\n', '|']
    
    # Start with the full text
    issues = [details.strip()]
    
    # Split by common separators
    for separator in separators:
        new_issues = []
        for issue in issues:
            if separator in issue:
                split_issues = [item.strip() for item in issue.split(separator) if item.strip()]
                new_issues.extend(split_issues)
            else:
                new_issues.append(issue)
        issues = new_issues
    
    # Clean up each issue
    cleaned_issues = []
    for issue in issues:
        # Remove common prefixes
        issue = re.sub(r'^(has|have|suffers from|diagnosed with|condition:?|issue:?)\s*', '', issue, flags=re.IGNORECASE)
        # Capitalize first letter
        issue = issue.strip()
        if issue:
            issue = issue[0].upper() + issue[1:] if len(issue) > 1 else issue.upper()
            cleaned_issues.append(issue)
    
    # Remove duplicates while preserving order
    unique_issues = []
    seen = set()
    for issue in cleaned_issues:
        issue_lower = issue.lower()
        if issue_lower not in seen:
            seen.add(issue_lower)
            unique_issues.append(issue)
    
    return unique_issues


# Test cases for development/debugging
if __name__ == "__main__":
    test_cases = [
        # Valid no issues
        ("No", "", True),
        ("n", "", True),
        ("Nope", "", True),
        
        # Valid yes with issues
        ("Yes", "Asthma", True),
        ("y", "diabetes, allergies to nuts", True),
        ("yeah", "has ADHD and wears glasses", True),
        
        # Invalid responses
        ("maybe", "", False),
        ("", "", False),
        ("yes", "", False),  # Yes but no details
        
        # Complex medical issues
        ("YES", "Asthma; diabetes; allergies to peanuts and shellfish", True),
        ("true", "ADHD, requires inhaler, wears contact lenses", True),
    ]
    
    print("Running medical issues validation tests:")
    print("-" * 60)
    
    for response, details, expected_valid in test_cases:
        result = validate_medical_issues(response, details)
        passed = result["valid"] == expected_valid
        status = "✅ PASS" if passed else "❌ FAIL"
        
        print(f"{status} '{response}' + '{details}' -> {result['valid']}")
        print(f"    Message: {result['message']}")
        if result["valid"]:
            print(f"    Has Issues: {result['has_medical_issues']}")
            if result["medical_issues_list"]:
                print(f"    Issues: {result['medical_issues_list']}")
            if result["normalizations_applied"]:
                print(f"    Normalizations: {result['normalizations_applied']}")
        print() 