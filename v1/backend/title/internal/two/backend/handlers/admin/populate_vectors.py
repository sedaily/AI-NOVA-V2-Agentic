"""
Lambda handler for populating vector database
Aurora VPC 내부에서만 실행 가능
"""
import sys
import os

# scripts 디렉토리를 path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

def handler(event, context):
    """
    벡터 DB 초기화 Lambda handler
    event.get('action'): 'populate' (기본) 또는 'check'
    """
    try:
        action = event.get('action', 'populate')

        if action == 'check':
            # 상태 확인만
            import psycopg2
            import os

            DB_CONFIG = {
                'host': os.environ.get('AURORA_HOST'),
                'database': os.environ.get('AURORA_DB', 'vectordb'),
                'user': os.environ.get('AURORA_USER', 'postgres'),
                'password': os.environ.get('AURORA_PASSWORD'),
                'port': 5432
            }

            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()

            # 테이블 존재 확인
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'prompt_chunks'
                )
            """)
            table_exists = cursor.fetchone()[0]

            if table_exists:
                cursor.execute("SELECT COUNT(*) FROM prompt_chunks")
                chunk_count = cursor.fetchone()[0]

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
                    'action': 'check',
                    'table_exists': table_exists,
                    'total_chunks': chunk_count,
                    'files': [{'file': f, 'chunks': c} for f, c in file_stats]
                }
            }

        else:
            # populate_vector_db 스크립트 import
            from scripts.populate_vector_db import main

            # 스크립트 실행
            result = main()

            return {
                'statusCode': 200,
                'body': {
                    'action': 'populate',
                    'message': 'Vector DB population completed successfully',
                    'result': result
                }
            }

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()

        print(f"Error: {str(e)}")
        print(error_trace)

        return {
            'statusCode': 500,
            'body': {
                'error': str(e),
                'trace': error_trace
            }
        }
