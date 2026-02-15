-- 벡터 유사도 검색 함수

-- KB 규칙 검색
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
        kr.id,
        kr.agent_id,
        kr.rule_type,
        kr.title,
        kr.content,
        1 - (kr.embedding <=> p_query_embedding) as similarity
    FROM kb_rules kr
    WHERE kr.agent_id = p_agent_id
      AND kr.is_active = TRUE
      AND 1 - (kr.embedding <=> p_query_embedding) >= p_threshold
    ORDER BY kr.embedding <=> p_query_embedding
    LIMIT p_top_k;
END;
$$ LANGUAGE plpgsql;


-- 스타일북 검색
CREATE OR REPLACE FUNCTION search_stylebook(
    p_query_embedding vector(1536),
    p_category VARCHAR(100) DEFAULT NULL,
    p_top_k INT DEFAULT 5,
    p_threshold FLOAT DEFAULT 0.6
)
RETURNS TABLE (
    id UUID,
    category VARCHAR(100),
    rule_name VARCHAR(300),
    description TEXT,
    correct_example TEXT,
    incorrect_example TEXT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.id,
        s.category,
        s.rule_name,
        s.description,
        s.correct_example,
        s.incorrect_example,
        1 - (s.embedding <=> p_query_embedding) as similarity
    FROM stylebook s
    WHERE s.is_active = TRUE
      AND (p_category IS NULL OR s.category = p_category)
      AND 1 - (s.embedding <=> p_query_embedding) >= p_threshold
    ORDER BY s.embedding <=> p_query_embedding
    LIMIT p_top_k;
END;
$$ LANGUAGE plpgsql;


-- Few-shot 예시 검색
CREATE OR REPLACE FUNCTION search_examples(
    p_query_embedding vector(1536),
    p_agent_id VARCHAR(20) DEFAULT NULL,
    p_example_type VARCHAR(50) DEFAULT NULL,
    p_top_k INT DEFAULT 3
)
RETURNS TABLE (
    id UUID,
    agent_id VARCHAR(20),
    example_type VARCHAR(50),
    wrong_text TEXT,
    correct_text TEXT,
    explanation TEXT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        e.id,
        e.agent_id,
        e.example_type,
        e.wrong_text,
        e.correct_text,
        e.explanation,
        1 - (e.embedding <=> p_query_embedding) as similarity
    FROM examples e
    WHERE e.is_active = TRUE
      AND (p_agent_id IS NULL OR e.agent_id = p_agent_id)
      AND (p_example_type IS NULL OR e.example_type = p_example_type)
    ORDER BY e.embedding <=> p_query_embedding
    LIMIT p_top_k;
END;
$$ LANGUAGE plpgsql;


-- 유사 기사 검색 (기자 스타일 학습용)
CREATE OR REPLACE FUNCTION search_similar_articles(
    p_query_embedding vector(1536),
    p_reporter_id VARCHAR(100) DEFAULT NULL,
    p_article_type VARCHAR(50) DEFAULT NULL,
    p_top_k INT DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    article_id VARCHAR(100),
    reporter_id VARCHAR(100),
    title VARCHAR(500),
    content TEXT,
    quality_score INT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ah.id,
        ah.article_id,
        ah.reporter_id,
        ah.title,
        ah.content,
        ah.quality_score,
        1 - (ah.embedding <=> p_query_embedding) as similarity
    FROM article_history ah
    WHERE (p_reporter_id IS NULL OR ah.reporter_id = p_reporter_id)
      AND (p_article_type IS NULL OR ah.article_type = p_article_type)
    ORDER BY ah.embedding <=> p_query_embedding
    LIMIT p_top_k;
END;
$$ LANGUAGE plpgsql;


-- updated_at 자동 업데이트 트리거
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 트리거 적용
CREATE TRIGGER update_kb_rules_updated_at
    BEFORE UPDATE ON kb_rules
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_stylebook_updated_at
    BEFORE UPDATE ON stylebook
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workflow_sessions_updated_at
    BEFORE UPDATE ON workflow_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
