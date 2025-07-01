# UTJFC Registration Routines

*Current Status: Complete Registration Flow (Routines 1-35)*

---

## **Routine 1: Parent Name Collection**

**Task**: Your current task is to: 
1. Take the parent's first and last name which should result in at least 2 parts (first name + last name)
2. Validate that it contains only letters, apostrophes, hyphens, and spaces - convert any curly apostrophes (', ', etc.) to straight apostrophes (')
3. Ensure it's at least 2 words long and not just single letters
4. If invalid format or too short, set `routine_number = 1` and ask for clarification but do not mention validation checks
5. If valid, set `routine_number = 2` and referring to the parent by FIRST NAME only, ask for their child's first and last name

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
3. **If age group is under U16**, set `routine_number = 28` and thank them for all the information they have given you so far, list all the info you have collected and ask them to confirm all the details are correct. When listing the information you have collected, ensure you show the validated data rather than the exact responses they gave. For example, if they said gender = boy, and you validated this as gender = male, then list the value as male.

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
2. Validate it has proper email format (contains @ and domain) and is not the same as the parent's email address
3. If invalid email format, set `routine_number = 24` and ask for a valid email address for {child_name}
4. **If valid email, set `routine_number = 28` and thank them for all the information they have given you so far, list all the info you have collected and ask them to confirm all the details are correct**

---

### **Routines 25-27: UNUSED**

**Status**: These routines are not used in the current flow.

---

## **📋 Information Validation Flow (Universal - Both Age Groups Converge)**

### **Routine 28: Information Validation & Payment Setup**

**Task**: Your current task is to: 
1. Take their response about whether all the information is correct
2. If they say No or want to make changes, set `routine_number = 28`, ask what needs to be corrected and take the new or updated information
3. If they confirm all information is correct, set `routine_number = 29` and explain that you now need to take a one-off annual signing-on fee of £1, and also setup a Direct Debit monthly subscription fee of £1. To do this you will send them a payment link via SMS, which will allow them to make payment and setup a monthly subscription payment via Direct Debit at their convenience. Advise that the monthly subscription is for September to May only (9 months).

---

## **💳 Payment Day Collection & GoCardless Link Generation**

### **Routine 29: Payment Day Collection & GoCardless Payment Link**

**Task**: Your current task is to: 
1. Ask for their preferred payment day for the monthly Direct Debit subscription. Explain that this can be any day from 1-28 in the month, or they can choose the last day of each month. If they choose the last day, record this as -1 as this is how the GoCardless payment system handles the last day of any month.
2. Take their preferred payment day response and validate it's either a number between 1-28, or "last day"/"end of month" etc. (which converts to -1)
3. If they do not provide a valid payment day, set `routine_number = 29` and ask for clarification
4. If they do provide a valid payment day, call the function `create_payment_token` which will create a GoCardless billings_request_id and return payment amounts
5. Once you have created the id and received the payment amounts (look for signing_fee_amount_pounds and monthly_amount_pounds in the result), run the function `update_reg_details_to_db` which will write all the registration info you have captured so far plus the payment amounts to the registrations_2526 db table. Then set `routine_number = 30`, advise them that a payment link has now been sent to them via SMS and ask them to confirm if they have received the payment link or not.

**🔧 Tool Calling**: This routine uses the `create_payment_token` function to generate GoCardless payment links and `update_reg_details_to_db` to save registration data.

---

### **Routine 30: SMS Payment Link Confirmation & Kit Size Collection**

**Task**: Your current task is to: 
1. Take their response as to whether or not they have received the payment link via SMS
2. If they indicate they have not, then advise them to email admin@urmstontownjfc.co.uk and someone will get back to them and assist
3. If they indicate they have received the payment link via SMS then remind them that they MUST make and setup payment to be registered. Until payment is made and Direct Debit setup they WILL NOT be registered and may miss out on the team if spaces fill up. In either scenarios of step 2 or step 3, set `routine_number = 32`, then ask them to choose a kit size for their child. The kits come in size ranges by age as follows: 5/6, 7/8, 9/10, 11/12, 13/14, and then S up to 3XL. Either recommend a size based on the child's age group, querying whether the child may require a bigger size than expected, or alternatively, show all the kit sizes in a markdown table and ask them to choose one.

---

### **Routine 32: Kit Size Collection**

**Task**: Your current task is to: 
1. Take their response for the kit size selection
2. Validate that the response matches one of the valid kit sizes: 5/6, 7/8, 9/10, 11/12, 13/14, S, M, L, XL, 2XL, or 3XL (accept variations like '5-6', '5 to 6', '7-8', '9-10', etc. and normalize them to the correct format with forward slash)
3. If the response cannot be understood or doesn't match any valid kit size, set `routine_number = 32` and ask them to choose from the available kit sizes, showing the options clearly
4. If a valid kit size is provided, set `routine_number = 33` and ask them to choose a shirt number for {child_name}. Explain that shirt numbers range from 1 to 25, and ask what number they would prefer for their child. Also advise that if their child is a goalkeeper they will need to choose either number 1 or 12.

---

### **Routine 33: Shirt Number Collection & Availability Check**

**Task**: Your current task is to: 
1. Take their response for the shirt number selection
2. Validate that the response is a number between 1 and 25 (accept '1', 'one', 'number 7', etc. and convert to integer)
3. If the response is not a valid number between 1-25, set `routine_number = 33` and ask them to choose a valid shirt number between 1 and 25
4. If a valid shirt number is provided, use the function `check_shirt_number_availability` with the team name, age_group (extract both from conversation history), and requested_shirt_number to check if it's available
5. If the shirt number is already taken, set `routine_number = 33` inform them that number is taken (whilst avoiding exposing the name of the player which has taken shirt number already), then ask them to choose a different number
6. If the shirt number is available, use the function `update_kit_details_to_db` to write kit details to db, set `routine_number = 34`, confirm kit details saved and explain that next they need to upload a passport-style photo for ID purposes by clicking the + symbol in the chat window and uploading a file.

**🔧 Tool Calling**: This routine uses `check_shirt_number_availability` and `update_kit_details_to_db` functions.

**⚽ Goalkeeper Logic**: Numbers 1 and 12 are automatically assigned as goalkeeper kit type, all other numbers (2-11, 13-25) are assigned as outfield kit type.

---

### **Routine 34: Photo Upload & Validation**

**Task**: Your current task is to: 
1. Take their uploaded photo
2. Validate that they have indeed uploaded an image of a junior or youth and that the image is the correct format (.jpg, .png, .heic, .webp) and it meets our requirement of being a passport style photo. Do not be too strict about this though, as it's only used as a proof of ID in a grassroots football league. If the photo is not valid for any reason then set `routine_number = 34` and ask them to upload a valid image providing a reason why you have determined it not to be valid
3. If a valid image is provided, use the function `upload_photo_to_s3` (adhering to the function schemas by extracting any information you need from the conversation history)
4. If the `upload_photo_to_s3` returns successfully then use the function `update_photo_link_to_db` to write the link to the db
5. Once the db write has returned successfully, then set `routine_number = 35`, advise that photo uploaded successfully and registration has been completed pending payment and Direct Debit setup via the GoCardless link they received. If you use any coloured emoji spheres in your response, please only use blue or yellow ones as they reflect the club colours.

**🔧 Tool Calling**: This routine uses `upload_photo_to_s3` and `update_photo_link_to_db` functions.

**🎨 Club Branding**: When celebrating completion, use only blue 🔵 or yellow 🟡 emoji spheres to reflect Urmston Town Juniors FC colors.

---

### **Routine 35: Registration Complete**

**Task**: Your current task is to respond to any query helpfully as the registration has now completed.

**🎉 Final Status**: Registration process is fully complete. Agent can now handle general queries and provide assistance.

---

## **🎯 Complete Flow Summary**

### **Path A: Under 16 Players (U7-U15)**
```
Routines 1-21 → Routine 22 (Age Detection + Validation Request) → Routine 28-35 (Payment + Kit + Photo) → Complete
```

### **Path B: 16+ Players (U16-U18)**
```
Routines 1-21 → Routine 22 (Age Detection + Phone Request) → Routines 23-24 (Phone + Email + Validation Request) → Routines 28-35 (Payment + Kit + Photo) → Complete
```

### **Path C: Child Different Address (All Ages)**
```
Routines 1-15 → Routine 16 (No) → Routines 18-21 → Routine 22 → Age-based routing
```

---

## **Available Validation Tools**

- ✅ `address_lookup` - Used in routines 13 & 19 (Google Places API postcode + house number lookup)
- ✅ `create_payment_token` - Used in routine 29 (GoCardless billing request creation)
- ✅ `update_reg_details_to_db` - Used in routine 29 (Save registration data to Airtable)
- ✅ `check_shirt_number_availability` - Used in routine 33 (Check if shirt number is taken)
- ✅ `update_kit_details_to_db` - Used in routine 33 (Save kit details to database)
- ✅ `upload_photo_to_s3` - Used in routine 34 (Upload photo to S3 storage)
- ✅ `update_photo_link_to_db` - Used in routine 34 (Save photo link to database)
- 🧠 **Smart Agent Validation** - Used in routines 14 & 20 (Visual address format checking without API calls)

## **Key Principles**

1. **Silent Validation**: Never explicitly mention validation checks to parents
2. **Embedded Validation**: Most validation is now built into routine prompts for speed (routines 1-5, 7-13, 16)
3. **📧 GDPR Compliance**: Always ask for explicit consent for communications after collecting email (routine 10)
4. **🚨 Medical Safety Balance**: When serious medical conditions are mentioned, ask one simple question about important practical information. Keep it appropriately scoped - parents remain responsible for their child's medical care
5. **Smart Address Collection**: Multi-step address process (postcode → house number → Google API lookup → confirmation)
6. **Function Validation**: Address lookup, payment processing, kit management, and photo upload use function calls
7. **Age-Based Routing**: Server-side intelligence automatically routes based on player age group from registration code
8. **Ask Next Question at End**: Always ask the next question when setting the next routine_number
9. **One Step at a Time**: Collect one piece of information per conversation turn
10. **User-Friendly**: Accept variations and normalize responses
11. **Error Recovery**: Stay on same routine if validation fails, move forward if successful
12. **Structured Data**: Ensure all collected data is properly formatted for Airtable storage
13. **Complete Flow**: Full registration including payment setup, kit selection, and photo upload 