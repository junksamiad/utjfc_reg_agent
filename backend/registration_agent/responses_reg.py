from openai import OpenAI
from dotenv import load_dotenv
import json
from .agents_reg import Agent
from .agent_response_schema_reg import AgentResponse

load_dotenv(override=True)  # Load environment variables from .env file, forcing override of existing vars

client = OpenAI()

def chat_loop_new_registration_1(agent: Agent, input_messages: list):
    """
    Gets a response from OpenAI's Responses API for NEW PLAYER registrations (200 codes).
    Based on the provided message history and agent configuration. 
    Uses structured outputs and supports both MCP and local function calling.
    Returns the full response object for inspection.
    """
    if not input_messages:
        print("Warning: chat_loop_1 called with empty input_messages list.")
        return {"error": "Input messages list cannot be empty"}

    try:
        # Prepare parameters for the Responses API call
        api_params = {
            "model": agent.model,
            "instructions": agent.instructions,
            "input": input_messages,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "agent_response",
                    "schema": AgentResponse.model_json_schema(),
                    "strict": True
                }
            }
        }
        
        # Add tools if the agent has any
        if agent.tools:
            openai_tools = agent.get_tools_for_openai()
            if openai_tools:
                api_params["tools"] = openai_tools

        print(f"Making Responses API call with model: {agent.model}")
        print(f"MCP mode: {agent.use_mcp}")
        
        # Make the API call using Responses API
        response = client.responses.create(**api_params)
        
        # Handle different types of tool calls
        if agent.use_mcp:
            # MCP mode: OpenAI handles tool calls automatically
            # Just return the response - tool calls are already executed
            print("MCP mode: Tool calls handled automatically by OpenAI")
            return response
        else:
            # Local function calling mode: Handle function calls manually
            # Check if we need to handle function calls
            has_function_calls = False
            if hasattr(response, 'output') and response.output:
                for output_item in response.output:
                    if hasattr(output_item, 'type') and output_item.type == 'function_call':
                        has_function_calls = True
                        break
            
            if has_function_calls:
                print("Local mode: Processing function calls manually")
                # Handle function calls
                tool_functions = agent.get_tool_functions()
                
                # Start with the original conversation
                conversation_with_tools = input_messages.copy()
                
                # Process each tool call in the response
                for tool_call in response.output:
                    if hasattr(tool_call, 'type') and tool_call.type == 'function_call':
                        function_name = tool_call.name
                        function_args = json.loads(tool_call.arguments)
                        
                        if function_name in tool_functions:
                            # Execute the function
                            function_result = tool_functions[function_name](**function_args)
                            
                            # Log the detailed tool response for debugging
                            print(f"--- TOOL CALL RESPONSE ---")
                            print(f"Function: {function_name}")
                            print(f"Arguments: {function_args}")
                            print(f"Result: {function_result}")
                            print(f"--- END TOOL CALL RESPONSE ---")
                            
                            # Add the tool call to conversation (Responses API format)
                            conversation_with_tools.append({
                                "type": "function_call",
                                "id": tool_call.id,
                                "call_id": tool_call.call_id,
                                "name": function_name,
                                "arguments": tool_call.arguments
                            })
                            
                            # Add the tool result to the conversation (Responses API format)
                            conversation_with_tools.append({
                                "type": "function_call_output",
                                "call_id": tool_call.call_id,
                                "output": str(function_result)
                            })
                
                # Make another API call to get the final response
                print("Making second API call for final response after tool execution")
                final_response = client.responses.create(
                    model=agent.model,
                    instructions=agent.instructions,
                    input=conversation_with_tools,
                    tools=openai_tools if openai_tools else None,
                    text={
                        "format": {
                            "type": "json_schema",
                            "name": "agent_response",
                            "schema": AgentResponse.model_json_schema(),
                            "strict": True
                        }
                    }
                )
                
                return final_response
            else:
                print("Local mode: No function calls detected")
        
        return response

    except Exception as e:
        print(f"Error in chat_loop_1: {e}")
        return {"error": f"API call failed: {str(e)}"}

def chat_loop_renew_registration_1(agent: Agent, input_messages: list):
    """
    Gets a response from OpenAI's Responses API for EXISTING PLAYER re-registrations (100 codes).
    Based on the provided message history and agent configuration. 
    Uses structured outputs and supports both MCP and local function calling.
    Returns the full response object for inspection.
    """
    if not input_messages:
        print("Warning: chat_loop_renew_registration_1 called with empty input_messages list.")
        return {"error": "Input messages list cannot be empty"}

    try:
        # Prepare parameters for the Responses API call
        api_params = {
            "model": agent.model,
            "instructions": agent.instructions,
            "input": input_messages,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "agent_response",
                    "schema": AgentResponse.model_json_schema(),
                    "strict": True
                }
            }
        }
        
        # Add tools if the agent has any
        if agent.tools:
            openai_tools = agent.get_tools_for_openai()
            if openai_tools:
                api_params["tools"] = openai_tools

        print(f"Making Responses API call with model: {agent.model}")
        print(f"MCP mode: {agent.use_mcp}")
        
        # Make the API call using Responses API
        response = client.responses.create(**api_params)
        
        # Handle different types of tool calls
        if agent.use_mcp:
            # MCP mode: OpenAI handles tool calls automatically
            # Just return the response - tool calls are already executed
            print("MCP mode: Tool calls handled automatically by OpenAI")
            return response
        else:
            # Local function calling mode: Handle function calls manually
            # Check if we need to handle function calls
            has_function_calls = False
            if hasattr(response, 'output') and response.output:
                for output_item in response.output:
                    if hasattr(output_item, 'type') and output_item.type == 'function_call':
                        has_function_calls = True
                        break
            
            if has_function_calls:
                print("Local mode: Processing function calls manually")
                # Handle function calls
                tool_functions = agent.get_tool_functions()
                
                # Start with the original conversation
                conversation_with_tools = input_messages.copy()
                
                # Process each tool call in the response
                for tool_call in response.output:
                    if hasattr(tool_call, 'type') and tool_call.type == 'function_call':
                        function_name = tool_call.name
                        function_args = json.loads(tool_call.arguments)
                        
                        if function_name in tool_functions:
                            # Execute the function
                            function_result = tool_functions[function_name](**function_args)
                            
                            # Log the detailed tool response for debugging
                            print(f"--- TOOL CALL RESPONSE ---")
                            print(f"Function: {function_name}")
                            print(f"Arguments: {function_args}")
                            print(f"Result: {function_result}")
                            print(f"--- END TOOL CALL RESPONSE ---")
                            
                            # Add the tool call to conversation (Responses API format)
                            conversation_with_tools.append({
                                "type": "function_call",
                                "id": tool_call.id,
                                "call_id": tool_call.call_id,
                                "name": function_name,
                                "arguments": tool_call.arguments
                            })
                            
                            # Add the tool result to the conversation (Responses API format)
                            conversation_with_tools.append({
                                "type": "function_call_output",
                                "call_id": tool_call.call_id,
                                "output": str(function_result)
                            })
                
                # Make another API call to get the final response
                print("Making second API call for final response after tool execution")
                final_response = client.responses.create(
                    model=agent.model,
                    instructions=agent.instructions,
                    input=conversation_with_tools,
                    tools=openai_tools if openai_tools else None,
                    text={
                        "format": {
                            "type": "json_schema",
                            "name": "agent_response",
                            "schema": AgentResponse.model_json_schema(),
                            "strict": True
                        }
                    }
                )
                
                return final_response
            else:
                print("Local mode: No function calls detected")
        
        return response

    except Exception as e:
        print(f"Error in chat_loop_renew_registration_1: {e}")
        return {"error": f"API call failed: {str(e)}"}

if __name__ == '__main__':
    # Example usage with history and an Agent
    default_agent = Agent(instructions="Please be very concise and respond in the structured format.")
    
    sample_history = [
        {"role": "user", "content": "What is the capital of France?"}
    ]
    
    print(f"Agent: {default_agent.name}, Model: {default_agent.model}")
    print(f"User History: {sample_history}")
    
    full_response = chat_loop_new_registration_1(agent=default_agent, input_messages=sample_history)
    print(f"AI Full Response Object: {full_response}")

    # Handle structured output extraction
    try:
        if hasattr(full_response, 'output_text') and full_response.output_text:
            # Try to parse as JSON first
            try:
                structured_response = json.loads(full_response.output_text)
                agent_text = structured_response.get('agent_final_response', full_response.output_text)
            except json.JSONDecodeError:
                agent_text = full_response.output_text
                
            print(f"Assistant Says: {agent_text}")
            sample_history.append({"role": "assistant", "content": agent_text})
        else:
            print("Could not extract response from structured output.")
    except Exception as e:
        print(f"Error extracting structured response: {e}")
    
    # Second turn
    sample_history.append({"role": "user", "content": "What is its population?"})
    print(f"User History (2nd turn): {sample_history}")
    
    full_response_2 = chat_loop_new_registration_1(agent=default_agent, input_messages=sample_history)
    print(f"AI Full Response Object (2nd turn): {full_response_2}")

    # Handle second response
    try:
        if hasattr(full_response_2, 'output_text') and full_response_2.output_text:
            try:
                structured_response_2 = json.loads(full_response_2.output_text)
                agent_text_2 = structured_response_2.get('agent_final_response', full_response_2.output_text)
            except json.JSONDecodeError:
                agent_text_2 = full_response_2.output_text
                
            print(f"Assistant Says (2nd turn): {agent_text_2}")
        else:
            print("Could not extract response from structured output (2nd turn).")
    except Exception as e:
        print(f"Error extracting structured response (2nd turn): {e}") 