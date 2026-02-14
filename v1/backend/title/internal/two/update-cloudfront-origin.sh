#!/bin/bash

# CloudFront Origin 설정 업데이트 스크립트
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   CloudFront Origin 설정 업데이트${NC}"
echo -e "${GREEN}========================================${NC}"

# 설정
BUCKET_NAME="nexus-title-frontend-20251204224204"
DISTRIBUTION_ID="E1I71DSF31VPF8"
REGION="ap-northeast-2"

# 1. 현재 CloudFront 설정 가져오기
echo -e "\n${YELLOW}1. 현재 CloudFront 설정 확인...${NC}"
aws cloudfront get-distribution-config --id ${DISTRIBUTION_ID} > /tmp/dist-config.json

# ETag 추출 (업데이트에 필요)
ETAG=$(jq -r '.ETag' /tmp/dist-config.json)
echo -e "ETag: ${ETAG}"

# 2. Origin을 S3 웹사이트 엔드포인트로 변경
echo -e "\n${YELLOW}2. CloudFront Origin을 S3 웹사이트 엔드포인트로 변경...${NC}"

# 설정 파일에서 DistributionConfig만 추출하고 Origin 수정
jq '.DistributionConfig | 
    .Origins.Items[0].DomainName = "'${BUCKET_NAME}'.s3-website-'${REGION}'.amazonaws.com" |
    .Origins.Items[0].CustomOriginConfig = {
        "HTTPPort": 80,
        "HTTPSPort": 443,
        "OriginProtocolPolicy": "http-only"
    } |
    del(.Origins.Items[0].S3OriginConfig)' /tmp/dist-config.json > /tmp/updated-config.json

# 3. CloudFront 설정 업데이트
echo -e "\n${YELLOW}3. CloudFront 설정 업데이트 중...${NC}"
aws cloudfront update-distribution \
    --id ${DISTRIBUTION_ID} \
    --distribution-config file:///tmp/updated-config.json \
    --if-match ${ETAG} \
    --output json > /tmp/update-result.json 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ CloudFront 설정 업데이트 완료${NC}"
else
    echo -e "${RED}✗ CloudFront 설정 업데이트 실패${NC}"
    cat /tmp/update-result.json
    exit 1
fi

# 4. CloudFront 캐시 무효화
echo -e "\n${YELLOW}4. CloudFront 캐시 무효화...${NC}"
INVALIDATION_ID=$(aws cloudfront create-invalidation \
    --distribution-id ${DISTRIBUTION_ID} \
    --paths "/*" \
    --query 'Invalidation.Id' \
    --output text)

echo -e "${GREEN}✓ 캐시 무효화 시작: ${INVALIDATION_ID}${NC}"

# 5. 접속 정보 출력
CF_DOMAIN=$(aws cloudfront get-distribution \
    --id ${DISTRIBUTION_ID} \
    --query 'Distribution.DomainName' \
    --output text)

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}   설정 업데이트 완료!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${YELLOW}CloudFront URL: ${GREEN}https://${CF_DOMAIN}${NC}"
echo -e "${YELLOW}S3 Website URL: ${GREEN}http://${BUCKET_NAME}.s3-website-${REGION}.amazonaws.com${NC}"
echo -e "\n${YELLOW}참고: 변경사항이 완전히 적용되기까지 10-15분 정도 소요됩니다.${NC}"

# 정리
rm -f /tmp/dist-config.json /tmp/updated-config.json /tmp/update-result.json