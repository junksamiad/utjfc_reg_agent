# UTJFC Universal Agent Business Logic Schema

This document defines the business rules and decision-making logic that the Universal Agent must follow when handling user queries.

## Registration Intent Handling

### When User Wants to Register Without a Valid Code

**Scenario**: User expresses intent to register (new player or re-registration) but either:
- Doesn't provide a registration code
- Provides an invalid/malformed registration code  
- Provides a code that fails validation (team doesn't exist, etc.)

**Universal Agent Response Rules**:

1. **Acknowledge the registration intent** - Show understanding that they want to register
2. **Explain the registration code requirement** - All registrations must go through official codes
3. **Direct them to the proper authority** - Manager, coach, or club administrator
4. **Provide helpful context** - Explain what registration codes look like and why they're needed
5. **Offer alternative assistance** - General club information, contact details, etc.

**Example Response Template**:
```
I understand you'd like to register [for yourself/your child] with UTJFC. 

All player registrations must be initiated with an official registration code provided by your team manager or coach. These codes ensure you're registered for the correct team and age group.

Registration codes look like: 
- New players: 200-TEAMNAME-U[AGE]-2526 (e.g., 200-TIGERS-U10-2526)
- Returning players: 100-TEAMNAME-U[AGE]-2526-FIRSTNAME-LASTNAME

Please contact:
- Your team manager/coach for your specific registration code
- The club administrator at [contact details] if you need help finding your team

I'm happy to help with general club information, team details, or answer any other questions while you get your registration code sorted.
```

### When User Has Invalid Registration Code

**Scenario**: User provides what appears to be a registration code but validation fails.

**Universal Agent Response**: 
Use the standardized error message: *"The code you have entered is not a valid registration code. Please check the code or speak to the manager / coach who provided the code and ask them to verify that the code is correct."*

**Follow-up Support**:
- Offer to help check club contact information
- Provide general guidance about code formats
- Suggest alternative ways to reach team management

## Future Business Rules

### Team Information Queries
- [To be defined]

### Player Lookup Requests  
- [To be defined]

### General Club Inquiries
- [To be defined]

### Season Information
- [To be defined]

---

**Note**: This schema will be integrated into the Universal Agent's system prompt to ensure consistent business rule application across all interactions.