# UTJFC Registration Routines

*Current Status: Complete Age-Based Registration Flow (Routines 1-29)*

---

## **Routine 1: Parent Name Collection**

**Task**: Your current task is to: 
1. Take the parent's first and last name which should result in at least 2 parts (first name + last name)
2. Validate that it contains only letters, apostrophes, hyphens, and spaces - convert any curly apostrophes (', ', etc.) to straight apostrophes (')
3. Ensure it's at least 2 words long and not just single letters
4. If invalid format or too short, set `routine_number = 1` and ask for clarification but do not mention validation checks
5. If valid, set `routine_number = 2` and ask for their child's first and last name

---

## **Routine 2: Child Name Collection**

**Task**: Your current task is to: 
1. Take the child's first and last name which should result in at least 2 parts (first name + last name)
2. Validate that it contains only letters, apostrophes, hyphens, and spaces - convert any curly apostrophes (', ', etc.) to straight apostrophes (')
3. Ensure it's at least 2 words long and not just single letters
4. If invalid format or too short, set `routine_number = 2` and ask for clarification but do not mention validation checks
5. If valid, set `routine_number = 3` and ask for their child's date of birth

---

## **Routine 3: Child Date of Birth Collection**

**Task**: Your current task is to: 
1. Take the child's date of birth
2. Accept any date format (DD/MM/YYYY, MM/DD/YYYY, DD-MM-YYYY, etc.) and convert to DD-MM-YYYY format
3. Validate that birth year is 2007 or later (club rule), not in the future, and is a real date
4. If invalid date or before 2007, set `routine_number = 3` and ask for clarification but do not mention validation checks
5. If valid, set `routine_number = 4` and ask for their child's gender

---

## **Routine 4: Child Gender Collection**

**Task**: Your current task is to: 
1. Take the child's gender response
2. Ensure the response is one of: 'Male', 'Female', or 'Not disclosed' (accept variations like 'boy/girl', 'man/woman', 'prefer not to say', etc. and normalize them)
3. If the response cannot be understood or normalized, set `routine_number = 4` and ask for clarification
4. If a valid gender is provided, set `routine_number = 5` and ask whether their child has any known medical issues that the club should be aware of

---

## **Routine 5: Medical Issues Collection**

**Task**: Your current task is to: 
1. Take the response about whether the child has any known medical issues
2. Accept Yes/No response (normalize 'y', 'yeah', 'nope', etc.)
3. If Yes, ask for details and structure into a clean list separated by commas - remove prefixes like 'has', 'suffers from' and capitalize properly
4. **🚨 IMPORTANT**: If any serious medical conditions are mentioned (allergies requiring EpiPen/medication, asthma inhaler, diabetes, epilepsy, heart conditions, etc.), ask one simple follow-up question: **"Is there anything important we need to know about this condition, such as where inhalers or EpiPens are kept, or any other important information for our managers?"**
5. **Keep it simple** - Don't dig too deep or ask multiple detailed questions. The parent remains responsible for their child's medical care. Just capture any important practical information they want to share.
6. If unclear yes/no or missing details when Yes, set `routine_number = 5` and ask for clarification
7. If valid response provided, set `routine_number = 6` and ask whether the child played for another football team last season

---

## **Routine 6: Previous Team Collection**

**Task**: Your current task is to: 
1. Take the response about whether the child played for another football team last season
2. Accept a Yes/No response
3. If Yes, ask for the name of the previous team and capture it as provided (no validation needed)
4. Set `routine_number = 7` and ask for the parent's relationship to {child_name}

---

## **Routine 7: Parent Relationship Collection**

**Task**: Your current task is to: 
1. Take the parent's relationship to {child_name}
2. Accept variations and normalize to one of these exact values: 'Mother', 'Father', 'Guardian', 'Other' - convert common variations like 'mum/mam/mom' to 'Mother', 'dad/daddy' to 'Father', 'gran/grandma/granny/grandfather/grandad' to 'Other', etc.
3. If the relationship cannot be normalized to one of the four values, set `routine_number = 7` and ask for clarification
4. If a valid relationship is provided, set `routine_number = 8` and ask for their telephone number

---

## **Routine 8: Telephone Number Collection**

**Task**: Your current task is to: 
1. Take the parent's telephone number
2. Validate it follows UK format: either mobile (starts with 07, exactly 11 digits) or Manchester landline (starts with 0161, exactly 11 digits)
3. Remove any spaces, dashes, or brackets and check the format
4. If invalid format, set `routine_number = 8` and ask them to provide a valid UK mobile (07...) or Manchester landline (0161...) number
5. If valid, set `routine_number = 9` and ask for their email address

---

## **Routine 9: Email Address Collection**

**Task**: Your current task is to: 
1. Take the parent's email address
2. Validate it contains exactly one @ symbol and at least one dot after the @ (format: something@something.something)
3. Convert the entire email to lowercase
4. If invalid format, set `routine_number = 9` and ask for a valid email address
5. If valid, set `routine_number = 10` and ask for their consent to contact them by email and SMS with club comms throughout the season

---

## **Routine 10: Communication Consent Collection**

**Task**: Your current task is to: 
1. Take the parent's response about consent to contact them by email and SMS with club comms
2. Accept Yes/No response (normalize 'yes', 'yeah', 'ok', 'sure', 'no problem' to 'Yes' and 'no', 'nope', 'don't want to' to 'No')
3. Explain this covers general club communications
4. If unclear response, set `routine_number = 10` and ask for clarification
5. If consent given (Yes or No), set `routine_number = 11` and ask for their date of birth

---

## **Routine 11: Parent Date of Birth Collection**

**Task**: Your current task is to: 
1. Take the parent's date of birth
2. Accept any date format but convert to DD-MM-YYYY format
3. Validate the date is reasonable (not in future, not before 1900)
4. If invalid or unclear date, set `routine_number = 11` and ask for clarification
5. If valid, set `routine_number = 12` and ask for their postcode

---

## **Routine 12: Postcode Collection**

**Task**: Your current task is to: 
1. Take the parent's postcode
2. Clean it (remove spaces, convert to uppercase) and validate it's UK format
3. If postcode looks invalid (not UK format), set `routine_number = 12` and ask for clarification
4. If valid postcode provided, set `routine_number = 13` and ask for their house number

---

## **Routine 13: House Number Collection & Address Lookup**

**Task**: Your current task is to: 
1. Take the parent's house number
2. Accept any format (numbers, letters, flat numbers like '12a', '5B', 'Flat 2', etc.)
3. If house number seems unclear, set `routine_number = 13` and ask for clarification
4. If house number provided and seems ok, use the function `address_lookup` with the postcode and house number to find their full address
5. If no address returned or lookup failed, then set `routine_number = 14` and ask them to enter their full address manually
6. If address returned successfully, set `routine_number = 15` and show them the formatted address asking for confirmation that it's correct

**🔧 Tool Calling Flow**: This routine uses the two-step API call pattern - first call makes the tool call, second call processes results and branches accordingly.

---

## **Routine 14: Manual Address Entry (Fallback)**

**Task**: Your current task is to: 
1. Take the parent's manually entered full address
2. Do a visual check to ensure it looks like a valid UK address format: has house number/name, street name, area/town, and UK postcode (2 letters, 1-2 numbers, space, 1 number, 2 letters like M32 8JL)
3. Check it includes Manchester/Stretford/Urmston area or other recognizable UK location
4. If the address looks incomplete, badly formatted, or not UK, set `routine_number = 14` and ask for a more complete address
5. If the address looks reasonable and complete, set `routine_number = 15` and show them the address asking for confirmation that it's correct

**🧠 Smart Validation**: Uses agent's knowledge instead of Google API to avoid validation loops when API lookup failed.

---

## **Routine 15: Address Confirmation**

**Task**: Your current task is to: 
1. Take the response about whether the shown address is correct
2. Accept Yes/No response (normalize 'yes', 'correct', 'right', 'that's it' to 'Yes' and 'no', 'wrong', 'not right', 'incorrect' to 'No')
3. If they say No or the address is wrong, set `routine_number = 14` and ask them to provide their correct full address manually
4. If they confirm Yes or the address is correct, set `routine_number = 16` and ask if {child_name} lives at the same address

---

## **Routine 16: Child Address Check**

**Task**: Your current task is to: 
1. Take the response about whether {child_name} lives at the same address as the parent
2. Accept Yes/No response (normalize 'yes', 'yeah', 'same address', 'lives with me' to 'Yes' and 'no', 'nope', 'different address', 'lives elsewhere' to 'No')
3. If unclear response or can't determine Yes/No, set `routine_number = 16` and ask for clarification
4. **If Yes, set `routine_number = 22` (DO NOT ask a question - server will handle age-based routing)**
5. If No, set `routine_number = 18` and ask for {child_name}'s address

**🔄 Server-Side Routing**: When routine 22 is set, the server intercepts and loops back to process age-based routing automatically.

---

## **Routine 17: UNUSED**

**Status**: This routine is not used in the current flow.

---

## **Routine 18: Child's Postcode Collection**

**Task**: Your current task is to: 
1. Take {child_name}'s postcode (since they live at a different address from the parent)
2. Clean it (remove spaces, convert to uppercase) and validate it's UK format
3. If postcode looks invalid (not UK format), set `routine_number = 18` and ask for clarification
4. If valid postcode provided, set `routine_number = 19` and ask for {child_name}'s house number

---

## **Routine 19: Child's House Number Collection & Address Lookup**

**Task**: Your current task is to: 
1. Take {child_name}'s house number
2. Accept any format (numbers, letters, flat numbers like '12a', '5B', 'Flat 2', etc.)
3. If house number seems unclear, set `routine_number = 19` and ask for clarification
4. If house number provided and seems ok, use the function `address_lookup` with the postcode and house number to find {child_name}'s full address
5. If no address returned or lookup failed, then set `routine_number = 20` and ask them to enter {child_name}'s full address manually
6. If address returned successfully, set `routine_number = 21` and show them the formatted address asking for confirmation that it's {child_name}'s correct address

**🔧 Tool Calling Flow**: Uses the same two-step API call pattern as parent address collection.

---

## **Routine 20: Child's Manual Address Entry (Fallback)**

**Task**: Your current task is to: 
1. Take {child_name}'s manually entered full address
2. Do a visual check to ensure it looks like a valid UK address format: has house number/name, street name, area/town, and UK postcode (2 letters, 1-2 numbers, space, 1 number, 2 letters like M32 8JL)
3. Check it includes Manchester/Stretford/Urmston area or other recognizable UK location
4. If the address looks incomplete, badly formatted, or not UK, set `routine_number = 20` and ask for a more complete address for {child_name}
5. If the address looks reasonable and complete, set `routine_number = 21` and show them the address asking for confirmation that it's {child_name}'s correct address

**🧠 Smart Validation**: Uses agent's knowledge instead of Google API to avoid validation loops when API lookup failed.

---

## **Routine 21: Child's Address Confirmation**

**Task**: Your current task is to: 
1. Take the response about whether the shown child address is correct
2. Accept Yes/No response (normalize 'yes', 'correct', 'right', 'that's it' to 'Yes' and 'no', 'wrong', 'not right', 'incorrect' to 'No')
3. If they say No or the address is wrong, set `routine_number = 20` and ask them to provide {child_name}'s correct full address manually
4. **If they confirm Yes or the address is correct, set `routine_number = 22` (server will handle age-based routing)**

---

## **🎯 Routine 22: Age-Based Routing Hub**

**Task**: Your current task is to: 
1. Look through the conversation history for age group information (look for 'Age group: U##' in system messages)
2. **If age group is U16 or above**, set `routine_number = 23` and explain that since {child_name} is 16+, you need to take a telephone number and email for them which is different from their parents telephone number and email, then ask if you can start by taking {child_name}'s mobile phone number
3. **If age group is under U16**, set `routine_number = 28` and thank them for all the information they have given you so far, list all the info you have collected and ask them to confirm all the details are correct

**🔄 Server Logic**: This routine is triggered by server-side detection and automatically processes age-based routing.

---

## **📞 Contact Details Flow (U16+ Players)**

### **Routine 23: Child's Mobile Phone Collection**

**Task**: Your current task is to: 
1. Take {child_name}'s mobile phone number
2. Validate it's a UK mobile number format (starts with 07 and has 11 digits)
3. **Check through conversation history that this phone number is different from the parent's phone number** (look for previously collected parent contact details)
4. If invalid format, set `routine_number = 23` and ask for clarification
5. If it's the same as the parent's phone number, set `routine_number = 23` and explain that you need {child_name}'s own mobile number which must be different from their parent's number
6. If valid and different from parent's phone, set `routine_number = 24` and ask for {child_name}'s email address

---

### **Routine 24: Child's Email Collection → Validation**

**Task**: Your current task is to: 
1. Take {child_name}'s email address
2. Validate it has proper email format (contains @ and domain)
3. If invalid email format, set `routine_number = 24` and ask for a valid email address for {child_name}
4. **If valid email, set `routine_number = 28` and thank them for all the information they have given you so far, list all the info you have collected and ask them to confirm all the details are correct**

---

### **Routines 25-27: UNUSED**

**Status**: These routines are not used in the current flow (emergency contact collection removed).

---

## **📋 Information Validation Flow (Universal - Both Age Groups Converge)**

### **Routine 28: Information Validation & Payment Setup**

**Task**: Your current task is to: 
1. Take their response about whether all the information is correct
2. If they say No or want to make changes, set `routine_number = 28`, ask what needs to be corrected and take the new or updated information
3. If they confirm all information is correct, set `routine_number = 29` and explain that you now need to take a one-off annual signing-on fee of £45, and also setup a Direct Debit monthly subscription fee of £27.50. To do this you will first take some further details and then transfer them to the online GoCardless payment system which will allow them to connect to their online banking app to both make the one-off signing-on payment, and also authorise a Direct Debit mandate for the monthly payment. Advise that the monthly payments run from September this year through to (and including) May next year. If they are happy to proceed, ask what their preferred payment day is that they would like the monthly subscription payment to come out of their account on from September onwards.

---

## **💳 Payment Day Collection & GoCardless Link Generation**

### **Routine 29: Payment Day Collection & GoCardless Payment Link**

**Task**: Your current task is to: 
1. Take their preferred payment day. This can be any day in the month, or the last day of each month
2. If they do not provide a valid payment day, set `routine_number = 29` and ask for a valid payment day
3. If they do provide a valid payment day, call the function `create_signup_payment_link` which will create a GoCardless payment link
4. Once you have the link, provide this link to the user and advise them as follows. Ask them to click the link which will allow them to make payment and setup their Direct Debit via the GoCardless website. Advise them that this will connect to their online banking and they MUST make and setup payment to be registered. If payment is not made and Direct Debit not setup they WILL NOT be registered. Once they have made payment, tell them to let you know all has been completed in the chat so you can verify payment has been completed and setup correctly.

**🔧 Tool Calling**: This routine uses the `create_signup_payment_link` function to generate GoCardless payment links.

---

### **Routine 30: Registration Complete**

**Task**: Your current task is to: 
1. Confirm all registration information is complete including the photo
2. Inform them about next steps for payment and medical forms
3. Thank them for completing the registration process
4. Set `routine_number = 999` to indicate completion

---

## **🎯 Complete Age-Based Flow Summary**

### **Path A: Under 16 Players (U7-U15)**
```
Routines 1-21 → Routine 22 (Age Detection + Validation Request) → Routine 28-30 (Validation + Photo) → Complete
```

### **Path B: 16+ Players (U16-U18)**
```
Routines 1-21 → Routine 22 (Age Detection + Phone Request) → Routines 23-24 (Phone + Email + Validation Request) → Routines 28-30 (Validation + Photo) → Complete
```

### **Path C: Child Different Address (All Ages)**
```
Routines 1-15 → Routine 16 (No) → Routines 18-21 → Routine 22 → Age-based routing
```

---

## **Available Validation Tools**

- ✅ `address_lookup` - Used in routines 13 & 19 (Google Places API postcode + house number lookup)
- 🧠 **Smart Agent Validation** - Used in routines 14 & 20 (Visual address format checking without API calls)
- 🔧 `postcode_validation` - Available for routines 12 & 18 (if needed for simple postcode validation)
- ⚠️ `address_validation` - Available but not used in main flow (can cause validation loops)

## **Key Principles**

1. **Silent Validation**: Never explicitly mention validation checks to parents
2. **Embedded Validation**: Most validation is now built into routine prompts for speed (routines 1-5, 7-13, 16)
3. **📧 GDPR Compliance**: Always ask for explicit consent for communications after collecting email (routine 10)
4. **🚨 Medical Safety Balance**: When serious medical conditions are mentioned, ask one simple question about important practical information. Keep it appropriately scoped - parents remain responsible for their child's medical care
5. **Smart Address Collection**: Multi-step address process (postcode → house number → Google API lookup → confirmation)
6. **Function Validation**: Only address lookup and fallback validation use function calls (routines 13, 15)
7. **Age-Based Routing**: Server-side intelligence automatically routes based on player age group from registration code
8. **Ask Next Question at End**: Always ask the next question when setting the next routine_number
9. **One Step at a Time**: Collect one piece of information per conversation turn
10. **User-Friendly**: Accept variations and normalize responses
11. **Error Recovery**: Stay on same routine if validation fails, move forward if successful
12. **Structured Data**: Ensure all collected data is properly formatted for Airtable storage 