# **SMS Integration Implementation Plan**

## **Phase 2: SMS Payment Link Implementation**

### **Architecture Decision: Async SMS Sending**
```
Routine 29 Flow (Updated):
Registration Complete → create_payment_token → [PARALLEL EXECUTION]
                                             ├── update_reg_details_to_db (sequential)
                                             └── send_sms_payment_link (async/parallel)
```

**Benefits:**
- No chat delay waiting for SMS delivery
- Database write completes immediately
- SMS delivery happens in background
- Better user experience

### **Implementation Steps**

#### **Step 1: Environment Setup**
- Add Twilio credentials to `.env` files
- Install `twilio` Python package
- Set up ngrok tunnel for local testing

```bash
# .env additions
TWILIO_ACCOUNT_SID=your_live_account_sid
TWILIO_AUTH_TOKEN=your_live_auth_token  
TWILIO_PHONE_NUMBER=your_twilio_number
PAYMENT_BASE_URL=https://your-ngrok-url.ngrok.io  # For testing
```

#### **Step 2: Create SMS Tool**
- **File**: `send_sms_payment_link_tool.py`
- **Function**: Async SMS sending with UK number formatting
- **Features**:
  - UK phone number formatting (`+44` conversion)
  - SMS delivery logging to database
  - Error handling and retry logic
  - Twilio client integration

#### **Step 3: Create Payment Endpoint** 
- **Route**: `/reg_setup/{billing_request_id}` in `server.py`
- **Function**: Lookup registration → generate fresh GoCardless payment URL → redirect
- **Testing**: Accessible via ngrok tunnel

#### **Step 4: Modify Routine 29 for Parallel Execution**
- Update registration routine to call SMS tool in parallel with database update
- Ensure both tools receive the `billing_request_id` from `create_payment_token`

#### **Step 5: Database Schema Updates**
Add SMS tracking fields to registration table:
```sql
sms_sent_at TIMESTAMP,
sms_delivery_status VARCHAR(50),  -- 'sent', 'delivered', 'failed', 'pending'
sms_delivery_error TEXT
```

### **Technical Implementation Details**

#### **SMS Tool Structure**
```python
class SendSMSPaymentLinkInput(BaseModel):
    billing_request_id: str
    parent_phone: str
    child_name: str
    
async def send_sms_payment_link(input_data):
    # 1. Format UK phone number for Twilio
    # 2. Generate payment link URL
    # 3. Send SMS via Twilio
    # 4. Log delivery status to database (async)
    # 5. Handle errors gracefully
```

#### **Payment Endpoint Structure**
```python
@app.get("/reg_setup/{billing_request_id}")
async def handle_payment_link(billing_request_id: str):
    # 1. Lookup registration by billing_request_id
    # 2. Check if already paid
    # 3. Generate fresh GoCardless payment URL
    # 4. Redirect to GoCardless
```

#### **Phone Number Formatting**
```python
def format_uk_phone_for_twilio(phone: str) -> str:
    # Remove spaces, dashes, etc.
    # Convert 07xxx to +447xxx
    # Validate UK mobile format
    # Return Twilio-ready format
```

### **Testing Strategy**

#### **Local Testing Setup**
1. **ngrok tunnel**: `ngrok http 8000`
2. **Test URL**: `https://abc123.ngrok.io/reg_setup/{billing_request_id}`
3. **SMS Testing**: Your live Twilio account → your phone number
4. **GoCardless**: Live environment with £1 test amounts

#### **Test Scenarios**
1. Complete registration flow with "lah" cheat code
2. Receive SMS with ngrok payment link
3. Click SMS link → redirected to GoCardless live payment page
4. Verify database logging of SMS delivery
5. Test error scenarios (invalid phone, SMS failures)
6. Test actual £1 payment completion via GoCardless live

### **Deployment Considerations (Future)**
- **Production Domain**: `http://urmstontownjfc.co.uk/reg_setup/{billing_request_id}`
- **Hostinger Integration**: Reverse proxy from Hostinger to your backend
- **SSL**: Ensure HTTPS for payment security

### **Risk Mitigation**
- **SMS Failures**: Log errors, implement retry mechanism
- **Phone Format Issues**: Comprehensive UK number validation
- **Payment Link Security**: Validate billing_request_id exists before redirect
- **Rate Limiting**: Monitor Twilio usage and costs
- **Live GoCardless**: £1 amounts minimize testing costs

---

## **Implementation Checklist**

- [ ] **Step 1**: Add Twilio env vars and install package
- [ ] **Step 2**: Create `send_sms_payment_link_tool.py`
- [ ] **Step 3**: Create `/reg_setup/{billing_request_id}` endpoint
- [ ] **Step 4**: Modify routine 29 for parallel SMS sending
- [ ] **Step 5**: Add SMS tracking fields to database
- [ ] **Step 6**: Set up ngrok tunnel for testing
- [ ] **Step 7**: End-to-end testing with live Twilio + live GoCardless

---

## **SMS Template**
```
"Registration complete for {child_name}! Pay when convenient: https://your-ngrok-url.ngrok.io/reg_setup/{billing_request_id} Registration not complete until payment made."
```

**Production Template:**
```
"Registration complete for {child_name}! Pay when convenient: http://urmstontownjfc.co.uk/reg_setup/{billing_request_id} Registration not complete until payment made."
```

---

**Final Confirmation:**

1. **Endpoint**: `/reg_setup/{billing_request_id}` ✅
2. **GoCardless**: Live environment with £1 amounts ✅ 
3. **SMS**: Parallel execution with database logging ✅
4. **Testing**: ngrok tunnel + live Twilio + live GoCardless ✅

**Ready to proceed with implementation once Twilio credentials are provided.** 