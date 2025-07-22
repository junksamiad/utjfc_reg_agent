# Validation Patterns Low-Level Design (LLD)
## UTJFC Data Validation & Business Logic Rules

### Table of Contents
1. [UK Phone Number Validation](#uk-phone-number-validation)
2. [Address Validation System](#address-validation-system)
3. [Parent Contact Validation](#parent-contact-validation)
4. [Date & Age Validation](#date--age-validation)
5. [Registration Code Validation](#registration-code-validation)
6. [File Upload Validation](#file-upload-validation)

---

## UK Phone Number Validation

### Implementation (`send_sms_payment_link_tool.py:30-64`)

#### Phone Number Formatting
```python
def format_uk_phone_for_twilio(phone: str) -> str:
    """
    Format UK phone number for Twilio SMS delivery.
    Handles multiple input formats and normalizes to +44 format.
    """
    phone = phone.strip().replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    
    # Handle different UK number formats
    if phone.startswith('07'):
        # UK mobile: 07123456789 → +447123456789
        return '+44' + phone[1:]
    elif phone.startswith('+44'):
        # Already in international format
        return phone
    elif phone.startswith('447'):
        # Missing + prefix: 447123456789 → +447123456789
        return '+' + phone
    elif phone.startswith('0044'):
        # Long international: 0044... → +44...
        return '+' + phone[2:]
    elif phone.startswith('44'):
        # International without +: 44... → +44...
        return '+' + phone
    else:
        # Assume UK mobile without prefix: 7123456789 → +447123456789
        return '+447' + phone
```

#### Mobile Number Validation
```python
def validate_uk_mobile(phone: str) -> bool:
    """
    Validate that the phone number is a UK mobile number.
    Only mobile numbers can receive SMS.
    """
    formatted = format_uk_phone_for_twilio(phone)
    # UK mobile numbers start with +447 and are 13 digits total
    uk_mobile_pattern = r'^\+447[0-9]{9}$'
    return bool(re.match(uk_mobile_pattern, formatted))
```

### Validation Rules

#### Supported Formats
- **07xxxxxxxxx**: Standard UK mobile format
- **+447xxxxxxxxx**: International format
- **447xxxxxxxxx**: International without +
- **0044xxxxxxxxx**: Long international format
- **7xxxxxxxxx**: Mobile without country code

#### Business Rules
- **Mobile Only**: Only mobile numbers accepted (landlines cannot receive SMS)
- **UK Only**: Only UK mobile numbers supported (+447 prefix)
- **Length Validation**: Exactly 13 digits in international format
- **Automatic Formatting**: All formats normalized to +447xxxxxxxxx

#### Manchester Landline Handling
While landlines (0161 prefix) are recognized in formatting, they are rejected for SMS delivery:
```python
# Landlines formatted but not used for SMS
if phone.startswith('0161'):
    formatted = '+44' + phone[1:]  # Format correctly
    # But validation will fail as it's not mobile
```

---

## Address Validation System

### Google Places API Integration (`address_lookup.py`)

#### Core Lookup Function
```python
def lookup_address_google_places(postcode: str, house_number: str, api_key: str = None) -> Dict[str, Any]:
    """
    Look up UK address using Google Places API with postcode and house number.
    Provides confidence assessment and fallback handling.
    """
```

#### API Configuration
```python
GOOGLE_PLACES_BASE_URL = "https://maps.googleapis.com/maps/api/place"
GOOGLE_PLACES_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY')

# Text search for UK addresses
search_url = f"{GOOGLE_PLACES_BASE_URL}/textsearch/json"
search_params = {
    'query': f"{house_number} {postcode} UK",
    'key': api_key,
    'region': 'uk',
    'type': 'street_address'
}
```

#### Confidence Assessment (`address_lookup.py:181-200`)
```python
def assess_confidence(result: dict, house_number: str, postcode: str) -> str:
    """
    Assess confidence level of address match.
    Returns: 'High', 'Medium', or 'Low'
    """
    formatted_address = result.get('formatted_address', '').upper()
    house_number_upper = house_number.upper()
    postcode_upper = postcode.upper().replace(' ', '')
    
    # Check if both house number and postcode are in the result
    has_house_number = house_number_upper in formatted_address
    has_postcode = postcode_upper in formatted_address.replace(' ', '')
    
    if has_house_number and has_postcode:
        return 'High'
    elif has_postcode:
        return 'Medium'
    else:
        return 'Low'
```

### Address Validation Response Format
```python
{
    "success": True,
    "confidence": "High|Medium|Low",
    "formatted_address": "123 Main Street, Manchester, M1 1AA, UK",
    "components": {
        "street_number": "123",
        "route": "Main Street", 
        "locality": "Manchester",
        "postal_code": "M1 1AA",
        "country": "United Kingdom"
    },
    "location": {
        "lat": 53.4808,
        "lng": -2.2426
    }
}
```

### Fallback Behavior (`address_lookup.py:115-130`)

#### API Key Missing
```python
if not api_key:
    print("⚠️ Google Places API key not configured")
    return {
        "success": False,
        "error": "Address validation temporarily unavailable",
        "confidence": "Low",
        "user_message": "Please enter your full address manually"
    }
```

#### API Error Handling
```python
except requests.RequestException as e:
    print(f"❌ Google Places API error: {e}")
    return {
        "success": False,
        "error": f"Address lookup failed: {str(e)}",
        "confidence": "Low", 
        "user_message": "Please verify your postcode and house number"
    }
```

#### Rate Limit Handling
```python
if response.status_code == 429:
    return {
        "success": False,
        "error": "Rate limit exceeded",
        "confidence": "Low",
        "user_message": "Address validation busy, please try again"
    }
```

---

## Parent Contact Validation

### Relationship Validation

#### Enum Normalization Patterns
While specific enum patterns were mentioned in old docs, the current implementation uses flexible text validation rather than strict enum patterns. The system accepts various relationship descriptions:

```python
# Flexible relationship handling
relationship = input_data.get('relationship_to_player', '').strip()
# System accepts: "Mother", "Father", "Guardian", "Grandparent", etc.
# No strict enum conversion implemented
```

### Email Validation

#### Format Validation
```python
import re

def validate_email(email: str) -> bool:
    """Basic email format validation"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email.strip().lower()))
```

#### Business Rules
- **Required Format**: Standard email format with @ and domain
- **Case Insensitive**: Automatically converted to lowercase
- **Whitespace Handling**: Leading/trailing whitespace removed
- **Domain Validation**: Must have valid TLD (2+ characters)

### Contact Method Validation

#### Multiple Contact Validation
```python
def validate_parent_contact(phone: str, email: str) -> Dict[str, Any]:
    """
    Validate parent contact information.
    Requires at least one valid contact method.
    """
    phone_valid = validate_uk_mobile(phone) if phone else False
    email_valid = validate_email(email) if email else False
    
    if not phone_valid and not email_valid:
        return {
            "success": False,
            "error": "At least one valid contact method required"
        }
    
    return {
        "success": True,
        "phone_valid": phone_valid,
        "email_valid": email_valid
    }
```

---

## Date & Age Validation

### Date of Birth Validation

#### Date Range Validation
```python
from datetime import datetime, date

def validate_date_of_birth(dob_string: str) -> Dict[str, Any]:
    """
    Validate date of birth with reasonable limits.
    """
    try:
        # Parse date (supports multiple formats)
        dob = datetime.strptime(dob_string.strip(), '%d/%m/%Y').date()
        
        # Validation rules
        today = date.today()
        min_date = date(1900, 1, 1)  # Not before 1900
        
        if dob > today:
            return {
                "success": False,
                "error": "Date of birth cannot be in the future"
            }
        
        if dob < min_date:
            return {
                "success": False, 
                "error": "Please enter a valid date of birth"
            }
        
        # Calculate age
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        
        return {
            "success": True,
            "date_of_birth": dob,
            "age": age,
            "formatted_date": dob.strftime('%d/%m/%Y')
        }
        
    except ValueError:
        return {
            "success": False,
            "error": "Please enter date in DD/MM/YYYY format"
        }
```

#### Age-Based Business Rules
```python
def get_age_group_from_date(dob: date, season_start: date = None) -> str:
    """
    Calculate age group based on date of birth and season start.
    Uses 31st August cutoff for age group determination.
    """
    if not season_start:
        # Use 31st August of current season year
        current_year = date.today().year
        season_start = date(current_year, 8, 31)
    
    # Calculate age on 31st August
    age_on_cutoff = season_start.year - dob.year - ((season_start.month, season_start.day) < (dob.month, dob.day))
    
    # Determine age group
    if age_on_cutoff <= 6:
        return "U7"
    elif age_on_cutoff <= 7:
        return "U8"
    elif age_on_cutoff <= 8:
        return "U9"
    # ... continue pattern up to U18
    else:
        return "Senior"
```

---

## Registration Code Validation

### Code Format Validation (`routing_validation.py`)

#### Registration Code Pattern
```python
import re

def validate_registration_code(code: str) -> Dict[str, Any]:
    """
    Validate UTJFC registration code format and extract components.
    Format: {series}-{team}-{age_group}-{season}
    Example: 200-Lions-U10-2526
    """
    # Clean the code
    code = code.strip().upper()
    
    # Registration code pattern
    pattern = r'^(\d{3})-([A-Z]+)-([UO]\d{1,2})-(\d{4})$'
    match = re.match(pattern, code)
    
    if not match:
        return {
            "success": False,
            "error": "Invalid registration code format. Expected: XXX-TEAM-UXX-YYYY"
        }
    
    series, team, age_group, season = match.groups()
    
    return {
        "success": True,
        "series": series,
        "team": team, 
        "age_group": age_group,
        "season": season,
        "agent_type": "re_registration" if series.startswith('1') else "new_registration"
    }
```

#### Database Validation
```python
def validate_code_against_database(code_components: dict) -> Dict[str, Any]:
    """
    Validate registration code against Airtable database.
    Ensures team and age group combinations exist.
    Includes special handling for Mens team exception.
    """
    team = code_components['team']
    age_group = code_components['age_group']
    
    # Handle special case for Mens team
    if team.capitalize() == "Mens":
        age_group = "Open Age"  # Override age group for Mens team
    else:
        age_group = age_group.lower() + 's'  # u10 -> u10s
    
    # Query Airtable for valid team/age group combinations
    formula = f"AND({{short_team_name}} = '{team.capitalize()}', {{age_group}} = '{age_group}', {{current_season}} = '2526')"
    
    try:
        records = table.all(formula=formula)
        
        if not records:
            return {
                "success": False,
                "error": f"No team found for {team} {age_group}"
            }
        
        return {
            "success": True,
            "team_record": records[0],
            "valid_combination": True
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Database validation failed: {str(e)}"
        }
```

#### Special Team Handling
**Mens Team Exception**: The Mens team has unique validation rules:
- **Team Name**: "Mens" in database (`short_team_name` = "Mens")
- **Age Group Override**: Any age group in the code becomes "Open Age" in database
- **Registration Code Format**: `200-mens-open-2526` (age group part can be anything)
- **Database Query**: Always searches for `age_group = "Open Age"` regardless of code

---

## File Upload Validation

### File Type Validation (`server.py:1300-1318`)

#### Allowed File Types
```python
def validate_upload_file(file: UploadFile) -> Dict[str, Any]:
    """
    Validate uploaded file type and size for photo uploads.
    """
    # Allowed content types
    valid_types = [
        'image/jpeg',
        'image/png', 
        'image/jpg',
        'image/heic',
        'image/webp'
    ]
    
    if file.content_type not in valid_types:
        return {
            "success": False,
            "error": f"Invalid file type. Supported: {', '.join(valid_types)}"
        }
    
    # File size validation (10MB limit)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    if hasattr(file, 'size') and file.size > MAX_FILE_SIZE:
        return {
            "success": False,
            "error": "File too large. Maximum size: 10MB"
        }
    
    return {
        "success": True,
        "content_type": file.content_type,
        "filename": file.filename
    }
```

### File Content Validation

#### HEIC Format Handling (`upload_photo_to_s3_tool.py:75-114`)
```python
def validate_heic_file(file_path: str) -> Dict[str, Any]:
    """
    Validate HEIC file and prepare for conversion.
    """
    try:
        # Check if HEIC support is available
        if not HEIC_SUPPORT:
            return {
                "success": False,
                "error": "HEIC format not supported on this server"
            }
        
        # Attempt to open HEIC file
        with Image.open(file_path) as img:
            # Validate image properties
            if img.size[0] < 100 or img.size[1] < 100:
                return {
                    "success": False,
                    "error": "Image too small. Minimum 100x100 pixels"
                }
            
            return {
                "success": True,
                "mode": img.mode,
                "size": img.size,
                "requires_conversion": True
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Invalid HEIC file: {str(e)}"
        }
```

### Photo Quality Validation

#### Passport-Style Photo Guidelines
```python
def validate_photo_quality(file_path: str) -> Dict[str, Any]:
    """
    Basic photo quality validation for passport-style photos.
    """
    try:
        with Image.open(file_path) as img:
            width, height = img.size
            
            # Minimum resolution check
            if width < 400 or height < 400:
                return {
                    "success": False,
                    "error": "Photo resolution too low. Minimum 400x400 pixels"
                }
            
            # Aspect ratio check (should be roughly square/portrait)
            aspect_ratio = width / height
            if aspect_ratio > 1.5 or aspect_ratio < 0.67:
                return {
                    "success": False,
                    "error": "Photo should be portrait or square format"
                }
            
            return {
                "success": True,
                "resolution": f"{width}x{height}",
                "aspect_ratio": aspect_ratio
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Photo validation failed: {str(e)}"
        }
```

---

## Validation Error Handling

### Centralized Error Response Format

#### Standard Validation Response
```python
class ValidationResponse:
    """Standard format for all validation responses"""
    
    def __init__(self, success: bool, error: str = None, data: dict = None):
        self.success = success
        self.error = error
        self.data = data or {}
    
    def to_dict(self) -> dict:
        response = {"success": self.success}
        if self.error:
            response["error"] = self.error
        if self.data:
            response.update(self.data)
        return response
```

#### User-Friendly Error Messages
```python
def format_user_error(validation_type: str, error: str) -> str:
    """
    Convert technical validation errors to user-friendly messages.
    """
    error_mappings = {
        "phone_invalid": "Please enter a valid UK mobile number (e.g., 07123456789)",
        "email_invalid": "Please enter a valid email address",
        "date_future": "Date of birth cannot be in the future",
        "file_too_large": "Photo file is too large. Please use a smaller image",
        "address_not_found": "Address not found. Please check your postcode and house number"
    }
    
    return error_mappings.get(error, f"Validation error: {error}")
```

---

## Conclusion

The UTJFC validation system implements comprehensive business rules and data validation patterns that ensure data quality and consistency across the registration process. The validation patterns are designed to be user-friendly while maintaining strict data integrity requirements.

Key features include:
- **Flexible Input Handling**: Multiple format support with automatic normalization
- **Business Rule Enforcement**: Age groups, team combinations, contact requirements
- **External Service Integration**: Google Places API with graceful fallback
- **File Upload Security**: Content type validation and size limits
- **User Experience**: Clear error messages and helpful guidance

The validation system supports both the registration workflow and general data quality requirements of the UTJFC system.