# backend/tools/airtable/airtable_setup.py
# Shared Airtable configuration, client setup, and helper functions

from pyairtable import Api
import os
from dotenv import load_dotenv

load_dotenv()

# Airtable configuration
AIRTABLE_BASE_ID = "appBLxf3qmGIBc6ue"
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')

# Table configurations for different seasons
TABLES_CONFIG = {
    "2526": {
        "table_name": "registrations_2526",
        "table_id": "tbl1D7hdjVcyHbT8a",
        "season": "2025-26"
    },
    "2425": {
        "table_name": "registrations_2425", 
        "table_id": "tbl_placeholder_2425",  # You'll need to provide this
        "season": "2024-25"
    }
}

def get_airtable_client():
    """Initialize and return Airtable API client"""
    if not AIRTABLE_API_KEY:
        raise ValueError("AIRTABLE_API_KEY environment variable is required")
    return Api(AIRTABLE_API_KEY)

def get_table(season: str):
    """Get the specific table instance for a given season"""
    if season not in TABLES_CONFIG:
        raise ValueError(f"Season {season} not configured. Available seasons: {list(TABLES_CONFIG.keys())}")
    
    client = get_airtable_client()
    table_config = TABLES_CONFIG[season]
    return client.table(AIRTABLE_BASE_ID, table_config["table_id"])

def get_table_config(season: str):
    """Get table configuration for a given season"""
    if season not in TABLES_CONFIG:
        raise ValueError(f"Season {season} not configured. Available seasons: {list(TABLES_CONFIG.keys())}")
    return TABLES_CONFIG[season]

def format_airtable_error(error):
    """Standardize error messages from Airtable API"""
    return {
        "status": "error",
        "message": f"Airtable API error: {str(error)}",
        "data": None
    }

def format_success_response(data, message="Operation successful"):
    """Standardize success responses"""
    return {
        "status": "success", 
        "message": message,
        "data": data
    } 