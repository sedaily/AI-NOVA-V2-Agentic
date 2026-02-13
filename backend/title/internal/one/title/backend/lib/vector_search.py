"""
Aurora PostgreSQL pgvector를 사용한 유사도 검색
벡터 기반 RAG (Retrieval-Augmented Generation) 구현
"""
import psycopg2
from psycopg2.pool import SimpleConnectionPool
import json
import boto3
from typing import List, Dict, Optional
import os
import sys

# utils 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import setup_logger

logger = setup_logger(__name__)


class VectorSearch:
    """
    Aurora PostgreSQL pgvector 기반 벡터 검색 클래스
    """

    def __init__(self):
        """초기화 및 DB 연결 풀 생성"""
        # DB 설정
        self.db_config = {
            'host': os.environ.get('AURORA_HOST'),
            'database': os.environ.get('AURORA_DB', 'vectordb'),
            'user': os.environ.get('AURORA_USER', 'postgres'),
            'password': os.environ.get('AURORA_PASSWORD'),
            'port': int(os.environ.get('AURORA_PORT', '5432'))
        }

        # 연결 풀 생성 (Lambda 컨테이너 재사용 시 효율적)
        try:
            self.pool = SimpleConnectionPool(
                minconn=1,
                maxconn=5,
                **self.db_config
            )
            logger.info("✅ Aurora PostgreSQL 연결 풀 생성 완료")
        except Exception as e:
            logger.error(f"❌ DB 연결 풀 생성 실패: {str(e)}")
            self.pool = None

        # Bedrock Runtime 클라이언트
        self.bedrock_runtime = boto3.client(
            'bedrock-runtime',
            region_name=os.environ.get('AWS_REGION', 'us-east-1')
        )

    def get_embedding(self, text: str) -> List[float]:
        """
        Bedrock Titan Embeddings로 텍스트를 벡터로 변환

        Args:
            text: 벡터화할 텍스트

        Returns:
            1536 차원 벡터
        """
        try:
            response = self.bedrock_runtime.invoke_model(
                modelId='amazon.titan-embed-text-v1',
                body=json.dumps({
                    "inputText": text[:25000]  # Titan 제한: 25K 문자
                })
            )

            result = json.loads(response['body'].read())
            embedding = result['embedding']

            logger.info(f"✅ 임베딩 생성 완료: {len(embedding)} 차원")
            return embedding

        except Exception as e:
            logger.error(f"❌ 임베딩 생성 실패: {str(e)}")
            raise

    def search_similar_chunks(
        self,
        query: str,
        top_k: int = 10,
        min_similarity: float = 0.7,
        source_filter: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        쿼리와 유사한 프롬프트 청크 검색

        Args:
            query: 검색 쿼리 (기사 내용)
            top_k: 반환할 최대 결과 수
            min_similarity: 최소 유사도 (0-1)
            source_filter: 특정 소스 파일만 검색 (예: ['instruction.txt'])

        Returns:
            유사한 청크 리스트 [{id, source_file, content, similarity, ...}]
        """
        if not self.pool:
            logger.error("❌ DB 연결 풀이 없습니다")
            return []

        try:
            # 1. 쿼리 벡터화
            logger.info(f"🔍 벡터 검색 시작: query_length={len(query)}, top_k={top_k}")
            query_embedding = self.get_embedding(query)

            # 2. DB 연결 가져오기
            conn = self.pool.getconn()
            cursor = conn.cursor()

            # 3. SQL 쿼리 구성
            # pgvector: <=> 연산자는 코사인 거리 (0에 가까울수록 유사)
            # 코사인 유사도 = 1 - 코사인 거리
            sql = """
                SELECT
                    id,
                    source_file,
                    chunk_index,
                    content,
                    metadata,
                    1 - (embedding <=> %s::vector) AS similarity
                FROM prompt_chunks
                WHERE 1 - (embedding <=> %s::vector) >= %s
            """

            params = [query_embedding, query_embedding, min_similarity]

            # 소스 필터 추가
            if source_filter:
                placeholders = ','.join(['%s'] * len(source_filter))
                sql += f" AND source_file IN ({placeholders})"
                params.extend(source_filter)

            sql += """
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """
            params.extend([query_embedding, top_k])

            # 4. 쿼리 실행
            cursor.execute(sql, params)
            rows = cursor.fetchall()

            # 5. 결과 구성
            results = []
            for row in rows:
                results.append({
                    'id': row[0],
                    'source_file': row[1],
                    'chunk_index': row[2],
                    'content': row[3],
                    'metadata': row[4],
                    'similarity': float(row[5])
                })

            # 6. 연결 반환
            cursor.close()
            self.pool.putconn(conn)

            logger.info(f"✅ 검색 완료: {len(results)}개 청크 발견")
            for i, result in enumerate(results[:3], 1):
                logger.info(f"   [{i}] {result['source_file']} (유사도: {result['similarity']:.2%})")

            return results

        except Exception as e:
            logger.error(f"❌ 벡터 검색 실패: {str(e)}")
            if conn:
                self.pool.putconn(conn)
            return []

    def build_context_from_results(
        self,
        results: List[Dict],
        max_tokens: int = 10000
    ) -> str:
        """
        검색 결과를 컨텍스트 문자열로 변환

        토큰 제한에 맞춰 가장 관련도 높은 청크들만 포함

        Args:
            results: search_similar_chunks() 결과
            max_tokens: 최대 토큰 수

        Returns:
            프롬프트에 포함할 컨텍스트 문자열
        """
        if not results:
            logger.warning("⚠️  검색 결과가 없습니다")
            return ""

        context_parts = []
        total_tokens = 0

        for result in results:
            content = result['content']
            # 대략적인 토큰 수 계산 (1 토큰 ≈ 4 문자)
            estimated_tokens = len(content) / 4

            if total_tokens + estimated_tokens > max_tokens:
                logger.info(f"⚠️  토큰 제한 도달: {total_tokens}/{max_tokens}")
                break

            context_parts.append({
                'source': result['source_file'],
                'chunk_index': result['chunk_index'],
                'similarity': result['similarity'],
                'content': content
            })

            total_tokens += estimated_tokens

        # 컨텍스트 문자열 구성
        context = "## 📚 관련 프롬프트 지침 (RAG 검색 결과)\n\n"
        context += f"검색된 청크: {len(context_parts)}개 (총 ~{int(total_tokens)} 토큰)\n\n"

        for i, part in enumerate(context_parts, 1):
            context += f"### [{i}] {part['source']} - 청크 #{part['chunk_index']} (유사도: {part['similarity']:.2%})\n\n"
            context += f"{part['content']}\n\n"
            context += "---\n\n"

        logger.info(f"✅ 컨텍스트 구성 완료: {len(context_parts)}개 청크, ~{int(total_tokens)} 토큰")

        return context

    def get_stats(self) -> Dict:
        """
        벡터 DB 통계 조회

        Returns:
            통계 정보 딕셔너리
        """
        if not self.pool:
            return {'error': 'DB 연결 없음'}

        try:
            conn = self.pool.getconn()
            cursor = conn.cursor()

            # 전체 청크 수
            cursor.execute("SELECT COUNT(*) FROM prompt_chunks")
            total_chunks = cursor.fetchone()[0]

            # 파일별 청크 수
            cursor.execute("""
                SELECT source_file, COUNT(*)
                FROM prompt_chunks
                GROUP BY source_file
                ORDER BY COUNT(*) DESC
            """)
            by_source = {row[0]: row[1] for row in cursor.fetchall()}

            # 평균 청크 크기
            cursor.execute("""
                SELECT AVG(LENGTH(content))
                FROM prompt_chunks
            """)
            avg_chunk_size = cursor.fetchone()[0]

            cursor.close()
            self.pool.putconn(conn)

            return {
                'total_chunks': total_chunks,
                'by_source': by_source,
                'avg_chunk_size': int(avg_chunk_size) if avg_chunk_size else 0
            }

        except Exception as e:
            logger.error(f"❌ 통계 조회 실패: {str(e)}")
            return {'error': str(e)}

    def close(self):
        """연결 풀 종료"""
        if self.pool:
            self.pool.closeall()
            logger.info("✅ DB 연결 풀 종료")


# 전역 인스턴스 (Lambda 컨테이너 재사용)
_vector_search_instance = None


def get_vector_search() -> VectorSearch:
    """
    VectorSearch 싱글톤 인스턴스 반환
    Lambda 컨테이너 재사용 시 연결 풀 유지
    """
    global _vector_search_instance

    if _vector_search_instance is None:
        _vector_search_instance = VectorSearch()

    return _vector_search_instance
