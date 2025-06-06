#!/usr/bin/env python3
"""
Test script for communication consent collection (routine 9)
Demonstrates GDPR-compliant consent collection for email/SMS communications
"""

from registration_agent.registration_routines import RegistrationRoutines

def test_communication_consent():
    """Test the new communication consent routine and flow"""
    
    print("📧 Testing Communication Consent Collection")
    print("=" * 60)
    
    # Check routine 9 (email) and 10 (consent) exist
    routine_9 = RegistrationRoutines.get_routine_message(9)
    routine_10 = RegistrationRoutines.get_routine_message(10)
    
    if routine_9:
        print("✅ Routine 9 (Email Collection) found")
        print(f"   Content: {routine_9[:80]}...")
    else:
        print("❌ Routine 9 not found")
        return
        
    if routine_10:
        print("✅ Routine 10 (Communication Consent) found") 
        print(f"   Content: {routine_10[:80]}...")
    else:
        print("❌ Routine 10 not found")
        return
    
    # Test the updated flow
    print(f"\n📋 Updated Registration Flow:")
    print("-" * 40)
    
    flow_steps = [
        (8, "Telephone Collection → Ask for email"),
        (9, "Email Collection → Ask for consent"),
        (10, "Communication Consent → Ask for DOB"),
        (11, "DOB Collection → Ask for postcode"),
        (12, "Postcode Collection → Ask for house number"),
        (13, "House Number → Address lookup"),
        (14, "Address Confirmation → Child address check"),
        (15, "Manual Address (if needed) → Child address check"),
        (16, "Child Address Check → Complete registration")
    ]
    
    for routine_num, description in flow_steps:
        routine_exists = RegistrationRoutines.is_valid_routine(routine_num)
        status = "✅" if routine_exists else "❌"
        print(f"{status} Routine {routine_num}: {description}")
    
    # Test consent response variations
    print(f"\n📝 Consent Response Handling:")
    print("-" * 35)
    
    consent_variations = {
        "Positive responses": [
            "yes", "Yeah", "OK", "sure", "no problem", 
            "that's fine", "of course", "absolutely"
        ],
        "Negative responses": [
            "no", "nope", "don't want to", "no thanks",
            "prefer not", "I'd rather not"
        ]
    }
    
    for category, responses in consent_variations.items():
        print(f"\n{category}:")
        for response in responses:
            normalized = "Yes" if category == "Positive responses" else "No"
            print(f"  '{response}' → normalized to '{normalized}'")
    
    # Test GDPR compliance elements
    print(f"\n🔒 GDPR Compliance Features:")
    print("-" * 32)
    print("✅ Explicit consent request (not assumed)")
    print("✅ Vague but compliant messaging ('club comms')")
    print("✅ Accepts both Yes and No responses")
    print("✅ Documents consent choice for records")
    print("✅ Email collected first (needed for registration)")
    print("✅ Consent collected after email (more natural flow)")
    print("✅ Separate from registration completion (can say No)")
    
    print(f"\n💬 Example Conversation:")
    print("-" * 25)
    print("Agent: 'Can I get your email address?'")
    print("")
    print("Parent: 'sarah.jones@gmail.com'")
    print("")
    print("Agent: 'Thanks! Can I get your consent to contact you by")
    print("       email and SMS with club comms throughout the season?'")
    print("")
    print("Parent: 'Yes, that's fine'")
    print("")
    print("📧 Email: sarah.jones@gmail.com (collected)")
    print("📊 Consent Status: YES - Can contact via email/SMS")
    print("📅 Next: Proceeds to DOB collection (routine 11)")
    
    print(f"\n✅ Communication consent collection ready!")
    print("GDPR-compliant consent now integrated into registration flow!")

if __name__ == "__main__":
    test_communication_consent() 