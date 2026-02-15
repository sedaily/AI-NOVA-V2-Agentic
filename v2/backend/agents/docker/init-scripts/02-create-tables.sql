-- KB 규칙 테이블 (벡터 검색용)
CREATE TABLE IF NOT EXISTS kb_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id VARCHAR(20) NOT NULL,           -- W1, T1, P1, R1 등
    rule_type VARCHAR(50) NOT NULL,          -- grammar, style, term, policy
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536),                   -- Claude/OpenAI embedding dimension
    priority INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 벡터 인덱스 생성 (IVFFlat)
CREATE INDEX IF NOT EXISTS kb_rules_embedding_idx
ON kb_rules USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Agent ID 인덱스
CREATE INDEX IF NOT EXISTS kb_rules_agent_idx ON kb_rules(agent_id);

-- 스타일북 테이블
CREATE TABLE IF NOT EXISTS stylebook (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category VARCHAR(100) NOT NULL,           -- 표기법, 용어, 문체, 인용
    subcategory VARCHAR(100),
    rule_name VARCHAR(300) NOT NULL,
    description TEXT NOT NULL,
    correct_example TEXT,
    incorrect_example TEXT,
    embedding vector(1536),
    priority INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 스타일북 벡터 인덱스
CREATE INDEX IF NOT EXISTS stylebook_embedding_idx
ON stylebook USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 50);

-- 카테고리 인덱스
CREATE INDEX IF NOT EXISTS stylebook_category_idx ON stylebook(category);

-- Few-shot 예시 테이블
CREATE TABLE IF NOT EXISTS examples (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id VARCHAR(20) NOT NULL,
    example_type VARCHAR(50) NOT NULL,        -- correction, writing, title
    wrong_text TEXT,
    correct_text TEXT NOT NULL,
    explanation TEXT,
    embedding vector(1536),
    source VARCHAR(200),                      -- 출처 (기사ID 등)
    usage_count INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 예시 벡터 인덱스
CREATE INDEX IF NOT EXISTS examples_embedding_idx
ON examples USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 50);

-- 기자 스타일 테이블
CREATE TABLE IF NOT EXISTS reporter_styles (
    reporter_id VARCHAR(100) PRIMARY KEY,
    reporter_name VARCHAR(100),
    writing_style TEXT,                        -- 문체 특성
    preferred_terms JSONB DEFAULT '[]',        -- 선호 용어
    sentence_patterns JSONB DEFAULT '[]',      -- 문장 패턴
    avg_sentence_length FLOAT,
    embedding vector(1536),
    article_count INT DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 기사 이력 테이블 (학습용)
CREATE TABLE IF NOT EXISTS article_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_id VARCHAR(100) UNIQUE NOT NULL,
    reporter_id VARCHAR(100),
    title VARCHAR(500),
    content TEXT,
    article_type VARCHAR(50),                  -- daily, print, online
    engine_type VARCHAR(10),                   -- 11, 22
    quality_score INT,
    embedding vector(1536),
    metadata JSONB DEFAULT '{}',
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 기사 이력 인덱스
CREATE INDEX IF NOT EXISTS article_history_reporter_idx ON article_history(reporter_id);
CREATE INDEX IF NOT EXISTS article_history_type_idx ON article_history(article_type, engine_type);

-- 세션 상태 테이블 (워크플로우 상태 저장)
CREATE TABLE IF NOT EXISTS workflow_sessions (
    session_id VARCHAR(100) PRIMARY KEY,
    user_id VARCHAR(100),
    workflow_state JSONB NOT NULL,
    current_step VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active',       -- active, paused, completed, failed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 세션 인덱스
CREATE INDEX IF NOT EXISTS workflow_sessions_user_idx ON workflow_sessions(user_id);
CREATE INDEX IF NOT EXISTS workflow_sessions_status_idx ON workflow_sessions(status);
