#!/bin/bash
# Nexus AI Agent - 로컬 환경 전체 설정

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "============================================"
echo "🚀 Nexus AI Agent 로컬 환경 설정"
echo "============================================"
echo ""

# 1. Docker 환경 시작
echo "📦 Step 1: Docker 서비스 시작..."
cd "$ROOT_DIR/docker"
./start-local.sh

# 2. Python 가상환경 확인
echo ""
echo "🐍 Step 2: Python 환경 확인..."
cd "$ROOT_DIR"

if [ ! -d "venv" ]; then
    echo "  가상환경 생성 중..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt

# 3. DynamoDB 프롬프트 로딩
echo ""
echo "📝 Step 3: DynamoDB 프롬프트 로딩..."
python scripts/load_prompts_dynamodb.py

# 4. KB/스타일북 데이터 로딩
echo ""
echo "📚 Step 4: KB/스타일북 데이터 로딩..."
python scripts/load_kb_data.py

echo ""
echo "============================================"
echo "🎉 로컬 환경 설정 완료!"
echo "============================================"
echo ""
echo "📌 서버 시작:"
echo "  cd $ROOT_DIR && source venv/bin/activate && python main.py"
echo ""
echo "📌 테스트:"
echo "  curl http://localhost:8001/health"
echo ""
