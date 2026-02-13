#!/bin/bash

# ============================================
# Nexus Foreign - ONE Frontend Deployment
# ============================================
# Last Updated: 2025-12-24 (KST)
# Target: https://d1zig3y52jaq1s.cloudfront.net
# Backend: Shared f1-two stack (us-east-1)
# ============================================

set -e

# Configuration
STACK_NAME="nexus-foreign"
S3_BUCKET="nexus-frontend-20251204224751"
REGION="ap-northeast-2"
DISTRIBUTION_ID="E1Y608786VRTT5"
CLOUDFRONT_DOMAIN="d22634fcti3bhs.cloudfront.net"
CUSTOM_DOMAIN="d22634fcti3bhs.cloudfront.net"

echo "========================================="
echo "   Nexus Foreign - ONE Deployment"
echo "========================================="
echo ""
echo "Stack: ${STACK_NAME}"
echo "S3 Bucket: ${S3_BUCKET}"
echo "CloudFront ID: ${DISTRIBUTION_ID}"
echo "Domain: ${CUSTOM_DOMAIN}"
echo ""

# Navigate to project root
cd "$(dirname "$0")"
PROJECT_ROOT=$(pwd)

# 1. Build frontend
echo "🔨 Building frontend..."
cd "${PROJECT_ROOT}/frontend"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing NPM packages..."
    npm install
fi

# Build
echo "⚙️  Running build..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Frontend build failed"
    exit 1
fi

echo "✅ Frontend build complete"

# 2. Upload to S3 (with correct MIME types)
echo ""
echo "📤 Uploading to S3..."

# Upload with correct content types to prevent MIME type errors
aws s3 sync dist/ "s3://${S3_BUCKET}/" --delete --region ${REGION} \
    --exclude "*.js" --exclude "*.css" --exclude "*.html"

# Upload JS files with correct MIME type
aws s3 cp dist/ "s3://${S3_BUCKET}/" --recursive --region ${REGION} \
    --exclude "*" --include "*.js" --content-type "application/javascript"

# Upload CSS files with correct MIME type
aws s3 cp dist/ "s3://${S3_BUCKET}/" --recursive --region ${REGION} \
    --exclude "*" --include "*.css" --content-type "text/css"

# Upload HTML files with correct MIME type
aws s3 cp dist/ "s3://${S3_BUCKET}/" --recursive --region ${REGION} \
    --exclude "*" --include "*.html" --content-type "text/html"

if [ $? -ne 0 ]; then
    echo "❌ S3 upload failed"
    exit 1
fi

echo "✅ S3 upload complete (MIME types applied)"

# 3. Invalidate CloudFront cache
echo ""
echo "🔄 Invalidating CloudFront cache..."
INVALIDATION_ID=$(aws cloudfront create-invalidation \
    --distribution-id ${DISTRIBUTION_ID} \
    --paths "/*" \
    --query 'Invalidation.Id' \
    --output text)

if [ $? -ne 0 ]; then
    echo "❌ CloudFront cache invalidation failed"
    exit 1
fi

echo "✅ CloudFront cache invalidation requested (ID: ${INVALIDATION_ID})"

# Output results
echo ""
echo "========================================="
echo "✅ Deployment Complete!"
echo "========================================="
echo ""
echo "🌐 Access URL:"
echo "   - https://${CUSTOM_DOMAIN}"
echo "   - https://${CLOUDFRONT_DOMAIN}"
echo ""
echo "⏳ CloudFront cache invalidation takes 1-2 minutes."
echo ""
echo "📋 Deployment Info:"
echo "   Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "   S3 Bucket: s3://${S3_BUCKET}/"
echo "   CloudFront ID: ${DISTRIBUTION_ID}"
echo "   Invalidation ID: ${INVALIDATION_ID}"
echo ""

cd "${PROJECT_ROOT}"
