#!/bin/bash

# AWS 리소스 정리 스크립트
# 사용법: ./cleanup-resources.sh

set -e

# deployment-config.json에서 설정 읽기
if [ ! -f "deployment-config.json" ]; then
    echo "❌ deployment-config.json 파일이 없습니다."
    exit 1
fi

# JSON 파싱
BUCKET_NAME=$(grep -o '"bucketName": *"[^"]*"' deployment-config.json | sed 's/.*: *"\(.*\)"/\1/')
DISTRIBUTION_ID=$(grep -o '"distributionId": *"[^"]*"' deployment-config.json | sed 's/.*: *"\(.*\)"/\1/')
PROFILE=$(grep -o '"profile": *"[^"]*"' deployment-config.json | sed 's/.*: *"\(.*\)"/\1/')

echo "================================================"
echo "⚠️ 경고: AWS 리소스 정리"
echo "================================================"
echo ""
echo "다음 리소스가 삭제됩니다:"
echo "- S3 버킷: $BUCKET_NAME (모든 파일 포함)"
echo "- CloudFront 배포: $DISTRIBUTION_ID"
echo ""
echo "이 작업은 되돌릴 수 없습니다!"
echo ""
echo "정말 삭제하시겠습니까? 확인하려면 'DELETE'를 입력하세요:"
read -r response

if [[ "$response" != "DELETE" ]]; then
    echo "취소되었습니다."
    exit 0
fi

echo ""
echo "리소스 삭제를 시작합니다..."

# 1. CloudFront 배포 비활성화
echo ""
echo "1. CloudFront 배포 비활성화 중..."

# 현재 배포 설정 가져오기
aws cloudfront get-distribution-config \
    --id "$DISTRIBUTION_ID" \
    --profile "$PROFILE" > current-config.json

# ETag 추출
ETAG=$(grep -o '"ETag": *"[^"]*"' current-config.json | sed 's/.*: *"\(.*\)"/\1/')

# 배포 설정에서 Enabled를 false로 변경
jq '.DistributionConfig.Enabled = false' current-config.json > disable-config.json

# 배포 비활성화
aws cloudfront update-distribution \
    --id "$DISTRIBUTION_ID" \
    --if-match "$ETAG" \
    --distribution-config file://disable-config.json \
    --profile "$PROFILE" > /dev/null 2>&1 || {
    echo "⚠️ CloudFront 배포 비활성화 실패. 수동으로 처리하세요."
}

echo "✓ CloudFront 배포 비활성화 시작"
echo "  ⏳ 비활성화 완료까지 15-20분 소요됩니다."

# 2. S3 버킷 비우기
echo ""
echo "2. S3 버킷 비우기..."

aws s3 rm "s3://$BUCKET_NAME" --recursive --profile "$PROFILE"
echo "✓ S3 버킷의 모든 파일 삭제 완료"

# 3. S3 버킷 버전 삭제 (버전 관리가 활성화된 경우)
echo ""
echo "3. S3 버킷 버전 정리..."

# 버전이 있는 객체 삭제
aws s3api list-object-versions \
    --bucket "$BUCKET_NAME" \
    --profile "$PROFILE" \
    --query 'Versions[].{Key:Key,VersionId:VersionId}' \
    --output json | jq -r '.[] | "--key \"\(.Key)\" --version-id \(.VersionId)"' | \
    while read -r line; do
        eval aws s3api delete-object --bucket "$BUCKET_NAME" --profile "$PROFILE" $line
    done 2>/dev/null || true

# 삭제 마커 제거
aws s3api list-object-versions \
    --bucket "$BUCKET_NAME" \
    --profile "$PROFILE" \
    --query 'DeleteMarkers[].{Key:Key,VersionId:VersionId}' \
    --output json | jq -r '.[] | "--key \"\(.Key)\" --version-id \(.VersionId)"' | \
    while read -r line; do
        eval aws s3api delete-object --bucket "$BUCKET_NAME" --profile "$PROFILE" $line
    done 2>/dev/null || true

echo "✓ S3 버전 정리 완료"

# 4. S3 버킷 삭제
echo ""
echo "4. S3 버킷 삭제..."

aws s3api delete-bucket \
    --bucket "$BUCKET_NAME" \
    --profile "$PROFILE"

echo "✓ S3 버킷 삭제 완료"

# 5. CloudFront 배포 삭제 시도
echo ""
echo "5. CloudFront 배포 삭제 시도..."
echo "   (비활성화가 완료되지 않으면 실패할 수 있습니다)"

# 배포 삭제 시도 (비활성화가 완료된 경우에만 성공)
aws cloudfront delete-distribution \
    --id "$DISTRIBUTION_ID" \
    --if-match "$ETAG" \
    --profile "$PROFILE" 2>/dev/null && {
    echo "✓ CloudFront 배포 삭제 완료"
} || {
    echo "⚠️ CloudFront 배포가 아직 비활성화 중입니다."
    echo "   15-20분 후에 다음 명령으로 삭제하세요:"
    echo ""
    echo "   aws cloudfront delete-distribution --id $DISTRIBUTION_ID --if-match \$(aws cloudfront get-distribution-config --id $DISTRIBUTION_ID --query ETag --output text)"
}

# 6. 정리
rm -f current-config.json disable-config.json deployment-config.json

echo ""
echo "================================================"
echo "리소스 정리 완료!"
echo "================================================"
echo "✓ S3 버킷 삭제: $BUCKET_NAME"
echo "⏳ CloudFront 배포: 비활성화 진행 중 (완전 삭제는 15-20분 후 가능)"
echo ""
echo "모든 AWS 리소스가 정리되었습니다."
echo "================================================"