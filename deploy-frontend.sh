#!/bin/bash

# UTJFC Frontend Deployment Script
# This script automates the complete frontend deployment process including CloudFront invalidation

set -e  # Exit on any error

echo "🚀 Starting UTJFC Frontend Deployment..."

# Change to frontend directory
cd frontend/web

echo "📦 Installing dependencies..."
npm install

echo "🔨 Building application..."
npm run build

echo "☁️  Syncing to S3..."
aws s3 sync out/ s3://utjfc-frontend-chat --profile footballclub --delete

echo "🗑️  Invalidating CloudFront cache..."
INVALIDATION_RESULT=$(aws cloudfront create-invalidation \
  --distribution-id E2WNKV9R9SX5XH \
  --paths "/*" \
  --profile footballclub \
  --query 'Invalidation.{Id:Id,Status:Status}' \
  --output json)

INVALIDATION_ID=$(echo $INVALIDATION_RESULT | grep -o '"Id":"[^"]*"' | cut -d'"' -f4)

echo "✅ Frontend deployed successfully!"
echo "📋 Invalidation ID: $INVALIDATION_ID"
echo "⏱️  Cache invalidation is in progress and may take 2-5 minutes to complete."
echo "🌐 Visit: https://urmstontownjfc.co.uk/chat/"
echo ""
echo "💡 Pro tip: Hard refresh your browser (Ctrl+Shift+R) to bypass local cache."

# Return to root directory
cd ../..