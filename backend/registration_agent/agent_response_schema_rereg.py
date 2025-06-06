from pydantic import BaseModel, Field

class ReRegistrationAgentResponse(BaseModel):
    """
    Structured response schema for re-registration agents using OpenAI Responses API.
    
    Re-registration flow is simpler and doesn't use the routine system,
    so this schema only includes the basic response field.
    """
    
    agent_final_response: str = Field(
        description="The final response text that should be displayed to the user. This is what gets sent to the frontend.",
        min_length=1
    )
    
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