#!/bin/bash

# 전체 AWS 인프라 설정 마스터 스크립트
# 이 스크립트는 모든 AWS 리소스를 순서대로 생성합니다

set -e  # 에러 발생 시 스크립트 중단

# 색상 설정
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}Nexus AWS Infrastructure Setup${NC}"
echo -e "${BLUE}=================================${NC}"

# 1. IAM 역할 및 정책 생성
echo -e "\n${YELLOW}Step 1: Creating IAM Roles and Policies...${NC}"
./01-setup-iam.sh

# 2. Cognito User Pool 생성
echo -e "\n${YELLOW}Step 2: Creating Cognito User Pool...${NC}"
./02-setup-cognito.sh

# 3. DynamoDB 테이블 생성
echo -e "\n${YELLOW}Step 3: Creating DynamoDB Tables...${NC}"
./03-setup-dynamodb.sh

# 4. S3 버킷 생성
echo -e "\n${YELLOW}Step 4: Creating S3 Buckets...${NC}"
./04-setup-s3.sh

# 5. Lambda 함수 생성
echo -e "\n${YELLOW}Step 5: Creating Lambda Functions...${NC}"
./05-setup-lambda.sh

# 6. API Gateway 생성
echo -e "\n${YELLOW}Step 6: Creating API Gateway...${NC}"
./06-setup-api-gateway.sh

# 7. CloudFront 배포 생성
echo -e "\n${YELLOW}Step 7: Creating CloudFront Distribution...${NC}"
./07-setup-cloudfront.sh

# 8. Route 53 DNS 설정
echo -e "\n${YELLOW}Step 8: Configuring Route 53...${NC}"
./08-setup-route53.sh

# 9. Bedrock 가드레일 설정
echo -e "\n${YELLOW}Step 9: Configuring Bedrock Guardrail...${NC}"
./09-setup-bedrock.sh

# 10. CloudWatch 알람 설정
echo -e "\n${YELLOW}Step 10: Setting up CloudWatch Alarms...${NC}"
./10-setup-monitoring.sh

echo -e "\n${GREEN}=================================${NC}"
echo -e "${GREEN}✅ Infrastructure Setup Complete!${NC}"
echo -e "${GREEN}=================================${NC}"

echo -e "\n${BLUE}Next Steps:${NC}"
echo -e "1. Update frontend .env with new endpoints"
echo -e "2. Deploy application code:"
echo -e "   - cd frontend/scripts && ./99-deploy-frontend.sh"
echo -e "   - cd backend/scripts && ./99-deploy-lambda.sh"
echo -e "3. Test the application"

echo -e "\n${YELLOW}Resource Summary:${NC}"
echo -e "• User Pool ID: $(aws cognito-idp list-user-pools --max-results 1 --query 'UserPools[0].Id' --output text)"
echo -e "• API Gateway URL: $(aws apigatewayv2 get-apis --query 'Items[0].ApiEndpoint' --output text)"
echo -e "• CloudFront Domain: $(aws cloudfront list-distributions --query 'DistributionList.Items[0].DomainName' --output text)"