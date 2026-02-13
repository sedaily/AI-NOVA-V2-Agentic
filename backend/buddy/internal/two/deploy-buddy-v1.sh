#!/bin/bash

# Buddy-v1 Secret을 사용하는 nexus-template-p2 배포 스크립트
# 이 스크립트는 Lambda 함수 배포 및 환경변수 설정을 수행합니다.

set -e

# Configuration
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$PROJECT_ROOT/backend"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}   Buddy-v1 API 배포 스크립트              ${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""

# Step 1: Secret 확인
echo -e "${BLUE}[1/4] buddy-v1 Secret 확인...${NC}"
SECRET_EXISTS=$(aws secretsmanager describe-secret --secret-id buddy-v1 --region us-east-1 2>/dev/null | jq -r '.Name' || echo "")

if [ "$SECRET_EXISTS" = "buddy-v1" ]; then
    echo -e "${GREEN}✓ buddy-v1 Secret 확인 완료${NC}"
    
    # API 키 확인 (처음 20자만 표시)
    API_KEY_PREFIX=$(aws secretsmanager get-secret-value \
        --secret-id buddy-v1 \
        --region us-east-1 \
        --query SecretString \
        --output text | jq -r '.api_key' | head -c 20)
    echo -e "${GREEN}  API Key: ${API_KEY_PREFIX}...${NC}"
else
    echo -e "${RED}✗ buddy-v1 Secret을 찾을 수 없습니다${NC}"
    echo -e "${YELLOW}AWS Console에서 buddy-v1 Secret을 먼저 생성해주세요${NC}"
    exit 1
fi

echo ""

# Step 2: 코드 백업
echo -e "${BLUE}[2/4] 현재 코드 백업...${NC}"
BACKUP_DIR="$BACKEND_DIR/backup_${TIMESTAMP}"
mkdir -p "$BACKUP_DIR"

# 중요 파일 백업
cp "$BACKEND_DIR/lib/anthropic_client.py" "$BACKUP_DIR/" 2>/dev/null || true
cp "$BACKEND_DIR/lib/bedrock_client_enhanced.py" "$BACKUP_DIR/" 2>/dev/null || true

echo -e "${GREEN}✓ 백업 완료: $BACKUP_DIR${NC}"
echo ""

# Step 3: Lambda 배포 패키지 생성
echo -e "${BLUE}[3/4] Lambda 배포 패키지 생성...${NC}"
cd "$BACKEND_DIR"

# 기존 패키지 삭제
rm -f lambda-deployment-buddy.zip

# 새 패키지 생성 (dependencies 포함)
if [ -f "lambda-deployment.zip" ]; then
    # 기존 패키지가 있으면 복사
    cp lambda-deployment.zip lambda-deployment-buddy.zip
    echo -e "${GREEN}✓ 기존 배포 패키지 사용${NC}"
else
    # 새로 생성
    zip -r lambda-deployment-buddy.zip \
        handlers/ lib/ services/ utils/ src/ package/ \
        -x "*.pyc" -x "*__pycache__*" -x ".*" \
        -x "*/test_*" -x "*backup*"
    echo -e "${GREEN}✓ 새 배포 패키지 생성${NC}"
fi

echo ""

# Step 4: Lambda 함수 확인 및 배포
echo -e "${BLUE}[4/4] Lambda 함수 업데이트...${NC}"

# Lambda 함수 목록 (프로젝트에 맞게 수정 필요)
LAMBDA_FUNCTIONS=(
    "buddy-websocket-message"
    "buddy-conversation-api"
    "buddy-prompt-crud"
    "buddy-usage-handler"
)

# 환경변수 설정
ENVIRONMENT_VARS='{
    "ANTHROPIC_SECRET_NAME":"buddy-v1",
    "USE_ANTHROPIC_API":"true",
    "USE_OPUS_MODEL":"true",
    "ANTHROPIC_MODEL_ID":"claude-opus-4-5-20251101",
    "SERVICE_NAME":"buddy",
    "AI_PROVIDER":"anthropic_api",
    "MAX_TOKENS":"4096",
    "TEMPERATURE":"0.3",
    "FALLBACK_TO_BEDROCK":"true"
}'

DEPLOY_SUCCESS=0
DEPLOY_FAILED=0

for FUNCTION_NAME in "${LAMBDA_FUNCTIONS[@]}"; do
    echo -e "${YELLOW}처리 중: $FUNCTION_NAME${NC}"
    
    # Lambda 함수 존재 확인
    if aws lambda get-function --function-name "$FUNCTION_NAME" --region us-east-1 &>/dev/null; then
        
        # 코드 업데이트
        echo "  코드 업데이트 중..."
        if aws lambda update-function-code \
            --function-name "$FUNCTION_NAME" \
            --zip-file fileb://lambda-deployment-buddy.zip \
            --region us-east-1 \
            --no-cli-pager &>/dev/null; then
            echo -e "  ${GREEN}✓ 코드 업데이트 성공${NC}"
        else
            echo -e "  ${RED}✗ 코드 업데이트 실패${NC}"
            ((DEPLOY_FAILED++))
            continue
        fi
        
        # 환경변수 업데이트
        echo "  환경변수 업데이트 중..."
        if aws lambda update-function-configuration \
            --function-name "$FUNCTION_NAME" \
            --environment "Variables=${ENVIRONMENT_VARS}" \
            --region us-east-1 \
            --no-cli-pager &>/dev/null; then
            echo -e "  ${GREEN}✓ 환경변수 업데이트 성공${NC}"
            ((DEPLOY_SUCCESS++))
        else
            echo -e "  ${RED}✗ 환경변수 업데이트 실패${NC}"
            ((DEPLOY_FAILED++))
        fi
        
    else
        echo -e "  ${YELLOW}⚠ Lambda 함수가 존재하지 않음 (건너뜀)${NC}"
    fi
    
    echo ""
done

# 정리
rm -f lambda-deployment-buddy.zip

# 결과 출력
echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}              배포 결과                     ${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""

if [ $DEPLOY_SUCCESS -gt 0 ]; then
    echo -e "${GREEN}✅ 성공: $DEPLOY_SUCCESS개 함수${NC}"
fi

if [ $DEPLOY_FAILED -gt 0 ]; then
    echo -e "${RED}❌ 실패: $DEPLOY_FAILED개 함수${NC}"
fi

echo ""
echo -e "${BLUE}📋 현재 설정:${NC}"
echo "  • Secret Name: buddy-v1"
echo "  • Model: Claude Opus 4.5 (claude-opus-4-5-20251101)"
echo "  • Service: buddy"
echo "  • Fallback: Bedrock (활성화됨)"
echo ""

echo -e "${YELLOW}💡 다음 단계:${NC}"
echo "1. CloudWatch 로그 확인"
echo "   aws logs tail /aws/lambda/buddy-websocket-message --follow"
echo "2. Lambda 함수 테스트"
echo "3. 웹사이트에서 기능 확인"
echo ""

echo -e "${CYAN}배포 스크립트 완료!${NC}"

# 롤백 스크립트 생성
cat > "$BACKEND_DIR/rollback-${TIMESTAMP}.sh" << 'EOF'
#!/bin/bash
# 롤백 스크립트
echo "Rolling back to previous version..."
BACKUP_DIR="backup_TIMESTAMP"
cp "$BACKUP_DIR/anthropic_client.py" lib/ 2>/dev/null
cp "$BACKUP_DIR/bedrock_client_enhanced.py" lib/ 2>/dev/null
echo "Rollback completed. Please redeploy Lambda functions."
EOF

sed -i "" "s/TIMESTAMP/${TIMESTAMP}/g" "$BACKEND_DIR/rollback-${TIMESTAMP}.sh"
chmod +x "$BACKEND_DIR/rollback-${TIMESTAMP}.sh"

echo -e "${GREEN}✓ 롤백 스크립트 생성: rollback-${TIMESTAMP}.sh${NC}"