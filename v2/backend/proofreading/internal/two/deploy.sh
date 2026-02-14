#!/bin/bash

# 색상 설정
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 프로젝트 루트 디렉토리
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 배포 대상 설정
DEPLOY_FRONTEND=true
DEPLOY_BACKEND=true
INVALIDATE_CACHE=true

# 명령행 인자 처리
while [[ $# -gt 0 ]]; do
    case $1 in
        --frontend)
            DEPLOY_BACKEND=false
            ;;
        --backend)
            DEPLOY_FRONTEND=false
            ;;
        --no-cache)
            INVALIDATE_CACHE=false
            ;;
        --help)
            echo "사용법: ./deploy.sh [옵션]"
            echo "옵션:"
            echo "  --frontend     프론트엔드만 배포"
            echo "  --backend      백엔드만 배포"
            echo "  --no-cache     CloudFront 캐시 무효화 건너뛰기"
            echo "  --help         도움말 표시"
            exit 0
            ;;
        *)
            echo -e "${RED}알 수 없는 옵션: $1${NC}"
            echo "도움말을 보려면 ./deploy.sh --help를 실행하세요"
            exit 1
            ;;
    esac
    shift
done

# 배포 시작
echo -e "${CYAN}=================================${NC}"
echo -e "${CYAN}   🚀 배포 자동화 스크립트 시작   ${NC}"
echo -e "${CYAN}=================================${NC}"
echo ""

# Git 상태 확인
echo -e "${BLUE}📌 Git 상태 확인...${NC}"
cd "$PROJECT_ROOT"
git_status=$(git status --porcelain)
if [ ! -z "$git_status" ]; then
    echo -e "${YELLOW}⚠️  커밋되지 않은 변경사항이 있습니다:${NC}"
    echo "$git_status"
    echo ""
    read -p "계속 진행하시겠습니까? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}배포가 취소되었습니다.${NC}"
        exit 1
    fi
fi

# 백엔드 배포
if [ "$DEPLOY_BACKEND" = true ]; then
    echo ""
    echo -e "${BLUE}🔧 백엔드 배포 시작...${NC}"
    echo -e "${BLUE}=================================${NC}"
    
    cd "$PROJECT_ROOT/backend"
    
    # Lambda 함수 배포 스크립트 실행
    if [ -f "scripts/99-deploy-lambda.sh" ]; then
        echo -e "${CYAN}Lambda 함수 배포 중...${NC}"
        ./scripts/99-deploy-lambda.sh
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ 백엔드 배포 완료${NC}"
        else
            echo -e "${RED}❌ 백엔드 배포 실패${NC}"
            exit 1
        fi
    else
        echo -e "${RED}❌ 배포 스크립트를 찾을 수 없습니다${NC}"
        exit 1
    fi
fi

# 프론트엔드 배포
if [ "$DEPLOY_FRONTEND" = true ]; then
    echo ""
    echo -e "${BLUE}🎨 프론트엔드 배포 시작...${NC}"
    echo -e "${BLUE}=================================${NC}"
    
    cd "$PROJECT_ROOT/frontend"
    
    # 빌드
    echo -e "${CYAN}프론트엔드 빌드 중...${NC}"
    npm run build
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ 프론트엔드 빌드 실패${NC}"
        exit 1
    fi
    
    # S3 동기화
    echo -e "${CYAN}S3에 업로드 중...${NC}"
    S3_BUCKET="nx-wt-prf-frontend-prod"
    aws s3 sync dist/ s3://$S3_BUCKET/ --delete
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ S3 업로드 완료${NC}"
    else
        echo -e "${RED}❌ S3 업로드 실패${NC}"
        exit 1
    fi
    
    # CloudFront 캐시 무효화
    if [ "$INVALIDATE_CACHE" = true ]; then
        echo -e "${CYAN}CloudFront 캐시 무효화 중...${NC}"
        
        # CloudFront Distribution ID 찾기
        DISTRIBUTION_ID=$(aws cloudfront list-distributions \
            --query "DistributionList.Items[?contains(Origins.Items[0].DomainName, '$S3_BUCKET')].Id" \
            --output text)
        
        if [ -z "$DISTRIBUTION_ID" ]; then
            echo -e "${YELLOW}⚠️  CloudFront Distribution을 찾을 수 없습니다${NC}"
        else
            aws cloudfront create-invalidation \
                --distribution-id $DISTRIBUTION_ID \
                --paths "/*" > /dev/null 2>&1
            
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✅ CloudFront 캐시 무효화 시작${NC}"
            else
                echo -e "${YELLOW}⚠️  CloudFront 캐시 무효화 실패 (배포는 완료됨)${NC}"
            fi
        fi
    fi
    
    echo -e "${GREEN}✅ 프론트엔드 배포 완료${NC}"
fi

# 배포 완료
echo ""
echo -e "${GREEN}=================================${NC}"
echo -e "${GREEN}   ✅ 배포가 완료되었습니다!   ${NC}"
echo -e "${GREEN}=================================${NC}"
echo ""

# 배포 정보 출력
echo -e "${CYAN}📋 배포 정보:${NC}"
echo -e "  • 프론트엔드: https://p1.sedaily.ai"
echo -e "  • CloudFront: https://d1tas3e2v5373v.cloudfront.net (E39OHKSWZD4F8J)"
echo -e "  • S3 버킷: nx-wt-prf-frontend-prod"
echo ""
echo -e "${CYAN}📡 백엔드 API:${NC}"
echo -e "  • REST API: https://wxwdb89w4m.execute-api.us-east-1.amazonaws.com/prod"
echo -e "  • WebSocket: wss://p062xh167h.execute-api.us-east-1.amazonaws.com/prod"
echo ""

# Git 커밋 제안
read -p "변경사항을 Git에 커밋하시겠습니까? (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd "$PROJECT_ROOT"
    git add -A
    echo "커밋 메시지를 입력하세요:"
    read commit_msg
    git commit -m "$commit_msg

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
    
    read -p "GitHub에 푸시하시겠습니까? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git push origin main
        echo -e "${GREEN}✅ GitHub 푸시 완료${NC}"
    fi
fi

echo ""
echo -e "${CYAN}배포 작업이 모두 완료되었습니다!${NC}"