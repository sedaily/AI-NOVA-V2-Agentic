# ============================================
# Regression ONE Frontend Deployment (PowerShell)
# ============================================
# Target: https://d1y2rjuowlwn37.cloudfront.net
# ============================================

$ErrorActionPreference = "Stop"

# Configuration
$S3_BUCKET = "sedaily-column-frontend-1764856283"
$CLOUDFRONT_ID = "E2Y96Q11K5DVPS"
$REGION = "ap-northeast-2"
$CLOUDFRONT_DOMAIN = "d1y2rjuowlwn37.cloudfront.net"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "   Regression ONE Frontend Deployment" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "S3 Bucket: $S3_BUCKET" -ForegroundColor Gray
Write-Host "CloudFront ID: $CLOUDFRONT_ID" -ForegroundColor Gray
Write-Host "Domain: $CLOUDFRONT_DOMAIN" -ForegroundColor Gray
Write-Host ""

# Navigate to frontend
Set-Location -Path "frontend"

# Install dependencies
Write-Host "📦 Installing NPM packages..." -ForegroundColor Yellow
npm install

# Build
Write-Host "🔨 Building frontend..." -ForegroundColor Yellow
npm run build

Write-Host "✅ Frontend build complete" -ForegroundColor Green

# Upload to S3
Write-Host ""
Write-Host "📤 Uploading to S3..." -ForegroundColor Yellow
aws s3 sync dist/ "s3://$S3_BUCKET/" --delete --region $REGION

Write-Host "✅ S3 upload complete" -ForegroundColor Green

# Invalidate CloudFront cache
Write-Host ""
Write-Host "🔄 Invalidating CloudFront cache..." -ForegroundColor Yellow
$INVALIDATION_ID = aws cloudfront create-invalidation `
    --distribution-id $CLOUDFRONT_ID `
    --paths "/*" `
    --query 'Invalidation.Id' `
    --output text

Write-Host "✅ CloudFront cache invalidation requested (ID: $INVALIDATION_ID)" -ForegroundColor Green

# Output results
Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host "✅ Deployment Complete!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Access URL:" -ForegroundColor Cyan
Write-Host "   - https://$CLOUDFRONT_DOMAIN" -ForegroundColor White
Write-Host ""
Write-Host "⏳ CloudFront cache invalidation takes 1-2 minutes." -ForegroundColor Yellow
Write-Host ""
Write-Host "📋 Deployment Info:" -ForegroundColor Cyan
Write-Host "   Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host "   S3 Bucket: s3://$S3_BUCKET/" -ForegroundColor Gray
Write-Host "   CloudFront ID: $CLOUDFRONT_ID" -ForegroundColor Gray
Write-Host "   Invalidation ID: $INVALIDATION_ID" -ForegroundColor Gray
Write-Host ""

# Return to original directory
Set-Location -Path ".."
