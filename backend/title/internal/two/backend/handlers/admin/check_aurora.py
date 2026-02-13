"""
Aurora 벡터 DB 상태 확인 Lambda handler
"""
import psycopg2
import json
import os

DB_CONFIG = {
    'host': os.environ.get('AURORA_HOST'),
    'database': os.environ.get('AURORA_DB', 'vectordb'),
    'user': os.environ.get('AURORA_USER', 'postgres'),
    'password': os.environ.get('AURORA_PASSWORD'),
    'port': 5432
}

def handler(event, context):
    """Aurora 상태 확인"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # 1. 테이블 존재 여부 확인
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'prompt_chunks'
            )
        """)
        table_exists = cursor.fetchone()[0]

        # 2. 데이터 개수 확인
        if table_exists:
            cursor.execute("SELECT COUNT(*) FROM prompt_chunks")
            chunk_count = cursor.fetchone()[0]

            # 3. 파일별 통계
            cursor.execute("""
                SELECT source_file, COUNT(*)
                FROM prompt_chunks
                GROUP BY source_file
                ORDER BY source_file
            """)
            file_stats = cursor.fetchall()
        else:
            chunk_count = 0
            file_stats = []

        cursor.close()
        conn.close()

        return {
            'statusCode': 200,
            'body': {
                'table_exists': table_exists,
                'total_chunks': chunk_count,
                'files': [{'file': f, 'chunks': c} for f, c in file_stats]
            }
        }

    except Exception as e:
        import traceback
        return {
            'statusCode': 500,
            'body': {
                'error': str(e),
                'trace': traceback.format_exc()
            }
        }
