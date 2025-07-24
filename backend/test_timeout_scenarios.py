"""
Test endpoints for simulating timeout scenarios.
Add these to server.py temporarily for testing the retry mechanism.
"""

import asyncio
import time
from fastapi import Request, Body
from fastapi.responses import JSONResponse

# Track attempts per session for testing retry behavior
attempt_counter = {}

async def test_timeout(scenario: str, request: dict = Body(...)):
    """
    Test endpoint that simulates various timeout scenarios.
    
    Scenarios:
    - always-timeout: Always times out (tests max retries)
    - succeed-on-retry: Succeeds on 2nd attempt (tests retry success)  
    - flaky-success: Random success/timeout (tests real-world behavior)
    """
    session_id = request.get('session_id', 'default')
    
    if scenario == "always-timeout":
        # Always timeout - sleep longer than CloudFront's 30s limit
        print(f"[TEST] Always timeout scenario - sleeping 35s")
        await asyncio.sleep(35)
        return {"response": "Should never see this"}
    
    elif scenario == "succeed-on-retry":
        # Track attempts and succeed on 2nd attempt
        key = f"{session_id}-{scenario}"
        attempt_counter[key] = attempt_counter.get(key, 0) + 1
        attempt = attempt_counter[key]
        
        print(f"[TEST] Succeed on retry - attempt {attempt}")
        
        if attempt < 2:
            print(f"[TEST] Simulating timeout on attempt {attempt}")
            await asyncio.sleep(35)  # Timeout on first attempt
        else:
            print(f"[TEST] Success on attempt {attempt}!")
            # Reset counter for next test
            attempt_counter[key] = 0
            return {"response": f"Success on retry! (attempt {attempt})"}
    
    elif scenario == "flaky-success":
        # 50/50 chance of success or timeout
        success = int(time.time()) % 2 == 0
        
        if success:
            print(f"[TEST] Flaky success - got lucky!")
            return {"response": "Lucky success!"}
        else:
            print(f"[TEST] Flaky success - timing out")
            await asyncio.sleep(35)
            return {"response": "Timed out"}
    
    elif scenario == "normal":
        # Normal fast response
        print(f"[TEST] Normal fast response")
        return {"response": "Fast response - no timeout"}
    
    return {"response": f"Unknown scenario: {scenario}"}


# Add these routes to server.py for testing:
"""
from test_timeout_scenarios import test_timeout

@app.post("/test-timeout/{scenario}")
async def handle_test_timeout(scenario: str, request: dict = Body(...)):
    return await test_timeout(scenario, request)
"""