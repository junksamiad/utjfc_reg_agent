#!/usr/bin/env python3
"""
Test script to verify Airtable integration through the deployed MCP server
"""

import requests
import json
import time

# MCP Server URL
MCP_SERVER_URL = "https://utjfc-mcp-server.replit.app"

def test_mcp_tool_call(season: str, query: str, test_name: str):
    """Make a tool call to the MCP server and display results"""
    print(f"\n{'='*60}")
    print(f"🧪 TEST: {test_name}")
    print(f"📋 Season: {season}")
    print(f"📝 Query: {query}")
    print(f"{'='*60}")
    
    # Prepare the JSON-RPC request
    request_data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "airtable_database_operation",
            "arguments": {
                "season": season,
                "query": query
            }
        }
    }
    
    try:
        # Make the request
        print("📤 Sending request to MCP server...")
        response = requests.post(
            f"{MCP_SERVER_URL}/mcp",
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Check for error in response
            if "error" in result:
                print(f"❌ Error: {result['error']}")
                return False
            
            # Extract the actual result
            if "result" in result and "content" in result["result"]:
                content = result["result"]["content"][0]["text"]
                parsed_content = json.loads(content)
                
                print(f"\n✅ Status: {parsed_content.get('status', 'unknown')}")
                print(f"📨 Message: {parsed_content.get('message', 'No message')}")
                
                # Display the data
                if "data" in parsed_content and parsed_content["data"]:
                    data = parsed_content["data"]
                    
                    # Show operation plan
                    if "operation_plan" in data:
                        op_plan = data["operation_plan"]
                        print(f"\n🔧 Operation Plan:")
                        print(f"   Type: {op_plan.get('operation_type')}")
                        print(f"   Method: {op_plan.get('method')}")
                        print(f"   Explanation: {op_plan.get('explanation')}")
                    
                    # Show results
                    if "result" in data:
                        result_data = data["result"]
                        
                        # Handle different result types
                        if isinstance(result_data, dict):
                            if "count" in result_data:
                                print(f"\n📊 Count: {result_data['count']}")
                            elif "error" in result_data:
                                print(f"\n❌ Operation Error: {result_data['error']}")
                            else:
                                print(f"\n📄 Result: {json.dumps(result_data, indent=2)}")
                        elif isinstance(result_data, list):
                            print(f"\n📊 Found {len(result_data)} records")
                            # Show first few records
                            for i, record in enumerate(result_data[:3]):
                                if "fields" in record:
                                    fields = record["fields"]
                                    print(f"\n   Record {i+1}:")
                                    print(f"   - Player: {fields.get('player_first_name', '')} {fields.get('player_last_name', '')}")
                                    print(f"   - Age Group: {fields.get('age_group', 'N/A')}")
                                    print(f"   - Team: {fields.get('team', 'N/A')}")
                            if len(result_data) > 3:
                                print(f"\n   ... and {len(result_data) - 3} more records")
                        else:
                            print(f"\n📄 Result: {result_data}")
                
                return True
            else:
                print("❌ Unexpected response format")
                print(f"Full response: {json.dumps(result, indent=2)}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out after 30 seconds")
        return False
    except Exception as e:
        print(f"❌ Exception: {type(e).__name__}: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing MCP Server Airtable Integration")
    print(f"🔗 Server: {MCP_SERVER_URL}")
    print("=" * 60)
    
    # Test 1: Count all registrations
    test_mcp_tool_call(
        season="2526",
        query="Count all registrations",
        test_name="Count All Registrations"
    )
    
    time.sleep(1)  # Small delay between requests
    
    # Test 2: Find specific player
    test_mcp_tool_call(
        season="2526",
        query="Find Stefan Hayton",
        test_name="Find Specific Player"
    )
    
    time.sleep(1)
    
    # Test 3: Find players by age group
    test_mcp_tool_call(
        season="2526",
        query="Show all players in age group u10",
        test_name="Find Players by Age Group"
    )
    
    time.sleep(1)
    
    # Test 4: Find players with medical issues
    test_mcp_tool_call(
        season="2526",
        query="Find all players with medical issues",
        test_name="Find Players with Medical Issues"
    )
    
    time.sleep(1)
    
    # Test 5: Find players by team
    test_mcp_tool_call(
        season="2526",
        query="Show all Tigers team players",
        test_name="Find Players by Team"
    )
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    main() 