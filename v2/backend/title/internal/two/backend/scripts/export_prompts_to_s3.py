"""
DynamoDB 프롬프트 데이터를 S3로 Export
Knowledge Base 생성을 위한 데이터 준비
"""
import boto3
import json
import os
from datetime import datetime

# AWS 설정
REGION = 'us-east-1'
BUCKET_NAME = 'nx-tt-knowledge-base'
PROMPTS_TABLE = 'nx-tt-dev-ver3-prompts'
FILES_TABLE = 'nx-tt-dev-ver3-files'

dynamodb = boto3.resource('dynamodb', region_name=REGION)
s3 = boto3.client('s3', region_name=REGION)

def create_s3_bucket():
    """S3 버킷 생성"""
    try:
        # 버킷 존재 확인
        try:
            s3.head_bucket(Bucket=BUCKET_NAME)
            print(f"✅ S3 버킷이 이미 존재합니다: {BUCKET_NAME}")
        except:
            # 버킷 생성
            if REGION == 'us-east-1':
                s3.create_bucket(Bucket=BUCKET_NAME)
            else:
                s3.create_bucket(
                    Bucket=BUCKET_NAME,
                    CreateBucketConfiguration={'LocationConstraint': REGION}
                )
            print(f"✅ S3 버킷 생성 완료: {BUCKET_NAME}")

        # 버킷 버저닝 활성화 (권장)
        s3.put_bucket_versioning(
            Bucket=BUCKET_NAME,
            VersioningConfiguration={'Status': 'Enabled'}
        )
        print(f"✅ 버킷 버저닝 활성화")

        return True
    except Exception as e:
        print(f"❌ S3 버킷 생성 실패: {str(e)}")
        return False

def export_prompts():
    """프롬프트 데이터 export"""
    try:
        table = dynamodb.Table(PROMPTS_TABLE)

        # T5 프롬프트 조회
        response = table.get_item(Key={'id': 'T5'})

        if 'Item' not in response:
            print("❌ T5 프롬프트를 찾을 수 없습니다")
            return False

        item = response['Item']

        # 1. Instruction export
        instruction_path = 'prompts/core/instruction.txt'
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=instruction_path,
            Body=item['instruction'].encode('utf-8'),
            ContentType='text/plain; charset=utf-8',
            Metadata={
                'source': 'dynamodb-prompts-table',
                'engine_type': 'T5',
                'field': 'instruction',
                'exported_at': datetime.utcnow().isoformat()
            }
        )
        print(f"✅ Instruction export 완료: {instruction_path} ({len(item['instruction'])} bytes)")

        # 2. Description export
        description_path = 'prompts/core/description.txt'
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=description_path,
            Body=item['description'].encode('utf-8'),
            ContentType='text/plain; charset=utf-8',
            Metadata={
                'source': 'dynamodb-prompts-table',
                'engine_type': 'T5',
                'field': 'description',
                'exported_at': datetime.utcnow().isoformat()
            }
        )
        print(f"✅ Description export 완료: {description_path} ({len(item['description'])} bytes)")

        # 3. Metadata export (JSON)
        metadata = {
            'id': item['id'],
            'model': item.get('model', 'unknown'),
            'temperature': item.get('temperature', 0.7),
            'maxTokens': item.get('maxTokens', 2000),
            'exportedAt': datetime.utcnow().isoformat(),
            'instructionSize': len(item['instruction']),
            'descriptionSize': len(item['description'])
        }

        metadata_path = 'prompts/core/metadata.json'
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=metadata_path,
            Body=json.dumps(metadata, ensure_ascii=False, indent=2).encode('utf-8'),
            ContentType='application/json; charset=utf-8'
        )
        print(f"✅ Metadata export 완료: {metadata_path}")

        return True

    except Exception as e:
        print(f"❌ 프롬프트 export 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def export_files():
    """Knowledge Base 파일들 export"""
    try:
        table = dynamodb.Table(FILES_TABLE)

        # T5 파일들 조회
        response = table.query(
            KeyConditionExpression='promptId = :pid',
            ExpressionAttributeValues={':pid': 'T5'}
        )

        files = response['Items']
        print(f"\n📁 T5 파일 {len(files)}개 발견")

        total_size = 0

        for file_item in files:
            file_name = file_item['fileName']
            file_content = file_item['fileContent']
            file_size = len(file_content)
            total_size += file_size

            # S3에 업로드
            s3_path = f'prompts/knowledge/{file_name}'
            s3.put_object(
                Bucket=BUCKET_NAME,
                Key=s3_path,
                Body=file_content.encode('utf-8'),
                ContentType='text/plain; charset=utf-8',
                Metadata={
                    'source': 'dynamodb-files-table',
                    'engine_type': 'T5',
                    'original_filename': file_name,
                    'exported_at': datetime.utcnow().isoformat()
                }
            )
            print(f"  ✅ {file_name}: {file_size:,} bytes → {s3_path}")

        print(f"\n✅ 총 {len(files)}개 파일 export 완료 (총 {total_size:,} bytes)")
        return True

    except Exception as e:
        print(f"❌ 파일 export 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def verify_export():
    """Export 검증"""
    try:
        print("\n" + "="*60)
        print("📊 S3 Export 검증")
        print("="*60)

        response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix='prompts/')

        if 'Contents' not in response:
            print("❌ Export된 파일이 없습니다")
            return False

        total_size = 0
        file_count = 0

        for obj in response['Contents']:
            key = obj['Key']
            size = obj['Size']
            total_size += size
            file_count += 1
            print(f"  ✅ {key}: {size:,} bytes")

        print(f"\n✅ 총 {file_count}개 파일, {total_size:,} bytes")
        print(f"✅ S3 버킷: s3://{BUCKET_NAME}/prompts/")

        return True

    except Exception as e:
        print(f"❌ 검증 실패: {str(e)}")
        return False

def main():
    """메인 실행"""
    print("="*60)
    print("🚀 DynamoDB → S3 Export 시작")
    print("="*60)

    # 1. S3 버킷 생성
    print("\n[1/4] S3 버킷 생성")
    if not create_s3_bucket():
        return

    # 2. 프롬프트 export
    print("\n[2/4] 프롬프트 데이터 export")
    if not export_prompts():
        return

    # 3. 파일 export
    print("\n[3/4] Knowledge Base 파일 export")
    if not export_files():
        return

    # 4. 검증
    print("\n[4/4] Export 검증")
    if not verify_export():
        return

    print("\n" + "="*60)
    print("✅ 모든 데이터 export 완료!")
    print("="*60)
    print(f"\n다음 단계:")
    print(f"1. AWS Console → Bedrock → Knowledge Bases")
    print(f"2. 'Create Knowledge Base' 클릭")
    print(f"3. Data source: S3, Bucket: {BUCKET_NAME}, Prefix: prompts/")
    print(f"4. Embeddings model: Titan Embeddings G1 - Text")
    print("="*60)

if __name__ == "__main__":
    main()
