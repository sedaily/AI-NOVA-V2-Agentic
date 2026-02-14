"""
AWS Bedrock Knowledge Base 생성 스크립트
S3에 export된 프롬프트 데이터로 Knowledge Base 구축
"""
import boto3
import json
import time

# AWS 설정
REGION = 'us-east-1'
S3_BUCKET = 'nx-tt-knowledge-base'
S3_PREFIX = 'prompts/'
KB_NAME = 'nexus-title-prompts-kb'
KB_DESCRIPTION = 'Nexus Title Generator - Prompt Knowledge Base'

# Bedrock Agent 클라이언트
bedrock_agent = boto3.client('bedrock-agent', region_name=REGION)
iam = boto3.client('iam', region_name=REGION)
sts = boto3.client('sts', region_name=REGION)

def get_account_id():
    """AWS 계정 ID 조회"""
    return sts.get_caller_identity()['Account']

def create_kb_role():
    """Knowledge Base용 IAM Role 생성"""
    account_id = get_account_id()
    role_name = 'AmazonBedrockExecutionRoleForKnowledgeBase_nxtt'

    print(f"\n[1/6] IAM Role 생성: {role_name}")

    # Trust policy
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "bedrock.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }

    # Permission policy
    permission_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:ListBucket"
                ],
                "Resource": [
                    f"arn:aws:s3:::{S3_BUCKET}",
                    f"arn:aws:s3:::{S3_BUCKET}/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel"
                ],
                "Resource": [
                    f"arn:aws:bedrock:{REGION}::foundation-model/amazon.titan-embed-text-v1"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "aoss:APIAccessAll"
                ],
                "Resource": [
                    f"arn:aws:aoss:{REGION}:{account_id}:collection/*"
                ]
            }
        ]
    }

    try:
        # Role 존재 확인
        try:
            role = iam.get_role(RoleName=role_name)
            print(f"  ✅ Role이 이미 존재합니다: {role['Role']['Arn']}")
            role_arn = role['Role']['Arn']
        except iam.exceptions.NoSuchEntityException:
            # Role 생성
            role = iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description='Execution role for Nexus Title Knowledge Base'
            )
            role_arn = role['Role']['Arn']
            print(f"  ✅ Role 생성 완료: {role_arn}")

            # Permission policy 추가
            iam.put_role_policy(
                RoleName=role_name,
                PolicyName='KnowledgeBasePolicy',
                PolicyDocument=json.dumps(permission_policy)
            )
            print(f"  ✅ Permission policy 추가 완료")

            # Role이 propagate될 시간 대기
            print(f"  ⏳ Role propagation 대기 (10초)...")
            time.sleep(10)

        return role_arn

    except Exception as e:
        print(f"  ❌ Role 생성 실패: {str(e)}")
        raise

def create_opensearch_collection():
    """OpenSearch Serverless Collection 생성"""
    account_id = get_account_id()
    collection_name = 'nxtt-kb-collection'

    print(f"\n[2/6] OpenSearch Serverless Collection 생성: {collection_name}")

    aoss = boto3.client('opensearchserverless', region_name=REGION)

    try:
        # Collection 존재 확인
        try:
            collections = aoss.list_collections(
                collectionFilters={'name': collection_name}
            )
            if collections['collectionSummaries']:
                collection_arn = collections['collectionSummaries'][0]['arn']
                collection_id = collections['collectionSummaries'][0]['id']
                print(f"  ✅ Collection이 이미 존재합니다")
                print(f"     ARN: {collection_arn}")
                print(f"     ID: {collection_id}")
                return collection_arn, collection_id
        except:
            pass

        # Encryption policy 생성
        encryption_policy_name = f"{collection_name}-encryption"
        encryption_policy = {
            "Rules": [
                {
                    "ResourceType": "collection",
                    "Resource": [f"collection/{collection_name}"]
                }
            ],
            "AWSOwnedKey": True
        }

        try:
            aoss.create_security_policy(
                name=encryption_policy_name,
                type='encryption',
                policy=json.dumps(encryption_policy)
            )
            print(f"  ✅ Encryption policy 생성 완료")
        except aoss.exceptions.ConflictException:
            print(f"  ⚠️  Encryption policy가 이미 존재합니다")

        # Network policy 생성 (public access)
        network_policy_name = f"{collection_name}-network"
        network_policy = [
            {
                "Rules": [
                    {
                        "ResourceType": "collection",
                        "Resource": [f"collection/{collection_name}"]
                    },
                    {
                        "ResourceType": "dashboard",
                        "Resource": [f"collection/{collection_name}"]
                    }
                ],
                "AllowFromPublic": True
            }
        ]

        try:
            aoss.create_security_policy(
                name=network_policy_name,
                type='network',
                policy=json.dumps(network_policy)
            )
            print(f"  ✅ Network policy 생성 완료")
        except aoss.exceptions.ConflictException:
            print(f"  ⚠️  Network policy가 이미 존재합니다")

        # Data access policy 생성
        data_policy_name = f"{collection_name}-data"
        data_policy = [
            {
                "Rules": [
                    {
                        "ResourceType": "collection",
                        "Resource": [f"collection/{collection_name}"],
                        "Permission": [
                            "aoss:CreateCollectionItems",
                            "aoss:UpdateCollectionItems",
                            "aoss:DescribeCollectionItems"
                        ]
                    },
                    {
                        "ResourceType": "index",
                        "Resource": [f"index/{collection_name}/*"],
                        "Permission": [
                            "aoss:CreateIndex",
                            "aoss:DescribeIndex",
                            "aoss:ReadDocument",
                            "aoss:WriteDocument",
                            "aoss:UpdateIndex",
                            "aoss:DeleteIndex"
                        ]
                    }
                ],
                "Principal": [
                    f"arn:aws:iam::{account_id}:role/AmazonBedrockExecutionRoleForKnowledgeBase_nxtt",
                    f"arn:aws:sts::{account_id}:assumed-role/Admin/*"  # 본인 admin role
                ]
            }
        ]

        try:
            aoss.create_access_policy(
                name=data_policy_name,
                type='data',
                policy=json.dumps(data_policy)
            )
            print(f"  ✅ Data access policy 생성 완료")
        except aoss.exceptions.ConflictException:
            print(f"  ⚠️  Data access policy가 이미 존재합니다")

        # Collection 생성
        print(f"  ⏳ Collection 생성 중... (5-10분 소요)")
        response = aoss.create_collection(
            name=collection_name,
            type='VECTORSEARCH',
            description='Vector search collection for Nexus Title prompts'
        )

        collection_id = response['createCollectionDetail']['id']
        collection_arn = response['createCollectionDetail']['arn']

        # Collection이 ACTIVE 상태가 될 때까지 대기
        while True:
            status_response = aoss.batch_get_collection(
                ids=[collection_id]
            )
            status = status_response['collectionDetails'][0]['status']
            print(f"     상태: {status}")

            if status == 'ACTIVE':
                print(f"  ✅ Collection 생성 완료!")
                print(f"     ARN: {collection_arn}")
                print(f"     ID: {collection_id}")
                break
            elif status == 'FAILED':
                raise Exception("Collection 생성 실패")

            time.sleep(30)

        return collection_arn, collection_id

    except Exception as e:
        print(f"  ❌ OpenSearch Collection 생성 실패: {str(e)}")
        raise

def create_knowledge_base(role_arn, collection_arn):
    """Knowledge Base 생성"""
    print(f"\n[3/6] Knowledge Base 생성: {KB_NAME}")

    try:
        # 기존 KB 확인
        try:
            kbs = bedrock_agent.list_knowledge_bases()
            for kb in kbs.get('knowledgeBaseSummaries', []):
                if kb['name'] == KB_NAME:
                    print(f"  ✅ Knowledge Base가 이미 존재합니다")
                    print(f"     ID: {kb['knowledgeBaseId']}")
                    return kb['knowledgeBaseId']
        except:
            pass

        # KB 생성
        response = bedrock_agent.create_knowledge_base(
            name=KB_NAME,
            description=KB_DESCRIPTION,
            roleArn=role_arn,
            knowledgeBaseConfiguration={
                'type': 'VECTOR',
                'vectorKnowledgeBaseConfiguration': {
                    'embeddingModelArn': f'arn:aws:bedrock:{REGION}::foundation-model/amazon.titan-embed-text-v1'
                }
            },
            storageConfiguration={
                'type': 'OPENSEARCH_SERVERLESS',
                'opensearchServerlessConfiguration': {
                    'collectionArn': collection_arn,
                    'vectorIndexName': 'nexus-prompts-index',
                    'fieldMapping': {
                        'vectorField': 'vector',
                        'textField': 'text',
                        'metadataField': 'metadata'
                    }
                }
            }
        )

        kb_id = response['knowledgeBase']['knowledgeBaseId']
        print(f"  ✅ Knowledge Base 생성 완료!")
        print(f"     ID: {kb_id}")
        return kb_id

    except Exception as e:
        print(f"  ❌ Knowledge Base 생성 실패: {str(e)}")
        raise

def create_data_source(kb_id):
    """Data Source (S3) 생성"""
    print(f"\n[4/6] Data Source 생성")

    try:
        response = bedrock_agent.create_data_source(
            knowledgeBaseId=kb_id,
            name='nexus-prompts-s3',
            description='S3 data source for Nexus Title prompts',
            dataSourceConfiguration={
                'type': 'S3',
                's3Configuration': {
                    'bucketArn': f'arn:aws:s3:::{S3_BUCKET}',
                    'inclusionPrefixes': [S3_PREFIX]
                }
            }
        )

        ds_id = response['dataSource']['dataSourceId']
        print(f"  ✅ Data Source 생성 완료!")
        print(f"     ID: {ds_id}")
        return ds_id

    except Exception as e:
        print(f"  ❌ Data Source 생성 실패: {str(e)}")
        raise

def ingest_data(kb_id, ds_id):
    """데이터 수집 (Ingestion) 시작"""
    print(f"\n[5/6] 데이터 수집 시작")

    try:
        response = bedrock_agent.start_ingestion_job(
            knowledgeBaseId=kb_id,
            dataSourceId=ds_id
        )

        job_id = response['ingestionJob']['ingestionJobId']
        print(f"  ✅ Ingestion job 시작!")
        print(f"     Job ID: {job_id}")

        # Job 상태 모니터링
        print(f"  ⏳ Ingestion 진행 중...")
        while True:
            status_response = bedrock_agent.get_ingestion_job(
                knowledgeBaseId=kb_id,
                dataSourceId=ds_id,
                ingestionJobId=job_id
            )

            status = status_response['ingestionJob']['status']
            print(f"     상태: {status}")

            if status == 'COMPLETE':
                stats = status_response['ingestionJob']['statistics']
                print(f"  ✅ Ingestion 완료!")
                print(f"     처리된 문서: {stats.get('numberOfDocumentsScanned', 0)}개")
                print(f"     성공: {stats.get('numberOfDocumentsIndexed', 0)}개")
                print(f"     실패: {stats.get('numberOfDocumentsFailed', 0)}개")
                break
            elif status == 'FAILED':
                raise Exception("Ingestion 실패")

            time.sleep(10)

        return True

    except Exception as e:
        print(f"  ❌ Data ingestion 실패: {str(e)}")
        raise

def verify_knowledge_base(kb_id):
    """Knowledge Base 검증"""
    print(f"\n[6/6] Knowledge Base 검증")

    try:
        # KB 정보 조회
        kb_response = bedrock_agent.get_knowledge_base(
            knowledgeBaseId=kb_id
        )

        kb = kb_response['knowledgeBase']
        print(f"  ✅ Knowledge Base: {kb['name']}")
        print(f"     ID: {kb['knowledgeBaseId']}")
        print(f"     Status: {kb['status']}")
        print(f"     Created: {kb['createdAt']}")

        # Data source 조회
        ds_response = bedrock_agent.list_data_sources(
            knowledgeBaseId=kb_id
        )

        print(f"\n  📁 Data Sources:")
        for ds in ds_response['dataSourceSummaries']:
            print(f"     - {ds['name']} (ID: {ds['dataSourceId']})")

        return True

    except Exception as e:
        print(f"  ❌ 검증 실패: {str(e)}")
        return False

def main():
    """메인 실행"""
    print("="*60)
    print("🚀 AWS Bedrock Knowledge Base 생성")
    print("="*60)

    try:
        # 1. IAM Role 생성
        role_arn = create_kb_role()

        # 2. OpenSearch Serverless Collection 생성
        collection_arn, collection_id = create_opensearch_collection()

        # 3. Knowledge Base 생성
        kb_id = create_knowledge_base(role_arn, collection_arn)

        # 4. Data Source 생성
        ds_id = create_data_source(kb_id)

        # 5. 데이터 수집
        ingest_data(kb_id, ds_id)

        # 6. 검증
        verify_knowledge_base(kb_id)

        print("\n" + "="*60)
        print("✅ Knowledge Base 생성 완료!")
        print("="*60)
        print(f"\n다음 단계:")
        print(f"1. Knowledge Base ID를 기록: {kb_id}")
        print(f"2. Bedrock Agent 생성 시 이 KB를 연결")
        print(f"3. Agent 코드에서 KB ID 사용")
        print("="*60)

        # 결과를 파일로 저장
        result = {
            'knowledge_base_id': kb_id,
            'collection_arn': collection_arn,
            'role_arn': role_arn,
            'data_source_id': ds_id
        }

        with open('kb_config.json', 'w') as f:
            json.dump(result, f, indent=2)

        print(f"\n💾 설정 정보가 kb_config.json에 저장되었습니다")

    except Exception as e:
        print(f"\n❌ 에러 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
