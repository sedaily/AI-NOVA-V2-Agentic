#!/bin/bash

# NOVA Frontend Deployment Script
# Deploys to S3 and invalidates CloudFront cache

set -e

# Configuration
S3_BUCKET="ai-agent-nova-frontend-202602"
CLOUDFRONT_DISTRIBUTION_ID="E3SWAW1GMJ762G"
REGION="ap-northeast-2"

echo "========================================"
echo "  NOVA Frontend Deployment"
echo "========================================"
echo ""

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "Error: package.json not found. Run this script from the frontend directory."
    exit 1
fi

# Step 1: Build
echo "[1/3] Building production bundle..."
npm run build

if [ ! -d "dist" ]; then
    echo "Error: Build failed. dist folder not found."
    exit 1
fi

echo "Build completed successfully."
echo ""

# Step 2: Upload to S3
echo "[2/3] Uploading to S3: $S3_BUCKET..."
aws s3 sync dist/ s3://$S3_BUCKET/ \
    --region $REGION \
    --delete \
    --cache-control "max-age=31536000,public" \
    --exclude "index.html" \
    --exclude "*.json"

# Upload HTML and JSON files with no-cache
aws s3 cp dist/index.html s3://$S3_BUCKET/index.html \
    --region $REGION \
    --cache-control "no-cache,no-store,must-revalidate" \
    --content-type "text/html"

echo "S3 upload completed."
echo ""

# Step 3: Invalidate CloudFront cache
echo "[3/3] Invalidating CloudFront cache..."
INVALIDATION_ID=$(aws cloudfront create-invalidation \
    --distribution-id $CLOUDFRONT_DISTRIBUTION_ID \
    --paths "/*" \
    --query 'Invalidation.Id' \
    --output text)

echo "CloudFront invalidation created: $INVALIDATION_ID"
echo ""

# Get CloudFront domain
CLOUDFRONT_DOMAIN=$(aws cloudfront get-distribution \
    --id $CLOUDFRONT_DISTRIBUTION_ID \
    --query 'Distribution.DomainName' \
    --output text)

echo "========================================"
echo "  Deployment Complete!"
echo "========================================"
echo ""
echo "CloudFront URL: https://$CLOUDFRONT_DOMAIN"
echo ""
echo "Note: CloudFront cache invalidation may take a few minutes."
