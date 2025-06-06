from pydantic import BaseModel
from .tools.airtable.airtable_tool_definition import AIRTABLE_DATABASE_OPERATION_TOOL
from .tools.registration_tools.person_name_validation_tool import PERSON_NAME_VALIDATION_TOOL
from .tools.registration_tools.child_dob_validation_tool import CHILD_DOB_VALIDATION_TOOL
from .tools.registration_tools.medical_issues_validation_tool import MEDICAL_ISSUES_VALIDATION_TOOL
from .tools.registration_tools.address_validation_tool import ADDRESS_VALIDATION_TOOL
from .tools.registration_tools.address_lookup_tool import ADDRESS_LOOKUP_TOOL
import os
from dotenv import load_dotenv

load_dotenv()

class Agent(BaseModel):
    name: str = "Agent"
    model: str = "gpt-4o-mini"
    instructions: str = "You are a helpful Agent"
    tools: list = [] # This will be used for function definitions
    use_mcp: bool = False  # New flag to enable MCP mode
    mcp_server_url: str = ""  # URL for the MCP server
    
    def get_tools_for_openai(self):
        """
        Get the tools formatted for OpenAI API calls.
        Returns either local function definitions or MCP server configuration.
        """
        if self.use_mcp and self.mcp_server_url:
            # Return MCP server configuration
            return [{
                "type": "mcp",
                "server_label": "utjfc_registration",
                "server_url": self.mcp_server_url,
                "require_approval": "never",  # Skip approvals for trusted internal server
                "allowed_tools": self.tools if self.tools else None  # Limit to specified tools
            }]
        else:
            # Return local function definitions (existing behavior)
            available_tools = {
                "airtable_database_operation": AIRTABLE_DATABASE_OPERATION_TOOL,
                "person_name_validation": PERSON_NAME_VALIDATION_TOOL,
                "child_dob_validation": CHILD_DOB_VALIDATION_TOOL,
                "medical_issues_validation": MEDICAL_ISSUES_VALIDATION_TOOL,
                "address_validation": ADDRESS_VALIDATION_TOOL,
                "address_lookup": ADDRESS_LOOKUP_TOOL
            }
            
            # Return the tool definitions for the tools specified in self.tools
            openai_tools = []
            for tool_name in self.tools:
                if tool_name in available_tools:
                    openai_tools.append(available_tools[tool_name])
            
            return openai_tools
    
    def get_tool_functions(self):
        """
        Get the actual Python functions that handle tool calls.
        Returns a dictionary mapping function names to their handlers.
        Only used for local function calling (when use_mcp=False).
        """
        if self.use_mcp:
            # MCP mode doesn't use local functions
            return {}
            
        from .tools.airtable.airtable_tool_definition import handle_airtable_tool_call
        from .tools.registration_tools.person_name_validation_tool import handle_person_name_validation
        from .tools.registration_tools.child_dob_validation_tool import handle_child_dob_validation
        from .tools.registration_tools.medical_issues_validation_tool import handle_medical_issues_validation
        from .tools.registration_tools.address_validation_tool import handle_address_validation
        from .tools.registration_tools.address_lookup_tool import handle_address_lookup
        
        return {
            "airtable_database_operation": handle_airtable_tool_call,
            "person_name_validation": handle_person_name_validation,
            "child_dob_validation": handle_child_dob_validation,
            "medical_issues_validation": handle_medical_issues_validation,
            "address_validation": handle_address_validation,
            "address_lookup": handle_address_lookup
        }
    
    def get_instructions_with_routine(self, routine_message: str = ""):
        """
        Get instructions with a routine message injected into the {routine_instructions} placeholder.
        Used for dynamic instruction injection in registration flows.
        """
        return self.instructions.format(routine_instructions=routine_message)
    
    @classmethod
    def create_mcp_agent(cls, name: str = "MCP Agent", instructions: str = "You are a helpful agent with access to UTJFC registration tools.", mcp_server_url: str = None):
        """
        Factory method to create an agent configured for MCP server usage.
        """
        if not mcp_server_url:
            # Default to local development server
            mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8002/sse")
        
        return cls(
            name=name,
            model="gpt-4.1",  # Use gpt-4.1 for MCP support
            instructions=instructions,
            tools=["airtable_database_operation"],  # Available MCP tools
            use_mcp=True,
            mcp_server_url=mcp_server_url
        ) 