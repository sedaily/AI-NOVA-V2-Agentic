#!/bin/bash

# Lambda 함수들에 Anthropic API 키 시크릿 연결

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Lambda 함수에 Anthropic API 키 시크릿 연결 시작...${NC}"

# 설정
AWS_REGION=${AWS_REGION:-"us-east-1"}
SECRET_NAME="regression-v1"

# Lambda 함수 목록
LAMBDA_FUNCTIONS=(
    "sedaily-column-conversation"
    "sedaily-column-websocket-message"
    "sedaily-column-prompt"
    "sedaily-column-usage"
)

# Secret ARN 가져오기
echo -e "${YELLOW}Secret ARN 가져오는 중...${NC}"
SECRET_ARN=$(aws secretsmanager describe-secret \
    --secret-id "$SECRET_NAME" \
    --region "$AWS_REGION" \
    --query 'ARN' \
    --output text)

if [ -z "$SECRET_ARN" ]; then
    echo -e "${RED}❌ Secret ARN을 찾을 수 없습니다. setup-anthropic-api-key.sh를 먼저 실행하세요.${NC}"
    exit 1
fi

echo -e "${GREEN}Secret ARN: $SECRET_ARN${NC}"

# 각 Lambda 함수 업데이트
for FUNCTION_NAME in "${LAMBDA_FUNCTIONS[@]}"; do
    echo -e "\n${YELLOW}$FUNCTION_NAME 업데이트 중...${NC}"
    
    # 함수가 존재하는지 확인
    if aws lambda get-function --function-name "$FUNCTION_NAME" --region "$AWS_REGION" &>/dev/null; then
        # 환경변수 업데이트
        aws lambda update-function-configuration \
            --function-name "$FUNCTION_NAME" \
            --region "$AWS_REGION" \
            --environment "Variables={ANTHROPIC_SECRET_NAME=$SECRET_NAME,ANTHROPIC_SECRET_ARN=$SECRET_ARN}" \
            --timeout 30 \
            --no-cli-pager
        
        echo -e "${GREEN}✅ $FUNCTION_NAME 환경변수 업데이트 완료${NC}"
        
        # Lambda 함수에 Secrets Manager 읽기 권한 추가
        echo -e "${YELLOW}IAM 권한 업데이트 중...${NC}"
        
        # 함수의 실행 역할 가져오기
        ROLE_ARN=$(aws lambda get-function-configuration \
            --function-name "$FUNCTION_NAME" \
            --region "$AWS_REGION" \
            --query 'Role' \
            --output text)
        
        ROLE_NAME=$(echo "$ROLE_ARN" | awk -F'/' '{print $NF}')
        
        # 정책 문서 생성
        cat > /tmp/secrets-policy.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue",
                "secretsmanager:DescribeSecret"
            ],
            "Resource": "$SECRET_ARN"
        }
    ]
}
EOF
        
        # 정책 추가
        aws iam put-role-policy \
            --role-name "$ROLE_NAME" \
            --policy-name "AnthropicSecretAccess" \
            --policy-document file:///tmp/secrets-policy.json \
            2>/dev/null || true
        
        echo -e "${GREEN}✅ $FUNCTION_NAME IAM 권한 업데이트 완료${NC}"
        
    else
        echo -e "${YELLOW}⚠️  $FUNCTION_NAME 함수를 찾을 수 없습니다. 건너뜁니다.${NC}"
    fi
done

# 임시 파일 삭제
rm -f /tmp/secrets-policy.json

echo -e "\n${GREEN}✅ 모든 Lambda 함수 업데이트 완료!${NC}"
echo -e "${YELLOW}참고: Lambda 함수 코드에서 다음과 같이 시크릿을 사용하세요:${NC}"
echo "import boto3"
echo "secrets_client = boto3.client('secretsmanager', region_name='$AWS_REGION')"
echo "response = secrets_client.get_secret_value(SecretId='$SECRET_NAME')"
echo "api_key = json.loads(response['SecretString'])['api_key']"