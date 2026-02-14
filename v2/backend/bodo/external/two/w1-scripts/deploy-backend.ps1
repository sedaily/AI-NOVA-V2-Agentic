# W1 Backend Deployment Script for Windows
# ==========================================

$ErrorActionPreference = "Continue"

# Configuration
$AWS_REGION = "us-east-1"
$SERVICE_NAME = "w1"
$SECRET_NAME = "bodo-v1"
$ANTHROPIC_MODEL = "opus-4-20250514"
$ANTHROPIC_MAX_TOKENS = "4096"
$ANTHROPIC_TEMPERATURE = "0.3"
$ENABLE_NATIVE_WEB_SEARCH = "true"

$LAMBDA_FUNCTIONS = @(
    "w1-websocket-message",
    "w1-websocket-connect",
    "w1-websocket-disconnect",
    "w1-conversation-api",
    "w1-usage-handler",
    "w1-prompt-crud"
)

# Paths
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_ROOT = Split-Path -Parent $SCRIPT_DIR
$BACKEND_DIR = Join-Path $PROJECT_ROOT "backend"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "   W1 Backend Deployment" -ForegroundColor Cyan
Write-Host "   Target: w1.sedaily.ai Lambda Functions" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Package Lambda code
Write-Host "[INFO] Packaging Lambda code..." -ForegroundColor Green

Set-Location $BACKEND_DIR

# Clean previous package
if (Test-Path "package") {
    Write-Host "[INFO] Removing old package..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "package"
}
if (Test-Path "lambda-deployment.zip") {
    Remove-Item -Force "lambda-deployment.zip"
}

# Create package directory
New-Item -ItemType Directory -Path "package" | Out-Null

# Install dependencies
Write-Host "[INFO] Installing dependencies (this may take a while)..." -ForegroundColor Green
pip install -r requirements.txt -t ./package --quiet

# Copy source code
Write-Host "[INFO] Copying source code..." -ForegroundColor Green
Copy-Item -Recurse -Path "handlers" -Destination "package/handlers"
Copy-Item -Recurse -Path "services" -Destination "package/services"
Copy-Item -Recurse -Path "src" -Destination "package/src"
Copy-Item -Recurse -Path "lib" -Destination "package/lib"
Copy-Item -Recurse -Path "utils" -Destination "package/utils"

# Clean up __pycache__
Write-Host "[INFO] Cleaning up..." -ForegroundColor Green
Get-ChildItem -Path "package" -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
Get-ChildItem -Path "package" -Recurse -File -Filter "*.pyc" -ErrorAction SilentlyContinue | Remove-Item -Force

# Create zip
Write-Host "[INFO] Creating deployment package..." -ForegroundColor Green
Set-Location "package"
Compress-Archive -Path * -DestinationPath "../lambda-deployment.zip" -Force
Set-Location ..

$zipSize = (Get-Item "lambda-deployment.zip").Length / 1MB
Write-Host "[INFO] Package created: lambda-deployment.zip ($([math]::Round($zipSize, 2)) MB)" -ForegroundColor Green
Write-Host ""

# Step 2: Deploy to Lambda functions
Write-Host "[INFO] Deploying to Lambda functions..." -ForegroundColor Green
Write-Host ""

$successCount = 0
$total = $LAMBDA_FUNCTIONS.Count

foreach ($function in $LAMBDA_FUNCTIONS) {
    Write-Host "  Updating $function..." -NoNewline
    
    $output = aws lambda update-function-code `
        --function-name $function `
        --zip-file fileb://lambda-deployment.zip `
        --region $AWS_REGION `
        --output json 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host " OK" -ForegroundColor Green
        $successCount++
    }
    else {
        Write-Host " FAILED" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "[INFO] Deployed $successCount/$total functions successfully" -ForegroundColor Green
Write-Host ""

# Step 3: Update environment variables
Write-Host "Update environment variables? (y/n): " -NoNewline
$updateEnv = Read-Host

if ($updateEnv -eq "y" -or $updateEnv -eq "Y") {
    Write-Host ""
    Write-Host "[INFO] Updating environment variables..." -ForegroundColor Green
    Write-Host ""
    
    foreach ($function in $LAMBDA_FUNCTIONS) {
        Write-Host "  Configuring $function..." -NoNewline
        
        $output = aws lambda update-function-configuration `
            --function-name $function `
            --environment "Variables={USE_ANTHROPIC_API=true,ANTHROPIC_SECRET_NAME=$SECRET_NAME,ANTHROPIC_MODEL_ID=$ANTHROPIC_MODEL,AI_PROVIDER=anthropic_api,FALLBACK_TO_BEDROCK=true,MAX_TOKENS=$ANTHROPIC_MAX_TOKENS,TEMPERATURE=$ANTHROPIC_TEMPERATURE,ENABLE_NATIVE_WEB_SEARCH=$ENABLE_NATIVE_WEB_SEARCH,USE_OPUS_MODEL=true}" `
            --region $AWS_REGION `
            --output json 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host " OK" -ForegroundColor Green
        }
        else {
            Write-Host " FAILED" -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "   Deployment Complete!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Test the service at https://w1.sedaily.ai"
Write-Host "2. Monitor logs: aws logs tail /aws/lambda/w1-websocket-message --follow"
Write-Host ""

# Return to original directory
Set-Location $SCRIPT_DIR
