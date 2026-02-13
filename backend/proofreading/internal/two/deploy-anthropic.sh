#!/bin/bash

# ============================================
# AI Writer - Anthropic API 배포 스크립트
# Claude 4.5 Opus 통합 배포
# ============================================

set -e

# 색상 설정
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 프로젝트 루트 디렉토리
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$PROJECT_ROOT/backend"
CONFIG_FILE="$PROJECT_ROOT/config/production.env"

# 환경 설정 로드
if [ -f "$CONFIG_FILE" ]; then
    echo -e "${BLUE}📋 환경 설정 로드 중...${NC}"
    source "$CONFIG_FILE"
    echo -e "${GREEN}✅ 설정 로드 완료${NC}"
else
    echo -e "${YELLOW}⚠️  설정 파일 없음. 기본값 사용${NC}"
fi

# Lambda 함수 이름 (실제 함수명)
LAMBDA_FUNCTIONS=(
    "nx-wt-prf-websocket-message"
    "nx-wt-prf-conversation-api"
    "nx-wt-prf-websocket-connect"
    "nx-wt-prf-websocket-disconnect"
)

echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}   🚀 AI Writer Anthropic API 배포${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# ============================================
# 1. 의존성 설치 및 패키징
# ============================================
echo -e "${BLUE}1. Python 패키지 설치 중...${NC}"
cd "$BACKEND_DIR"

# 기존 package 디렉토리 삭제
rm -rf package
mkdir -p package

# 의존성 설치
pip install -r requirements.txt -t package/ --upgrade 2>&1 | tail -5

echo -e "${GREEN}✅ 패키지 설치 완료${NC}"

# ============================================
# 2. 소스 코드 복사
# ============================================
echo ""
echo -e "${BLUE}2. 소스 코드 복사 중...${NC}"

cp -r handlers package/
cp -r lib package/
cp -r services package/
cp -r utils package/
cp -r src package/

echo -e "${GREEN}✅ 소스 코드 복사 완료${NC}"

# ============================================
# 3. Lambda 패키지 생성
# ============================================
echo ""
echo -e "${BLUE}3. Lambda 배포 패키지 생성 중...${NC}"

cd package
zip -r ../lambda-deployment.zip . -q
cd ..

PACKAGE_SIZE=$(ls -lh lambda-deployment.zip | awk '{print $5}')
echo -e "${GREEN}✅ 배포 패키지 생성 완료 (크기: $PACKAGE_SIZE)${NC}"

# ============================================
# 4. Lambda 함수 업데이트
# ============================================
echo ""
echo -e "${BLUE}4. Lambda 함수 업데이트 중...${NC}"

UPDATED=0
FAILED=0

for func in "${LAMBDA_FUNCTIONS[@]}"; do
    echo -e "${YELLOW}→ $func 확인 중...${NC}"
    
    # 함수 존재 여부 확인
    if aws lambda get-function --function-name $func --region $AWS_REGION &>/dev/null; then
        echo -e "  ${CYAN}함수 발견. 코드 업데이트 중...${NC}"
        
        # 코드 업데이트
        aws lambda update-function-code \
            --function-name $func \
            --zip-file fileb://lambda-deployment.zip \
            --region $AWS_REGION \
            --output json 2>&1 | grep -E "FunctionName|CodeSize" || true
        
        if [ $? -eq 0 ]; then
            echo -e "  ${GREEN}✅ 코드 업데이트 완료${NC}"
            ((UPDATED++))
        else
            echo -e "  ${RED}❌ 코드 업데이트 실패${NC}"
            ((FAILED++))
        fi
    else
        echo -e "  ${YELLOW}⚠️  함수를 찾을 수 없음: $func${NC}"
        ((FAILED++))
    fi
done

# ============================================
# 5. Lambda 환경 변수 업데이트
# ============================================
echo ""
echo -e "${BLUE}5. Lambda 환경 변수 업데이트 중...${NC}"

# Anthropic API 환경 변수
ENV_VARS=$(cat <<EOF
{
    "USE_ANTHROPIC_API": "${USE_ANTHROPIC_API:-true}",
    "ANTHROPIC_SECRET_NAME": "${ANTHROPIC_SECRET_NAME:-claude-opus-45-api-key}",
    "ANTHROPIC_MODEL_ID": "${ANTHROPIC_MODEL_ID:-claude-opus-4-5-20251101}",
    "AI_PROVIDER": "${AI_PROVIDER:-anthropic_api}",
    "FALLBACK_TO_BEDROCK": "${FALLBACK_TO_BEDROCK:-true}",
    "ANTHROPIC_MAX_TOKENS": "${ANTHROPIC_MAX_TOKENS:-4096}",
    "ANTHROPIC_TEMPERATURE": "${ANTHROPIC_TEMPERATURE:-0.7}"
}
EOF
)

for func in "${LAMBDA_FUNCTIONS[@]}"; do
    if aws lambda get-function --function-name $func --region $AWS_REGION &>/dev/null; then
        echo -e "${YELLOW}→ $func 환경 변수 업데이트 중...${NC}"
        
        aws lambda update-function-configuration \
            --function-name $func \
            --region $AWS_REGION \
            --environment Variables="$ENV_VARS" \
            --timeout 120 \
            --memory-size 512 \
            --output json 2>&1 | grep -E "FunctionName|State" || echo "  처리 중..."
        
        echo -e "  ${GREEN}✅ 환경 변수 업데이트 완료${NC}"
    fi
done

# ============================================
# 6. IAM 권한 확인/추가
# ============================================
echo ""
echo -e "${BLUE}6. IAM 권한 설정 중...${NC}"

# Lambda 실행 역할 가져오기 (첫 번째 함수 기준)
FIRST_FUNC="${LAMBDA_FUNCTIONS[0]}"
if aws lambda get-function --function-name $FIRST_FUNC --region $AWS_REGION &>/dev/null; then
    ROLE_ARN=$(aws lambda get-function --function-name $FIRST_FUNC --region $AWS_REGION --query 'Configuration.Role' --output text)
    ROLE_NAME=$(echo $ROLE_ARN | awk -F'/' '{print $NF}')
    
    echo -e "${CYAN}Lambda 실행 역할: $ROLE_NAME${NC}"
    
    # Secrets Manager 정책 생성
    cat > /tmp/secrets-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:$AWS_REGION:*:secret:claude-opus-45-api-key-*"
    }
  ]
}
EOF
    
    # 정책 추가/업데이트
    aws iam put-role-policy \
        --role-name $ROLE_NAME \
        --policy-name AnthropicSecretAccess \
        --policy-document file:///tmp/secrets-policy.json 2>&1 \
        && echo -e "${GREEN}✅ IAM 권한 설정 완료${NC}" \
        || echo -e "${YELLOW}⚠️  IAM 권한이 이미 존재하거나 권한 부족${NC}"
fi

# ============================================
# 7. 정리
# ============================================
echo ""
echo -e "${BLUE}7. 정리 작업 중...${NC}"

rm -f lambda-deployment.zip
rm -rf package
rm -f /tmp/secrets-policy.json

echo -e "${GREEN}✅ 정리 완료${NC}"

# ============================================
# 배포 결과
# ============================================
echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}   📊 배포 결과${NC}"
echo -e "${CYAN}========================================${NC}"
echo -e "성공: ${GREEN}$UPDATED${NC} / 실패: ${RED}$FAILED${NC}"
echo ""
echo -e "${BLUE}📌 적용된 설정:${NC}"
echo -e "  • AI Provider: ${CYAN}${AI_PROVIDER:-anthropic_api}${NC}"
echo -e "  • Model: ${CYAN}${ANTHROPIC_MODEL_ID:-claude-opus-4-5-20251101}${NC}"
echo -e "  • Fallback: ${CYAN}${FALLBACK_TO_BEDROCK:-true}${NC}"
echo ""
echo -e "${YELLOW}⚠️  다음 단계:${NC}"
echo "  1. AWS Secrets Manager에서 API 키 설정 확인"
echo "  2. CloudWatch Logs에서 동작 확인"
echo "  3. 웹 애플리케이션에서 테스트"
echo ""

if [ $FAILED -gt 0 ]; then
    echo -e "${RED}⚠️  일부 Lambda 함수를 찾을 수 없습니다.${NC}"
    echo "  실제 Lambda 함수 이름을 확인하고 스크립트를 수정하세요."
    echo ""
    echo "  현재 Lambda 함수 목록 확인:"
    echo "  aws lambda list-functions --region $AWS_REGION --query \"Functions[?contains(FunctionName, 'nx-wt') || contains(FunctionName, 'prf')].FunctionName\""
fi

echo -e "${GREEN}✅ 배포 스크립트 완료${NC}"