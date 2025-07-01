# UTJFC Registration Agent - AWS Deployment Strategy (Optimized)

## Project Overview
Deploy a full-stack registration agent system consisting of:
- **Backend**: FastAPI application with OpenAI SDK (Responses API) for AI-powered registration assistance
- **Frontend**: Next.js chat interface deployed as static files for optimal cost and performance
- **Domain Integration**: Frontend accessible via existing Hostinger domain at `/chat` route

## Architecture Summary
```
User → urmstontownjfc.co.uk/chat/* → CloudFront → S3 Static Website (Next.js Frontend)
                                                    ↓ API calls
                                              AWS Elastic Beanstalk (FastAPI Backend)
```

## Cost Optimization Analysis
**Previous Strategy (Dual EB):**
- Frontend EB: ~$15-20/month
- Backend EB: ~$15-20/month  
- **Total: ~$35-40/month**

**Optimized Strategy (S3 + EB):**
- Frontend S3 + CloudFront: ~$1-3/month
- Backend EB: ~$15-20/month
- **Total: ~$18-22/month**
- **Annual Savings: ~$200-250**

## Static Export Validation ✅
**Test Results**: Frontend successfully exports to static files
- ✅ All pages export correctly (`/`, `/chat`)
- ✅ All assets bundled (`_next/`, images, fonts)
- ✅ No server-side dependencies blocking static hosting
- ✅ Chat functionality works with external API calls

## File Structure Context
The project is located in `/utjfc_reg_agent/` with:
- `backend/` - FastAPI application with OpenAI agents and tools
- `frontend/web/` - Next.js application (static export compatible)

## Deployment Strategy: Backend EB + Frontend S3

### Why This Architecture?
- **Cost Optimized** - 50%+ cost reduction vs dual EB
- **Performance** - CloudFront CDN provides global edge caching
- **Scalability** - S3 handles unlimited traffic spikes at no extra cost
- **Simplicity** - Static files eliminate server management for frontend
- **Future-proof** - Easy to migrate backend to serverless later if needed

## Step 1: Backend Deployment (FastAPI on Elastic Beanstalk)

### 1.1 Prepare Backend for Deployment
- **Location**: `/utjfc_reg_agent/backend/`
- **Create Dockerfile** if not exists for FastAPI application
- **Environment variables**: Prepare `.env` configuration for:
  - OpenAI API keys
  - Airtable credentials
  - GoCardless API keys
  - Twilio credentials
  - AWS S3 credentials

### 1.2 Deploy Backend to Elastic Beanstalk
- **Create EB Application**: `utjfc-agent-backend`
- **Environment name**: `utjfc-agent-backend-prod`
- **Platform**: Docker
- **Region**: Choose consistent with S3 bucket region
- **Configuration**:
  - Instance type: t3.small (can scale up later)
  - Auto-scaling: Min 1, Max 3 instances
  - Load balancer: Application Load Balancer
  - Health check: Configure for FastAPI health endpoint

#### Concurrent User Capacity
- **One backend instance** can handle **50-200 concurrent users**
- **For 150 seasonal users**: Single instance with auto-scaling is sufficient
- **Auto-scaling triggers**: CPU/memory thresholds spin up additional instances
- **Cost consideration**: Max 3 instances provides ample headroom

### 1.3 Backend Access Pattern
- **Backend URL**: `http://utjfc-agent-backend-prod.region.elasticbeanstalk.com`
- **CORS Configuration**: Allow requests from CloudFront distribution domain
- **API Documentation**: Available at `/docs` endpoint

## Step 2: Frontend Deployment (S3 Static Website + CloudFront)

### 2.1 Prepare Frontend for Static Export
- **Location**: `/utjfc_reg_agent/frontend/web/`
- **Modify next.config.ts** for production static export:

```typescript
const nextConfig: NextConfig = {
  output: 'export',
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
  // Environment variables for production
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'https://your-backend-url.elasticbeanstalk.com'
  }
};
```

### 2.2 Build and Export Static Files
```bash
cd frontend/web
npm run build  # Generates static files in 'out' directory
```

### 2.3 Deploy to S3
- **Create S3 Bucket**: `utjfc-chat-frontend`
- **Enable Static Website Hosting**: 
  - Index document: `index.html`
  - Error document: `404.html`
- **Upload static files**: Contents of `out/` directory
- **Bucket Policy**: Public read access for web assets

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::utjfc-chat-frontend/*"
    }
  ]
}
```

## Step 3: Domain Integration with CloudFront

### 3.1 CloudFront Distribution Setup
Create CloudFront distribution with multiple origins:

#### Origin 1: S3 Static Website (Frontend)
- **Origin domain**: S3 bucket website endpoint (not the bucket itself)
- **Origin path**: `/`
- **Custom headers**: None required

#### Origin 2: Hostinger (Main Website)  
- **Origin domain**: Current Hostinger hosting IP/domain
- **Origin path**: `/`
- **Custom headers**: Host header forwarding if required

### 3.2 CloudFront Behaviors Configuration
```
Precedence | Path Pattern | Origin          | Cache Behavior
0          | /chat*       | S3 Frontend     | Cache optimized for SPA
1          | /_next/*     | S3 Frontend     | Long-term caching for assets  
2          | *.js         | S3 Frontend     | Long-term caching
3          | *.css        | S3 Frontend     | Long-term caching
4          | *.png        | S3 Frontend     | Long-term caching
5          | *.svg        | S3 Frontend     | Long-term caching
6          | *            | Hostinger       | Pass-through (default)
```

### 3.3 Cache Configuration
- **Static assets** (`/_next/*`, `*.js`, `*.css`): Long-term caching (1 year)
- **HTML files** (`/chat*`): Short-term caching (5 minutes) for updates
- **API calls**: No caching (pass-through to backend)

### 3.4 SSL Certificate
- Use existing SSL certificate for the domain
- Ensure certificate covers all paths including `/chat`

## Step 4: Environment Variables and Configuration

### 4.1 Backend Environment Variables
```
# OpenAI Configuration
OPENAI_API_KEY=your_openai_key

# Database Configuration  
AIRTABLE_API_KEY=your_airtable_key
AIRTABLE_BASE_ID=your_base_id

# Payment Integration
GOCARDLESS_API_KEY=your_gocardless_key

# SMS Integration
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=your_twilio_number

# CORS Configuration
CORS_ORIGINS=https://urmstontownjfc.co.uk

# File Storage
AWS_S3_BUCKET=utjfc-player-photos
```

### 4.2 Frontend Environment Variables (Build Time)
```
# API Configuration
NEXT_PUBLIC_API_URL=https://utjfc-agent-backend-prod.region.elasticbeanstalk.com

# Build Configuration
NODE_ENV=production
```

## Step 5: Testing and Validation

### 5.1 Backend Testing
- Test EB environment directly via EB URL
- Verify all API endpoints respond correctly
- Test OpenAI agent functionality and tool execution
- Validate external service integrations (Airtable, GoCardless, Twilio)
- Confirm CORS headers allow frontend domain

### 5.2 Frontend Testing  
- Test S3 website endpoint directly
- Verify all routes load correctly (`/`, `/chat`)
- Test static asset loading (CSS, JS, images)
- Confirm responsive design on mobile devices

### 5.3 End-to-End Testing
- Test complete flow via `urmstontownjfc.co.uk/chat`
- Verify CloudFront routing works correctly
- Test full registration conversation flow
- Validate file upload functionality
- Test payment link generation and SMS delivery
- Verify conversation state persistence across page reloads

## Step 6: CORS and Security Configuration

### 6.1 Backend CORS Setup
Configure FastAPI CORS to allow requests from:
- `https://urmstontownjfc.co.uk` (CloudFront domain)
- Backend EB URL (for direct testing)

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://urmstontownjfc.co.uk",
        "https://utjfc-agent-backend-prod.region.elasticbeanstalk.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 6.2 CloudFront Security Headers
Configure CloudFront to forward necessary headers:
- `Origin`
- `Access-Control-Request-Method` 
- `Access-Control-Request-Headers`
- `Content-Type` (for file uploads)

## Deployment Execution Order
1. **Deploy Backend** → Get EB URL for frontend configuration
2. **Configure Frontend** → Update API URL in build configuration
3. **Build Static Frontend** → Generate optimized static files
4. **Deploy to S3** → Upload static files with public access
5. **Configure CloudFront** → Set up distribution with path routing
6. **Test End-to-End** → Verify complete registration flow

## Post-Deployment Monitoring and Maintenance

### Cost Monitoring
- **S3 Storage**: ~$0.023 per GB (minimal for static files)
- **CloudFront**: ~$0.085 per GB transfer + $0.01 per 10,000 requests
- **EB Backend**: Fixed monthly cost based on instance type
- **Expected Monthly Cost**: $18-22 total

### Performance Monitoring
- **CloudWatch**: Monitor EB backend performance and auto-scaling
- **CloudFront Reports**: Track cache hit ratios and global performance
- **Real User Monitoring**: Consider adding analytics for user experience

### Maintenance Tasks
- **Frontend Updates**: Rebuild and redeploy static files to S3
- **Backend Updates**: Deploy through EB as usual
- **SSL Certificate**: Renew annually through AWS Certificate Manager
- **Cache Invalidation**: Clear CloudFront cache when frontend updates

## Success Criteria
- ✅ Users can access chat interface at `urmstontownjfc.co.uk/chat`
- ✅ Static frontend loads in <2 seconds globally
- ✅ Chat interface successfully connects to backend API
- ✅ Complete registration flow works end-to-end
- ✅ File uploads function correctly through CloudFront
- ✅ OpenAI agents respond appropriately
- ✅ External integrations work (Airtable, GoCardless, Twilio)
- ✅ Main website on Hostinger remains unaffected
- ✅ Monthly costs reduced by 50%+ vs original dual-EB strategy

## Rollback Strategy
If issues arise with static hosting:
1. **Quick Fix**: Deploy frontend to EB as originally planned
2. **Update CloudFront**: Point `/chat/*` behavior to frontend EB origin
3. **Cost Impact**: Returns to original $35-40/month but maintains functionality

This optimized architecture provides the best balance of cost, performance, and maintainability for your seasonal usage pattern. 