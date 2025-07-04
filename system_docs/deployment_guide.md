# UTJFC Registration System - Production Deployment Guide

**Version**: 1.1  
**Date**: January 2025 (Updated from July 2, 2025)  
**Purpose**: This document provides a complete, step-by-step guide for deploying updates to the production frontend and backend of the UTJFC Registration System. It is designed to be used by developers or AI agents to ensure consistent and safe deployments.

---

## 1. System Architecture Overview

Before deploying, it is crucial to understand the high-level architecture:

*   **Backend**: A FastAPI application running in a Docker container, managed by **AWS Elastic Beanstalk**.
*   **Frontend**: A statically exported Next.js application, hosted on **AWS S3** and served globally via **AWS CloudFront**.
*   **API Routing**: CloudFront acts as a reverse proxy, routing requests starting with `/api/` to the Elastic Beanstalk backend. This solves the mixed-content (HTTPS/HTTP) issue and provides a single public domain for the entire application.

---

## 2. Prerequisites

1.  **AWS CLI**: The AWS Command Line Interface must be installed and configured.
2.  **AWS Profile**: An AWS credentials profile named `footballclub` must be configured with the necessary permissions for Elastic Beanstalk, S3, and CloudFront. All AWS commands in this guide use this profile.
3.  **Node.js & npm**: Required for building the frontend application.
4.  **Workspace Root**: All commands should be run from the root directory of the project repository unless otherwise specified.

### Important: AWS CLI Pager Issue for AI Agents

**Problem**: If you're an AI agent using terminal execution tools, you may encounter errors like:
```
head: |: No such file or directory
head: cat: No such file or directory
```

This happens because terminal execution tools often set `PAGER="head -n 10000 | cat"`, which AWS CLI misinterprets.

**Solution**: Always use one of these approaches:

1. **Recommended**: Add `--no-cli-pager` to all AWS commands in this guide:
   ```bash
   aws --profile footballclub --no-cli-pager <command>
   ```

2. **Alternative**: Clear the pager for each command:
   ```bash
   AWS_PAGER="" aws --profile footballclub <command>
   ```

All commands in this guide now include `--no-cli-pager` to prevent this issue.

---

## 3. Backend Deployment Process

Follow these steps to deploy changes made within the `backend/` directory.

### Step 3.1: Create the Deployment Package

The application is deployed as a zip archive. It is critical to exclude development artifacts, test files, and local environment files.

1.  **Navigate to the backend directory**:
    ```bash
    cd backend
    ```

2.  **Create the zip archive**. **IMPORTANT**: Update `[vX.X.X]` to the new version number. This version label will be used in subsequent AWS commands.

    ```bash
    # Example version: v1.6.4
    zip -r ../utjfc-backend-v1.6.4.zip . -x '*.pyc' '__pycache__/*' '*.pytest_cache*' 'test_*.py' '*.log' '.venv/*' 'venv/*' '.env*' '*.db'
    ```

3.  **Return to the root directory**:
    ```bash
    cd ..
    ```

### Step 3.2: Upload the Package to S3

Elastic Beanstalk pulls the application code from a designated S3 bucket.

1.  **Upload the new version**. Replace `[vX.X.X]` with the same version number used in the previous step.

    ```bash
    aws --profile footballclub s3 cp utjfc-backend-v[vX.X.X].zip s3://elasticbeanstalk-eu-north-1-650251723700-1/ --no-cli-pager
    ```

### Step 3.3: Create a New Application Version

Register the uploaded package as a new version in Elastic Beanstalk.

1.  **Create the application version**. Replace `[vX.X.X]` with your new version number and `[zip-file-name]` with the full name of the zip file.

    ```bash
    aws --profile footballclub elasticbeanstalk create-application-version \
      --application-name "utjfc-registration-backend" \
      --version-label "v[vX.X.X]" \
      --source-bundle S3Bucket="elasticbeanstalk-eu-north-1-650251723700-1",S3Key="[zip-file-name]" \
      --no-cli-pager
    ```

### Step 3.4: Deploy to the Production Environment

Trigger the environment update to pull the new version and deploy it.

1.  **Execute the update**. Replace `[vX.X.X]` with your new version label.

    ```bash
    aws --profile footballclub elasticbeanstalk update-environment \
      --environment-name "utjfc-backend-prod-3" \
      --version-label "v[vX.X.X]" \
      --no-cli-pager
    ```

### Step 3.5: Verify the Deployment

1.  **Monitor deployment events**:
    ```bash
    aws --profile footballclub elasticbeanstalk describe-events --environment-name "utjfc-backend-prod-3" --max-records 10 --no-cli-pager
    ```
2.  **Check environment health**. Wait for the `Status` to return to `Ready` and `Health` to become `Green`.
    ```bash
    aws --profile footballclub elasticbeanstalk describe-environments --environment-names "utjfc-backend-prod-3" --no-cli-pager
    ```
3.  **Test the health endpoint** via the CloudFront proxy:
    ```bash
    curl https://d1ahgtos8kkd8y.cloudfront.net/api/health
    # Expected output: {"status":"healthy","message":"UTJFC Registration Backend is running"}
    ```

---

## 4. Frontend Deployment Process

Follow these steps to deploy changes made within the `frontend/web/` directory.

### Step 4.1: Build the Static Site

1.  **Navigate to the frontend directory**:
    ```bash
    cd frontend/web
    ```
2.  **Install dependencies** (if not already done):
    ```bash
    npm install
    ```
3.  **Build the application**. This generates the static files in the `out/` directory.
    ```bash
    npm run build
    ```

### Step 4.2: Sync Files to S3

Upload the contents of the `out/` directory to the S3 bucket that serves as the CloudFront origin. The `--delete` flag removes any old files that are no longer part of the build.

**IMPORTANT**: The output structure (`page.html` vs. `page/index.html`) is controlled by the `trailingSlash` setting in `frontend/web/next.config.ts`. This is set to `true` to produce `chat/index.html`. If this is ever changed, the CloudFront configuration may also need to be updated.

1.  **Execute the sync command**:
    ```bash
    aws --profile footballclub s3 sync out/ s3://utjfc-frontend-chat/ --delete --no-cli-pager
    ```

### Step 4.3: Invalidate the CloudFront Cache

To ensure users see the latest version immediately, you must invalidate the CloudFront edge caches.

1.  **Create the invalidation**. This command invalidates all files.
    ```bash
    aws --profile footballclub cloudfront create-invalidation \
      --distribution-id E2WNKV9R9SX5XH \
      --paths "/*" \
      --no-cli-pager
    ```
    *Note: CloudFront invalidations can take several minutes to complete.*

### Step 4.4: Verify the Deployment

1.  Open a browser and navigate to `https://urmstontownjfc.co.uk/chat/`. You may need to perform a hard refresh (Ctrl+Shift+R or Cmd+Shift+R) to bypass your local browser cache.

---

## 5. Managing Environment Variables

**CRITICAL**: Sensitive keys must **never** be stored in code or `.env` files. They are managed directly in the Elastic Beanstalk environment configuration.

### To Update an Environment Variable:

1.  Log in to the **AWS Management Console**.
2.  Navigate to the **Elastic Beanstalk** service.
3.  Select the `utjfc-backend-prod-3` environment.
4.  Go to **Configuration** -> **Software** -> **Edit**.
5.  Scroll down to **Environment properties** and add or modify the variables.
6.  Click **Apply**.

This action will automatically trigger an environment update, which takes a few minutes. **You do not need to redeploy the application code via zip file when only changing an environment variable.**

### To Verify the Update:

1.  **Check the environment status** to ensure it has returned to `Ready` and `Green`:
    ```bash
    aws --profile footballclub elasticbeanstalk describe-environments --environment-names "utjfc-backend-prod-3" --no-cli-pager
    ```
2.  **Inspect the configuration** to confirm the variable was updated correctly. Look for the `aws:elasticbeanstalk:application:environment` namespace in the output.
    ```bash
    aws --profile footballclub elasticbeanstalk describe-configuration-settings --application-name "utjfc-registration-backend" --environment-name "utjfc-backend-prod-3" --no-cli-pager
    ```

---

## 6. Critical Deployment Notes

-   **Current Production Environment**: The current production backend environment is `utjfc-backend-prod-3` (created July 2025 due to AWS Launch Configuration deprecation). If you need to create a new environment, use Launch Templates instead of Launch Configurations.
-   **CloudFront Configuration**: The CloudFront distribution points to `utjfc-backend-prod-3.eba-3bpsyeak.eu-north-1.elasticbeanstalk.com`. If a new backend environment is created, run the `update_cloudfront.py` script to update the CloudFront distribution.
-   **Nginx Configuration**: The backend uses `.platform/nginx/conf.d/proxy.conf` for nginx configuration. **Important**: Do not use `.ebextensions/01_nginx.config` as it conflicts with the modern platform approach and causes deployment failures with "nginx.service is not active, cannot reload" errors.
-   **CloudFront Path Rewriting**: A CloudFront Function named `utjfc-api-path-rewrite` is attached to the `/api/*` behavior. It strips the `/api` prefix from the URL before forwarding the request to the backend. The backend application itself does **not** use `/api` in its routes.
-   **Docker Port**: The `Dockerfile` in the backend **must** expose port `80`. The Elastic Beanstalk Nginx proxy is configured to route traffic to this port.
-   **Deployment Time**: CloudFront and Elastic Beanstalk updates are not instantaneous. Allow 5-15 minutes for changes to fully propagate.
-   **AWS CLI Pager**: All commands in this guide include `--no-cli-pager` to prevent issues with AI agents or environments where `PAGER` is set to non-standard values. 