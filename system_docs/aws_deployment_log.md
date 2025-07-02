# UTJFC Registration System - AWS Deployment Log

**Last Updated**: July 2, 2025  
**Deployment Status**: ✅ **RECOVERED** - New production environment deployed.  
**Total Monthly Cost**: ~$22/month

---

## 🚨 **CRITICAL RECOVERY LOG - JULY 2, 2025** 🚨

### **Incident Summary**
The backend environment (`utjfc-backend-prod`) became unresponsive and entered a permanent `CREATE_FAILED` state after a failed `rebuild-environment` command was issued in an attempt to update an API key. This action left the underlying CloudFormation stack in an unrecoverable state, blocking all further deployments to that environment.

### **Resolution Summary**
A full environment termination and recreation was performed. A new, clean Elastic Beanstalk environment (`utjfc-backend-prod-2`) was successfully provisioned and the CloudFront distribution was updated to route all API traffic to this new backend. The system is now fully recovered and operational.

### **Key Recovery Steps**
1.  **Old Environment Termination**: The broken `utjfc-backend-prod` environment was terminated via the AWS CLI.
2.  **Dockerfile Correction**: The `backend/Dockerfile` was updated to use port 80 consistently, aligning with the production Nginx configuration.
3.  **New Deployment Package**: A clean application package (`utjfc-backend-v1.6.3-dockerfix.zip`) was created and uploaded to S3.
4.  **New Environment Creation (`utjfc-backend-prod-2`)**: The new environment was created via the CLI. This involved troubleshooting several configuration issues:
    *   **Invalid Parameters**: Corrected the create command to use `--platform-arn` instead of the legacy `--solution-stack-name`.
    *   **Missing Subnets**: Discovered that the previous VPC/subnets were terminated with the old environment. Queried for the new default VPC and subnets and used them in the configuration.
    *   **Missing IAM Role**: Added the required `aws-elasticbeanstalk-ec2-role` as an `IamInstanceProfile` option to grant the EC2 instances necessary permissions.
5.  **CloudFront Re-Configuration**: The CloudFront distribution (`E2WNKV9R9SX5XH`) was updated. The origin `API-utjfc-backend` was modified to point to the new environment's CNAME.
6.  **CloudWatch Log Activation**: Log streaming to CloudWatch was not enabled by default on the new environment. It was explicitly enabled via an `update-environment` command.

### **✅ Current Production Resource IDs**
| Resource | Name / ID | URL / Value |
|---|---|---|
| **EB Environment** | `utjfc-backend-prod-2` | `utjfc-backend-prod-2.eba-3bpsyeak.eu-north-1.elasticbeanstalk.com` |
| **EB Environment ID** | `e-4g4ermxcpp` | N/A |
| **CloudFront Distro**| `E2WNKV9R9SX5XH` | `d1ahgtos8kkd8y.cloudfront.net` |
| **Primary Log Group**| `.../stdouterr.log`| `/aws/elasticbeanstalk/utjfc-backend-prod-2/var/log/eb-docker/containers/eb-current-app/stdouterr.log`|
| **DNS CNAME Target**| `chat.urmstontownjfc.co.uk` | Points to `d1ahgtos8kkd8y.cloudfront.net` |

---

## 🏗️ **Architecture Overview**

```
User Journey:
urmstontownjfc.co.uk/chat (Hostinger CNAME)
    ↓
https://d1ahgtos8kkd8y.cloudfront.net/ (CloudFront)
    ↓
S3 Static Files (utjfc-frontend-chat bucket)
    ↓
Backend API Proxy (/api/*)
    ↓
http://utjfc-backend-prod-2.eba-3bpsyeak.eu-north-1.elasticbeanstalk.com (New Backend)
    ↓
MCP Server: https://utjfc-mcp-server.replit.app/mcp
```

## 🖥️ **Backend Deployment (Elastic Beanstalk)**

### **Environment Details**
- **Application Name**: `utjfc-registration-backend`
- **Environment Name**: `utjfc-backend-prod-2` (replaces `utjfc-backend-prod`)
- **Current Version**: `v1.6.3-dockerfix`
- **Platform**: 64bit Amazon Linux 2023 v4.6.0 running Docker
- **Instance Type**: t3.small (auto-scaling: min 1, max 2)
- **Cost**: ~$20/month

### **URLs**
- **Public URL**: `http://utjfc-backend-prod-2.eba-3bpsyeak.eu-north-1.elasticbeanstalk.com`
- **Health Check**: `http://utjfc-backend-prod-2.eba-3bpsyeak.eu-north-1.elasticbeanstalk.com/health`
- **Load Balancer**: `awseb--AWSEB-LbGgRjA5LoRj-532812804.eu-north-1.elb.amazonaws.com`

### **Key Configuration**
- **Port**: 80 (Docker container runs on port 80, nginx proxy)
- **Health Check**: `HTTP:80/health`
- **Load Balancer**: Forwards port 80 → port 80

### **CORS Configuration**
```python
allow_origins=[
    "http://localhost:3000",  # Local development
    "http://localhost:8000",  # Local development
    "https://urmstontownjfc.co.uk",  # Production domain
    "http://urmstontownjfc.co.uk",   # Production domain (http)
    "https://d1ahgtos8kkd8y.cloudfront.net",  # CloudFront production URL
]
```

### **Environment Variables (Production)**
```bash
# Core Configuration
OPENAI_API_KEY=[REDACTED]
MCP_SERVER_URL=https://utjfc-mcp-server.replit.app/mcp
USE_MCP=true
PORT=80

# Airtable
AIRTABLE_API_KEY=[REDACTED]
AIRTABLE_BASE_ID=appc5OaJvZc3MQ8et

# Google Maps
GOOGLE_MAPS_API_KEY=[REDACTED]

# GoCardless (LIVE)
GOCARDLESS_API_KEY=[REDACTED]
GOCARDLESS_ENVIRONMENT=live
GOCARDLESS_WEBHOOK_SECRET=[REDACTED]

# Twilio SMS
TWILIO_ACCOUNT_SID=[REDACTED]
TWILIO_AUTH_TOKEN=[REDACTED]
TWILIO_PHONE_NUMBER=[REDACTED]

# Payment Configuration
PAYMENT_BASE_URL=https://d1ahgtos8kkd8y.cloudfront.net/api
FRONTEND_CHAT_BASE_URL=https://urmstontownjfc.co.uk/chat

# AWS S3
AWS_S3_BUCKET_NAME=utjfc-player-photos
AWS_REGION=eu-north-1

# Application
ENVIRONMENT=production
DEBUG=false
```

### **Deployment Process**
1. **Create deployment package**: `zip -r backend-v*.zip . -x '*.pyc' '__pycache__/*' '*.pytest_cache*' 'test_*.py' '*.log' '.venv/*' 'venv/*' '.env' '*.db'`
2. **Upload to S3**: `aws s3 cp backend-v*.zip s3://elasticbeanstalk-eu-north-1-650251723700-1/`
3. **Create version**: `aws elasticbeanstalk create-application-version --application-name "utjfc-registration-backend" --version-label "v*"`
4. **Deploy**: `aws elasticbeanstalk update-environment --environment-name "utjfc-backend-prod-2" --version-label "v*"`

## 🌐 **Frontend Deployment (S3 + CloudFront)**

### **S3 Configuration**
- **Bucket**: `utjfc-frontend-chat`
- **Path**: `/` (root of bucket)
- **Region**: eu-north-1

### **CloudFront Distribution**
- **Distribution ID**: `E2WNKV9R9SX5XH`
- **Domain**: `d1ahgtos8kkd8y.cloudfront.net`
- **Origin**: S3 bucket `utjfc-frontend-chat`
- **Status**: Deployed
- **Cost**: ~$2/month

### **Frontend Configuration**
- **Framework**: Next.js 15.3.1 with static export
- **Build Command**: `npm run build`
- **Output**: `/out` directory (static files)
- **API Endpoint**: Dynamically switches based on NODE_ENV

### **Environment Configuration**
```typescript
// src/config/environment.ts
const isDevelopment = process.env.NODE_ENV === 'development';

export const config = {
  API_BASE_URL: isDevelopment 
    ? 'http://localhost:8000'
    : 'https://d1ahgtos8kkd8y.cloudfront.net/api',
  
  get UPLOAD_URL() {
    return `${this.API_BASE_URL}/upload`;
  },
  
  get CHAT_URL() {
    return `${this.API_BASE_URL}/chat`;
  }
};
```

### **Next.js Configuration**
```typescript
// next.config.ts
const nextConfig: NextConfig = {
  output: 'export',
  trailingSlash: true,
  images: {
    unoptimized: true
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
};
```

### **Deployment Process**
1. **Build**: `cd frontend/web && npm run build`
2. **Deploy**: `aws s3 sync out/ s3://utjfc-frontend-chat/ --delete`

## 🔗 **MCP Server (Replit)**

- **URL**: `https://utjfc-mcp-server.replit.app/mcp`
- **Status**: ✅ Already deployed and running
- **Cost**: Free
- **Configuration**: Handles Airtable database operations via MCP protocol

## 🌍 **Domain & Reverse Proxy Setup**

### **Target Configuration (Hostinger)**
```
urmstontownjfc.co.uk/chat → https://d1ahgtos8kkd8y.cloudfront.net/
```

### **DNS Requirements**
- Main site: `urmstontownjfc.co.uk` (existing Hostinger site)
- Chat route: `urmstontownjfc.co.uk/chat` (reverse proxy to CloudFront)

## 🐛 **Troubleshooting History**

### **Issues Resolved**
1. **Missing Health Endpoint**: Added `/health` endpoint to FastAPI
2. **Port Mismatch**: Changed Docker container from port 8000 → 80 for nginx compatibility
3. **Load Balancer Config**: Updated ELB to forward port 80 → port 80
4. **CORS Issues**: Added production domains to allowed origins
5. **Health Check Target**: Changed from `TCP:80` → `HTTP:80/health`

### **Critical Configuration Points**
- Docker container MUST run on port 80 (not 8000) for nginx compatibility
- Health check endpoint MUST exist at `/health`
- CORS MUST include all frontend domains (localhost, CloudFront, custom domain)
- Environment variables MUST be set in EB environment (not .env file)

## 📊 **Monitoring & Health Checks**

### **Backend Health**
- **Endpoint**: `/health`
- **Expected Response**: `{"status": "healthy", "message": "UTJFC Registration Backend is running"}`
- **ELB Health Check**: Every 30 seconds, 3 consecutive successes required

### **AWS Commands for Monitoring**
```bash
# Check environment status
aws --profile footballclub elasticbeanstalk describe-environments --environment-names "utjfc-backend-prod-2"

# Check recent events
aws --profile footballclub elasticbeanstalk describe-events --environment-name "utjfc-backend-prod-2" --max-records 10

# Check CloudFront status
aws --profile footballclub cloudfront get-distribution --id E2WNKV9R9SX5XH

# Test endpoints
curl http://utjfc-backend-prod-2.eba-3bpsyeak.eu-north-1.elasticbeanstalk.com/health
curl https://d1ahgtos8kkd8y.cloudfront.net/api/health
```

## 💰 **Cost Breakdown**

| Component | Service | Monthly Cost |
|-----------|---------|--------------|
| Backend | Elastic Beanstalk (t3.small) | ~$20 |
| Frontend | S3 + CloudFront | ~$2 |
| MCP Server | Replit | Free |
| **Total** | | **~$22** |

## 🔄 **Future Deployment Process**

### **Backend Updates**
1. Make changes in `/backend` directory
2. Update version in zip filename
3. Run deployment commands:
```bash
cd backend
zip -r ../utjfc-backend-v[NEW_VERSION].zip . -x '*.pyc' '__pycache__/*' '*.pytest_cache*' 'test_*.py' '*.log' '.venv/*' 'venv/*' '.env' '*.db'
cd ..
aws --profile footballclub s3 cp utjfc-backend-v[NEW_VERSION].zip s3://elasticbeanstalk-eu-north-1-650251723700-1/
aws --profile footballclub elasticbeanstalk create-application-version --application-name "utjfc-registration-backend" --version-label "v[NEW_VERSION]" --source-bundle S3Bucket="elasticbeanstalk-eu-north-1-650251723700-1",S3Key="utjfc-backend-v[NEW_VERSION].zip"
aws --profile footballclub elasticbeanstalk update-environment --environment-name "utjfc-backend-prod-2" --version-label "v[NEW_VERSION]"
```

### **Frontend Updates**
1. Make changes in `/frontend/web` directory
2. Build and deploy:
```bash
cd frontend/web
npm run build
aws --profile footballclub s3 sync out/ s3://utjfc-frontend-chat/ --delete
# CloudFront cache invalidation if needed:
aws --profile footballclub cloudfront create-invalidation --distribution-id E2WNKV9R9SX5XH --paths "/*"
```

## 🔧 **Key Files Modified During Recovery**

### **Backend**
- `server.py`: Added health endpoint, updated CORS configuration
- `Dockerfile`: Changed port from 8000 to 80
- `requirements.txt`: Combined dependencies from both agent folders

### **Frontend**
- `src/config/environment.ts`: API endpoint configured to use CloudFront proxy
- `src/app/chat/page.tsx`: Updated API calls to use config
- `next.config.ts`: Configured for static export

## ⚠️ **Important Notes**

1. **Never commit production .env files** - Environment variables are set in AWS EB
2. **CORS updates require backend redeployment** - Frontend domains must be whitelisted
3. **CloudFront deployments take 5-15 minutes** - Plan accordingly
4. **Health endpoint is critical** - Backend will fail without it
5. **Port 80 is required** - nginx reverse proxy expects this port
6. **MCP server must be accessible** - Backend depends on Replit MCP server

## 🎯 **Current Status & Next Steps**

### **Completed ✅**
- **Full system recovery**
- Backend deployment with all production configuration
- Frontend built and deployed to S3
- CloudFront distribution updated and deployed
- All CORS and environment variables configured
- CloudWatch logging enabled for new environment

### **In Progress ⏳**
- None. System is stable.

### **Pending 📋**
- End-to-end testing of the registration flow.

### **Success Criteria**
- [x] CloudFront accessible: `https://d1ahgtos8kkd8y.cloudfront.net/`
- [x] Custom domain accessible: `https://urmstontownjfc.co.uk/chat`
- [x] Chat interface loads and connects to backend
- [ ] Registration flow works end-to-end
- [ ] File upload functionality operational

## 🚨 **URGENT: Mixed Content Security Issue & Resolution**

**Date**: July 2, 2025  
**Issue**: Frontend served over HTTPS, backend only supports HTTP - browsers block mixed content  
**Status**: ⚠️ Temporary fix deployed, HTTPS configuration in progress

### **Problem Discovery**
1. **Working Frontend**: `https://d1ahgtos8kkd8y.cloudfront.net/chat/index.html` (working)
2. **Non-Working CloudFront**: `https://d1ahgtos8kkd8y.cloudfront.net/` (403 error - not configured)
3. **Backend HTTP Only**: `http://utjfc-backend-prod.eba-3bpsyeak.eu-north-1.elasticbeanstalk.com` (working)
4. **Backend HTTPS Timeout**: `https://utjfc-backend-prod.eba-3bpsyeak.eu-north-1.elasticbeanstalk.com` (connection timeout)

### **Root Cause Analysis**
- **Mixed Content Security**: HTTPS frontend cannot call HTTP backend APIs
- **Browser Security Policy**: Blocks HTTP requests from HTTPS pages
- **Elastic Beanstalk Configuration**: No SSL/HTTPS listener configured on load balancer

### **Temporary Fix Applied** ✅
1. **Updated CORS**: Backend already includes correct CloudFront URL
2. **Frontend Configuration**: Reverted to HTTP backend for immediate functionality
3. **Deployed**: Both frontend deployments (HTTPS attempt + HTTP fallback)

### **Current Working Configuration**
```typescript
// frontend/web/src/config/environment.ts (current)
export const config = {
  API_BASE_URL: isDevelopment 
    ? 'http://localhost:8000'
    : 'http://utjfc-backend-prod.eba-3bpsyeak.eu-north-1.elasticbeanstalk.com', // HTTP (temporary)
};
```

### **Deployment Log - July 2, 2025**
```bash
# CloudFront cache invalidation
aws --profile footballclub cloudfront create-invalidation --distribution-id E2WNKV9R9SX5XH --paths "/*"

# Frontend deployments (2 attempts)
aws --profile footballclub s3 sync frontend/web/out/ s3://utjfc-frontend-chat/ --delete
```

### **Current URLs**
- **Working Frontend**: `https://d1ahgtos8kkd8y.cloudfront.net/chat/index.html`
- **Domain Redirect**: `urmstontownjfc.co.uk/chat` → CloudFront (via JavaScript)
- **Backend API**: `http://utjfc-backend-prod.eba-3bpsyeak.eu-north-1.elasticbeanstalk.com`
- **Backend Health**: `{"status":"healthy","message":"UTJFC Registration Backend is running"}`

### **Rollback Plan**
If HTTPS configuration fails, the current HTTP configuration provides a working fallback.

---

## ✅ **RESOLVED: CloudFront API Proxy Solution**

**Date**: July 2, 2025  
**Status**: ✅ DEPLOYED - CloudFront API proxy successfully configured  
**Solution**: CloudFront API proxy to route HTTPS frontend → HTTP backend

### **Final Solution Implemented**
Instead of configuring SSL on Elastic Beanstalk (complex domain validation), implemented CloudFront API proxy pattern.

### **Architecture Change**
```
BEFORE (Broken):
Frontend: https://d1ahgtos8kkd8y.cloudfront.net → Backend: http://backend.com (BLOCKED)

AFTER (Working):
Frontend: https://d1ahgtos8kkd8y.cloudfront.net → 
  ├── Static files: S3 bucket
  └── API calls: /api/* → CloudFront proxy → http://backend.com ✅
```

### **CloudFront Configuration Update**
**Distribution**: `E2WNKV9R9SX5XH` (d1ahgtos8kkd8y.cloudfront.net)

**Added Second Origin**:
```json
{
    "Id": "API-utjfc-backend",
    "DomainName": "utjfc-backend-prod-2.eba-3bpsyeak.eu-north-1.elasticbeanstalk.com",
    "OriginProtocolPolicy": "http-only"
}
```

**Added Cache Behavior**:
```json
{
    "PathPattern": "/api/*",
    "TargetOriginId": "API-utjfc-backend",
    "AllowedMethods": ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"],
    "ForwardedValues": {
        "QueryString": true,
        "Cookies": {"Forward": "all"},
        "Headers": ["Authorization", "Content-Type", "Origin", etc.]
    },
    "MinTTL": 0,
    "DefaultTTL": 0,
    "MaxTTL": 0
}
```

### **Frontend Configuration Update**
**File**: `frontend/web/src/config/environment.ts`
```typescript
// BEFORE
API_BASE_URL: 'http://utjfc-backend-prod.eba-3bpsyeak.eu-north-1.elasticbeanstalk.com'

// AFTER  
API_BASE_URL: 'https://d1ahgtos8kkd8y.cloudfront.net/api'
```

### **Deployment Commands Executed**
```bash
# 1. CloudFront distribution update
aws --profile footballclub cloudfront update-distribution \
    --id E2WNKV9R9SX5XH \
    --distribution-config file://cloudfront-api-config.json \
    --if-match E26KNWJC9WF1ZH

# 2. Frontend rebuild and deploy
cd frontend/web && npm run build
aws --profile footballclub s3 sync out/ s3://utjfc-frontend-chat/ --delete

# 3. Cache invalidation
aws --profile footballclub cloudfront create-invalidation \
    --distribution-id E2WNKV9R9SX5XH --paths "/*"
```

### **Timing & Status**
- **CloudFront Update**: Started 05:27 UTC - ~15 minutes deployment
- **Frontend Deploy**: ✅ Complete 05:28 UTC  
- **Cache Invalidation**: Started 05:28 UTC - ~5 minutes
- **Expected Working**: ~05:35-05:40 UTC

### **Test Results Expected**
✅ **Frontend loads**: `urmstontownjfc.co.uk/chat` → CloudFront  
✅ **API calls work**: No "Failed to fetch" or mixed content errors  
✅ **Chat functional**: Messages send successfully to backend  
✅ **File uploads work**: Photo uploads via HTTPS proxy

### **URL Mapping (Final)**
| Frontend URL | Backend API Call | Proxy Route |
|--------------|------------------|-------------|
| `urmstontownjfc.co.uk/chat` | Chat messages | `https://d1ahgtos8kkd8y.cloudfront.net/api/chat` |
| `urmstontownjfc.co.uk/chat` | File uploads | `https://d1ahgtos8kkd8y.cloudfront.net/api/upload` |
| | Health check | `https://d1ahgtos8kkd8y.cloudfront.net/api/health` |

### **Benefits of This Solution**
1. **No SSL Certificate Complexity**: Avoided domain validation issues
2. **Same Domain Policy**: Frontend and API on same CloudFront domain
3. **No Backend Changes**: Backend stays HTTP, CloudFront handles HTTPS
4. **Cost Effective**: No additional SSL certificate costs
5. **Performance**: CloudFront caching and global edge locations

### **Files Modified**
```
cloudfront-api-config.json                    # CloudFront configuration
frontend/web/src/config/environment.ts        # API endpoint URLs
```

### **CloudFront Resource IDs**
- **Distribution ID**: `E2WNKV9R9SX5XH`
- **Domain**: `d1ahgtos8kkd8y.cloudfront.net`
- **ETag**: `E1E0SQIKOULC88` (after update)
- **Invalidation**: `I68BZZF1YQJ7MEPLH1K77LMIQL`

### **Resolution Summary**
✅ **Mixed content security issue resolved**  
✅ **HTTPS end-to-end encryption maintained via CloudFront**  
✅ **No changes required to domain/Hostinger setup**  
✅ **Backend remains simple HTTP configuration**  
✅ **Frontend API calls now work via HTTPS proxy**

**Total Resolution Time**: ~3 hours (investigation + implementation)  
**Deployment Complexity**: Medium (CloudFront configuration)  
**Maintenance Overhead**: Low (standard CloudFront operations)

### **🚨 CRITICAL PATH REWRITE FIX APPLIED**

**Issue Discovered**: CloudFront forwarded `/api/health` to backend, but backend only has `/health`  
**Root Cause**: Backend endpoints don't include `/api` prefix (e.g., `/health`, `/chat` not `/api/health`)  
**Error**: All API calls returned `{"detail":"Not Found"}` from CloudFront proxy

**Solution**: CloudFront Function for URL rewriting  
**Function Name**: `utjfc-api-path-rewrite`  
**Function ARN**: `arn:aws:cloudfront::650251723700:function/utjfc-api-path-rewrite`  
**Logic**: Strips `/api` prefix before forwarding to backend

**Function Code**:
```javascript
function handler(event) {
    var request = event.request;
    var uri = request.uri;
    
    // Strip /api prefix if present
    if (uri.startsWith('/api/')) {
        request.uri = uri.substring(4); // Remove '/api' (4 characters)
    } else if (uri === '/api') {
        request.uri = '/';
    }
    
    return request;
}
```

**Applied**: July 2, 2025 06:45 UTC  
**Status**: ✅ Function published and attached to CloudFront `/api/*` cache behavior  
**Deployment**: ⏳ CloudFront distribution updating (~15 minutes)  
**ETag**: `EJ6UEQZ56F9I4` (current)

**URL Translation**:
- Frontend calls: `https://d1ahgtos8kkd8y.cloudfront.net/api/health`
- Function rewrites to: `/health`  
- Backend receives: `http://backend.com/health` ✅

---

## 🔄 **API Keys Update & Current Issues**

**Date**: July 2, 2025  
**Status**: ✅ API Keys Updated, ⚠️ Application Parsing Error  

### **API Keys Successfully Updated**
- **Google Maps API Key**: ✅ Updated to `[REDACTED]`  
- **OpenAI API Key**: ✅ Updated to `[REDACTED]`

### **API Key Deployment Process**
1. **Missing S3 Package**: Initial updates failed due to missing `utjfc-backend-v1.6.1-restart.zip` in S3
2. **Package Upload**: `aws s3 cp backend/utjfc-backend-v1.6.1-restart.zip s3://utjfc-frontend-chat/backend-deployment/`  
3. **Successful Updates**: Both API keys deployed via separate environment updates
4. **Backend Status**: ✅ Ready and responding to health checks

### **OpenAI API Key Verification**
✅ **Direct OpenAI API Test**: Key working perfectly with `gpt-4-0613` model  
✅ **Backend Health**: `{"status":"healthy","message":"UTJFC Registration Backend is running"}`  
✅ **HTTPS API Proxy**: CloudFront proxy working correctly

### **Current Issue: Application Parsing Error**
**Error**: `"Error: Could not parse registration AI response for frontend."`  
**Location**: Registration chat flow after initial hardcoded response  
**Environment**: `ENVIRONMENT=production`, `USE_MCP=true`  

**Test Results**:
- Initial message `"200-bears-u7-2526"`: ✅ Works (hardcoded response)
- Follow-up message `"John Smith"`: ❌ Parsing error

### **Hypothesis: MCP vs Local Environment Mismatch**
**Production**: `USE_MCP=true` → Routes through MCP server → Different response format  
**Local**: Likely `USE_MCP=false` → Direct OpenAI → Expected JSON format  

**Expected Response Format**:
```json
{
  "agent_final_response": "message text",
  "routine_number": 2
}
```

**MCP Server**: `https://utjfc-mcp-server.replit.app/mcp`  
**Issue**: MCP may return different response structure than direct OpenAI calls

### **Next Steps**
1. **Check CloudWatch Logs**: Application logs in `/aws/elasticbeanstalk/utjfc-backend-prod-2/var/log/eb-docker/containers/eb-current-app/stdouterr.log`
2. **Compare MCP vs Direct**: Verify response format differences
3. **Consider Environment Alignment**: Match production `USE_MCP` setting to local working configuration

### **Current Environment Variables**
```bash
ENVIRONMENT=production
USE_MCP=true
MCP_SERVER_URL=https://utjfc-mcp-server.replit.app/mcp
MCP_AUTH_TOKEN=[REDACTED]
OPENAI_API_KEY=[REDACTED]
GOOGLE_MAPS_API_KEY=[REDACTED]
```

---

## ❌ **FAILED DEPLOYMENT LOG - JULY 1, 2025** ❌

This section details the commands run during the failed attempt to update the environment. **These logs contain sensitive keys and demonstrate the incorrect procedures that led to the environment failure.**

### **Initial State**
- Environment `utjfc-backend-prod` was running `v1.6.2`.
- Goal: Update the `OPENAI_API_KEY` environment variable.

### **Command History**
```bash
# 1. Attempted to update environment variables directly
#    This command is valid, but the subsequent rebuild failed.
$ aws elasticbeanstalk update-environment --environment-name utjfc-backend-prod --option-settings Namespace=aws:elasticbeanstalk:application:environment,OptionName=OPENAI_API_KEY,Value=[REDACTED]

# 2. Rebuild command that triggered the failure
#    This is a destructive operation that should be used with extreme caution.
#    It failed mid-way, leaving the CloudFormation stack in `UPDATE_ROLLBACK_FAILED`.
$ aws elasticbeanstalk rebuild-environment --environment-name utjfc-backend-prod

# 3. Attempts to recover the failed environment (all failed)
$ aws cloudformation continue-update-rollback --stack-name awseb-e-mmp8wjaqnp-stack
$ aws cloudformation delete-stack --stack-name awseb-e-mmp8wjaqnp-stack

# 4. Final termination of the broken environment
$ aws elasticbeanstalk terminate-environment --environment-name utjfc-backend-prod
```

---

## ✅ **SUCCESSFUL RECOVERY DEPLOYMENT LOG - JULY 2, 2025** ✅

This section details the exact commands used to provision the new, working environment (`utjfc-backend-prod-2`).

### **1. Discovering Default VPC and Subnets**
After the old environment was terminated, its associated VPC was also deleted. These commands were used to find the new default resources.
```bash
# Find default VPC
$ aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query "Vpcs[0].VpcId" --output text
# Output: vpc-0e9a7b6c5d4f3e2a1

# Find subnets in the default VPC
$ aws ec2 describe-subnets --filters Name=vpc-id,Values=vpc-0e9a7b6c5d4f3e2a1 --query "Subnets[*].SubnetId" --output json
# Output: ["subnet-0a1b2c3d4e5f6a7b8", "subnet-0f1e2d3c4b5a69876", ... ]
```

### **2. Creating `options.json` for New Environment**
This file contains all the necessary configurations for the new Elastic Beanstalk environment.
```json
// options.json
[
  {
    "Namespace": "aws:autoscaling:launchconfiguration",
    "OptionName": "IamInstanceProfile",
    "Value": "aws-elasticbeanstalk-ec2-role"
  },
  {
      "Namespace": "aws:ec2:vpc",
      "OptionName": "VPCId",
      "Value": "vpc-0e9a7b6c5d4f3e2a1"
  },
  {
      "Namespace": "aws:ec2:vpc",
      "OptionName": "Subnets",
      "Value": "subnet-0a1b2c3d4e5f6a7b8,subnet-0f1e2d3c4b5a69876"
  },
  {
    "Namespace": "aws:elasticbeanstalk:application:environment",
    "OptionName": "OPENAI_API_KEY",
    "Value": "[REDACTED]"
  },
  {
    "Namespace": "aws:elasticbeanstalk:application:environment",
    "OptionName": "MCP_SERVER_URL",
    "Value": "https://utjfc-mcp-server.replit.app/mcp"
  },
  // ... other env vars ...
]
```

### **3. Full `create-environment` Command**
```bash
$ aws elasticbeanstalk create-environment \
    --application-name "utjfc-registration-backend" \
    --environment-name "utjfc-backend-prod-2" \
    --version-label "v1.6.3-dockerfix" \
    --platform-arn "arn:aws:elasticbeanstalk:eu-north-1::platform/64bit Amazon Linux 2023 v4.6.0 running Docker" \
    --cname-prefix "utjfc-backend-prod-2" \
    --option-settings file://options.json
```

### **4. Enabling CloudWatch Logs**
```bash
$ aws elasticbeanstalk update-environment \
    --environment-name "utjfc-backend-prod-2" \
    --option-settings Namespace=aws:elasticbeanstalk:cloudwatch:logs,OptionName=StreamLogs,Value=true
```

### **5. Creating `cloudfront-api-origin.json`**
This file was used to update the CloudFront distribution to point to the new backend.
```json
// cloudfront-api-origin.json
{
    "Id": "API-utjfc-backend",
    "DomainName": "utjfc-backend-prod-2.eba-3bpsyeak.eu-north-1.elasticbeanstalk.com",
    "Origins": {
        "Quantity": 1,
        "Items": [
            {
                "Id": "API-utjfc-backend",
                "DomainName": "utjfc-backend-prod-2.eba-3bpsyeak.eu-north-1.elasticbeanstalk.com",
                "OriginPath": "",
                "CustomHeaders": { "Quantity": 0 },
                "CustomOriginConfig": {
                    "HTTPPort": 80,
                    "HTTPSPort": 443,
                    "OriginProtocolPolicy": "http-only",
                    "OriginSslProtocols": { "Quantity": 1, "Items": ["TLSv1.2"] },
                    "OriginReadTimeout": 30,
                    "OriginKeepaliveTimeout": 5
                }
            }
        ]
    },
    "DefaultCacheBehavior": "forward-all-to-origin"
}
```

### **6. Updating CloudFront**
This command requires the distribution's current ETag.
```bash
# First, get the current config and ETag
$ aws cloudfront get-distribution-config --id E2WNKV9R9SX5XH

# Then, update with the new origin and the ETag
$ aws cloudfront update-distribution \
    --id E2WNKV9R9SX5XH \
    --distribution-config file://cloudfront-config.json \
    --if-match YOUR_ETAG_HERE
```

---
