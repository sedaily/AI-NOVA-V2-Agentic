#!/bin/bash

# API 테스트 스크립트
# Usage: ./test-api.sh [stage] [region]

set -e

# 기본값 설정
STAGE=${1:-prod}
REGION=${2:-us-east-1}
API_ID="t75vorhge1"
BASE_URL="https://$API_ID.execute-api.$REGION.amazonaws.com/$STAGE"

# 색상 설정
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== API 테스트 시작 ===${NC}"
echo -e "Base URL: ${YELLOW}$BASE_URL${NC}"
echo -e "Stage: ${YELLOW}$STAGE${NC}"
echo -e "Region: ${YELLOW}$REGION${NC}"

# 테스트 결과 저장
RESULTS=()
TOTAL_TESTS=0
PASSED_TESTS=0

# 테스트 함수
test_endpoint() {
    local method=$1
    local endpoint=$2
    local expected_status=$3
    local description=$4
    local data=$5
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo -e "\n${BLUE}🧪 테스트 $TOTAL_TESTS: $description${NC}"
    echo -e "   ${method} ${endpoint}"
    
    if [ -n "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data" 2>/dev/null || echo -e "\n000")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" 2>/dev/null || echo -e "\n000")
    fi
    
    # 응답 분리
    body=$(echo "$response" | head -n -1)
    status=$(echo "$response" | tail -n 1)
    
    # 결과 확인
    if [ "$status" = "$expected_status" ]; then
        echo -e "   ${GREEN}✅ PASS (HTTP $status)${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        RESULTS+=("✅ $description")
        
        # JSON 응답 예쁘게 출력 (jq가 있는 경우)
        if command -v jq &> /dev/null && [ -n "$body" ]; then
            echo "$body" | jq . 2>/dev/null | head -10 || echo "$body" | head -3
        else
            echo "$body" | head -3
        fi
    else
        echo -e "   ${RED}❌ FAIL (Expected: $expected_status, Got: $status)${NC}"
        RESULTS+=("❌ $description")
        echo "   Response: $body" | head -3
    fi
}

# 1. 프롬프트 API 테스트
echo -e "\n${YELLOW}📝 프롬프트 API 테스트${NC}"

test_endpoint "GET" "/prompts" "200" "프롬프트 목록 조회"

test_endpoint "GET" "/prompts/C1" "200" "특정 프롬프트 조회 (C1)"

test_endpoint "POST" "/prompts" "200" "프롬프트 생성/업데이트" '{
    "engineType": "TEST",
    "description": "테스트 프롬프트",
    "instruction": "테스트용 지시사항입니다."
}'

test_endpoint "PUT" "/prompts/TEST" "200" "프롬프트 수정" '{
    "description": "수정된 테스트 프롬프트",
    "instruction": "수정된 테스트용 지시사항입니다."
}'

# 2. 파일 API 테스트
echo -e "\n${YELLOW}📁 파일 API 테스트${NC}"

test_endpoint "GET" "/prompts/C1/files" "200" "파일 목록 조회"

test_endpoint "POST" "/prompts/TEST/files" "201" "파일 생성" '{
    "fileName": "test-file.txt",
    "fileContent": "테스트 파일 내용입니다."
}'

# 3. 대화 API 테스트
echo -e "\n${YELLOW}💬 대화 API 테스트${NC}"

test_endpoint "GET" "/conversations?userId=test@example.com" "200" "대화 목록 조회"

test_endpoint "POST" "/conversations" "201" "대화 생성" '{
    "userId": "test@example.com",
    "engineType": "C1",
    "title": "테스트 대화",
    "messages": [
        {
            "role": "user",
            "content": "안녕하세요"
        },
        {
            "role": "assistant",
            "content": "안녕하세요! 무엇을 도와드릴까요?"
        }
    ]
}'

# 4. 사용량 API 테스트
echo -e "\n${YELLOW}📊 사용량 API 테스트${NC}"

test_endpoint "GET" "/usage/test@example.com/all" "200" "전체 사용량 조회"

test_endpoint "POST" "/usage" "200" "사용량 업데이트" '{
    "userId": "test@example.com",
    "engineType": "C1",
    "inputText": "테스트 입력 텍스트",
    "outputText": "테스트 출력 텍스트",
    "userPlan": "free"
}'

# 5. 에러 케이스 테스트
echo -e "\n${YELLOW}❌ 에러 케이스 테스트${NC}"

test_endpoint "GET" "/prompts/NONEXISTENT" "200" "존재하지 않는 프롬프트 조회"

test_endpoint "GET" "/conversations" "400" "userId 없이 대화 목록 조회"

test_endpoint "POST" "/usage" "400" "필수 파라미터 없이 사용량 업데이트" '{}'

# 6. CORS 테스트
echo -e "\n${YELLOW}🌐 CORS 테스트${NC}"

test_endpoint "OPTIONS" "/prompts" "200" "CORS Preflight - 프롬프트"

test_endpoint "OPTIONS" "/conversations" "200" "CORS Preflight - 대화"

test_endpoint "OPTIONS" "/usage" "200" "CORS Preflight - 사용량"

# 7. 성능 테스트 (간단한 응답 시간 측정)
echo -e "\n${YELLOW}⚡ 성능 테스트${NC}"

echo -e "\n${BLUE}📊 응답 시간 측정 (5회 평균)${NC}"

ENDPOINTS=(
    "/prompts"
    "/conversations?userId=test@example.com"
    "/usage/test@example.com/all"
)

for endpoint in "${ENDPOINTS[@]}"; do
    echo -e "\n   Testing: $endpoint"
    total_time=0
    
    for i in {1..5}; do
        time=$(curl -s -w "%{time_total}" -o /dev/null "$BASE_URL$endpoint" 2>/dev/null || echo "0")
        total_time=$(echo "$total_time + $time" | bc -l 2>/dev/null || echo "$total_time")
    done
    
    avg_time=$(echo "scale=3; $total_time / 5" | bc -l 2>/dev/null || echo "N/A")
    echo -e "   평균 응답 시간: ${YELLOW}${avg_time}초${NC}"
done

# 8. 테스트 결과 요약
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📊 테스트 결과 요약${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "총 테스트: ${YELLOW}$TOTAL_TESTS${NC}"
echo -e "성공: ${GREEN}$PASSED_TESTS${NC}"
echo -e "실패: ${RED}$((TOTAL_TESTS - PASSED_TESTS))${NC}"

if [ $PASSED_TESTS -eq $TOTAL_TESTS ]; then
    echo -e "성공률: ${GREEN}100%${NC} 🎉"
else
    success_rate=$(echo "scale=1; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc -l)
    echo -e "성공률: ${YELLOW}${success_rate}%${NC}"
fi

echo -e "\n${BLUE}📋 상세 결과:${NC}"
for result in "${RESULTS[@]}"; do
    echo -e "   $result"
done

# 9. 추가 정보
echo -e "\n${BLUE}📚 추가 정보:${NC}"
echo -e "• API 문서: ${YELLOW}./API_ENDPOINTS.md${NC}"
echo -e "• 배포 가이드: ${YELLOW}./API_DEPLOYMENT_GUIDE.md${NC}"
echo -e "• CloudWatch 로그: https://console.aws.amazon.com/cloudwatch/home?region=$REGION#logsV2:log-groups"
echo -e "• API Gateway 콘솔: https://console.aws.amazon.com/apigateway/home?region=$REGION#/apis/$API_ID"

# 10. 최종 상태
if [ $PASSED_TESTS -eq $TOTAL_TESTS ]; then
    echo -e "\n${GREEN}🎉 모든 테스트가 성공했습니다!${NC}"
    exit 0
else
    echo -e "\n${YELLOW}⚠️  일부 테스트가 실패했습니다. 로그를 확인해주세요.${NC}"
    exit 1
fi