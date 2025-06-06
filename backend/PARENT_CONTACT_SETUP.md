# Parent Contact Details Setup

## Overview
Extended UTJFC registration system with comprehensive parent contact collection (routines 7-11) including relationship, phone, email, date of birth, and address validation.

## New Features Added

### **Routines 7-11: Parent Contact Collection**
- **Routine 7**: Relationship to child (Mother/Father/Guardian/Other enums)
- **Routine 8**: UK telephone validation (mobile 07..., Manchester landline 0161...)
- **Routine 9**: Email validation with lowercase formatting
- **Routine 10**: Parent date of birth with reasonable date checking
- **Routine 11**: Address validation using Google Places API

### **Validation Approach**
- **Embedded Validation** (Routines 7-10): Logic built into routine instructions for speed
- **Function Validation** (Routine 11): Google Places API for address verification

## Setup Requirements

### **1. Google Places API Key**
For address validation to work, you need a Google Places API key:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create/select a project
3. Enable "Places API" 
4. Create an API key
5. Add to your `.env` file:

```bash
GOOGLE_PLACES_API_KEY=your_api_key_here
```

**Note**: Without the API key, address validation will gracefully fall back to basic acceptance.

### **2. Updated Agent Tools**
Both registration agents now have access to:
```python
tools = [
    "person_name_validation",      # Routines 1-2
    "child_dob_validation",        # Routine 3  
    "medical_issues_validation",   # Routine 5
    "address_validation"           # Routine 11
]
```

## Validation Logic Details

### **Relationship Enum Normalization (Routine 7)**
Accepts variations and converts to exact values:
- `mum/mam/mom/mama` → `Mother`
- `dad/daddy/papa/father` → `Father`  
- `guardian/carer` → `Guardian`
- `gran/grandma/granny/grandfather/grandad/aunt/uncle/relative` → `Other`

### **UK Phone Number Validation (Routine 8)**
Validates and cleans phone numbers:
- **Mobile**: Must start with `07` and be exactly 11 digits
- **Manchester Landline**: Must start with `0161` and be exactly 11 digits
- **Cleaning**: Removes spaces, dashes, brackets automatically
- **Examples**: `07123456789`, `0161 234 5678`, `(07) 123-456-789`

### **Email Validation (Routine 9)**
Basic email validation with formatting:
- Must contain exactly one `@` symbol
- Must have at least one dot after the `@`
- Converts entire email to lowercase
- **Format**: `something@something.something`

### **Date of Birth Validation (Routine 10)**
Parent DOB validation:
- Accepts any date format, converts to DD-MM-YYYY
- Must not be in the future
- Must not be before 1900 (reasonable limits)
- **Examples**: `15/03/1985`, `March 15, 1985`, `1985-03-15`

### **Address Validation (Routine 11)**
Google Places API validation:
- Verifies address exists in Google Places database
- Ensures UK address (rejects non-UK locations)
- Returns formatted address and confidence level
- Provides structured address components

## Testing

### **Run Parent Contact Tests**
```bash
python test_parent_contact_routines.py
```

**Expected Results**: All tests should pass (current: ✅ All major tests passing)

### **Test Individual Address Validation**
```bash
python -m registration_agent.tools.registration_tools.address_validation
```

## Complete Registration Flow (1-11)

**Child Information (1-6):**
1. Parent name → validate → next
2. Child name → validate → next  
3. Child DOB → validate & format → next
4. Child gender → normalize → next
5. Medical issues → validate & structure → next
6. Previous team → capture → next

**Parent Contact (7-11):**
7. Relationship → normalize to enum → next
8. Phone → validate UK format → next
9. Email → validate & lowercase → next
10. DOB → validate & format → next
11. Address → Google Places validate → complete

## Error Handling

### **Graceful Degradation**
- Missing Google API key: Address validation disabled, basic acceptance
- API service down: Timeout handling with retry suggestion
- Invalid formats: Clear error messages with examples

### **User Experience**
- All validation errors provide specific guidance
- No technical jargon exposed to parents
- Silent validation approach (no mention of "checking" or "validating")

## Next Steps

Ready for routines 12+ covering:
- Emergency contact information
- Photo permissions  
- Payment setup
- Terms & conditions

The parent contact collection is complete and production-ready! 🎯 