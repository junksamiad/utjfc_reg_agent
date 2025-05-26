from openai import OpenAI
from dotenv import load_dotenv
from agents import Agent # Changed from .agents to agents

load_dotenv()  # Load environment variables from .env file

client = OpenAI()

def chat_loop_1(agent: Agent, input_messages: list): # Modified to accept an Agent object
    """
    Gets a response from OpenAI's Responses API based on the provided message history
    and agent configuration.
    Returns the full response object for inspection.
    """
    if not input_messages:
        print("Warning: chat_loop_1 called with empty input_messages list.")
        return {"error": "Input messages list cannot be empty"}

    try:
        # Prepare parameters for the API call using the agent's attributes
        api_params = {
            "model": agent.model,
            "input": input_messages,
            "store": False,  # Ensure store is set to False
            "instructions": "You are a helpful agent, please respond in CAPS"
        }
        if agent.tools: # Add tools if the agent has any defined
            api_params["tools"] = agent.tools
        
        response = client.responses.create(**api_params)
        return response

    except Exception as e:
        print(f"Error calling OpenAI Responses API: {e}")
        return f"Error from OpenAI: {e}"

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