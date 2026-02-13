#!/bin/bash

# S3 버킷 생성 및 정적 웹사이트 호스팅 설정 스크립트
# 사용법: ./01-create-s3-bucket.sh

set -e

# 변수 설정 - 원하는 값으로 변경하세요
BUCKET_NAME="nexus-multi-frontend-$(date +%Y%m%d)"
REGION="ap-northeast-2"  # 서울 리전
PROFILE="default"  # AWS CLI 프로필

echo "================================================"
echo "새로운 S3 버킷 생성 스크립트"
echo "================================================"
echo ""
echo "버킷 이름: $BUCKET_NAME"
echo "리전: $REGION"
echo "AWS 프로필: $PROFILE"
echo ""
echo "계속하시겠습니까? (y/n)"
read -r response

if [[ "$response" != "y" ]]; then
    echo "취소되었습니다."
    exit 0
fi

# 1. S3 버킷 생성
echo ""
echo "1. S3 버킷 생성 중..."
aws s3api create-bucket \
    --bucket "$BUCKET_NAME" \
    --region "$REGION" \
    --create-bucket-configuration LocationConstraint="$REGION" \
    --profile "$PROFILE" 2>/dev/null || {
    echo "버킷이 이미 존재하거나 생성 실패. 다른 이름을 시도하세요."
    exit 1
}

echo "✓ S3 버킷 생성 완료: $BUCKET_NAME"

# 2. 버킷 버전 관리 활성화
echo ""
echo "2. 버킷 버전 관리 활성화..."
aws s3api put-bucket-versioning \
    --bucket "$BUCKET_NAME" \
    --versioning-configuration Status=Enabled \
    --profile "$PROFILE"

echo "✓ 버전 관리 활성화 완료"

# 3. 퍼블릭 액세스 차단 해제 (CloudFront에서만 접근 가능하도록 설정)
echo ""
echo "3. 퍼블릭 액세스 차단 설정..."
aws s3api put-public-access-block \
    --bucket "$BUCKET_NAME" \
    --public-access-block-configuration \
        "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false" \
    --profile "$PROFILE"

echo "✓ 퍼블릭 액세스 차단 설정 완료"

# 4. 버킷 정책 설정 (CloudFront OAC용)
echo ""
echo "4. S3 버킷 정책 생성 중..."

# 버킷 정책 JSON 파일 생성
cat > bucket-policy-temp.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowCloudFrontServicePrincipal",
            "Effect": "Allow",
            "Principal": {
                "Service": "cloudfront.amazonaws.com"
            },
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::${BUCKET_NAME}/*"
        }
    ]
}
EOF

# 버킷 정책 적용은 CloudFront 생성 후에 진행
echo "✓ 버킷 정책 파일 생성 완료 (CloudFront 생성 후 적용 예정)"

# 5. 정적 웹사이트 호스팅 설정
echo ""
echo "5. 정적 웹사이트 호스팅 설정..."
aws s3 website "s3://$BUCKET_NAME/" \
    --index-document index.html \
    --error-document index.html \
    --profile "$PROFILE"

echo "✓ 정적 웹사이트 호스팅 설정 완료"

# 6. CORS 설정
echo ""
echo "6. CORS 설정..."
cat > cors-config.json <<EOF
{
    "CORSRules": [
        {
            "AllowedHeaders": ["*"],
            "AllowedMethods": ["GET", "HEAD"],
            "AllowedOrigins": ["*"],
            "ExposeHeaders": [],
            "MaxAgeSeconds": 3000
        }
    ]
}
EOF

aws s3api put-bucket-cors \
    --bucket "$BUCKET_NAME" \
    --cors-configuration file://cors-config.json \
    --profile "$PROFILE"

echo "✓ CORS 설정 완료"

# 7. 설정 정보 저장
echo ""
echo "7. 설정 정보 저장..."
cat > deployment-config.json <<EOF
{
    "bucketName": "$BUCKET_NAME",
    "region": "$REGION",
    "profile": "$PROFILE",
    "websiteUrl": "http://${BUCKET_NAME}.s3-website.${REGION}.amazonaws.com",
    "createdAt": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF

echo "✓ 설정 정보 저장 완료: deployment-config.json"

# 정리
rm -f cors-config.json

echo ""
echo "================================================"
echo "S3 버킷 생성 완료!"
echo "================================================"
echo "버킷 이름: $BUCKET_NAME"
echo "리전: $REGION"
echo "웹사이트 URL: http://${BUCKET_NAME}.s3-website.${REGION}.amazonaws.com"
echo ""
echo "다음 단계: ./02-create-cloudfront.sh 실행"
echo "================================================"