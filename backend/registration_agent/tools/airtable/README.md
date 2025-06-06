# Airtable Tool Module

A hybrid AI-powered database interface for UTJFC registration management that combines OpenAI's code interpreter with the pyairtable SDK for intelligent CRUD operations.

## 🏗️ Architecture Overview

This module implements a **hybrid approach** where:
1. **OpenAI Code Interpreter** analyzes natural language queries and generates operation plans
2. **pyairtable SDK** executes the operations with full Airtable functionality
3. **Main Agent** uses this as a tool for database interactions

```
User Query → Main Agent → airtable_database_operation → Helper Agent → pyairtable SDK → Airtable
```

## 📁 File Structure

```
backend/tools/airtable/
├── README.md                     # This documentation
├── __init__.py                   # Package initialization
├── airtable_setup.py            # Airtable client configuration & utilities
├── airtable_agent.py            # 🌟 Main hybrid agent implementation
├── airtable_tool_definition.py  # OpenAI function schema for main agent
└── table_schema/
    ├── __init__.py
    └── registrations_2526.py    # Table schema definitions
```

## 🔧 How It Works

### 1. Main Agent Integration

The main UTJFC agent has access to the `airtable_database_operation` tool:

```python
# In server.py
default_agent = Agent(
    name="UTJFC Registration Assistant",
    tools=["airtable_database_operation"]  # Enables database access
)
```

### 2. Tool Function Schema

When the main agent needs database access, it calls:

```python
{
    "name": "airtable_database_operation",
    "description": "Execute CRUD operations on UTJFC registration database",
    "parameters": {
        "season": "2526|2425",  # Season identifier
        "query": "Natural language description of what to do"
    }
}
```

### 3. Hybrid Processing Pipeline

```mermaid
graph TD
    A[User: "Find Stefan Hayton"] --> B[Main Agent]
    B --> C[airtable_database_operation tool]
    C --> D[Helper Agent - Code Interpreter]
    D --> E[Generate Operation Plan]
    E --> F[Backend - pyairtable SDK]
    F --> G[Execute on Airtable]
    G --> H[Return Results]
    H --> I[Main Agent Response]
```

## 🤖 Helper Agent Details

### Purpose
The `AirtableAgent` class acts as an intelligent intermediary that:
- Understands natural language database requests
- Analyzes table schemas to validate operations
- Generates structured operation plans
- Executes operations using the full pyairtable SDK

### Code Interpreter Role
Uses OpenAI's code interpreter to:
- Parse complex natural language queries
- Generate appropriate Airtable filterByFormula expressions
- Plan optimal CRUD operations
- Validate field names against schema

### Operation Plan Format
```python
{
    "operation_type": "read|create|update|delete",
    "method": "table.all|table.first|table.search|table.create|table.update|table.delete",
    "params": {
        "formula": "AND({player_first_name} = 'Stefan', {player_last_name} = 'Hayton')",
        "max_records": 10,
        "fields": {"player_first_name": "John"},
        "record_id": "recXXXXXXXXXXXXXX"
    },
    "explanation": "Human readable description"
}
```

## 🛠️ CRUD Capabilities

### ✅ CREATE Operations
```python
# Natural language: "Add a new player John Smith with parent contact info"
{
    "operation_type": "create",
    "method": "table.create",
    "params": {
        "fields": {
            "player_first_name": "John",
            "player_last_name": "Smith",
            "parent_first_name": "Jane",
            "parent_last_name": "Smith"
        }
    }
}
```

### 📖 READ Operations
```python
# Natural language: "Find all players with medical issues"
{
    "operation_type": "read",
    "method": "table.all",
    "params": {
        "formula": "{player_has_any_medical_issues} = 'Y'"
    }
}
```

### 🔄 UPDATE Operations
```python
# Natural language: "Update Stefan's medical info to indicate asthma"
{
    "operation_type": "update",
    "method": "table.update",
    "params": {
        "record_id": "recXXXXXXXXXXXXXX",
        "fields": {
            "player_has_any_medical_issues": "Y",
            "player_medical_details": "Asthma"
        }
    }
}
```

### 🗑️ DELETE Operations
```python
# Natural language: "Remove the duplicate registration for Stefan"
{
    "operation_type": "delete",
    "method": "table.delete",
    "params": {
        "record_id": "recXXXXXXXXXXXXXX"
    }
}
```

## 🔗 Integration Points

### Environment Variables
```bash
OPENAI_API_KEY=your_openai_api_key
AIRTABLE_API_KEY=your_airtable_api_key
```

### Airtable Configuration
```python
# In airtable_setup.py
AIRTABLE_BASE_ID = "appBLxf3qmGIBc6ue"
TABLE_CONFIGS = {
    "2526": {
        "table_id": "tbl1D7hdjVcyHbT8a",
        "table_name": "registrations_2526",
        "season": "2025-26"
    }
}
```

### Agent Registration
```python
# In agents.py - tool registration
def get_tool_functions(self):
    if "airtable_database_operation" in self.tools:
        return {
            "airtable_database_operation": execute_airtable_request
        }
```

## 📊 Table Schema System

### Schema Definition
Each season has a detailed schema file defining:
- Field names and types
- Relationships between fields
- Validation rules
- Field descriptions

```python
# Example from registrations_2526.py
REGISTRATIONS_2526_SCHEMA = {
    "table_name": "registrations_2526",
    "description": "Player registrations for 2025-26 season",
    "fields": {
        "player_first_name": {
            "type": "singleLineText",
            "description": "Player's first name"
        },
        # ... more fields
    }
}
```

### Schema Usage
The helper agent uses schemas to:
- Validate field names in queries
- Generate appropriate filterByFormula expressions
- Understand data relationships
- Provide intelligent operation planning

## 🚀 Usage Examples

### Through Chat Interface
```
User: "Find Stefan Hayton"
Agent: Uses airtable_database_operation → Returns formatted results

User: "How many players are registered this season?"
Agent: Uses airtable_database_operation → Returns count

User: "Show me all Tigers team players"
Agent: Uses airtable_database_operation → Returns filtered list
```

### Direct Function Call
```python
from tools.airtable.airtable_agent import execute_airtable_request

result = execute_airtable_request(
    season="2526",
    query="Find all players with medical issues"
)
```

## 🔍 Response Format

### Success Response
```python
{
    "status": "success",
    "message": "Airtable operation completed successfully",
    "data": {
        "query": "Find Stefan Hayton",
        "season": "2526",
        "table": "registrations_2526",
        "operation_plan": {
            "operation_type": "read",
            "method": "table.all",
            "params": {"formula": "..."},
            "explanation": "Search for records..."
        },
        "result": [
            {
                "id": "recXXXXXXXXXXXXXX",
                "fields": {
                    "player_first_name": "Stefan",
                    "player_last_name": "Hayton",
                    # ... more fields
                }
            }
        ]
    }
}
```

### Error Response
```python
{
    "status": "error",
    "message": "Airtable API error: [error description]",
    "data": null
}
```

## 🛡️ Error Handling

The module handles various error scenarios:
- Invalid season codes
- Missing environment variables
- Airtable API errors
- Schema validation failures
- Operation plan generation failures

## 🔧 Development & Testing

### Adding New Seasons
1. Create new schema file in `table_schema/`
2. Add table configuration to `airtable_setup.py`
3. Update helper agent to handle new season

### Testing
```bash
# Test individual components
python -c "from tools.airtable.airtable_agent import execute_airtable_request; print(execute_airtable_request('2526', 'test query'))"

# Test through chat endpoint
curl -X POST "http://localhost:8001/chat" -H "Content-Type: application/json" -d '{"user_message": "Find Stefan Hayton"}'
```

## 🎯 Key Benefits

1. **Natural Language Interface**: Users can query in plain English
2. **Full Airtable Functionality**: Access to all pyairtable SDK features
3. **Intelligent Planning**: AI generates optimal database operations
4. **Schema Awareness**: Validates operations against table structure
5. **Error Resilience**: Comprehensive error handling and fallbacks
6. **Extensible**: Easy to add new seasons and table configurations

## 🔮 Future Enhancements

- Support for multiple table operations in single query
- Batch operations for bulk data management
- Advanced analytics and reporting capabilities
- Integration with other club systems
- Automated data validation and cleanup

---

*This module represents a cutting-edge approach to database interaction, combining the power of AI with robust database operations for an intuitive user experience.* 