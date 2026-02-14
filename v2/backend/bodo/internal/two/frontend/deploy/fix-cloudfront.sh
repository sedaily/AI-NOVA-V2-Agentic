#!/bin/bash

# 색상 코드 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 기존 배포 정보 읽기
BUCKET_NAME="bodo-frontend-20251204-230645dc"
CF_ID="EDF1H6DB796US"
REGION="ap-northeast-2"

echo -e "${GREEN}🔧 CloudFront 배포 수정 중...${NC}"

# 1. CloudFront OAI 생성
echo -e "${GREEN}1. CloudFront Origin Access Identity 생성 중...${NC}"
OAI_RESULT=$(aws cloudfront create-cloud-front-origin-access-identity \
    --cloud-front-origin-access-identity-config \
    CallerReference="${BUCKET_NAME}-oai",Comment="OAI for ${BUCKET_NAME}" \
    --output json 2>/dev/null || echo '{"CloudFrontOriginAccessIdentity":{"Id":"existing"}}')

if [[ "$OAI_RESULT" == *"existing"* ]]; then
    # 기존 OAI 목록에서 첫 번째 OAI 사용
    echo -e "${YELLOW}기존 OAI를 사용합니다...${NC}"
    OAI_LIST=$(aws cloudfront list-cloud-front-origin-access-identities --output json)
    OAI_ID=$(echo $OAI_LIST | jq -r '.CloudFrontOriginAccessIdentityList.Items[0].Id')
    OAI_S3_USER=$(echo $OAI_LIST | jq -r '.CloudFrontOriginAccessIdentityList.Items[0].S3CanonicalUserId')
else
    OAI_ID=$(echo $OAI_RESULT | jq -r '.CloudFrontOriginAccessIdentity.Id')
    OAI_S3_USER=$(echo $OAI_RESULT | jq -r '.CloudFrontOriginAccessIdentity.S3CanonicalUserId')
fi

echo -e "${YELLOW}OAI ID: ${OAI_ID}${NC}"

# 2. S3 버킷 정책 업데이트 (OAI 접근 허용)
echo -e "${GREEN}2. S3 버킷 정책 업데이트 중...${NC}"
cat > /tmp/bucket-policy-oai.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowCloudFrontOAI",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::cloudfront:user/CloudFront Origin Access Identity ${OAI_ID}"
            },
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::${BUCKET_NAME}/*"
        },
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

aws s3api put-bucket-policy --bucket ${BUCKET_NAME} --policy file:///tmp/bucket-policy-oai.json

# 3. CloudFront 배포 설정 가져오기
echo -e "${GREEN}3. 현재 CloudFront 설정 가져오는 중...${NC}"
aws cloudfront get-distribution-config --id ${CF_ID} > /tmp/current-config.json

# ETag 추출
ETAG=$(jq -r '.ETag' /tmp/current-config.json)

# 4. 설정 수정
echo -e "${GREEN}4. CloudFront 설정 수정 중...${NC}"
jq '.DistributionConfig' /tmp/current-config.json > /tmp/modified-config.json

# Origin을 S3 REST API 엔드포인트로 변경하고 OAI 추가
cat > /tmp/update-config.json <<EOF
{
  "Origins": {
    "Quantity": 1,
    "Items": [
      {
        "Id": "S3-${BUCKET_NAME}",
        "DomainName": "${BUCKET_NAME}.s3.amazonaws.com",
        "S3OriginConfig": {
          "OriginAccessIdentity": "origin-access-identity/cloudfront/${OAI_ID}"
        },
        "ConnectionAttempts": 3,
        "ConnectionTimeout": 10
      }
    ]
  }
}
EOF

# jq를 사용하여 Origins 섹션만 업데이트
jq --slurpfile update /tmp/update-config.json '.Origins = $update[0].Origins' /tmp/modified-config.json > /tmp/final-config.json

# 5. CloudFront 배포 업데이트
echo -e "${GREEN}5. CloudFront 배포 업데이트 중...${NC}"
aws cloudfront update-distribution \
    --id ${CF_ID} \
    --if-match ${ETAG} \
    --distribution-config file:///tmp/final-config.json \
    --output json > /dev/null

# 6. 캐시 무효화
echo -e "${GREEN}6. CloudFront 캐시 무효화 중...${NC}"
INVALIDATION_ID=$(aws cloudfront create-invalidation \
    --distribution-id ${CF_ID} \
    --paths "/*" \
    --output json | jq -r '.Invalidation.Id')

echo -e "${GREEN}✅ CloudFront 배포가 수정되었습니다!${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}CloudFront URL: https://d2emwatb21j743.cloudfront.net${NC}"
echo -e "${GREEN}Invalidation ID: ${INVALIDATION_ID}${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}⚠️  변경사항이 적용되는데 5-10분이 소요됩니다.${NC}"

# 정리
rm /tmp/bucket-policy-oai.json
rm /tmp/current-config.json
rm /tmp/modified-config.json
rm /tmp/update-config.json
rm /tmp/final-config.json