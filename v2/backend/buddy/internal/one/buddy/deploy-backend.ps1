# Buddy (p2-two) Backend Deployment Script - PowerShell
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "   Buddy Backend Deployment" -ForegroundColor Cyan
Write-Host "   Target: p2-two Lambda Functions" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

$REGION = "us-east-1"
$BACKEND_DIR = "$PSScriptRoot\backend"
$TEMP_DIR = "$env:TEMP\lambda-deploy-buddy"

# Lambda 함수 목록
$LAMBDA_FUNCTIONS = @(
    "p2-two-websocket-message-two",
    "p2-two-websocket-connect-two",
    "p2-two-websocket-disconnect-two",
    "p2-two-conversation-api-two",
    "p2-two-prompt-crud-two",
    "p2-two-usage-handler-two"
)

Write-Host "`n[INFO] Packaging Lambda code..." -ForegroundColor Yellow

# 임시 디렉토리 생성
if (Test-Path $TEMP_DIR) { Remove-Item -Recurse -Force $TEMP_DIR }
New-Item -ItemType Directory -Path $TEMP_DIR -Force | Out-Null

# 소스 코드 복사
Write-Host "[INFO] Copying source files..." -ForegroundColor Yellow
Copy-Item -Recurse "$BACKEND_DIR\handlers" "$TEMP_DIR\" -ErrorAction SilentlyContinue
Copy-Item -Recurse "$BACKEND_DIR\src" "$TEMP_DIR\" -ErrorAction SilentlyContinue
Copy-Item -Recurse "$BACKEND_DIR\utils" "$TEMP_DIR\" -ErrorAction SilentlyContinue
Copy-Item -Recurse "$BACKEND_DIR\services" "$TEMP_DIR\" -ErrorAction SilentlyContinue
Copy-Item -Recurse "$BACKEND_DIR\lib" "$TEMP_DIR\" -ErrorAction SilentlyContinue

# pip 설치
Write-Host "[INFO] Installing dependencies..." -ForegroundColor Yellow
pip install -r "$BACKEND_DIR\requirements.txt" -t $TEMP_DIR --upgrade --quiet 2>$null

# __pycache__ 삭제
Get-ChildItem -Path $TEMP_DIR -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# ZIP 생성
Write-Host "[INFO] Creating deployment package..." -ForegroundColor Yellow
$ZIP_PATH = "$TEMP_DIR\deployment.zip"
if (Test-Path $ZIP_PATH) { Remove-Item $ZIP_PATH }
Compress-Archive -Path "$TEMP_DIR\*" -DestinationPath $ZIP_PATH -Force

$zipSize = [math]::Round((Get-Item $ZIP_PATH).Length / 1MB, 2)
Write-Host "[INFO] Package created: $zipSize MB" -ForegroundColor Green

# Lambda 함수 업데이트
Write-Host "`n[INFO] Deploying Lambda functions..." -ForegroundColor Yellow
$success = 0
$failed = 0

foreach ($func in $LAMBDA_FUNCTIONS) {
    Write-Host "  Deploying $func..." -NoNewline
    try {
        aws lambda update-function-code --function-name $func --zip-file "fileb://$ZIP_PATH" --region $REGION --output text 2>$null | Out-Null
        Write-Host " OK" -ForegroundColor Green
        $success++
    } catch {
        Write-Host " FAILED" -ForegroundColor Red
        $failed++
    }
}

# 정리
Remove-Item -Recurse -Force $TEMP_DIR -ErrorAction SilentlyContinue

Write-Host "`n=========================================" -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "Success: $success / $($LAMBDA_FUNCTIONS.Count)" -ForegroundColor $(if ($failed -eq 0) { "Green" } else { "Yellow" })
if ($failed -gt 0) { Write-Host "Failed: $failed" -ForegroundColor Red }
Write-Host "=========================================" -ForegroundColor Cyan
