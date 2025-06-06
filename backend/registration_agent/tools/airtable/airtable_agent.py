# backend/tools/airtable/airtable_agent.py
# Airtable Helper Agent - handles natural language CRUD requests for Airtable operations

from openai import OpenAI
from dotenv import load_dotenv
import json
import ast
from .airtable_setup import get_table, get_table_config, format_airtable_error, format_success_response, AIRTABLE_BASE_ID, AIRTABLE_API_KEY
from .table_schema.registrations_2526 import REGISTRATIONS_2526_SCHEMA

load_dotenv()
client = OpenAI()

class AirtableAgent:
    def __init__(self):
        self.model = "gpt-4.1"
        self.instructions = """You are an Airtable data validator and normalizer. Your job is to:

1. Receive operation requests with data from the main agent
2. Validate and normalize the data according to the table schema
3. Ensure all data conforms to schema standards before database operations
4. Return a clean, validated operation plan

Your role is NOT to generate data, but to clean and validate data provided to you.

Data normalization examples:
- "u10s" → "U10" (age group formatting)
- "tigers" → "Tigers" (team name capitalization)
- "yes" → "Y" (medical issues boolean)
- "no" → "N" (medical issues boolean)
- "under 12" → "U12" (age group standardization)
- Names: Proper case formatting and space normalization:
  - "john smith" → "John Smith"
  - "MARY  JONES" → "Mary Jones" (remove extra spaces)
  - "  bob  brown  " → "Bob Brown" (trim and normalize spaces)

For each field, check the schema for:
- valid_values: Exact values that must be used
- common_values: Preferred values to normalize to
- examples: Format patterns to follow
- validation: Rules that must be enforced

Your output should be a validated operation plan with clean data."""

        self.tools = [
            {
                "type": "code_interpreter",
                "container": {"type": "auto"}
            }
        ]

    def process_request(self, season: str, natural_language_query: str) -> dict:
        """
        Process a request and validate/normalize any data according to schema
        """
        try:
            # Get table configuration and schema
            table_config = get_table_config(season)
            
            # For now, we'll focus on the 2526 schema since that's what we have
            if season == "2526":
                schema = REGISTRATIONS_2526_SCHEMA
            else:
                # Placeholder for other seasons
                schema = {"message": f"Schema for season {season} not yet implemented"}
                return format_airtable_error(f"Schema for season {season} not yet implemented")

            # Step 1: Use code interpreter to parse the request and validate data
            operation_plan = self._generate_validated_operation_plan(table_config, schema, natural_language_query)
            
            if not operation_plan:
                return format_airtable_error("Failed to generate validated operation plan")
            
            # Step 2: Execute the operation using pyairtable SDK
            result = self._execute_operation(season, operation_plan)
            
            return format_success_response(
                data={
                    "query": natural_language_query,
                    "season": season,
                    "table": table_config['table_name'],
                    "operation_plan": operation_plan,
                    "result": result
                },
                message="Airtable operation completed successfully"
            )

        except Exception as e:
            return format_airtable_error(e)

    def _generate_validated_operation_plan(self, table_config, schema, query):
        """Use code interpreter to parse request and validate data according to schema"""
        try:
            # Prepare the system instructions for data validation and operation planning
            system_instructions = f"""
{self.instructions}

CURRENT CONTEXT:
- Season: {table_config['season']}
- Table: {table_config['table_name']}
- Table ID: {table_config['table_id']}

TABLE SCHEMA:
{json.dumps(schema, indent=2)}

TASK: Parse this request and create a validated operation plan: "{query}"

IMPORTANT: You must write and execute Python code that:
1. Analyzes the request to determine the operation type (CREATE/READ/UPDATE/DELETE)
2. Extracts any data provided in the request
3. Validates and normalizes the data according to the schema
4. Creates a clean operation plan

Data Validation Rules:
- For age_group: Convert variations like "u10s", "under 10", "U-10" to standard "u10" format (lowercase u)
- For team: Capitalize team names to match common_values (tigers → Tigers)
- For player_has_any_medical_issues: Convert "yes/no", "true/false" to "Y/N"
- For names: Proper case formatting AND space normalization (remove extra spaces, trim whitespace)
- For dates: Normalize to YYYY-MM-DD format
- For fields with enums: Intelligently map user input to the closest matching enum value using semantic understanding
- Check enums arrays in schema for controlled vocabulary fields

Example for CREATE with data validation:
```python
# Parse the request
request = "{query}"

# Extract operation and data (example)
operation_plan = {{
    "operation_type": "create",
    "method": "table.create",
    "params": {{
        "fields": {{
            "player_first_name": "Seb",  # Properly capitalized
            "player_last_name": "Charlton",  # Properly capitalized  
            "age_group": "u10",  # Normalized from "u10s" (lowercase u)
            "team": "Tigers",  # Normalized from "tigers"
            "player_has_any_medical_issues": "N"  # Default if not specified
        }}
    }},
    "explanation": "Create registration for Seb Charlton with validated data"
}}

print("OPERATION_PLAN:", operation_plan)
```

Example for READ operations:
```python
# For search operations
operation_plan = {{
    "operation_type": "read",
    "method": "table.all",
    "params": {{
        "formula": "{{player_has_any_medical_issues}} = 'Y'"  # Use schema-compliant values
    }},
    "explanation": "Find players with medical issues using validated schema values"
}}

print("OPERATION_PLAN:", operation_plan)
```

CRITICAL: 
1. Always validate data against schema before creating operation plan
2. Use exact field names from schema
3. Normalize data to match schema standards
4. Print the operation plan with "OPERATION_PLAN:" prefix

Generate and execute the Python code now for: "{query}"
"""

            # Use the Responses API with code interpreter
            response = client.responses.create(
                model=self.model,
                instructions=system_instructions,
                input=f"Parse and validate data for: {query}",
                tools=self.tools
            )

            # Extract the operation plan from the response
            operation_plan = self._extract_operation_plan(response)
            return operation_plan

        except Exception as e:
            print(f"Error generating validated operation plan: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _extract_operation_plan(self, response):
        """Extract the operation plan from the code interpreter response"""
        try:
            if hasattr(response, 'output') and response.output:
                for output_item in response.output:
                    if hasattr(output_item, 'type'):
                        # Check both code_interpreter_call and message types
                        if output_item.type == "code_interpreter_call":
                            # Look for code output containing OPERATION_PLAN
                            if hasattr(output_item, 'output') and output_item.output:
                                output_text = str(output_item.output)
                                if "OPERATION_PLAN:" in output_text:
                                    # Extract the operation plan
                                    lines = output_text.split('\n')
                                    for line in lines:
                                        if "OPERATION_PLAN:" in line:
                                            # Extract the dictionary part
                                            plan_str = line.split("OPERATION_PLAN:", 1)[1].strip()
                                            try:
                                                # Safely evaluate the dictionary
                                                operation_plan = ast.literal_eval(plan_str)
                                                return operation_plan
                                            except:
                                                continue
                        elif output_item.type == "message":
                            # Look for operation plan in message content
                            if hasattr(output_item, 'content') and output_item.content:
                                for content_item in output_item.content:
                                    if hasattr(content_item, 'text'):
                                        text = content_item.text
                                        print(f"DEBUG: Full text from code interpreter:\n{text}")
                                        
                                        # Try comprehensive multi-line dictionary extraction
                                        operation_plan = self._extract_multiline_dict(text)
                                        if operation_plan:
                                            return operation_plan
            return None
        except Exception as e:
            print(f"Error extracting operation plan: {e}")
            return None

    def _extract_multiline_dict(self, text):
        """Extract operation plan dictionary from multi-line text using multiple strategies"""
        import re
        import json
        
        # Strategy 1: Look for OPERATION_PLAN: followed by a dictionary (single or multi-line)
        operation_plan_patterns = [
            r'OPERATION_PLAN:\s*(\{[^{}]*\})',  # Simple single line
            r'OPERATION_PLAN:\s*(\{(?:[^{}]|(?:\{[^{}]*\}))*\})',  # Nested braces - improved
            r'OPERATION_PLAN:\s*(\{.*?\n\s*\})',  # Multi-line ending with }
        ]
        
        for pattern in operation_plan_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    dict_str = match.group(1)
                    print(f"DEBUG: Extracted OPERATION_PLAN dict (Strategy 1): {dict_str}")
                    operation_plan = ast.literal_eval(dict_str)
                    print(f"DEBUG: Successfully parsed OPERATION_PLAN: {operation_plan}")
                    return operation_plan
                except Exception as e:
                    print(f"DEBUG: Error evaluating OPERATION_PLAN dict: {e}")
                    continue
        
        # Strategy 2: Look for operation_plan = { ... } assignment
        assignment_patterns = [
            r'operation_plan\s*=\s*(\{.*?\})',  # Single line
            r'operation_plan\s*=\s*(\{(?:[^{}]|\{[^{}]*\})*\})',  # Multi-line with nesting
        ]
        
        for pattern in assignment_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    dict_str = match.group(1)
                    print(f"DEBUG: Extracted assignment dict (Strategy 2): {dict_str}")
                    operation_plan = ast.literal_eval(dict_str)
                    print(f"DEBUG: Successfully parsed assignment: {operation_plan}")
                    return operation_plan
                except Exception as e:
                    print(f"DEBUG: Error evaluating assignment dict: {e}")
                    continue
        
        # Strategy 3: Extract using balanced brace counting
        operation_plan = self._extract_balanced_braces(text)
        if operation_plan:
            return operation_plan
        
        # Strategy 4: Fallback to manual field extraction
        return self._manual_field_extraction(text)
    
    def _extract_balanced_braces(self, text):
        """Extract dictionary using balanced brace counting"""
        try:
            import re
            
            # Find all potential starting positions for dictionaries
            start_positions = []
            for match in re.finditer(r'(?:OPERATION_PLAN:|operation_plan\s*=)\s*\{', text):
                start_positions.append(match.end() - 1)  # Position of the opening brace
            
            for start_pos in start_positions:
                brace_count = 0
                in_string = False
                escape_next = False
                
                for i, char in enumerate(text[start_pos:], start_pos):
                    if escape_next:
                        escape_next = False
                        continue
                    
                    if char == '\\':
                        escape_next = True
                        continue
                    
                    if char in ['"', "'"]:
                        in_string = not in_string
                        continue
                    
                    if not in_string:
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                # Found complete dictionary
                                dict_str = text[start_pos:i+1]
                                try:
                                    print(f"DEBUG: Extracted balanced braces dict: {dict_str}")
                                    operation_plan = ast.literal_eval(dict_str)
                                    print(f"DEBUG: Successfully parsed balanced braces: {operation_plan}")
                                    return operation_plan
                                except Exception as e:
                                    print(f"DEBUG: Error evaluating balanced braces dict: {e}")
                                    break
            return None
        except Exception as e:
            print(f"DEBUG: Error in balanced brace extraction: {e}")
            return None
    
    def _manual_field_extraction(self, text):
        """Fallback manual field extraction using regex"""
        try:
            print("DEBUG: Using fallback manual field extraction")
            import re
            
            plan_dict = {}
            
            # Extract operation_type
            op_type_match = re.search(r'"operation_type":\s*"([^"]+)"', text)
            if op_type_match:
                plan_dict['operation_type'] = op_type_match.group(1)
            
            # Extract method
            method_match = re.search(r'"method":\s*"([^"]+)"', text)
            if method_match:
                plan_dict['method'] = method_match.group(1)
            
            # Extract explanation
            exp_match = re.search(r'"explanation":\s*"([^"]+)"', text)
            if exp_match:
                plan_dict['explanation'] = exp_match.group(1)
            
            # Extract params
            params = {}
            
            # Look for record_id (for UPDATE/DELETE operations)
            record_id_match = re.search(r'"record_id":\s*"([^"]+)"', text)
            if record_id_match:
                params['record_id'] = record_id_match.group(1)
            
            # Also look for record_id in the OPERATION_PLAN output format
            if not record_id_match:
                record_id_alt_match = re.search(r"'record_id':\s*'([^']+)'", text)
                if record_id_alt_match:
                    params['record_id'] = record_id_alt_match.group(1)
            
            # Look for max_records
            max_records_match = re.search(r'"max_records":\s*(\d+)', text)
            if max_records_match:
                params['max_records'] = int(max_records_match.group(1))
            
            # Look for formula
            formula_match = re.search(r'"formula":\s*"([^"]+)"', text)
            if formula_match:
                params['formula'] = formula_match.group(1)
            
            # Look for fields object (for CREATE operations)
            fields_match = re.search(r'"fields":\s*\{([^}]+)\}', text)
            if fields_match:
                fields_content = fields_match.group(1)
                print(f"DEBUG: Found fields content: {fields_content}")
                
                # Parse individual field entries - handle both literal values and variables
                fields = {}
                
                # First try to extract literal string values
                field_pattern = r'"([^"]+)":\s*"([^"]+)"'
                field_matches = re.findall(field_pattern, fields_content)
                
                for field_name, field_value in field_matches:
                    fields[field_name] = field_value
                
                # Also try to extract variable references and resolve them from the text
                var_pattern = r'"([^"]+)":\s*([a-zA-Z_][a-zA-Z0-9_]*)'
                var_matches = re.findall(var_pattern, fields_content)
                
                for field_name, var_name in var_matches:
                    # Try to find the variable value in the text
                    var_value_pattern = rf'{var_name}\s*=\s*["\']([^"\']+)["\']'
                    var_value_match = re.search(var_value_pattern, text)
                    if var_value_match:
                        fields[field_name] = var_value_match.group(1)
                        print(f"DEBUG: Resolved variable {var_name} = '{var_value_match.group(1)}'")
                
                if fields:
                    params['fields'] = fields
                    print(f"DEBUG: Extracted fields: {fields}")
            
            plan_dict['params'] = params
            
            # Return if we have the required fields
            if 'operation_type' in plan_dict and 'method' in plan_dict:
                print(f"DEBUG: Final manual parsed plan: {plan_dict}")
                return plan_dict
            else:
                print(f"DEBUG: Manual parsing failed - missing required fields. Found: {list(plan_dict.keys())}")
            
            return None
        except Exception as e:
            print(f"Error in manual field extraction: {e}")
            return None

    def _execute_operation(self, season, operation_plan):
        """Execute the operation plan using pyairtable SDK"""
        try:
            # Get the table instance
            table = get_table(season)
            
            operation_type = operation_plan.get("operation_type")
            method = operation_plan.get("method")
            params = operation_plan.get("params", {})
            
            print(f"Executing {operation_type} operation: {method} with params: {params}")
            
            if method == "table.all":
                # Handle table.all() with optional parameters
                if "formula" in params:
                    result = table.all(formula=params["formula"])
                elif "max_records" in params:
                    result = table.all(max_records=params["max_records"])
                else:
                    result = table.all()
                    
            elif method == "table.first":
                # Handle table.first() with optional formula
                if "formula" in params:
                    result = table.first(formula=params["formula"])
                else:
                    result = table.first()
                    
            elif method == "table.find":
                # Handle table.find() - get a single record by record_id
                record_id = params.get("record_id")
                if record_id:
                    result = table.get(record_id)  # pyairtable uses get() for finding by record_id
                else:
                    result = {"error": "record_id required for find"}
                    
            elif method == "table.search":
                # Handle table.search() 
                field_name = params.get("field_name")
                field_value = params.get("field_value")
                formula = params.get("formula")
                
                if field_name and field_value:
                    result = table.search(field_name, field_value)
                elif formula:
                    # If a formula is provided, use table.all with formula instead
                    result = table.all(formula=formula)
                else:
                    result = []
                    
            elif method == "table.create":
                # Handle table.create()
                fields = params.get("fields", {})
                result = table.create(fields)
                
            elif method == "table.update":
                # Handle table.update()
                record_id = params.get("record_id")
                fields = params.get("fields", {})
                if record_id:
                    result = table.update(record_id, fields)
                else:
                    result = {"error": "record_id required for update"}
                    
            elif method == "table.delete":
                # Handle table.delete()
                record_id = params.get("record_id")
                if record_id:
                    result = table.delete(record_id)
                else:
                    result = {"error": "record_id required for delete"}
                    
            elif method == "table.count":
                # Handle table.count() - count all records or with formula
                if "formula" in params:
                    # Count records matching a formula
                    all_records = table.all(formula=params["formula"])
                    result = {"count": len(all_records)}
                else:
                    # Count all records in the table
                    all_records = table.all()
                    result = {"count": len(all_records)}
                    
            else:
                result = {"error": f"Unknown method: {method}"}
            
            # Convert result to a serializable format
            if hasattr(result, '__dict__'):
                result = result.__dict__
            elif isinstance(result, list):
                result = [item.__dict__ if hasattr(item, '__dict__') else item for item in result]
            
            return result
            
        except Exception as e:
            return {"error": f"Execution failed: {str(e)}"}

# Global instance
airtable_agent = AirtableAgent()

def execute_airtable_request(season: str, query: str) -> dict:
    """
    Main function to execute airtable requests
    This is what gets called by the main agent's tool
    """
    return airtable_agent.process_request(season, query) 