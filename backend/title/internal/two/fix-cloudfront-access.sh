#!/bin/bash

# CloudFront 접근 권한 수정 스크립트
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   CloudFront 접근 권한 수정${NC}"
echo -e "${GREEN}========================================${NC}"

# 설정
BUCKET_NAME="nexus-title-frontend-20251204224204"
DISTRIBUTION_ID="E1I71DSF31VPF8"
OAI_ID="E2JZ1638UDIIFJ"

# 1. S3 버킷을 퍼블릭 액세스로 설정 (임시)
echo -e "\n${YELLOW}1. S3 버킷 퍼블릭 액세스 차단 해제...${NC}"
aws s3api put-public-access-block \
    --bucket ${BUCKET_NAME} \
    --public-access-block-configuration \
    "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"

# 2. 새로운 버킷 정책 적용 (퍼블릭 읽기 + CloudFront)
echo -e "\n${YELLOW}2. 새로운 S3 버킷 정책 적용...${NC}"
cat > /tmp/new-bucket-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::${BUCKET_NAME}/*"
        }
    ]
}
EOF

aws s3api put-bucket-policy \
    --bucket ${BUCKET_NAME} \
    --policy file:///tmp/new-bucket-policy.json

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ S3 버킷 정책 업데이트 완료${NC}"
else
    echo -e "${RED}✗ S3 버킷 정책 업데이트 실패${NC}"
fi

# 3. CloudFront 캐시 무효화
echo -e "\n${YELLOW}3. CloudFront 캐시 무효화...${NC}"
INVALIDATION_ID=$(aws cloudfront create-invalidation \
    --distribution-id ${DISTRIBUTION_ID} \
    --paths "/*" \
    --query 'Invalidation.Id' \
    --output text)

echo -e "${GREEN}✓ 캐시 무효화 시작: ${INVALIDATION_ID}${NC}"

# 4. CloudFront 배포 상태 확인
echo -e "\n${YELLOW}4. CloudFront 배포 상태 확인...${NC}"
STATUS=$(aws cloudfront get-distribution \
    --id ${DISTRIBUTION_ID} \
    --query 'Distribution.Status' \
    --output text)

echo -e "배포 상태: ${STATUS}"

if [ "$STATUS" = "Deployed" ]; then
    echo -e "${GREEN}✓ CloudFront 배포가 활성화되었습니다${NC}"
else
    echo -e "${YELLOW}⏳ CloudFront 배포 진행 중... (몇 분 더 기다려주세요)${NC}"
fi

# 5. 접속 정보 출력
CF_DOMAIN=$(aws cloudfront get-distribution \
    --id ${DISTRIBUTION_ID} \
    --query 'Distribution.DomainName' \
    --output text)

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}   접근 권한 수정 완료!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${YELLOW}접속 URL: ${GREEN}https://${CF_DOMAIN}${NC}"
echo -e "${YELLOW}S3 URL: ${GREEN}https://${BUCKET_NAME}.s3.ap-northeast-2.amazonaws.com/index.html${NC}"
echo -e "\n${YELLOW}참고: 변경사항이 적용되기까지 5-10분 정도 소요될 수 있습니다.${NC}"

# 정리
rm -f /tmp/new-bucket-policy.json