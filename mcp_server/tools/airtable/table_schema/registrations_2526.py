# backend/tools/airtable/table_schema/registrations_2526.py
# Schema definition for the registrations_2526 table in Airtable

REGISTRATIONS_2526_SCHEMA = {
    "table_name": "registrations_2526",
    "table_id": "tbl1D7hdjVcyHbT8a",
    "description": "Contains registration details for all new players registered for Urmston Town Juniors Football Club for the 2025-26 season. Typically filled out by parents/guardians.",
    "season": "2025-26",
    "purpose": "Player registration and enrollment management",
    
    "fields": {
        # System/Computed Fields
        "record_id": {
            "field_id": "fldPAoJXYSolqPwa1",
            "type": "formula",
            "airtable_type": "number, string, array of numbers or strings",
            "description": "Unique record identifier computed by Airtable",
            "computed_value": "RECORD_ID()",
            "required": False,
            "editable": False,
            "examples": ["recFBay3RhaXhwqyb", "rec33FWRM8iUOSivY", "reccdXajTZSQfhMk1"]
        },
        
        "last_modified": {
            "field_id": "fldsYZGZRj4XeP73D",
            "type": "formula",
            "airtable_type": "number, string, array of numbers or strings",
            "description": "Timestamp when the record was last modified",
            "computed_value": "LAST_MODIFIED_TIME()",
            "required": False,
            "searchable": True,
            "editable": False,
            "examples": ["2025-05-26T07:19:19.000Z", "2025-05-26T07:19:27.000Z", "2025-05-26T09:25:28.000Z"]
        },
        
        "created": {
            "field_id": "fldOTeG1PqbEnvXTf",
            "type": "created_time",
            "airtable_type": "string",
            "description": "The time the record was created in UTC",
            "required": False,
            "searchable": True,
            "editable": False,
            "examples": ["2025-05-20T18:57:34.000Z", "2025-05-20T18:57:38.000Z", "2025-05-20T19:24:30.000Z"]
        },
        
        # Player Information
        "player_first_name": {
            "field_id": "fld3Sf8SL32Ap0129",
            "type": "text",
            "airtable_type": "string",
            "description": "Player's first name",
            "required": True,
            "searchable": True,
            "editable": True,
            "examples": ["Stefan", "Emma", "James"]
        },
        
        "player_last_name": {
            "field_id": "fldtlmDvpC2bCjHQ0",
            "type": "text", 
            "airtable_type": "string",
            "description": "Player's last name/surname",
            "required": True,
            "searchable": True,
            "editable": True,
            "examples": ["Hayton", "Smith", "Johnson"]
        },
        
        "player_full_name": {
            "field_id": "fldCJA9nt7D6N8Fo7",
            "type": "formula",
            "airtable_type": "number, string, array of numbers or strings", 
            "description": "Player's full name (computed from first + last name)",
            "computed_value": "{player_first_name} & \" \" & {player_last_name}",
            "required": False,
            "editable": False,
            "searchable": True,
            "examples": ["Stefan Hayton", "Emma Smith", "James Johnson"]
        },
        
        "age_group": {
            "field_id": "fldlWMyTAOzwj1ieCText",
            "type": "text",
            "airtable_type": "string",
            "description": "Age group/category the player belongs to based on UTJFC standards",
            "required": True,
            "searchable": True,
            "editable": True,
            "enums": ["u6", "u7", "u8", "u9", "u10", "u11", "u12", "u13", "u14", "u15", "u16", "u17", "u18"],
            "validation": "Must be one of the valid UTJFC age groups",
            "examples": ["u8", "u10", "u12", "u14", "u16"],
            "notes": "Age groups follow under-X format where X is the maximum age for that category"
        },
        
        "team": {
            "field_id": "fld5A9XRyY7taSNq6",
            "type": "text",
            "airtable_type": "string", 
            "description": "Team assignment for the player within their age group",
            "required": False,
            "searchable": True,
            "editable": True,
            "enums": ["Tigers", "Lions", "Eagles", "Wolves", "Panthers", "Leopards", "Hawks", "Bears"],
            "common_values": ["Tigers", "Lions", "Eagles", "Wolves", "Panthers", "Leopards", "Hawks", "Bears"],
            "examples": ["Tigers", "Lions", "Eagles", "Wolves"],
            "notes": "Team names are typically animals and may vary by age group"
        },
        
        "player_dob": {
            "field_id": "fldlsHncdd83eX81g",
            "type": "text",
            "airtable_type": "string",
            "description": "Player's date of birth in YYYY-MM-DD format",
            "required": True,
            "searchable": True,
            "editable": True,
            "preferred_format": "YYYY-MM-DD",
            "input_formats_accepted": ["DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD", "DD-MM-YYYY"],
            "format_notes": "Input accepts multiple formats but will be normalized to YYYY-MM-DD for database storage",
            "examples": ["2019-01-11", "2014-11-02", "2013-08-15"],
            "validation": "Must be a valid date, will be converted to YYYY-MM-DD format"
        },
        
        "player_gender": {
            "field_id": "fldRvcLwiLkbqbrA3",
            "type": "text",
            "airtable_type": "string",
            "description": "Player's gender identity",
            "required": False,
            "searchable": True,
            "editable": True,
            "enums": ["Male", "Female", "Not Disclosed", "Other"],
            "examples": ["Male", "Female", "Not Disclosed", "Other"]
        },
        
        # Medical Information
        "player_has_any_medical_issues": {
            "field_id": "fldl5r4xPoLX8Cw6J",
            "type": "text",
            "airtable_type": "string",
            "description": "Whether player has any medical conditions that need to be considered",
            "required": True,
            "searchable": True,
            "editable": True,
            "enums": ["Y", "N"],
            "validation": "Must be exactly 'Y' for Yes or 'N' for No - no other values accepted",
            "examples": ["Y", "N"],
            "notes": "Use 'Y' if player has medical conditions, 'N' if no medical conditions"
        },
        
        "description_of_player_medical_issues": {
            "field_id": "fldFv7BYetLPqhRhV",
            "type": "text",
            "airtable_type": "string",
            "description": "Detailed description of any medical conditions",
            "required": False,
            "searchable": True,
            "editable": True,
            "conditional": "Required if player_has_any_medical_issues = 'Y'",
            "examples": ["Asthma", "Diabetes", "Allergies to nuts"]
        },
        
        # Parent/Guardian Information
        "parent_relationship_to_player": {
            "field_id": "fldc80clw3tAcpuBu",
            "type": "text",
            "airtable_type": "string",
            "description": "Relationship of the registering person to the player",
            "required": True,
            "searchable": True,
            "editable": True,
            "enums": ["Father", "Mother", "Guardian", "Grandparent", "Other Relative", "Other Guardian"],
            "examples": ["Father", "Mother", "Guardian", "Grandparent"]
        },
        
        "parent_first_name": {
            "field_id": "fldDFSO3oxWlMJafc",
            "type": "text",
            "airtable_type": "string",
            "description": "First name of parent/guardian",
            "required": True,
            "searchable": True,
            "editable": True,
            "examples": ["Lee", "Sarah", "Michael"]
        },
        
        "parent_last_name": {
            "field_id": "fldHdCuH1BX6UUq4Z",
            "type": "text",
            "airtable_type": "string",
            "description": "Last name of parent/guardian",
            "required": True,
            "searchable": True,
            "editable": True,
            "examples": ["Hayton", "Smith", "Johnson"]
        },
        
        "parent_full_name": {
            "field_id": "fld2o47LWmF2qtaMw",
            "type": "formula",
            "airtable_type": "number, string, array of numbers or strings",
            "description": "Parent's full name (computed from first + last name)",
            "computed_value": "{parent_first_name} & \" \" & {parent_last_name}",
            "required": False,
            "editable": False,
            "examples": ["Lee Hayton", "Sarah Smith", "Michael Johnson"]
        },
        
        "registree_role": {
            "field_id": "fldpOmc8hnETjxPyj",
            "type": "text",
            "airtable_type": "string",
            "description": "Role of the person completing the registration",
            "required": True,
            "searchable": True,
            "editable": True,
            "enums": ["Parent", "Player", "Other"],
            "examples": ["Parent", "Player", "Other"]
        },
        
        # Registration Details
        "registration_code": {
            "field_id": "fldI1Tc5tcAiZ9gLZ",
            "type": "text",
            "airtable_type": "string",
            "description": "Unique registration code for this enrollment",
            "required": True,
            "searchable": True,
            "editable": True,
            "format": "Typically: number-team-age-season",
            "examples": ["100-tigers-10-2526", "200-lions-12-2526"]
        },
        
        # Player Address Information
        "player_full_address": {
            "field_id": "fldZqOftnp0XcFmYf",
            "type": "text",
            "airtable_type": "string",
            "description": "Complete address of the player",
            "required": False,
            "searchable": True,
            "editable": True,
            "examples": ["123 Main Street, Manchester, M1 1AA"]
        },
        
        "player_house_number": {
            "field_id": "fldwvIf74PdhKOCW2",
            "type": "text",
            "airtable_type": "string",
            "description": "House number of player's address",
            "required": False,
            "searchable": True,
            "editable": True,
            "examples": ["123", "45A", "Flat 2"]
        },
        
        "player_address_line_1": {
            "field_id": "fldPPrymnsi7NQQt0",
            "type": "text",
            "airtable_type": "string",
            "description": "First line of player's address (street name)",
            "required": False,
            "searchable": True,
            "editable": True,
            "examples": ["Main Street", "Oak Avenue", "Church Lane"]
        },
        
        "player_town": {
            "field_id": "fld25QcDmMJC5L1H7",
            "type": "text",
            "airtable_type": "string",
            "description": "Town where player lives",
            "required": False,
            "searchable": True,
            "editable": True,
            "examples": ["Urmston", "Stretford", "Sale"]
        },
        
        "player_city": {
            "field_id": "fldEo2ncq7QqtNvgi",
            "type": "text",
            "airtable_type": "string",
            "description": "City where player lives",
            "required": False,
            "searchable": True,
            "editable": True,
            "examples": ["Manchester", "Trafford", "Salford"]
        },
        
        "player_post_code": {
            "field_id": "fldKI8TVoCTxlWUMI",
            "type": "text",
            "airtable_type": "string",
            "description": "Postal code of player's address",
            "required": False,
            "searchable": True,
            "editable": True,
            "format": "UK postcode format",
            "examples": ["M41 5AB", "M33 2CD", "M15 6EF"]
        },
        
        # Parent Address Information
        "parent_full_address": {
            "field_id": "fldsufIBYmL99GYlt",
            "type": "text",
            "airtable_type": "string",
            "description": "Complete address of the parent/guardian",
            "required": False,
            "searchable": True,
            "editable": True,
            "examples": ["123 Main Street, Manchester, M1 1AA"]
        },
        
        "parent_house_number": {
            "field_id": "fldNi7WQZCZl4SiQb",
            "type": "text",
            "airtable_type": "string",
            "description": "House number of parent's address",
            "required": False,
            "searchable": True,
            "editable": True,
            "examples": ["123", "45A", "Flat 2"]
        },
        
        "parent_address_line_1": {
            "field_id": "fldwbECPeUzqrlfDk",
            "type": "text",
            "airtable_type": "string",
            "description": "First line of parent's address (street name)",
            "required": False,
            "searchable": True,
            "editable": True,
            "examples": ["Main Street", "Oak Avenue", "Church Lane"]
        },
        
        "parent_town": {
            "field_id": "fldGSbY2YQyM2nsPW",
            "type": "text",
            "airtable_type": "string",
            "description": "Town where parent lives",
            "required": False,
            "searchable": True,
            "editable": True,
            "examples": ["Urmston", "Stretford", "Sale"]
        },
        
        "parent_city": {
            "field_id": "fld882Irai2feWpnr",
            "type": "text",
            "airtable_type": "string",
            "description": "City where parent lives",
            "required": False,
            "searchable": True,
            "editable": True,
            "examples": ["Manchester", "Trafford", "Salford"]
        },
        
        "parent_post_code": {
            "field_id": "fldSdJqQOkWAYK6kZ",
            "type": "text",
            "airtable_type": "string",
            "description": "Postal code of parent's address",
            "required": False,
            "searchable": True,
            "editable": True,
            "format": "UK postcode format",
            "examples": ["M41 5AB", "M33 2CD", "M15 6EF"]
        }
    },
    
    # Logical groupings for easier understanding
    "field_groups": {
        "player_identity": ["player_first_name", "player_last_name", "player_full_name", "player_dob", "player_gender"],
        "player_football": ["age_group", "team", "registration_code"],
        "player_medical": ["player_has_any_medical_issues", "description_of_player_medical_issues"],
        "player_address": ["player_full_address", "player_house_number", "player_address_line_1", "player_town", "player_city", "player_post_code"],
        "parent_identity": ["parent_first_name", "parent_last_name", "parent_full_name", "parent_relationship_to_player", "registree_role"],
        "parent_address": ["parent_full_address", "parent_house_number", "parent_address_line_1", "parent_town", "parent_city", "parent_post_code"],
        "system_fields": ["record_id", "last_modified", "created"]
    },
    
    # Common search patterns
    "search_patterns": {
        "find_by_player_name": ["player_first_name", "player_last_name"],
        "find_by_parent_name": ["parent_first_name", "parent_last_name"],
        "find_by_registration_code": ["registration_code"],
        "find_by_age_group": ["age_group"],
        "find_by_team": ["team"]
    },
    
    # Business rules and relationships
    "business_rules": {
        "medical_conditional": "If player_has_any_medical_issues = 'Y', then description_of_player_medical_issues should be provided",
        "address_relationship": "Player and parent addresses may be the same or different",
        "registration_uniqueness": "Each registration_code should be unique per season",
        "age_group_validation": "Age group should correspond to player's date of birth"
    },
    
    # Indexes for performance (conceptual - Airtable handles this)
    "suggested_indexes": [
        "player_first_name + player_last_name",
        "registration_code",
        "age_group",
        "team"
    ],
    
    # Related tables (for future expansion)
    "relationships": {
        # Future: Could link to teams table, age_groups table, etc.
        "potential_links": {
            "teams_table": "team field could link to a teams table",
            "age_groups_table": "age_group field could link to age groups configuration",
            "medical_conditions_table": "medical issues could link to standardized conditions"
        }
    }
}

# Helper functions for agents to use this schema
def get_field_by_name(field_name: str) -> dict:
    """Get field definition by field name"""
    return REGISTRATIONS_2526_SCHEMA["fields"].get(field_name)

def get_field_by_id(field_id: str) -> dict:
    """Get field definition by field ID"""
    for field_name, field_def in REGISTRATIONS_2526_SCHEMA["fields"].items():
        if field_def.get("field_id") == field_id:
            return field_def
    return None

def get_searchable_fields() -> list:
    """Get list of fields that are marked as searchable"""
    searchable = []
    for field_name, field_def in REGISTRATIONS_2526_SCHEMA["fields"].items():
        if field_def.get("searchable", False):
            searchable.append(field_name)
    return searchable

def get_required_fields() -> list:
    """Get list of fields that are required"""
    required = []
    for field_name, field_def in REGISTRATIONS_2526_SCHEMA["fields"].items():
        if field_def.get("required", False):
            required.append(field_name)
    return required

def get_fields_by_group(group_name: str) -> list:
    """Get list of field names in a specific group"""
    return REGISTRATIONS_2526_SCHEMA["field_groups"].get(group_name, []) 