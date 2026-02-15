#!/bin/bash
# Nexus AI Agent - 로컬 개발 환경 중지

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🛑 Nexus AI Agent 로컬 환경 중지..."
docker-compose down

echo "✅ 완료"
