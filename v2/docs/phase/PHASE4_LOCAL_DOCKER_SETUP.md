# Phase 4: 로컬 Docker 환경 설정

## 개요
로컬 개발을 위한 Docker 기반 인프라 구축

**작업 기간**: 2026-02-15
**상태**: 완료

---

## 1. Docker Compose 구성

### 1.1 서비스 구성

| 서비스 | 이미지 | 포트 | 용도 |
|-------|-------|-----|-----|
| postgres-pgvector | pgvector/pgvector:pg16 | 5432 | 벡터 DB (Aurora 대체) |
| dynamodb-local | amazon/dynamodb-local | 8000 | 프롬프트 저장 |
| redis | redis:7-alpine | 6379 | 세션/캐시 |

### 1.2 docker-compose.yml

```yaml
version: '3.8'

services:
  # PostgreSQL with pgvector extension
  postgres-pgvector:
    image: pgvector/pgvector:pg16
    container_name: nexus-pgvector
    environment:
      POSTGRES_USER: nexus_user
      POSTGRES_PASSWORD: nexus_dev_password
      POSTGRES_DB: nexus_kb
    ports:
      - "5432:5432"
    volumes:
      - pgvector_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U nexus_user -d nexus_kb"]
      interval: 10s
      timeout: 5s
      retries: 5

  # DynamoDB Local
  dynamodb-local:
    image: amazon/dynamodb-local:latest
    container_name: nexus-dynamodb
    ports:
      - "8000:8000"
    command: ["-jar", "DynamoDBLocal.jar", "-sharedDb", "-dbPath", "/data"]
    volumes:
      - dynamodb_data:/data

  # Redis
  redis:
    image: redis:7-alpine
    container_name: nexus-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  pgvector_data:
  dynamodb_data:
  redis_data:
```

---

## 2. 데이터베이스 스키마

### 2.1 초기화 스크립트

#### 01-init-extensions.sql
```sql
-- pgvector Extension 활성화
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

#### 02-create-tables.sql

```sql
-- KB 규칙 테이블 (벡터 검색용)
CREATE TABLE IF NOT EXISTS kb_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id VARCHAR(20) NOT NULL,           -- W1, T1, P1, R1 등
    rule_type VARCHAR(50) NOT NULL,          -- grammar, style, term, policy
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536),                   -- Claude/OpenAI embedding
    priority INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 스타일북 테이블
CREATE TABLE IF NOT EXISTS stylebook (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100),
    rule_name VARCHAR(300) NOT NULL,
    description TEXT NOT NULL,
    correct_example TEXT,
    incorrect_example TEXT,
    embedding vector(1536),
    priority INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Few-shot 예시 테이블
CREATE TABLE IF NOT EXISTS examples (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id VARCHAR(20) NOT NULL,
    example_type VARCHAR(50) NOT NULL,
    wrong_text TEXT,
    correct_text TEXT NOT NULL,
    explanation TEXT,
    embedding vector(1536),
    source VARCHAR(200),
    usage_count INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 기자 스타일 테이블
CREATE TABLE IF NOT EXISTS reporter_styles (
    reporter_id VARCHAR(100) PRIMARY KEY,
    reporter_name VARCHAR(100),
    writing_style TEXT,
    preferred_terms JSONB DEFAULT '[]',
    sentence_patterns JSONB DEFAULT '[]',
    avg_sentence_length FLOAT,
    embedding vector(1536),
    article_count INT DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 워크플로우 세션 테이블
CREATE TABLE IF NOT EXISTS workflow_sessions (
    session_id VARCHAR(100) PRIMARY KEY,
    user_id VARCHAR(100),
    workflow_state JSONB NOT NULL,
    current_step VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 벡터 인덱스 생성
CREATE INDEX IF NOT EXISTS kb_rules_embedding_idx
ON kb_rules USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS stylebook_embedding_idx
ON stylebook USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);

CREATE INDEX IF NOT EXISTS examples_embedding_idx
ON examples USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);
```

#### 03-create-functions.sql

```sql
-- KB 규칙 검색 함수
CREATE OR REPLACE FUNCTION search_kb_rules(
    p_agent_id VARCHAR(20),
    p_query_embedding vector(1536),
    p_top_k INT DEFAULT 5,
    p_threshold FLOAT DEFAULT 0.7
)
RETURNS TABLE (
    id UUID,
    agent_id VARCHAR(20),
    rule_type VARCHAR(50),
    title VARCHAR(500),
    content TEXT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        kr.id, kr.agent_id, kr.rule_type, kr.title, kr.content,
        1 - (kr.embedding <=> p_query_embedding) as similarity
    FROM kb_rules kr
    WHERE kr.agent_id = p_agent_id
      AND kr.is_active = TRUE
      AND 1 - (kr.embedding <=> p_query_embedding) >= p_threshold
    ORDER BY kr.embedding <=> p_query_embedding
    LIMIT p_top_k;
END;
$$ LANGUAGE plpgsql;

-- 스타일북 검색 함수
CREATE OR REPLACE FUNCTION search_stylebook(
    p_query_embedding vector(1536),
    p_category VARCHAR(100) DEFAULT NULL,
    p_top_k INT DEFAULT 5,
    p_threshold FLOAT DEFAULT 0.6
)
RETURNS TABLE (...) AS $$ ... $$;

-- Few-shot 예시 검색 함수
CREATE OR REPLACE FUNCTION search_examples(
    p_query_embedding vector(1536),
    p_agent_id VARCHAR(20) DEFAULT NULL,
    p_top_k INT DEFAULT 3
)
RETURNS TABLE (...) AS $$ ... $$;
```

---

## 3. 시작/중지 스크립트

### 3.1 start-local.sh

```bash
#!/bin/bash
# 로컬 환경 시작

echo "🚀 Nexus AI Agent 로컬 환경 시작..."

docker-compose up -d

# 서비스 준비 대기
echo "⏳ 서비스 초기화 대기 중..."
sleep 5

# PostgreSQL 확인
until docker exec nexus-pgvector pg_isready -U nexus_user -d nexus_kb; do
    sleep 2
done
echo "✅ PostgreSQL 준비 완료"

# DynamoDB 확인
until curl -s http://localhost:8000 > /dev/null; do
    sleep 2
done
echo "✅ DynamoDB 준비 완료"

# Redis 확인
until docker exec nexus-redis redis-cli ping; do
    sleep 2
done
echo "✅ Redis 준비 완료"

echo "🎉 로컬 환경 준비 완료!"
echo "📌 접속 정보:"
echo "  - PostgreSQL: localhost:5432"
echo "  - DynamoDB:   localhost:8000"
echo "  - Redis:      localhost:6379"
```

### 3.2 stop-local.sh

```bash
#!/bin/bash
docker-compose down
echo "✅ 완료"
```

---

## 4. 환경 변수

### 4.1 .env.example

```bash
# ==================================================
# 로컬 개발 환경 (docker-compose 사용 시)
# ==================================================

# PostgreSQL (pgvector)
DATABASE_URL=postgresql://nexus_user:nexus_dev_password@localhost:5432/nexus_kb
AURORA_HOST=localhost
AURORA_PORT=5432
AURORA_DB=nexus_kb
AURORA_USER=nexus_user
AURORA_PASSWORD=nexus_dev_password

# DynamoDB (로컬)
USE_LOCAL_DYNAMODB=true
DYNAMODB_ENDPOINT=http://localhost:8000

# Redis
REDIS_URL=redis://localhost:6379

# DynamoDB 프롬프트 테이블
DYNAMO_BODO_TABLE=sedaily-bodo-prompts
DYNAMO_TITLE_TABLE=sedaily-title-prompts
DYNAMO_PROOF_TABLE=sedaily-proofreading-prompts
DYNAMO_REGRESSION_TABLE=sedaily-regression-prompts

# AWS Bedrock
AWS_REGION=ap-northeast-2
BEDROCK_MODEL_ID=anthropic.claude-sonnet-4-20250514

# Server
PORT=8001
DEBUG=true
```

---

## 5. 디렉토리 구조

```
backend/agents/
├── docker/
│   ├── docker-compose.yml
│   ├── init-scripts/
│   │   ├── 01-init-extensions.sql
│   │   ├── 02-create-tables.sql
│   │   └── 03-create-functions.sql
│   ├── start-local.sh
│   └── stop-local.sh
│
├── scripts/
│   ├── load_kb_data.py
│   ├── load_prompts_dynamodb.py
│   └── setup_local.sh
│
├── src/
│   └── database/
│       └── connection.py  # DATABASE_URL 지원 추가
│
└── .env.example
```

---

## 6. 사용 방법

### 6.1 빠른 시작

```bash
# 1. Docker 환경 시작
cd backend/agents/docker
./start-local.sh

# 2. 전체 설정 (DB + 프롬프트 + 데이터)
cd backend/agents
./scripts/setup_local.sh

# 3. 서버 실행
source venv/bin/activate
python main.py
```

### 6.2 개별 실행

```bash
# Docker만 시작
docker-compose up -d

# 프롬프트 로딩만
python scripts/load_prompts_dynamodb.py

# KB 데이터 로딩만
python scripts/load_kb_data.py
```
