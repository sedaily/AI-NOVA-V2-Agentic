#!/bin/bash
# Nexus AI Agent - 로컬 개발 환경 시작

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Nexus AI Agent 로컬 환경 시작..."

# Docker Compose 실행
docker-compose up -d

# 서비스 상태 확인 대기
echo "⏳ 서비스 초기화 대기 중..."
sleep 5

# PostgreSQL 연결 확인
echo "📦 PostgreSQL (pgvector) 확인..."
until docker exec nexus-pgvector pg_isready -U nexus_user -d nexus_kb > /dev/null 2>&1; do
    echo "  - 대기 중..."
    sleep 2
done
echo "  ✅ PostgreSQL 준비 완료"

# DynamoDB 확인
echo "📦 DynamoDB Local 확인..."
until curl -s http://localhost:8000 > /dev/null 2>&1; do
    echo "  - 대기 중..."
    sleep 2
done
echo "  ✅ DynamoDB 준비 완료"

# Redis 확인
echo "📦 Redis 확인..."
until docker exec nexus-redis redis-cli ping > /dev/null 2>&1; do
    echo "  - 대기 중..."
    sleep 2
done
echo "  ✅ Redis 준비 완료"

echo ""
echo "============================================"
echo "🎉 로컬 개발 환경 준비 완료!"
echo "============================================"
echo ""
echo "📌 서비스 정보:"
echo "  - PostgreSQL: localhost:5432 (user: nexus_user, db: nexus_kb)"
echo "  - DynamoDB:   localhost:8000"
echo "  - Redis:      localhost:6379"
echo ""
echo "📌 환경 변수 설정 (.env):"
echo "  DATABASE_URL=postgresql://nexus_user:nexus_dev_password@localhost:5432/nexus_kb"
echo "  DYNAMODB_ENDPOINT=http://localhost:8000"
echo "  REDIS_URL=redis://localhost:6379"
echo ""
echo "📌 중지하려면: ./stop-local.sh"
echo ""
