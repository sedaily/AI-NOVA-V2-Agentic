# W1 Frontend Deployment Script for Windows
# ===========================================

$ErrorActionPreference = "Continue"

# Configuration
$AWS_REGION = "us-east-1"
$FRONTEND_BUCKET = "w1-frontend"
$CLOUDFRONT_ID = "E10S6CKR5TLUBG"
$DOMAIN = "w1.sedaily.ai"

# Paths
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_ROOT = Split-Path -Parent $SCRIPT_DIR
$FRONTEND_DIR = Join-Path $PROJECT_ROOT "frontend"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "   W1 Frontend Deployment" -ForegroundColor Cyan
Write-Host "   Target: https://w1.sedaily.ai" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check if frontend directory exists
if (-not (Test-Path (Join-Path $FRONTEND_DIR "package.json"))) {
    Write-Host "[ERROR] Frontend directory not found" -ForegroundColor Red
    exit 1
}

Set-Location $FRONTEND_DIR

# Show current configuration
Write-Host "[INFO] Current configuration:" -ForegroundColor Green
if (Test-Path ".env") {
    Get-Content ".env" | Select-String "VITE_API_BASE_URL", "VITE_WS_URL" | ForEach-Object {
        Write-Host "  $_"
    }
}
Write-Host ""

# Step 1: Build frontend
Write-Host "[INFO] Building frontend..." -ForegroundColor Green

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "[INFO] Installing dependencies..." -ForegroundColor Yellow
    npm install
}

# Build the project
Write-Host "[INFO] Running build..." -ForegroundColor Green
npm run build

if (-not (Test-Path "dist")) {
    Write-Host "[ERROR] Build failed - dist directory not created" -ForegroundColor Red
    exit 1
}

Write-Host "[INFO] Build successful!" -ForegroundColor Green
Write-Host ""

# Step 2: Deploy to S3
Write-Host "[INFO] Deploying to S3..." -ForegroundColor Green

# Sync all files
aws s3 sync dist s3://$FRONTEND_BUCKET --delete --region $AWS_REGION --cache-control "public, max-age=3600"

# Set correct MIME types for JS files
Write-Host "[INFO] Setting correct MIME types for JS files..." -ForegroundColor Green
Get-ChildItem "dist/assets/*.js" -ErrorAction SilentlyContinue | ForEach-Object {
    $filename = $_.Name
    aws s3 cp $_.FullName "s3://$FRONTEND_BUCKET/assets/$filename" `
        --region $AWS_REGION `
        --content-type "application/javascript" `
        --cache-control "public, max-age=31536000" `
        --quiet
}

# Set correct MIME types for CSS files
Write-Host "[INFO] Setting correct MIME types for CSS files..." -ForegroundColor Green
Get-ChildItem "dist/assets/*.css" -ErrorAction SilentlyContinue | ForEach-Object {
    $filename = $_.Name
    aws s3 cp $_.FullName "s3://$FRONTEND_BUCKET/assets/$filename" `
        --region $AWS_REGION `
        --content-type "text/css" `
        --cache-control "public, max-age=31536000" `
        --quiet
}

# Set correct MIME type for HTML
Write-Host "[INFO] Setting correct MIME type for HTML..." -ForegroundColor Green
aws s3 cp "dist/index.html" "s3://$FRONTEND_BUCKET/index.html" `
    --region $AWS_REGION `
    --content-type "text/html; charset=utf-8" `
    --cache-control "public, max-age=3600" `
    --quiet

Write-Host "[INFO] S3 deployment complete" -ForegroundColor Green
Write-Host ""

# Step 3: Invalidate CloudFront cache
Write-Host "[INFO] Creating CloudFront invalidation..." -ForegroundColor Green

$invalidationOutput = aws cloudfront create-invalidation `
    --distribution-id $CLOUDFRONT_ID `
    --paths "/*" `
    --query 'Invalidation.Id' `
    --output text

Write-Host "[INFO] Invalidation created: $invalidationOutput" -ForegroundColor Green
Write-Host "  Note: Cache invalidation may take 5-10 minutes to complete" -ForegroundColor Yellow
Write-Host ""

# Step 4: Verify deployment
Write-Host "[INFO] Verifying deployment..." -ForegroundColor Green

$fileCount = (aws s3 ls "s3://$FRONTEND_BUCKET" --recursive --region $AWS_REGION | Measure-Object).Count
Write-Host "[INFO] Files uploaded to S3: $fileCount" -ForegroundColor Green

try {
    $response = Invoke-WebRequest -Uri "https://$DOMAIN" -Method Head -TimeoutSec 10 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "[INFO] Website responding: HTTP $($response.StatusCode) OK" -ForegroundColor Green
    }
}
catch {
    Write-Host "[WARNING] Website status check failed" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "   Frontend Deployment Complete!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Access the site: https://$DOMAIN" -ForegroundColor Yellow
Write-Host ""
Write-Host "Note: CloudFront cache invalidation in progress." -ForegroundColor Yellow
Write-Host "Full update may take 5-10 minutes." -ForegroundColor Yellow
Write-Host ""

Set-Location $SCRIPT_DIR
