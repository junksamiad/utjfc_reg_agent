from pydantic import BaseModel
from tools.airtable.airtable_tool_definition import AIRTABLE_DATABASE_OPERATION_TOOL

class Agent(BaseModel):
    name: str = "Agent"
    model: str = "gpt-4o-mini"
    instructions: str = "You are a helpful Agent"
    tools: list = [] # This will be used for function definitions
    
    def get_tools_for_openai(self):
        """
        Get the tools formatted for OpenAI API calls
        Returns the actual tool definitions, not just names
        """
        available_tools = {
            "airtable_database_operation": AIRTABLE_DATABASE_OPERATION_TOOL
        }
        
        # Return the tool definitions for the tools specified in self.tools
        openai_tools = []
        for tool_name in self.tools:
            if tool_name in available_tools:
                openai_tools.append(available_tools[tool_name])
        
        return openai_tools
    
    def get_tool_functions(self):
        """
        Get the actual Python functions that handle tool calls
        Returns a dictionary mapping function names to their handlers
        """
        from tools.airtable.airtable_tool_definition import handle_airtable_tool_call
        
        return {
            "airtable_database_operation": handle_airtable_tool_call
        } 