import boto3
import json
import zipfile
import io
import os

# AWS 클라이언트 생성
iam = boto3.client('iam', region_name='us-east-1')
lambda_client = boto3.client('lambda', region_name='us-east-1')
sts = boto3.client('sts')

print("🚀 Phase 1: Lambda 함수 배포 시작...")

# Account ID 가져오기
account_id = sts.get_caller_identity()['Account']
role_arn = f"arn:aws:iam::{account_id}:role/BedrockAgentExecutionRole"

print(f"📋 Account ID: {account_id}")
print(f"📋 Role ARN: {role_arn}")

# Lambda 함수 배포
agents = [
    'language-detector',
    'category-detector', 
    'length-detector',
    'content-type-detector'
]

for agent_name in agents:
    function_name = f"bedrock-{agent_name}"
    
    print(f"\n📦 {agent_name} Lambda 배포 중...")
    
    # ZIP 파일 생성 (메모리에서)
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        lambda_file = os.path.join(agent_name, 'lambda_function.py')
        zip_file.write(lambda_file, 'lambda_function.py')
    
    zip_buffer.seek(0)
    zip_content = zip_buffer.read()
    
    try:
        # Lambda 함수 생성
        response = lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.11',
            Role=role_arn,
            Handler='lambda_function.lambda_handler',
            Code={'ZipFile': zip_content},
            Timeout=30,
            MemorySize=256,
            Description=f"Bedrock Agent: {agent_name}",
            Tags={
                'Project': 'AI-NOVA',
                'Environment': 'Production'
            }
        )
        print(f"✅ {function_name} 생성 완료")
        print(f"📋 ARN: {response['FunctionArn']}")
        
    except lambda_client.exceptions.ResourceConflictException:
        # 이미 존재하면 업데이트
        print(f"⚠️  {function_name} 이미 존재 - 업데이트 중...")
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        print(f"✅ {function_name} 업데이트 완료")
        print(f"📋 ARN: {response['FunctionArn']}")
    
    except Exception as e:
        print(f"❌ {function_name} 배포 실패: {str(e)}")

print("\n🎉 Phase 1 완료!")
print("\n생성된 Lambda 함수:")

# Lambda 함수 목록 출력
response = lambda_client.list_functions()
bedrock_functions = [f['FunctionName'] for f in response['Functions'] if f['FunctionName'].startswith('bedrock-')]
for func in bedrock_functions:
    print(f"  - {func}")

print("\n다음 단계: Bedrock Agent 생성 (AWS Console)")
