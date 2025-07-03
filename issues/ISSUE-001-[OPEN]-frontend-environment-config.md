# Issue #001: Frontend Environment Configuration - Hardcoded API URLs

**Priority**: Medium  
**Type**: Configuration / Security  
**Component**: Frontend  
**Created**: January 2025  
**Status**: Open  

## Executive Summary

The frontend application has production API URLs hardcoded in the source code instead of using environment variables. This creates security, deployment, and maintenance issues.

## Current Implementation

### Location: `frontend/web/src/config/environment.ts`

```typescript
const isDevelopment = process.env.NODE_ENV === 'development';

export const config = {
  API_BASE_URL: isDevelopment 
    ? 'http://localhost:8000'
    : 'https://d1ahgtos8kkd8y.cloudfront.net/api',  // ← ISSUE: Hardcoded production URL
  
  get UPLOAD_URL() {
    return `${this.API_BASE_URL}/upload`;
  },
  
  get CHAT_URL() {
    return `${this.API_BASE_URL}/chat`;
  }
};
```

## Problems Identified

### 1. Security Risk
- CloudFront distribution URL is exposed in client-side code
- Anyone viewing the source can see your infrastructure details
- URL is committed to version control (GitHub)

### 2. Deployment Inflexibility
- Cannot change API URL without rebuilding the entire frontend
- No way to point to different backends for staging/testing
- Requires code changes for infrastructure updates

### 3. Development Workflow Issues
- Developers might accidentally commit changes to production URL
- No easy way to test against different backend environments
- Makes local development against remote backends difficult

### 4. Infrastructure Lock-in
- If CloudFront URL changes, requires code update and full deployment
- Cannot easily switch between environments (dev/staging/prod)
- No disaster recovery flexibility

## Proposed Solution

### Step 1: Update Configuration File

```typescript
// frontend/web/src/config/environment.ts
const isDevelopment = process.env.NODE_ENV === 'development';

// Use Next.js public environment variables (must be prefixed with NEXT_PUBLIC_)
export const config = {
  API_BASE_URL: process.env.NEXT_PUBLIC_API_URL || (isDevelopment 
    ? 'http://localhost:8000'
    : 'http://localhost:8000'), // Fallback only, not production URL
  
  get UPLOAD_URL() {
    return `${this.API_BASE_URL}/upload`;
  },
  
  get CHAT_URL() {
    return `${this.API_BASE_URL}/chat`;
  }
};

// Optional: Add validation
if (!process.env.NEXT_PUBLIC_API_URL && process.env.NODE_ENV === 'production') {
  console.warn('NEXT_PUBLIC_API_URL is not set in production environment');
}

export default config;
```

### Step 2: Create Environment Files

```bash
# frontend/web/.env.local (for local development - not committed to git)
NEXT_PUBLIC_API_URL=http://localhost:8000

# frontend/web/.env.development (for development builds)
NEXT_PUBLIC_API_URL=http://localhost:8000

# frontend/web/.env.production (for production builds)
# This file can be committed with a placeholder
NEXT_PUBLIC_API_URL=YOUR_PRODUCTION_API_URL_HERE

# frontend/web/.env.staging (optional - for staging environment)
NEXT_PUBLIC_API_URL=https://staging-api.yourdomain.com
```

### Step 3: Update .gitignore

```bash
# frontend/web/.gitignore
# Environment files
.env.local
.env.production.local
# Keep .env.production with placeholder committed
```

### Step 4: Update Deployment Process

For production deployments (e.g., Vercel, AWS Amplify, or custom):

1. Set environment variable in deployment platform:
   ```
   NEXT_PUBLIC_API_URL=https://d1ahgtos8kkd8y.cloudfront.net/api
   ```

2. For Docker deployments, update Dockerfile:
   ```dockerfile
   # Accept build arg
   ARG NEXT_PUBLIC_API_URL
   ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
   
   # Build command:
   # docker build --build-arg NEXT_PUBLIC_API_URL=https://your-api.com .
   ```

### Step 5: Create Documentation

Create `frontend/web/README.md` section:

```markdown
## Environment Configuration

This application uses environment variables for API configuration:

- `NEXT_PUBLIC_API_URL`: The backend API URL (required for production)

### Local Development
Copy `.env.example` to `.env.local` and update values:
```bash
cp .env.example .env.local
```

### Production Deployment
Set `NEXT_PUBLIC_API_URL` in your deployment platform's environment variables.
```

## Implementation Checklist

- [ ] Update `frontend/web/src/config/environment.ts` to use environment variables
- [ ] Create `.env.example` with documented variables
- [ ] Create `.env.local` for local development (add to .gitignore)
- [ ] Update `.gitignore` to exclude sensitive env files
- [ ] Remove hardcoded CloudFront URL from source
- [ ] Test with different environment configurations
- [ ] Update deployment documentation
- [ ] Configure environment variables in production deployment platform
- [ ] Verify production build uses correct API URL
- [ ] Add environment validation/warnings

## Testing Instructions

1. **Local Development Test**:
   ```bash
   cd frontend/web
   echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
   pnpm dev
   # Check browser console - should use localhost:8000
   ```

2. **Production Build Test**:
   ```bash
   cd frontend/web
   NEXT_PUBLIC_API_URL=https://test-api.com pnpm build
   pnpm start
   # Check browser console - should use test-api.com
   ```

3. **Missing Environment Variable Test**:
   ```bash
   cd frontend/web
   rm .env.local
   pnpm dev
   # Should fall back to default or show warning
   ```

## Additional Context

### Next.js Environment Variables
- Must be prefixed with `NEXT_PUBLIC_` to be available in browser
- Are inlined at build time (not runtime)
- Different from server-side environment variables
- See: https://nextjs.org/docs/basic-features/environment-variables

### Current Infrastructure
- Backend: FastAPI on port 8000
- Frontend: Next.js on port 3000  
- Production: CloudFront distribution
- The frontend makes API calls to `/chat` and `/upload` endpoints

### Related Files
- `frontend/web/src/app/chat/page.tsx` - Uses config for API calls
- `frontend/web/package.json` - Build scripts
- `frontend/web/Dockerfile` - Container configuration

## Impact Analysis

- **No breaking changes** for existing functionality
- **Improved security** by removing hardcoded URLs
- **Enhanced flexibility** for deployments
- **Better developer experience** with environment switching

## References

- [Next.js Environment Variables Documentation](https://nextjs.org/docs/basic-features/environment-variables)
- [12-Factor App Config](https://12factor.net/config)
- [Security Best Practices for Environment Variables](https://owasp.org/www-project-application-security-verification-standard/)

---

**Note for Developer**: When implementing this, ensure you have the current production API URL saved elsewhere before removing it from the code. The current production URL is: `https://d1ahgtos8kkd8y.cloudfront.net/api` 