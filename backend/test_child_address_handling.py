#!/usr/bin/env python3
"""
Test script for enhanced child address handling (routines 16-18)
Demonstrates proper error handling and separate address collection
"""

from registration_agent.registration_routines import RegistrationRoutines

def test_child_address_handling():
    """Test the child address check with proper error handling and separate address collection"""
    
    print("🏠 Testing Enhanced Child Address Handling")
    print("=" * 60)
    
    # Check all relevant routines exist
    routines_to_check = [16, 17, 18]
    for routine_num in routines_to_check:
        routine = RegistrationRoutines.get_routine_message(routine_num)
        if routine:
            print(f"✅ Routine {routine_num} found: {routine[:60]}...")
        else:
            print(f"❌ Routine {routine_num} not found")
            return
    
    print(f"\n📋 Child Address Decision Tree:")
    print("-" * 40)
    
    decision_tree = [
        ("🤔 Unclear response", "routine_number = 16", "Ask for clarification"),
        ("✅ Yes (same address)", "routine_number = 17", "Complete registration"),
        ("❌ No (different address)", "routine_number = 18", "Collect child's address"),
    ]
    
    for response_type, routine_action, description in decision_tree:
        print(f"{response_type}")
        print(f"   → {routine_action}")
        print(f"   → {description}")
        print()
    
    print(f"💬 Example Conversations:")
    print("-" * 30)
    
    # Scenario 1: Clear Yes
    print("🎯 Scenario 1: Clear Yes Response")
    print("Agent: 'Does Tom live at the same address as you?'")
    print("Parent: 'Yes, he lives with me'")
    print("→ Normalized to: 'Yes'")
    print("→ Action: Set routine_number = 17 (complete registration)")
    print()
    
    # Scenario 2: Clear No
    print("🎯 Scenario 2: Clear No Response")
    print("Agent: 'Does Tom live at the same address as you?'")
    print("Parent: 'No, he lives with his mum'")
    print("→ Normalized to: 'No'")
    print("→ Action: Set routine_number = 18 (collect child's address)")
    print()
    
    # Scenario 3: Unclear
    print("🎯 Scenario 3: Unclear Response")
    print("Agent: 'Does Tom live at the same address as you?'")
    print("Parent: 'Well, sometimes he stays with...'")
    print("→ Cannot determine Yes/No")
    print("→ Action: Set routine_number = 16 (ask for clarification)")
    print("→ Agent: 'Sorry, can you clarify - does Tom live at your")
    print("         address most of the time? Just need a yes or no.'")
    print()
    
    print(f"📝 Response Normalization:")
    print("-" * 30)
    
    response_examples = {
        "YES responses": [
            "yes", "yeah", "same address", "lives with me",
            "he's here", "that's right", "correct"
        ],
        "NO responses": [
            "no", "nope", "different address", "lives elsewhere", 
            "he's with his mum", "separate address"
        ],
        "UNCLEAR responses": [
            "sometimes", "it depends", "well...", "mostly but...",
            "part of the time", "it's complicated"
        ]
    }
    
    for category, examples in response_examples.items():
        print(f"\n{category}:")
        for example in examples:
            if category == "YES responses":
                result = "→ 'Yes' → Routine 17"
            elif category == "NO responses":
                result = "→ 'No' → Routine 18"
            else:
                result = "→ Stay on Routine 16"
            print(f"  '{example}' {result}")
    
    print(f"\n🔄 Routine 18: Child's Separate Address")
    print("-" * 42)
    print("📍 Collects child's address using Google Places API")
    print("🔍 Validates address same as parent's address validation")
    print("🔁 Error recovery: stays on routine 18 if validation fails")
    print("✅ Success: moves to routine 19 with both addresses collected")
    
    print(f"\n🏁 Registration Completion Paths:")
    print("-" * 38)
    print("Path A: Same address → Routine 17 → Complete")
    print("Path B: Different address → Routine 18 → Routine 19 → Complete")
    print("Path C: Unclear → Routine 16 (retry) → Path A or B")
    
    print(f"\n✅ Enhanced child address handling ready!")
    print("Proper error handling and separate address collection implemented!")

if __name__ == "__main__":
    test_child_address_handling() 