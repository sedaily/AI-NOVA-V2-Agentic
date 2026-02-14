# Quick Deploy - Use existing package
# ====================================

$ErrorActionPreference = "Continue"

# Configuration
$AWS_REGION = "us-east-1"

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
Write-Host "   W1 Quick Backend Deployment" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $BACKEND_DIR

# Remove old zip
if (Test-Path "lambda-deployment.zip") {
    Remove-Item -Force "lambda-deployment.zip"
}

# Clean old source code from package
Write-Host "[INFO] Cleaning old source code..." -ForegroundColor Green
$foldersToClean = @("handlers", "services", "src", "lib", "utils")
foreach ($folder in $foldersToClean) {
    $path = Join-Path "package" $folder
    if (Test-Path $path) {
        Remove-Item -Recurse -Force $path
    }
}

# Copy new source code
Write-Host "[INFO] Copying updated source code..." -ForegroundColor Green
Copy-Item -Recurse -Path "handlers" -Destination "package/handlers"
Copy-Item -Recurse -Path "services" -Destination "package/services"
Copy-Item -Recurse -Path "src" -Destination "package/src"
Copy-Item -Recurse -Path "lib" -Destination "package/lib"
Copy-Item -Recurse -Path "utils" -Destination "package/utils"

# Clean up __pycache__
Get-ChildItem -Path "package" -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
Get-ChildItem -Path "package" -Recurse -File -Filter "*.pyc" -ErrorAction SilentlyContinue | Remove-Item -Force

# Create zip
Write-Host "[INFO] Creating deployment package..." -ForegroundColor Green
Set-Location "package"
Compress-Archive -Path * -DestinationPath "../lambda-deployment.zip" -Force
Set-Location ..

$zipSize = (Get-Item "lambda-deployment.zip").Length / 1MB
Write-Host "[INFO] Package created: $([math]::Round($zipSize, 2)) MB" -ForegroundColor Green
Write-Host ""

# Deploy to Lambda functions
Write-Host "[INFO] Deploying to Lambda functions..." -ForegroundColor Green
Write-Host ""

$successCount = 0
$total = $LAMBDA_FUNCTIONS.Count

foreach ($function in $LAMBDA_FUNCTIONS) {
    Write-Host "  $function..." -NoNewline
    
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
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "   Deployed $successCount/$total functions" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $SCRIPT_DIR
