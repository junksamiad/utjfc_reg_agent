#!/usr/bin/env python3
import sys
import os
import json

# Add the parent directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from registration_data_models import RegistrationDataContract
from pydantic_to_openai_schema import pydantic_to_openai_schema

def test_ai_schema():
    """Test what the AI will see in the OpenAI function schema."""
    
    schema = pydantic_to_openai_schema(
        pydantic_model=RegistrationDataContract,
        function_name="update_reg_details_to_db",
        function_description="""
        Save complete registration data to the registrations_2526 database.
        
        Use your AI intelligence to extract each piece of information from the conversation 
        history and provide it in the exact format specified for each field below.
        """
    )
    
    print("🎯 What the AI will see:")
    print("=" * 60)
    print(f"Function name: {schema['function']['name']}")
    print(f"Total properties: {len(schema['function']['parameters']['properties'])}")
    print(f"Required fields: {len(schema['function']['parameters']['required'])}")
    print()
    
    print("📋 Sample of what AI sees for each field:")
    print("=" * 60)
    
    # Show a few example properties
    properties = schema['function']['parameters']['properties']
    
    for i, (field_name, field_def) in enumerate(properties.items()):
        if i < 8:  # Show first 8 fields as examples
            print(f"{field_name}:")
            print(f"  Type: {field_def.get('type', 'unknown')}")
            print(f"  Description: {field_def.get('description', 'No description')}")
            if 'enum' in field_def:
                print(f"  Allowed values: {field_def['enum']}")
            if 'pattern' in field_def:
                print(f"  Format pattern: {field_def['pattern']}")
            print()
    
    print("..." * 20)
    print(f"Plus {len(properties) - 8} more fields with detailed descriptions")
    print()
    
    print("✅ Required fields (AI must provide these):")
    print("=" * 60)
    required = schema['function']['parameters']['required']
    for field in required[:10]:  # Show first 10 required fields
        print(f"  - {field}")
    if len(required) > 10:
        print(f"  ... and {len(required) - 10} more required fields")
    
    print()
    print("🎉 This gives you the best of both worlds:")
    print("   ✅ AI intelligence for data extraction")
    print("   ✅ Detailed field-level descriptions") 
    print("   ✅ Pydantic validation for data integrity")
    print("   ✅ Just like the old OpenAI function calling!")


if __name__ == "__main__":
    test_ai_schema() 