# Buddy Internal 프론트엔드 배포 스크립트 (PowerShell)
# CloudFront: EJX326D0QZ4T1
# S3 Bucket: buddy-frontend-202512042253

$ErrorActionPreference = "Stop"

Write-Host "🚀 Buddy Internal 프론트엔드 배포 시작..." -ForegroundColor Cyan
Write-Host "📅 배포 시각: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host ""

# 설정
$S3_BUCKET = "buddy-frontend-202512042253"
$CLOUDFRONT_ID = "EJX326D0QZ4T1"
$REGION = "us-east-1"

# frontend 디렉토리로 이동
Set-Location -Path "frontend"

Write-Host "📦 의존성 설치 중..." -ForegroundColor Yellow
npm install

Write-Host "🔨 프론트엔드 빌드 중..." -ForegroundColor Yellow
npm run build

Write-Host "📤 S3에 업로드 중..." -ForegroundColor Yellow
Write-Host "   S3 버킷: s3://$S3_BUCKET/" -ForegroundColor Gray
aws s3 sync dist/ "s3://$S3_BUCKET/" --delete

Write-Host "🔄 CloudFront 캐시 무효화 중..." -ForegroundColor Yellow
Write-Host "   CloudFront 배포 ID: $CLOUDFRONT_ID" -ForegroundColor Gray
$INVALIDATION_RESULT = aws cloudfront create-invalidation `
    --distribution-id $CLOUDFRONT_ID `
    --paths "/*" `
    --query 'Invalidation.Id' `
    --output text

Write-Host ""
Write-Host "✅ 배포 완료!" -ForegroundColor Green
Write-Host "🌐 접속 URL:" -ForegroundColor Cyan
Write-Host "   - https://d3bwe2ohfohm85.cloudfront.net" -ForegroundColor White
Write-Host ""
Write-Host "📋 배포 정보:" -ForegroundColor Cyan
Write-Host "   배포 시각: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host "   S3 버킷: s3://$S3_BUCKET/" -ForegroundColor Gray
Write-Host "   CloudFront 배포 ID: $CLOUDFRONT_ID" -ForegroundColor Gray
Write-Host "   캐시 무효화 ID: $INVALIDATION_RESULT" -ForegroundColor Gray
Write-Host ""
Write-Host "⏳ CloudFront 캐시 무효화가 완료되기까지 2-3분 소요됩니다." -ForegroundColor Yellow

# 원래 디렉토리로 복귀
Set-Location -Path ".."
