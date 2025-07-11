# Test Scripts Directory

This directory contains organized test scripts for the UTJFC Registration Agent project.

## Directory Structure

```
test_scripts/
├── integration/        # Integration tests for CI/CD pipeline
├── utilities/         # Maintenance and utility scripts
├── archive/          # Archived/deprecated test scripts
└── README.md         # This file
```

## Integration Tests (`/integration/`)

**Purpose**: High-value integration tests suitable for CI/CD pipeline

### `test_photo_upload.py` ⭐ **PRIORITY**
- **Purpose**: Comprehensive test of photo upload flow (routine 34)
- **Tests**: API endpoints, S3 upload, async processing, polling mechanism
- **Dependencies**: `requests`, `pillow`, AWS CLI with `footballclub` profile
- **Usage**: 
  ```bash
  # Standard test (API + timer logic simulation)
  python test_photo_upload.py
  
  # With browser UI validation (experimental)
  python test_photo_upload.py --browser
  ```
- **CI/CD**: Essential for automated testing
- **Notes**: Tests critical production feature with real endpoints

#### What it validates:
- ✅ Async upload endpoint (`/upload-async`)
- ✅ Immediate response with processing flag
- ✅ Polling workflow (`/upload-status/{session_id}`)
- ✅ Timer logic simulation (validates timing/duration)
- ✅ Final success response
- ✅ S3 photo upload verification
- ✅ Automatic cleanup of test photos
- 🧪 Browser UI validation (experimental)

#### Expected Output:
```
=== UTJFC Photo Upload Test Suite ===
✅ Verify test image exists PASSED
✅ Test async upload endpoint PASSED  
✅ Test polling workflow PASSED
✅ Test frontend timer logic PASSED
✅ Verify S3 upload PASSED
🎉 ALL TESTS PASSED! Async photo upload is working correctly.
Results: 17/17 tests passed

📊 Timer Logic Validation:
- Timer starts: 0.9s after upload
- Timer duration: 9.4 seconds total
- Timer shows: 0.0s → 3.1s → 6.2s → 9.3s → stops
✅ Timer duration is reasonable for user to see
```

#### Timer Behavior (Frontend UI):
When testing in the browser, you should see:
1. **Immediate response**: "📸 Photo received! Processing your registration..." with typing animation
2. **Timer appears**: Shows elapsed time (X.Xs) immediately after typing completes
3. **Timer continues**: Keeps running throughout entire polling phase (13+ seconds)
4. **Processing indicator**: Shows "Processing..." alongside timer
5. **Timer stops**: When final success message appears

### `test_backend_mcp_flow.py` ⚠️ **UPDATE NEEDED**
- **Purpose**: Tests backend to MCP server integration
- **Tests**: OpenAI Responses API with MCP protocol
- **Dependencies**: `requests`, backend with `USE_MCP=true`
- **Usage**: `python test_backend_mcp_flow.py`
- **Issues**: Hardcoded expected values, needs configuration flexibility
- **Recommendations**: 
  - Add environment variable support for MCP_SERVER_URL
  - Make expected player count configurable
  - Add error handling for MCP server unavailability

### `test_photo.jpg`
- **Purpose**: Test image file for photo upload tests
- **Format**: JPEG image suitable for registration photo testing
- **Size**: Optimized for mobile upload simulation

## Utilities (`/utilities/`)

**Purpose**: Maintenance and operational scripts

### `cleanup_test_photos.py`
- **Purpose**: Removes test photos from S3 bucket to manage costs
- **Dependencies**: AWS CLI with `footballclub` profile
- **Usage**: 
  ```bash
  # List all photos
  python cleanup_test_photos.py
  
  # Delete photos matching pattern
  python cleanup_test_photos.py test
  python cleanup_test_photos.py "specific_filename"
  ```
- **Safety Features**:
  - Shows all files before deletion
  - Requires confirmation (y/N)
  - Only deletes files matching your pattern
  - Safe interactive deletion process
- **Schedule**: Run periodically to maintain S3 bucket hygiene

## Archive (`/archive/`)

**Purpose**: Deprecated test scripts kept for reference

### `test_minimal_mcp.py`
- **Status**: Archived - Development/debugging tool only
- **Purpose**: Direct OpenAI Responses API test with MCP
- **Issues**: Uses deprecated "gpt-4.1" model, hardcoded URLs
- **Note**: Useful for MCP protocol debugging but not production testing

### `test_mcp_id_handling.py`
- **Status**: Archived - Protocol-level testing
- **Purpose**: Tests MCP JSON-RPC ID handling
- **Note**: Only relevant for MCP server development

### `test_mcp_session_header.py`
- **Status**: Archived - Protocol-level testing
- **Purpose**: Tests MCP session headers and DELETE endpoints
- **Note**: Low-level protocol testing for MCP development

## Running Tests

### Prerequisites
```bash
# Install dependencies
pip install requests pillow

# Configure AWS CLI (for photo upload tests)
aws configure --profile footballclub

# Ensure backend is running (for integration tests)
cd backend && source .venv/bin/activate && uvicorn server:app --reload --port 8000
```

### Individual Test Execution
```bash
# Photo upload integration test
cd test_scripts/integration
python test_photo_upload.py

# MCP flow integration test (requires MCP enabled)
cd test_scripts/integration
python test_backend_mcp_flow.py

# Cleanup utility
cd test_scripts/utilities
python cleanup_test_photos.py
```

### CI/CD Pipeline Integration

**Recommended GitHub Actions workflow:**

```yaml
name: Integration Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          pip install requests pillow
          
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: eu-north-1
          
      - name: Run photo upload integration test
        run: |
          cd test_scripts/integration
          python test_photo_upload.py
          
      - name: Run MCP integration test
        if: env.USE_MCP == 'true'
        run: |
          cd test_scripts/integration
          python test_backend_mcp_flow.py
```

## Test Environment Configuration

### Environment Variables
```bash
# Backend configuration
BACKEND_URL=http://localhost:8000  # Local development
BACKEND_URL=https://d1ahgtos8kkd8y.cloudfront.net  # Production

# MCP configuration
MCP_SERVER_URL=https://utjfc-mcp-server.replit.app/mcp
USE_MCP=true

# AWS configuration
AWS_PROFILE=footballclub
AWS_REGION=eu-north-1
S3_BUCKET_NAME=utjfc-player-photos
```

### Test Data Management
- **Photo uploads**: Test photos are automatically cleaned up
- **Registration data**: Tests use dedicated test session IDs
- **S3 storage**: Regular cleanup prevents cost accumulation

## Best Practices

### For CI/CD Pipeline
1. **Focus on integration tests** - Test complete user flows
2. **Use environment variables** - Make tests configurable
3. **Clean up test data** - Prevent resource accumulation
4. **Test real endpoints** - Verify production connectivity
5. **Handle failures gracefully** - Provide meaningful error messages

### For Development
1. **Test locally first** - Verify tests work before CI/CD
2. **Use separate test data** - Avoid contaminating production data
3. **Document test scenarios** - Explain what each test validates
4. **Keep tests fast** - Optimize for quick feedback cycles

## Future Enhancements

### Planned Improvements
1. **Environment detection** - Automatic local vs production configuration
2. **Parallel test execution** - Speed up test suite
3. **Test reporting** - Generate test reports and metrics
4. **Mock services** - Add local testing without external dependencies
5. **Performance testing** - Add load and stress testing capabilities

### Integration with CI/CD
- **Automated cleanup** - Schedule regular S3 cleanup
- **Test metrics** - Track test success rates and performance
- **Failure notifications** - Alert on test failures
- **Deployment gates** - Block deployments on test failures

This organized structure supports both current development needs and future CI/CD pipeline implementation.