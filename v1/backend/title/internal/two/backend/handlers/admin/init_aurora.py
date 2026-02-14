"""
Aurora RDS Data API를 사용한 초기화
psycopg2 없이 boto3만으로 실행
"""
import boto3
import json
import os

rds_data = boto3.client('rds-data', region_name='us-east-1')

# Aurora 클러스터 정보
CLUSTER_ARN = 'arn:aws:rds:us-east-1:887078546492:cluster:nx-tt-vector-db'
SECRET_ARN = os.environ.get('AURORA_SECRET_ARN')  # Secrets Manager ARN
DATABASE_NAME = 'vectordb'


def handler(event, context):
    """
    Aurora 초기화 handler
    1. pgvector extension 활성화
    2. prompt_chunks 테이블 생성
    3. 인덱스 생성
    """
    try:
        results = {}

        # 1. pgvector Extension 활성화
        print("[1/3] pgvector Extension 활성화")
        response = rds_data.execute_statement(
            resourceArn=CLUSTER_ARN,
            secretArn=SECRET_ARN,
            database=DATABASE_NAME,
            sql='CREATE EXTENSION IF NOT EXISTS vector'
        )
        results['extension'] = 'created'
        print("  ✅ pgvector extension 활성화 완료")

        # 2. 테이블 생성
        print("[2/3] 테이블 생성")
        create_table_sql = """
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
        """
        response = rds_data.execute_statement(
            resourceArn=CLUSTER_ARN,
            secretArn=SECRET_ARN,
            database=DATABASE_NAME,
            sql=create_table_sql
        )
        results['table'] = 'created'
        print("  ✅ prompt_chunks 테이블 생성 완료")

        # 3. 인덱스 생성
        print("[3/3] 인덱스 생성")

        # 벡터 인덱스
        index_sqls = [
            """
            CREATE INDEX IF NOT EXISTS idx_embedding
            ON prompt_chunks
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_source_file
            ON prompt_chunks(source_file)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_metadata
            ON prompt_chunks USING GIN(metadata)
            """
        ]

        for idx_sql in index_sqls:
            response = rds_data.execute_statement(
                resourceArn=CLUSTER_ARN,
                secretArn=SECRET_ARN,
                database=DATABASE_NAME,
                sql=idx_sql
            )

        results['indexes'] = 'created'
        print("  ✅ 인덱스 생성 완료")

        return {
            'statusCode': 200,
            'body': {
                'message': 'Aurora initialization completed successfully',
                'results': results
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
