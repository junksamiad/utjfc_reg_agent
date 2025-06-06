from pydantic import BaseModel, Field
from typing import Optional

class AgentResponse(BaseModel):
    """
    Structured response schema for agents using OpenAI Responses API.
    
    This ensures consistent output format while allowing for future extension
    with additional metadata fields for agent routing and workflow control.
    """
    
    agent_final_response: str = Field(
        description="The final response text that should be displayed to the user. This is what gets sent to the frontend.",
        min_length=1
    )
    
    # Future agent handoff fields - commented out for now
    # These will be used when implementing agent-controlled routing decisions
    # last_agent: Optional[str] = Field(
    #     description="The name of the current agent handling this response (e.g., 'universal', 're_registration', 'new_registration')",
    #     default=None
    # )
    # next_agent: Optional[str] = Field(
    #     description="The name of the next agent that should handle the conversation flow (agent-controlled handoff)",
    #     default=None
    # )
    
    class Config:
        """Pydantic configuration for the schema."""
        # Ensure JSON schema is generated with additionalProperties: false for OpenAI structured outputs
        extra = "forbid"
        
    @classmethod
    def model_json_schema(cls, by_alias=True, ref_template='#/$defs/{model}'):
        """Override to ensure additionalProperties is set to false"""
        schema = super().model_json_schema(by_alias=by_alias, ref_template=ref_template)
        # Ensure additionalProperties is explicitly set to false for structured outputs
        schema["additionalProperties"] = False
        return schema 