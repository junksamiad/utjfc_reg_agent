from .agents_reg import Agent

# Re-registration agent (100 codes)
re_registration_agent = Agent(
    name="UTJFC Re-registration Assistant",
    model="gpt-4o-mini",
    instructions="You are a helpful agent, respond to all queries in CAPS, and put a 100 on the end of each sentence",
    tools=[],
    use_mcp=False  # Local function calling
)

# New registration agent (200 codes)  
new_registration_agent = Agent(
    name="UTJFC New Player Registration Assistant",
    model="gpt-4o-mini", 
    instructions="You are a helpful agent, respond to all queries in CAPS and put a 200 on the end of each sentence",
    tools=[],
    use_mcp=False  # Local function calling
) 