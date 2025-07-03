# Issue #002: Photo Upload 413 Request Entity Too Large Error

**Priority**: Critical  
**Type**: Bug  
**Component**: Backend / Infrastructure  
**Created**: January 2025  
**Status**: Closed  
**Resolution Date**: January 2025  
**Fixed In Version**: v1.6.5-nginx-sms-fix  

## Executive Summary

Photo uploads during the registration process are failing with HTTP 413 "Request Entity Too Large" errors. This is blocking users from completing their registration as photo upload is a required step (routine 34 of 35).

## Error Details

### Browser Console Errors
```
Failed to load resource: the server responded with a status of 413 ()
<head><title>413 Request Entity Too Large</title></head>
<body>
<center><h1>413 Request Entity Too Large</h1></center>
<hr><center>nginx/1.26.0</center>
</body>
```

### Affected Endpoint
- `/api/upload` - Photo upload endpoint

## Root Cause Analysis

The nginx proxy in AWS Elastic Beanstalk has a default `client_max_body_size` limit (typically 1MB) that is rejecting photo uploads before they reach the FastAPI application.

### Current Configuration Mismatch
- **Frontend limit**: 10MB (defined in `chat-input.tsx`)
- **Backend expectation**: Handles up to 10MB files
- **Nginx default**: ~1MB (blocking larger uploads)

## Solution

Two configuration files have been created to fix this issue:

### 1. Primary Solution: `.ebextensions/01_nginx.config`
```yaml
files:
  "/etc/nginx/conf.d/proxy.conf":
    mode: "000644"
    owner: root
    group: root
    content: |
      client_max_body_size 20M;
      client_body_buffer_size 20M;

container_commands:
  01_reload_nginx:
    command: "sudo service nginx reload"
```

### 2. Alternative Solution: `.platform/nginx/conf.d/proxy.conf`
```
client_max_body_size 20M;
client_body_buffer_size 20M;
proxy_read_timeout 300;
proxy_connect_timeout 300;
proxy_send_timeout 300;
```

## Deployment Instructions

### Quick Fix Deployment

1. **Create deployment package with the fix**:
   ```bash
   cd backend
   # Ensure .ebextensions is included
   ls -la .ebextensions/  # Should show 01_nginx.config
   
   # Create new version (increment version number)
   zip -r ../utjfc-backend-v1.6.5-nginx-fix.zip . -x '*.pyc' '__pycache__/*' '*.pytest_cache*' 'test_*.py' '*.log' '.venv/*' 'venv/*' '.env*' '*.db'
   cd ..
   ```

2. **Deploy using existing process**:
   ```bash
   # Upload to S3
   aws --profile footballclub s3 cp utjfc-backend-v1.6.5-nginx-fix.zip s3://elasticbeanstalk-eu-north-1-650251723700-1/ --no-cli-pager
   
   # Create application version
   aws --profile footballclub elasticbeanstalk create-application-version \
     --application-name "utjfc-registration-backend" \
     --version-label "v1.6.5-nginx-fix" \
     --source-bundle S3Bucket="elasticbeanstalk-eu-north-1-650251723700-1",S3Key="utjfc-backend-v1.6.5-nginx-fix.zip" \
     --no-cli-pager
   
   # Deploy to environment
   aws --profile footballclub elasticbeanstalk update-environment \
     --environment-name "utjfc-backend-prod-2" \
     --version-label "v1.6.5-nginx-fix" \
     --no-cli-pager
   ```

3. **Monitor deployment**:
   ```bash
   aws --profile footballclub elasticbeanstalk describe-events --environment-name "utjfc-backend-prod-2" --max-records 10 --no-cli-pager
   ```

## Testing Instructions

After deployment (wait 5-10 minutes for propagation):

1. **Test with a sample image**:
   - Go to registration flow
   - Reach photo upload step (routine 34)
   - Upload a photo between 5-10MB
   - Should upload successfully without 413 error

2. **Verify via curl** (if you have a test image):
   ```bash
   curl -X POST https://d1ahgtos8kkd8y.cloudfront.net/api/upload \
     -F "file=@large_test_image.jpg" \
     -F "session_id=test-session" \
     -F "routine_number=34" \
     -v
   ```

## Additional Context

### Why 20MB limit?
- Frontend validates up to 10MB
- 20MB nginx limit provides buffer for:
  - Base64 encoding overhead
  - Form data overhead
  - Future increases without redeployment

### File Size Validation Chain
1. **Frontend**: 10MB limit with user-friendly error
2. **Nginx**: 20MB limit (hard stop with 413)
3. **Backend**: Should also validate file size

### Related Files
- `frontend/web/src/app/chat/_components/chat-input.tsx` - Frontend validation
- `backend/registration_agent/tools/registration_tools/upload_photo_to_s3_tool.py` - Backend handler
- `backend/.ebextensions/01_nginx.config` - Nginx configuration

## Long-term Recommendations

1. **Add backend file size validation** to provide better error messages
2. **Consider image compression** on frontend before upload
3. **Add progress indicators** for large file uploads
4. **Monitor nginx logs** for other potential limits

## Impact if Not Fixed

- Users cannot complete registration
- Registration abandonment at step 34/35
- Poor user experience
- Potential loss of registrations

## References

- [AWS EB Nginx Configuration](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/java-se-nginx.html)
- [Nginx client_max_body_size Documentation](http://nginx.org/en/docs/http/ngx_http_core_module.html#client_max_body_size)
- [HTTP 413 Status Code](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/413)

## Resolution

### What Was Done

1. **Created nginx configuration files** to increase upload limits:
   - `.ebextensions/01_nginx.config` - Standard EB configuration
   - `.platform/nginx/conf.d/proxy.conf` - Alternative for newer platforms
   
2. **Set nginx parameters**:
   - `client_max_body_size 20M` - Allows up to 20MB uploads
   - `client_body_buffer_size 20M` - Buffers large uploads
   - Added timeout settings for large uploads

3. **Fixed SMS payment link** (bonus fix in same deployment):
   - Updated from `https://utjfc.ngrok.app` to production CloudFront URL
   - Removed unused redirect_uri parameter

4. **Deployed to production** as v1.6.5-nginx-sms-fix on January 2025

### Verification

- Deployment completed successfully at 05:33:12 UTC
- Environment Status: Ready
- Health: Green/OK
- Chat endpoint tested and working
- Ready for photo upload testing 