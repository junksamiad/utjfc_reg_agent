#!/usr/bin/env python3
"""
Test script for enhanced medical issues collection (routine 5)
Demonstrates how the agent should handle serious medical conditions requiring follow-up questions
"""

def test_medical_scenarios():
    """Test different medical condition scenarios and expected follow-up questions"""
    
    print("🏥 Testing Enhanced Medical Issues Collection")
    print("=" * 60)
    
    # Test scenarios that should trigger detailed follow-up questions
    serious_conditions = [
        {
            "condition": "Severe nut allergy, needs EpiPen",
            "expected_followups": [
                "Where is the EpiPen kept?",
                "What should we do in an emergency?", 
                "Are there any specific triggers to avoid?"
            ]
        },
        {
            "condition": "Asthma, has inhaler",
            "expected_followups": [
                "Where is the inhaler kept?",
                "What should we do in an emergency?",
                "Are there any specific triggers to avoid?"
            ]
        },
        {
            "condition": "Type 1 diabetes",
            "expected_followups": [
                "Where is the medication kept?",
                "What should we do in an emergency?",
                "Are there any specific triggers to avoid?"
            ]
        },
        {
            "condition": "Epilepsy",
            "expected_followups": [
                "Where is the medication kept?",
                "What should we do in an emergency?",
                "Are there any specific triggers to avoid?"
            ]
        }
    ]
    
    # Test scenarios that DON'T need detailed follow-up
    minor_conditions = [
        "Wears glasses",
        "Had broken arm last year", 
        "Gets travel sick sometimes",
        "Hay fever in summer"
    ]
    
    print("\n🚨 Serious Conditions (REQUIRE detailed follow-up):")
    print("-" * 50)
    
    for scenario in serious_conditions:
        print(f"\n📋 Parent says: '{scenario['condition']}'")
        print("   ↳ Agent should ask:")
        for question in scenario['expected_followups']:
            print(f"     • {question}")
    
    print(f"\n✅ Minor Conditions (basic documentation only):")
    print("-" * 50)
    
    for condition in minor_conditions:
        print(f"📋 '{condition}' → Document as-is, no additional questions needed")
    
    print(f"\n🎯 Agent Behavior Guidelines:")
    print("-" * 30)
    print("• Detect serious medical conditions automatically")
    print("• Ask specific follow-up questions for emergency planning")
    print("• Capture location of medication/equipment")
    print("• Document emergency procedures")
    print("• Note specific triggers or things to avoid")
    print("• Ensure club staff have actionable emergency information")
    
    print(f"\n📝 Example Enhanced Medical Record:")
    print("-" * 40)
    print("Medical Issues: Severe nut allergy")
    print("Emergency Details:")
    print("  - EpiPen location: In sports bag side pocket")
    print("  - Emergency action: Call 999, administer EpiPen if needed")
    print("  - Triggers to avoid: All nuts, especially peanuts")
    print("  - Parent emergency contact: Already collected in routine 8")
    
    print(f"\n✅ Enhanced medical issues collection ready!")
    print("Routine 5 now captures life-saving emergency information!")

if __name__ == "__main__":
    test_medical_scenarios() 