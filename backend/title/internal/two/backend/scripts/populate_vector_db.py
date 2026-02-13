"""
S3 프롬프트 파일을 읽어서 Aurora PostgreSQL에 벡터 저장
Titan Embeddings를 사용한 벡터화 및 pgvector 인덱싱
"""
import boto3
import psycopg2
from psycopg2.extras import execute_values
import json
from typing import List, Dict
import time
import os

# AWS 설정
S3_BUCKET = 'nx-tt-knowledge-base'
S3_PREFIX = 'prompts/'

# Aurora 설정 (환경변수에서 읽기)
DB_CONFIG = {
    'host': os.environ.get('AURORA_HOST', 'nx-tt-vector-db.cluster-c83iuyksky7r.us-east-1.rds.amazonaws.com'),
    'database': os.environ.get('AURORA_DB', 'vectordb'),
    'user': os.environ.get('AURORA_USER', 'postgres'),
    'password': os.environ.get('AURORA_PASSWORD', 'NexusRAG2024VectorDB'),
    'port': int(os.environ.get('AURORA_PORT', '5432'))
}

# Bedrock 클라이언트
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
s3 = boto3.client('s3', region_name='us-east-1')


def get_db_connection():
    """Aurora PostgreSQL 연결"""
    return psycopg2.connect(**DB_CONFIG)


def chunk_text(text: str, max_tokens: int = 500) -> List[str]:
    """
    텍스트를 의미 단위로 분할

    전략:
    1. XML 태그 기반 분할 (프롬프트가 XML 형식이므로)
    2. 문단 기반 분할
    3. max_tokens 제한 준수

    Args:
        text: 원본 텍스트
        max_tokens: 최대 토큰 수 (1 토큰 ≈ 4 문자)

    Returns:
        청크 리스트
    """
    # XML 섹션 분할 시도
    import re

    # XML 태그로 섹션 구분
    # <principle>, <technique>, <method> 등
    xml_pattern = r'<(\w+)[^>]*>.*?</\1>'
    sections = re.findall(xml_pattern, text, re.DOTALL)

    if sections:
        # XML 섹션 기반 분할
        chunks = []
        for match in re.finditer(xml_pattern, text, re.DOTALL):
            section_text = match.group(0)
            estimated_tokens = len(section_text) / 4

            if estimated_tokens > max_tokens:
                # 너무 크면 문단으로 재분할
                sub_chunks = _chunk_by_paragraphs(section_text, max_tokens)
                chunks.extend(sub_chunks)
            else:
                chunks.append(section_text)

        return chunks if chunks else [text]
    else:
        # XML이 아니면 문단 기반 분할
        return _chunk_by_paragraphs(text, max_tokens)


def _chunk_by_paragraphs(text: str, max_tokens: int) -> List[str]:
    """문단 기반 텍스트 분할"""
    paragraphs = text.split('\n\n')

    chunks = []
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        estimated_tokens = len(current_chunk + para) / 4

        if estimated_tokens > max_tokens and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = para
        else:
            current_chunk += "\n\n" + para if current_chunk else para

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks if chunks else [text]


def get_embedding(text: str) -> List[float]:
    """
    Bedrock Titan Embeddings로 벡터 생성

    Args:
        text: 벡터화할 텍스트 (최대 25,000 문자)

    Returns:
        1536 차원 벡터
    """
    # Titan 제한: 25K 문자
    truncated_text = text[:25000]

    response = bedrock_runtime.invoke_model(
        modelId='amazon.titan-embed-text-v1',
        body=json.dumps({
            "inputText": truncated_text
        })
    )

    result = json.loads(response['body'].read())
    return result['embedding']


def process_file(file_key: str, conn) -> int:
    """
    S3 파일 하나를 처리하여 Aurora에 저장

    Args:
        file_key: S3 파일 키
        conn: PostgreSQL 연결

    Returns:
        저장된 청크 수
    """
    print(f"\n📄 Processing: {file_key}")

    # S3에서 파일 읽기
    response = s3.get_object(Bucket=S3_BUCKET, Key=file_key)
    content = response['Body'].read().decode('utf-8')

    # 파일명 추출
    source_file = file_key.split('/')[-1]

    # 텍스트 청크로 분할
    chunks = chunk_text(content, max_tokens=500)
    print(f"   → {len(chunks)}개 청크로 분할")

    # 각 청크 처리
    cursor = conn.cursor()
    inserted_count = 0

    for idx, chunk in enumerate(chunks):
        try:
            # 임베딩 생성
            embedding = get_embedding(chunk)

            # 메타데이터
            metadata = {
                'source_type': 'core' if 'core' in file_key else 'knowledge',
                'chunk_size': len(chunk),
                'chunk_tokens': int(len(chunk) / 4),
                'file_key': file_key
            }

            # DB에 저장
            cursor.execute(
                """
                INSERT INTO prompt_chunks
                (source_file, chunk_index, content, embedding, metadata)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (source_file, idx, chunk, embedding, json.dumps(metadata))
            )

            inserted_count += 1

            if (idx + 1) % 10 == 0:
                print(f"   → {idx + 1}/{len(chunks)} 청크 처리 완료")
                conn.commit()

                # Rate limiting (Titan Embeddings: 1000 req/min)
                time.sleep(0.1)

        except Exception as e:
            print(f"   ❌ 청크 {idx} 처리 실패: {str(e)}")
            continue

    conn.commit()
    cursor.close()

    print(f"   ✅ {source_file}: {inserted_count}개 청크 저장 완료")
    return inserted_count


def create_tables(conn):
    """벡터 테이블 및 인덱스 생성"""
    cursor = conn.cursor()

    print("\n[1/3] pgvector Extension 활성화")
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
    conn.commit()
    print("   ✅ pgvector extension 활성화 완료")

    print("\n[2/3] 테이블 생성")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prompt_chunks (
            id SERIAL PRIMARY KEY,
            source_file VARCHAR(255) NOT NULL,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            embedding vector(1536),
            metadata JSONB,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()
    print("   ✅ prompt_chunks 테이블 생성 완료")

    print("\n[3/3] 인덱스 생성")

    # 벡터 인덱스 (ivfflat)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_embedding
        ON prompt_chunks
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    """)

    # 일반 인덱스
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_source_file
        ON prompt_chunks(source_file)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_metadata
        ON prompt_chunks USING GIN(metadata)
    """)

    conn.commit()
    cursor.close()
    print("   ✅ 인덱스 생성 완료")


def main():
    """메인 실행"""
    print("="*60)
    print("🚀 S3 → Aurora PostgreSQL 벡터 저장")
    print("="*60)

    # DB 연결
    try:
        conn = get_db_connection()
        print("✅ Aurora PostgreSQL 연결 완료")
    except Exception as e:
        print(f"❌ DB 연결 실패: {str(e)}")
        return

    # 테이블 생성
    try:
        create_tables(conn)
    except Exception as e:
        print(f"❌ 테이블 생성 실패: {str(e)}")
        conn.close()
        return

    # 기존 데이터 삭제 여부 확인
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM prompt_chunks")
    existing_count = cursor.fetchone()[0]
    cursor.close()

    if existing_count > 0:
        print(f"\n⚠️  기존 데이터 {existing_count}개가 있습니다. 자동으로 건너뜁니다.")
        # 자동으로 건너뜀 (기존 데이터 유지)

    # S3 파일 목록 조회
    print("\n" + "="*60)
    print("📁 S3 파일 조회")
    print("="*60)

    response = s3.list_objects_v2(
        Bucket=S3_BUCKET,
        Prefix=S3_PREFIX
    )

    files = [obj['Key'] for obj in response.get('Contents', [])
             if obj['Key'].endswith('.txt')]

    print(f"✅ 처리할 파일: {len(files)}개")

    # 각 파일 처리
    print("\n" + "="*60)
    print("🔄 파일 처리 시작")
    print("="*60)

    total_chunks = 0
    start_time = time.time()

    for i, file_key in enumerate(files, 1):
        print(f"\n[{i}/{len(files)}]", end=" ")
        try:
            count = process_file(file_key, conn)
            total_chunks += count
        except Exception as e:
            print(f"   ❌ 파일 처리 실패: {str(e)}")
            continue

    elapsed = time.time() - start_time

    # 통계 조회
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM prompt_chunks")
    total_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT source_file, COUNT(*)
        FROM prompt_chunks
        GROUP BY source_file
        ORDER BY COUNT(*) DESC
    """)
    stats = cursor.fetchall()

    cursor.close()
    conn.close()

    # 결과 출력
    print("\n" + "="*60)
    print("✅ 벡터 저장 완료!")
    print("="*60)
    print(f"\n총 청크 수: {total_count}개")
    print(f"처리 시간: {elapsed:.1f}초")
    print(f"평균 처리 속도: {total_count / elapsed:.1f} 청크/초")
    print("\n파일별 통계:")
    for source_file, count in stats:
        print(f"  - {source_file}: {count}개")

    print("\n" + "="*60)
    print("다음 단계:")
    print("1. Lambda 환경변수 설정:")
    print(f"   AURORA_HOST={DB_CONFIG['host']}")
    print(f"   AURORA_DB={DB_CONFIG['database']}")
    print(f"   AURORA_USER={DB_CONFIG['user']}")
    print("   AURORA_PASSWORD=<Secrets Manager>")
    print("   USE_RAG=true  # RAG 활성화")
    print("2. Lambda VPC 설정 (Aurora와 동일 VPC)")
    print("3. Lambda Security Group → Aurora SG 접근 허용")
    print("4. requirements.txt에 psycopg2-binary 추가")
    print("="*60)


if __name__ == "__main__":
    main()
