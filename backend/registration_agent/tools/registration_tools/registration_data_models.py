from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import Optional, Literal
from datetime import datetime
import re


class RegistrationDataContract(BaseModel):
    """
    Pydantic model defining the exact data contract for writing registration data to the database.
    
    This model ensures:
    1. All required fields are mandatory
    2. Data formats are validated and normalized
    3. Clear distinction between required and optional fields
    4. Type safety and validation rules
    
    The AI agent will parse conversation history to populate this model.
    """
    
    # ============================================================================
    # PLAYER INFORMATION (ALL REQUIRED)
    # ============================================================================
    player_first_name: str = Field(
        ..., 
        min_length=1, 
        max_length=50,
        description="Player's first name - required, validated in routine 2"
    )
    
    player_last_name: str = Field(
        ..., 
        min_length=1, 
        max_length=50,
        description="Player's last name - required, validated in routine 2"
    )
    
    player_dob: str = Field(
        ..., 
        pattern=r'^\d{2}-\d{2}-\d{4}$',
        description="Player's date of birth in DD-MM-YYYY format - required, validated in routine 3"
    )
    
    player_gender: Literal["Male", "Female", "Not Disclosed"] = Field(
        ...,
        description="Player's gender - required, normalized in routine 4"
    )
    
    age_group: str = Field(
        ..., 
        pattern=r'^u\d{1,2}$',
        description="Age group in lowercase format u## (e.g., u10, u16) - injected from registration code"
    )
    
    team: str = Field(
        ..., 
        min_length=1, 
        max_length=20,
        description="Team name - injected from registration code"
    )
    
    # ============================================================================
    # MEDICAL INFORMATION (REQUIRED)
    # ============================================================================
    player_has_any_medical_issues: Literal["Y", "N"] = Field(
        ...,
        description="Whether player has medical issues - required, validated in routine 5"
    )
    
    description_of_player_medical_issues: Optional[str] = Field(
        None,
        max_length=500,
        description="Details of medical issues - required if player_has_any_medical_issues='Y'"
    )
    
    # ============================================================================
    # PARENT/GUARDIAN INFORMATION (ALL REQUIRED)
    # ============================================================================
    parent_first_name: str = Field(
        ..., 
        min_length=1, 
        max_length=50,
        description="Parent's first name - required, validated in routine 1"
    )
    
    parent_last_name: str = Field(
        ..., 
        min_length=1, 
        max_length=50,
        description="Parent's last name - required, validated in routine 1"
    )
    
    parent_relationship_to_player: Literal["Mother", "Father", "Guardian", "Other"] = Field(
        ...,
        description="Parent's relationship to player - required, normalized in routine 7"
    )
    
    parent_telephone: str = Field(
        ..., 
        min_length=1,
        max_length=20,
        description="Parent's phone number - UK mobile (07...) or Manchester landline (0161...) - required, validated in routine 8"
    )
    
    parent_email: EmailStr = Field(
        ...,
        description="Parent's email address - required, validated and lowercased in routine 9"
    )
    
    parent_dob: str = Field(
        ..., 
        pattern=r'^\d{2}-\d{2}-\d{4}$',
        description="Parent's date of birth in DD-MM-YYYY format - required, validated in routine 11"
    )
    
    # ============================================================================
    # COMMUNICATION PREFERENCES (REQUIRED)
    # ============================================================================
    communication_consent: Literal["Y", "N"] = Field(
        ...,
        description="Parent's consent for email/SMS communications - required, validated in routine 10"
    )
    
    registree_role: Literal["Parent", "Player", "Other"] = Field(
        default="Parent",
        description="Role of person completing registration - typically 'Parent'"
    )
    
    # ============================================================================
    # ADDRESS INFORMATION (REQUIRED)
    # ============================================================================
    parent_post_code: str = Field(
        ..., 
        pattern=r'^[A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2}$',
        description="Parent's postcode in UK format - required, validated in routine 12"
    )
    
    parent_house_number: str = Field(
        ..., 
        min_length=1, 
        max_length=20,
        description="Parent's house number/name - required, validated in routine 13"
    )
    
    parent_full_address: str = Field(
        ..., 
        min_length=10, 
        max_length=200,
        description="Parent's complete address - required, validated in routines 13-15"
    )
    
    parent_address_line_1: str = Field(
        ..., 
        min_length=1, 
        max_length=100,
        description="Parent's street address (house number + street name) - REQUIRED: Parse from parent_full_address by combining parent_house_number with street name"
    )
    
    parent_town: str = Field(
        ..., 
        min_length=1, 
        max_length=50,
        description="Parent's town/area - REQUIRED: Parse from parent_full_address (typically the part before the city)"
    )
    
    parent_city: str = Field(
        ..., 
        min_length=1, 
        max_length=50,
        description="Parent's city - REQUIRED: Parse from parent_full_address (typically 'Manchester', 'Trafford', or similar)"
    )
    
    # Child address (conditional - same as parent or different)
    player_post_code: Optional[str] = Field(
        None, 
        pattern=r'^[A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2}$',
        description="Player's postcode - required if lives at different address from parent, or copy from parent if same address"
    )
    
    player_house_number: Optional[str] = Field(
        None, 
        max_length=20,
        description="Player's house number - required if lives at different address from parent, or copy from parent if same address"
    )
    
    player_full_address: Optional[str] = Field(
        None, 
        max_length=200,
        description="Player's complete address - required if lives at different address from parent, or copy from parent if same address"
    )
    
    player_address_line_1: Optional[str] = Field(
        None, 
        max_length=100,
        description="Player's street address - REQUIRED: If same address as parent, copy parent_address_line_1. If different, parse from player_full_address"
    )
    
    player_town: Optional[str] = Field(
        None, 
        max_length=50,
        description="Player's town/area - REQUIRED: If same address as parent, copy parent_town. If different, parse from player_full_address"
    )
    
    player_city: Optional[str] = Field(
        None, 
        max_length=50,
        description="Player's city - REQUIRED: If same address as parent, copy parent_city. If different, parse from player_full_address"
    )
    
    # ============================================================================
    # PREVIOUS CLUB INFORMATION (CONDITIONAL)
    # ============================================================================
    played_elsewhere_last_season: Literal["Y", "N"] = Field(
        ...,
        description="Whether child played for another team last season - required, validated in routine 6"
    )
    
    previous_team_name: Optional[str] = Field(
        None, 
        max_length=100,
        description="Name of previous team - required if played_elsewhere_last_season='Y'"
    )
    
    # ============================================================================
    # U16+ PLAYER CONTACT DETAILS (CONDITIONAL)
    # ============================================================================
    player_telephone: Optional[str] = Field(
        None, 
        max_length=20,
        description="Player's mobile number - required for U16+, must be different from parent's"
    )
    
    player_email: Optional[EmailStr] = Field(
        None,
        description="Player's email address - required for U16+, must be different from parent's"
    )
    
    # ============================================================================
    # REGISTRATION META INFORMATION (ALL REQUIRED)
    # ============================================================================
    registration_type: Literal["100", "200"] = Field(
        ...,
        description="Registration type - 100=re-registration, 200=new registration - injected from code"
    )
    
    season: Literal["2526"] = Field(
        ...,
        description="Season code - currently 2526 for 2025-26 season - injected from code"
    )
    
    # ============================================================================
    # PAYMENT INFORMATION (ALL REQUIRED)
    # ============================================================================
    billing_request_id: str = Field(
        ..., 
        min_length=10, 
        max_length=50,
        description="GoCardless billing request ID - returned from create_payment_token function"
    )
    
    preferred_payment_day: int = Field(
        ..., 
        ge=-1, 
        le=31,
        description="Day of month for monthly payments (1-31 or -1 for last day) - validated in routine 29"
    )
    
    # ============================================================================
    # PAYMENT AMOUNTS (CONVERTED FROM PENCE TO POUNDS)
    # ============================================================================
    signing_on_fee_amount: Optional[float] = Field(
        None,
        ge=0,
        description="One-off signing fee amount in pounds (converted from pence by create_payment_token function)"
    )
    
    monthly_subscription_amount: Optional[float] = Field(
        None,
        ge=0,
        description="Monthly subscription amount in pounds (converted from pence by create_payment_token function)"
    )
    
    # ============================================================================
    # PAYMENT STATUS FIELDS (DEFAULTS)
    # ============================================================================
    signing_on_fee_paid: Literal["Y", "N"] = Field(
        default="N",
        description="Whether £45 signing fee has been paid - defaults to 'N'"
    )
    
    mandate_authorised: Literal["Y", "N"] = Field(
        default="N",
        description="Whether Direct Debit mandate has been authorised - defaults to 'N'"
    )
    
    subscription_activated: Literal["Y", "N"] = Field(
        default="N",
        description="Whether monthly subscription is active - defaults to 'N'"
    )
    
    registration_status: Literal["pending_payment", "active", "suspended", "incomplete"] = Field(
        default="pending_payment",
        description="Current registration status - defaults to 'pending_payment'"
    )
    
    payment_follow_up_count: int = Field(
        default=0,
        ge=0,
        description="Number of follow-up reminders sent - defaults to 0"
    )
    
    # ============================================================================
    # KIT INFORMATION (COLLECTED IN ROUTINES 32-33)
    # ============================================================================
    new_kit_required: Optional[Literal["Y", "N"]] = Field(
        None,
        description="Whether player requires a new kit this season - collected after payment setup"
    )
    
    kit_type_required: Optional[Literal["Goalkeeper", "Outfield"]] = Field(
        None,
        description="Type of kit required (Goalkeeper or Outfield) - collected after payment setup"
    )
    
    kit_size: Optional[Literal["5/6", "7/8", "9/10", "11/12", "13/14", "S", "M", "L", "XL", "2XL", "3XL"]] = Field(
        None,
        description="Kit size selected by player/parent - validated in routine 32"
    )
    
    shirt_number: Optional[int] = Field(
        None,
        ge=1,
        le=20,
        description="Shirt number chosen by player (1-20) - validated for availability in routine 33"
    )
    
    # ============================================================================
    # COMPUTED/DERIVED FIELDS
    # ============================================================================
    registration_code: str = Field(
        ...,
        description="Clean registration code for database storage - derived from original_registration_code"
    )

    @field_validator('description_of_player_medical_issues')
    @classmethod
    def validate_medical_description(cls, v, info):
        """Ensure medical description is provided if player has medical issues."""
        values = info.data if hasattr(info, 'data') else {}
        if values.get('player_has_any_medical_issues') == 'Y' and not v:
            raise ValueError('Medical issues description is required when player has medical issues')
        return v
    
    @field_validator('previous_team_name')
    @classmethod
    def validate_previous_team(cls, v, info):
        """Ensure previous team name is provided if played elsewhere."""
        values = info.data if hasattr(info, 'data') else {}
        if values.get('played_elsewhere_last_season') == 'Y' and not v:
            raise ValueError('Previous team name is required when played elsewhere last season')
        return v
    
    @field_validator('parent_telephone', 'player_telephone')
    @classmethod
    def validate_phone_format(cls, v):
        """Clean and validate phone number format."""
        if not v:
            return v
        # Remove any spaces, dashes, brackets
        cleaned = re.sub(r'[\s\-\(\)]', '', v)
        if not re.match(r'^(07\d{9}|0161\d{7})$', cleaned):
            raise ValueError('Phone number must be UK mobile (07...) or Manchester landline (0161...)')
        return cleaned
    
    @field_validator('parent_post_code', 'player_post_code')
    @classmethod
    def validate_postcode_format(cls, v):
        """Clean and validate UK postcode format."""
        if v:
            # Remove spaces and convert to uppercase
            cleaned = re.sub(r'\s+', '', v.upper())
            # Add space before last 3 characters if needed
            if len(cleaned) > 3:
                cleaned = cleaned[:-3] + ' ' + cleaned[-3:]
            return cleaned
        return v
    
    @field_validator('parent_email', 'player_email')
    @classmethod
    def lowercase_email(cls, v):
        """Convert email to lowercase."""
        return v.lower() if v else v

    class Config:
        """Pydantic configuration."""
        # Validate assignment to catch issues during field updates
        validate_assignment = True
        # Use enum values for validation
        use_enum_values = True
        # Allow extra fields for future expansion
        extra = "forbid"  # Strict - no extra fields allowed


class RegistrationDataInput(BaseModel):
    """
    Simplified input model for the AI agent to populate from conversation history.
    
    This allows the AI agent to provide data in a more flexible format,
    which then gets validated and transformed into the strict RegistrationDataContract.
    """
    
    # Basic info that AI agent must extract from conversation
    conversation_history: str = Field(
        ...,
        description="Complete conversation history from routines 1-29"
    )
    
    # Registration code components (injected by system)
    registration_code_info: dict = Field(
        ...,
        description="Parsed registration code information from routing validation"
    )
    
    # Payment token from create_payment_token function
    billing_request_id: str = Field(
        ...,
        description="Billing request ID returned from GoCardless"
    )
    
    # Session metadata
    session_id: str = Field(
        ...,
        description="Chat session ID for tracking"
    )
    
    class Config:
        extra = "allow"  # Allow extra fields for flexibility 