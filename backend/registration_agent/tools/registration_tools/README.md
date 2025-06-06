# Registration Tools

A collection of validation and utility tools specifically designed for UTJFC player registration processes. These tools are shared between the new registration agent and re-registration agent.

## Available Tools

### 1. Person Name Validation (`person_name_validation`)

Validates full person names according to UTJFC registration standards.

#### **Validation Rules**
- Must contain at least 2 parts (first name + last name minimum)
- Only letters, apostrophes (`'`), and hyphens (`-`) allowed
- No numbers, symbols, or special characters
- Automatic whitespace normalization
- **Curly apostrophes automatically converted to straight apostrophes**

#### **Valid Name Examples**
- `"John Smith"`
- `"Mary-Jane O'Connor"`
- `"Jean-Pierre Van Der Berg"`
- `"Sarah Jane Smith-Jones"`
- `"Patrick O'Boyle"` ✅ (curly apostrophe normalized)
- `"D'Angelo Martinez"` ✅ (curly apostrophe normalized)

#### **Invalid Name Examples**
- `"John"` ❌ (only one part)
- `"John Smith123"` ❌ (contains numbers)
- `"John@Smith"` ❌ (contains symbols)
- `"John_Smith"` ❌ (contains underscore)

#### **Usage in Agents**

```python
# Tool definition for OpenAI
{
    "type": "function",
    "name": "person_name_validation",
    "parameters": {
        "full_name": "John Smith",
        "extract_parts": true
    }
}
```

#### **Response Format**

```json
{
  "valid": true,
  "message": "Valid name with 2 parts",
  "parts": ["John", "Smith"],
  "normalized_name": "John Smith",
  "original_name": "John Smith",
  "normalizations_applied": [],
  "first_name": "John",
  "last_name": "Smith",
  "usage_note": "Name is valid and ready for registration use (no normalization needed)"
}
```

#### **Response with Normalizations**

When normalizations are applied, the response includes detailed information:

```json
{
  "valid": true,
  "message": "Valid name with 2 parts",
  "parts": ["D'Angelo", "Martinez"],
  "normalized_name": "D'Angelo Martinez",
  "original_name": "  D'Angelo   Martinez  ",
  "normalizations_applied": [
    "whitespace_normalized",
    "curly_apostrophes_normalized"
  ],
  "first_name": "D'Angelo",
  "last_name": "Martinez",
  "usage_note": "Name is valid and ready for registration use. Note: extra spaces were removed and curly apostrophes were converted to straight apostrophes during processing."
}
```

## Integration

### **In Registration Agents**

Add to agent tools list:
```python
tools = ["person_name_validation", "other_tools"]
```

### **In Agent Instructions**

```
Use the person_name_validation tool to validate any full names provided by users before proceeding with registration. This ensures data quality and prevents common name formatting issues.
```

## Benefits

1. **Data Quality**: Ensures consistent name formatting across all registrations
2. **User Experience**: Provides clear feedback on name validation issues
3. **Code Cleanliness**: Keeps validation logic separate from agent prompts
4. **Reusability**: Shared between multiple registration agents
5. **Maintainability**: Centralized validation rules that can be updated in one place

## Future Enhancements

- Age validation tools
- Address validation tools
- Registration code validation tools
- Phone number validation tools
- Email validation tools 