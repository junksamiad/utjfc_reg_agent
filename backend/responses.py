from openai import OpenAI
from dotenv import load_dotenv
import json
from agents import Agent # Changed from .agents to agents

load_dotenv()  # Load environment variables from .env file

client = OpenAI()

def chat_loop_1(agent: Agent, input_messages: list): # Modified to accept an Agent object
    """
    Gets a response from OpenAI's Responses API based on the provided message history
    and agent configuration. Now supports function calling.
    Returns the full response object for inspection.
    """
    if not input_messages:
        print("Warning: chat_loop_1 called with empty input_messages list.")
        return {"error": "Input messages list cannot be empty"}

    try:
        # Prepare parameters for the API call using the agent's attributes
        api_params = {
            "model": agent.model,
            "messages": [
                {"role": "system", "content": agent.instructions}
            ] + input_messages
        }
        
        # Add tools if the agent has any
        if agent.tools:
            openai_tools = agent.get_tools_for_openai()
            if openai_tools:
                api_params["tools"] = openai_tools
                api_params["tool_choice"] = "auto"

        # Make the API call
        response = client.chat.completions.create(**api_params)
        
        # Check if the response includes tool calls
        if response.choices[0].message.tool_calls:
            # Handle function calls
            tool_functions = agent.get_tool_functions()
            
            # Process each tool call
            messages_with_tool_calls = api_params["messages"] + [response.choices[0].message]
            
            for tool_call in response.choices[0].message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)  # Parse JSON arguments safely
                
                if function_name in tool_functions:
                    # Execute the function
                    function_result = tool_functions[function_name](**function_args)
                    
                    # Log the detailed tool response for debugging
                    print(f"--- TOOL CALL RESPONSE ---")
                    print(f"Function: {function_name}")
                    print(f"Arguments: {function_args}")
                    print(f"Result: {function_result}")
                    print(f"--- END TOOL CALL RESPONSE ---")
                    
                    # Add the tool result to the conversation
                    messages_with_tool_calls.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_result
                    })
            
            # Make another API call to get the final response
            final_response = client.chat.completions.create(
                model=agent.model,
                messages=messages_with_tool_calls,
                tools=openai_tools if openai_tools else None,
                tool_choice="auto" if openai_tools else None
            )
            
            return final_response
        
        return response

    except Exception as e:
        print(f"Error in chat_loop_1: {e}")
        return {"error": f"API call failed: {str(e)}"}

if __name__ == '__main__':
    # Example usage with history and an Agent
    default_agent = Agent(instructions="Please be very concise and speak like a pirate.") # Example agent
    
    sample_history = [
        {"role": "user", "content": "What is the capital of France?"}
    ]
    
    print(f"Agent: {default_agent.name}, Model: {default_agent.model}, Instructions: {default_agent.instructions}")
    print(f"User History: {sample_history}")
    
    full_response = chat_loop_1(agent=default_agent, input_messages=sample_history)
    print(f"AI Full Response Object: {full_response}")

    if hasattr(full_response, 'output') and full_response.output:
        # Assuming the first output message contains the text content
        # This parsing might need adjustment based on the actual response structure with tools
        if full_response.output[0].content and isinstance(full_response.output[0].content, list) and hasattr(full_response.output[0].content[0], 'text'):
            assistant_text = full_response.output[0].content[0].text
            print(f"Assistant Says: {assistant_text}")
            sample_history.append({"role": "assistant", "content": assistant_text})
        else:
            print("Could not extract assistant text from response.")
    
    sample_history.append({"role": "user", "content": "What is its population?"})
    print(f"User History (2nd turn): {sample_history}")
    
    # For the second call, let's use a slightly different agent instruction or the same one
    pirate_agent_turn_2 = Agent(instructions="Continue speaking like a pirate, and be brief, matey!")
    full_response_2 = chat_loop_1(agent=pirate_agent_turn_2, input_messages=sample_history)
    print(f"AI Full Response Object (2nd turn): {full_response_2}")

    if hasattr(full_response_2, 'output') and full_response_2.output:
        if full_response_2.output[0].content and isinstance(full_response_2.output[0].content, list) and hasattr(full_response_2.output[0].content[0], 'text'):
            assistant_text_2 = full_response_2.output[0].content[0].text
            print(f"Assistant Says (2nd turn): {assistant_text_2}")
        else:
            print("Could not extract assistant text from response (2nd turn).") 