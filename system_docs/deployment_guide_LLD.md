# UTJFC Production Deployment Guide
## Complete Step-by-Step Deployment Procedures

### Document Information
- **Version**: 1.2 (Updated January 2025)
- **Purpose**: Step-by-step deployment guide for developers and AI agents
- **Scope**: Frontend and backend production deployment procedures

---

## Table of Contents
1. [Prerequisites & Setup](#prerequisites--setup)
2. [System Architecture Summary](#system-architecture-summary)
3. [Backend Deployment Process](#backend-deployment-process)
4. [Frontend Deployment Process](#frontend-deployment-process)
5. [Environment Variable Management](#environment-variable-management)
6. [Verification & Health Checks](#verification--health-checks)
7. [Troubleshooting Common Issues](#troubleshooting-common-issues)
8. [Critical Deployment Notes](#critical-deployment-notes)

---

## Prerequisites & Setup

### Required Tools
1. **AWS CLI**: Must be installed and configured
2. **AWS Profile**: `footballclub` profile configured with necessary permissions
3. **Node.js & npm**: For frontend builds
4. **Workspace**: All commands run from project root directory

### AWS CLI Configuration for AI Agents

#### Critical: Pager Configuration Issue
**Problem**: AI agents may encounter errors like:
```
head: |: No such file or directory
head: cat: No such file or directory
```

**Solution**: All AWS CLI commands in this guide include `--no-cli-pager` flag:
```bash
aws --profile footballclub --no-cli-pager <command>
```

#### Alternative Approach
```bash
AWS_PAGER="" aws --profile footballclub <command>
```

### Current Production Environment Details
- **Backend Environment**: `utjfc-backend-prod-3`
- **Frontend S3 Bucket**: `utjfc-frontend-chat`
- **CloudFront Distribution**: `E2WNKV9R9SX5XH`
- **Region**: `eu-north-1` (Stockholm)
- **Current Version Format**: `v1.6.13` (as of January 2025)

---

## System Architecture Summary

### Infrastructure Overview
```
Internet → CloudFront CDN → {
    Static Content → S3 (utjfc-frontend-chat)
    API Requests (/api/*) → Elastic Beanstalk (utjfc-backend-prod-3)
}
```

### Key Components
- **Backend**: FastAPI in Docker container on AWS Elastic Beanstalk
- **Frontend**: Static Next.js site on S3 served via CloudFront
- **API Routing**: CloudFront strips `/api` prefix and routes to backend
- **Domain**: `https://urmstontownjfc.co.uk/chat/`

---

## Backend Deployment Process

### Step 1: Create Deployment Package

#### 1.1 Navigate to Backend Directory
```bash
cd backend
```

#### 1.2 Create Versioned Zip Archive
**IMPORTANT**: Update version number in filename for tracking.

```bash
# Example: v1.6.14 (increment from current v1.6.13)
zip -r ../utjfc-backend-v1.6.14.zip . \
  -x '*.pyc' '__pycache__/*' '*.pytest_cache*' 'test_*.py' \
     '*.log' '.venv/*' 'venv/*' '.env*' '*.db'
```

#### 1.3 Return to Root Directory
```bash
cd ..
```

### Step 2: Upload to S3

#### 2.1 Upload Deployment Package
```bash
aws --profile footballclub s3 cp utjfc-backend-v1.6.14.zip \
  s3://elasticbeanstalk-eu-north-1-650251723700-1/ --no-cli-pager
```

### Step 3: Create Application Version

#### 3.1 Register New Version with Elastic Beanstalk
```bash
aws --profile footballclub elasticbeanstalk create-application-version \
  --application-name "utjfc-registration-backend" \
  --version-label "v1.6.14" \
  --source-bundle S3Bucket="elasticbeanstalk-eu-north-1-650251723700-1",S3Key="utjfc-backend-v1.6.14.zip" \
  --no-cli-pager
```

### Step 4: Deploy to Production

#### 4.1 Execute Environment Update
```bash
aws --profile footballclub elasticbeanstalk update-environment \
  --environment-name "utjfc-backend-prod-3" \
  --version-label "v1.6.14" \
  --no-cli-pager
```

### Step 5: Monitor Deployment

#### 5.1 Watch Deployment Events
```bash
aws --profile footballclub elasticbeanstalk describe-events \
  --environment-name "utjfc-backend-prod-3" \
  --max-records 10 --no-cli-pager
```

#### 5.2 Check Environment Health
```bash
aws --profile footballclub elasticbeanstalk describe-environments \
  --environment-names "utjfc-backend-prod-3" --no-cli-pager
```

**Wait for**: `Status: Ready` and `Health: Green`

#### 5.3 Verify Health Endpoint
```bash
curl https://d1ahgtos8kkd8y.cloudfront.net/api/health
```

**Expected Response**:
```json
{
  "status": "healthy",
  "message": "UTJFC Registration Backend is running"
}
```

---

## Frontend Deployment Process

### Option A: Automated Deployment (Recommended)

#### A.1 Run Deployment Script
```bash
./deploy-frontend.sh
```

**This script automatically**:
- Installs dependencies
- Builds the application
- Syncs to S3
- **Invalidates CloudFront cache** (critical!)
- Provides deployment status

### Option B: Manual Step-by-Step Deployment

#### B.1 Build Static Site

##### Navigate to Frontend Directory
```bash
cd frontend/web
```

##### Install Dependencies (if needed)
```bash
npm install
```

##### Build Application
```bash
npm run build
```

#### B.2 Sync to S3

##### Upload Built Files
```bash
aws --profile footballclub s3 sync out/ s3://utjfc-frontend-chat/ \
  --delete --no-cli-pager
```

**Note**: `--delete` removes old files no longer in build

#### B.3 Invalidate CloudFront Cache (CRITICAL)

##### Create Cache Invalidation
```bash
aws --profile footballclub cloudfront create-invalidation \
  --distribution-id E2WNKV9R9SX5XH \
  --paths "/*" \
  --no-cli-pager
```

**🚨 CRITICAL**: Skipping this step results in users seeing old cached content!

#### B.4 Verify Deployment

##### Test Frontend
1. Open browser to: `https://urmstontownjfc.co.uk/chat/`
2. Hard refresh: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
3. Verify latest changes are visible

---

## Environment Variable Management

### Updating Environment Variables

#### Via AWS Management Console
1. **Login**: AWS Management Console
2. **Navigate**: Elastic Beanstalk service
3. **Select**: `utjfc-backend-prod-3` environment
4. **Configure**: Configuration → Software → Edit
5. **Update**: Environment properties section
6. **Apply**: Click Apply button

#### Automatic Environment Update
- Environment automatically updates when variables change
- **No code redeployment needed** for variable-only changes
- Update takes 2-5 minutes

### Verification Commands

#### Check Environment Status
```bash
aws --profile footballclub elasticbeanstalk describe-environments \
  --environment-names "utjfc-backend-prod-3" --no-cli-pager
```

#### Inspect Configuration
```bash
aws --profile footballclub elasticbeanstalk describe-configuration-settings \
  --application-name "utjfc-registration-backend" \
  --environment-name "utjfc-backend-prod-3" --no-cli-pager
```

**Look for**: `aws:elasticbeanstalk:application:environment` namespace

---

## Verification & Health Checks

### Backend Health Verification

#### Direct Backend Health Check
```bash
curl -f https://utjfc-backend-prod-3.eba-3bpsyeak.eu-north-1.elasticbeanstalk.com/health
```

#### Via CloudFront (Production Route)
```bash
curl -f https://d1ahgtos8kkd8y.cloudfront.net/api/health
```

#### Expected Response
```json
{
  "status": "healthy",
  "message": "UTJFC Registration Backend is running"
}
```

### Frontend Verification

#### Production URL
```
https://urmstontownjfc.co.uk/chat/
```

#### Alternative CloudFront URL
```
https://d1ahgtos8kkd8y.cloudfront.net/chat/
```

### Integration Testing

#### Test Chat Endpoint
```bash
curl -X POST https://d1ahgtos8kkd8y.cloudfront.net/api/chat \
  -H "Content-Type: application/json" \
  -d '{"user_message": "test", "session_id": "test"}'
```

#### Test File Upload
```bash
curl -X POST https://d1ahgtos8kkd8y.cloudfront.net/api/upload-async \
  -F "file=@test_photo.jpg" \
  -F "session_id=test"
```

### Monitoring Commands

#### Watch Environment Events
```bash
aws --profile footballclub elasticbeanstalk describe-events \
  --environment-name "utjfc-backend-prod-3" \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --no-cli-pager
```

#### Check CloudFront Invalidation Status
```bash
aws --profile footballclub cloudfront list-invalidations \
  --distribution-id E2WNKV9R9SX5XH --no-cli-pager
```

---

## Troubleshooting Common Issues

### Backend Deployment Issues

#### Issue: Environment Stuck in "Updating"
**Symptoms**: Environment status remains "Updating" for >15 minutes

**Diagnosis**:
```bash
aws --profile footballclub elasticbeanstalk describe-events \
  --environment-name "utjfc-backend-prod-3" \
  --max-records 20 --no-cli-pager
```

**Common Causes**:
- Docker build failures
- Health check failures
- Environment variable issues

**Solutions**:
- Check application logs for errors
- Verify Dockerfile port 80 exposure
- Confirm environment variables are set

#### Issue: Health Check Failures
**Symptoms**: Environment health shows "Severe" or "Degraded"

**Diagnosis**:
```bash
# Check health endpoint directly
curl -v http://utjfc-backend-prod-3.eba-3bpsyeak.eu-north-1.elasticbeanstalk.com/health

# Check application logs
aws --profile footballclub elasticbeanstalk retrieve-environment-info \
  --environment-name "utjfc-backend-prod-3" \
  --info-type tail --no-cli-pager
```

**Solutions**:
- Verify `/health` endpoint returns 200 status
- Check application startup logs
- Confirm Docker container is running

#### Issue: Version Already Exists
**Symptoms**: `create-application-version` fails with version conflict

**Solution**: Increment version number or delete old version:
```bash
aws --profile footballclub elasticbeanstalk delete-application-version \
  --application-name "utjfc-registration-backend" \
  --version-label "v1.6.14" --no-cli-pager
```

### Frontend Deployment Issues

#### Issue: Changes Not Visible After Deployment
**Symptoms**: Old content still visible despite successful deployment

**Cause**: CloudFront cache not invalidated

**Solution**: Force cache invalidation:
```bash
aws --profile footballclub cloudfront create-invalidation \
  --distribution-id E2WNKV9R9SX5XH \
  --paths "/*" --no-cli-pager
```

**Prevention**: Always use automated deployment script

#### Issue: Build Failures
**Symptoms**: `npm run build` fails

**Common Causes**:
- Missing dependencies
- Environment variable issues
- TypeScript errors

**Solutions**:
```bash
# Clear node modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check for TypeScript errors
npm run type-check

# Build with verbose output
npm run build -- --verbose
```

### CloudFront Issues

#### Issue: API Requests Return 404
**Symptoms**: Frontend loads but API calls fail

**Diagnosis**:
```bash
# Test API directly
curl -v https://d1ahgtos8kkd8y.cloudfront.net/api/health

# Check CloudFront configuration
aws --profile footballclub cloudfront get-distribution \
  --id E2WNKV9R9SX5XH --no-cli-pager
```

**Solutions**:
- Verify CloudFront origin points to current backend
- Check API path rewrite function is active
- Confirm backend environment is healthy

---

## Critical Deployment Notes

### Production Environment Information

#### Current Environment Details
- **Environment Name**: `utjfc-backend-prod-3`
- **Created**: July 2025 (due to AWS Launch Configuration deprecation)
- **Platform**: Docker running on 64bit Amazon Linux 2
- **Domain**: `utjfc-backend-prod-3.eba-3bpsyeak.eu-north-1.elasticbeanstalk.com`

#### CloudFront Configuration
- **Distribution ID**: `E2WNKV9R9SX5XH`
- **Domain**: `d1ahgtos8kkd8y.cloudfront.net`
- **Custom Domain**: `urmstontownjfc.co.uk`
- **API Function**: `utjfc-api-path-rewrite` (strips `/api` prefix)

### Important Configuration Details

#### Docker Configuration
- **Port**: Must expose port 80 (Dockerfile requirement)
- **Health Check**: `/health` endpoint on port 80
- **Platform**: `.platform/nginx/conf.d/proxy.conf` for nginx config
- **Avoid**: `.ebextensions/01_nginx.config` (causes conflicts)

#### Frontend Configuration
- **Build Output**: `out/` directory from Next.js build
- **Trailing Slash**: Set to `true` in `next.config.ts`
- **Static Export**: Required for S3 hosting
- **Index Files**: Uses `chat/index.html` structure

#### Version Management
- **Format**: `vX.Y.Z` (e.g., v1.6.14)
- **Increment**: Patch version for bug fixes, minor for features
- **Tracking**: Version labels must be unique in Elastic Beanstalk

### Timing Expectations

#### Backend Deployment
- **Package Upload**: 30-60 seconds
- **Version Creation**: 10-30 seconds  
- **Environment Update**: 5-15 minutes
- **Health Check**: 2-5 minutes

#### Frontend Deployment
- **Build Process**: 1-3 minutes
- **S3 Sync**: 30-120 seconds
- **CloudFront Invalidation**: 5-15 minutes
- **Global Propagation**: 5-15 minutes

#### Total Deployment Time
- **Backend Only**: 10-20 minutes
- **Frontend Only**: 10-20 minutes
- **Full Deployment**: 15-25 minutes

### Security Considerations

#### Environment Variables
- **Never commit**: Sensitive keys to code repository
- **Use AWS Console**: For production environment variables
- **Validation**: Test changes in staging first
- **Backup**: Document current values before changes

#### Access Control
- **AWS Profile**: `footballclub` has limited permissions
- **MFA**: Required for production changes
- **Logging**: All deployment actions are logged
- **Rollback**: Previous versions available for emergency rollback

### Emergency Procedures

#### Quick Rollback (Backend)
```bash
# Get previous version
aws --profile footballclub elasticbeanstalk describe-application-versions \
  --application-name "utjfc-registration-backend" \
  --max-records 5 --no-cli-pager

# Deploy previous version
aws --profile footballclub elasticbeanstalk update-environment \
  --environment-name "utjfc-backend-prod-3" \
  --version-label "v1.6.13" \
  --no-cli-pager
```

#### CloudFront Cache Clear (Frontend)
```bash
# Emergency cache clear
aws --profile footballclub cloudfront create-invalidation \
  --distribution-id E2WNKV9R9SX5XH \
  --paths "/*" --no-cli-pager
```

#### Health Check URLs
- **Backend Direct**: `https://utjfc-backend-prod-3.eba-3bpsyeak.eu-north-1.elasticbeanstalk.com/health`
- **Via CloudFront**: `https://d1ahgtos8kkd8y.cloudfront.net/api/health`
- **Frontend**: `https://urmstontownjfc.co.uk/chat/`

---

## Conclusion

This deployment guide provides complete, tested procedures for safely deploying both frontend and backend changes to the UTJFC production environment. Following these steps ensures:

### Deployment Safety
- **Version Control**: Proper version labeling and tracking
- **Health Verification**: Comprehensive health checks before go-live
- **Rollback Capability**: Quick recovery procedures if issues arise
- **Cache Management**: Proper CloudFront cache invalidation

### Operational Excellence
- **Consistent Process**: Standardized procedures for all deployments
- **Error Prevention**: Common issue identification and solutions
- **Monitoring**: Real-time deployment status tracking
- **Documentation**: Complete audit trail of all changes

### AI Agent Compatibility
- **Pager Configuration**: Resolved AWS CLI pager conflicts
- **Step-by-Step Commands**: Copy-paste ready command sequences
- **Error Handling**: Clear diagnostic and resolution procedures
- **Verification**: Multiple validation checkpoints

The procedures in this guide have been tested in production and provide reliable, repeatable deployment workflows for maintaining the UTJFC registration system.