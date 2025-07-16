#!/bin/bash

# Deployment commands for restart chat feature v1.6.21

echo "🚀 Starting deployment of restart chat feature..."

# Navigate to project root
cd "/Users/leehayton/Cursor Projects/utjfc_reg_agent"

# Commit changes
echo "📦 Committing changes..."
git add .
git commit -m "feat: implement registration resume for disconnected users

- Add check_if_record_exists_in_db core function for database record lookup
- Add check_if_record_exists_in_db_tool with OpenAI schema and handler
- Update routine 2 with resume logic (steps 5-8) based on existing records
- Register new tool in __init__.py, agents_reg.py, and registration_agents.py
- Enable users to resume registration after accidental disconnection
- Route based on played_for_urmston_town_last_season field and kit requirements
- Create comprehensive test suite in organized directory structure
- Update feature documentation with new organizational structure

This addresses the 50% disconnection rate at payment SMS step by allowing
users to resume their registration without re-entering all data.

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"

# Step 1: Navigate to backend directory
echo "📁 Navigating to backend directory..."
cd backend

# Step 2: Create deployment package
echo "📦 Creating deployment package v1.6.21..."
zip -r ../utjfc-backend-v1.6.21.zip . \
  -x '*.pyc' '__pycache__/*' '*.pytest_cache*' 'test_*.py' \
     '*.log' '.venv/*' 'venv/*' '.env*' '*.db'

# Step 3: Return to root
cd ..

# Step 4: Upload to S3
echo "☁️ Uploading to S3..."
aws --profile footballclub s3 cp utjfc-backend-v1.6.21.zip \
  s3://elasticbeanstalk-eu-north-1-650251723700-1/ --no-cli-pager

# Step 5: Create application version
echo "📋 Creating application version..."
aws --profile footballclub elasticbeanstalk create-application-version \
  --application-name "utjfc-registration-backend" \
  --version-label "v1.6.21" \
  --source-bundle S3Bucket="elasticbeanstalk-eu-north-1-650251723700-1",S3Key="utjfc-backend-v1.6.21.zip" \
  --no-cli-pager

# Step 6: Deploy to production
echo "🚀 Deploying to production..."
aws --profile footballclub elasticbeanstalk update-environment \
  --environment-name "utjfc-backend-prod-3" \
  --version-label "v1.6.21" \
  --no-cli-pager

echo "✅ Deployment initiated! Monitoring..."

# Step 7: Monitor deployment
echo "👀 Checking deployment status..."
aws --profile footballclub elasticbeanstalk describe-events \
  --environment-name "utjfc-backend-prod-3" \
  --max-records 10 --no-cli-pager

echo "🏥 Checking environment health..."
aws --profile footballclub elasticbeanstalk describe-environments \
  --environment-names "utjfc-backend-prod-3" --no-cli-pager

echo "🔍 Testing health endpoint..."
curl https://d1ahgtos8kkd8y.cloudfront.net/api/health

echo "🎉 Deployment complete! Please verify the health endpoint shows 'healthy' status."