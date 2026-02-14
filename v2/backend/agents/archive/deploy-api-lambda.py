import boto3
import zipfile
import io
import os

lambda_client = boto3.client('lambda', region_name='us-east-1')
sts = boto3.client('sts')

account_id = sts.get_caller_identity()['Account']
role_arn = f"arn:aws:iam::{account_id}:role/BedrockAgentExecutionRole"

function_name = 'bedrock-agent-api'

print(f"🚀 {function_name} Lambda 배포 중...\n")

# ZIP 생성
zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
    zip_file.write('api-gateway/lambda_function.py', 'lambda_function.py')

zip_buffer.seek(0)
zip_content = zip_buffer.read()

try:
    response = lambda_client.create_function(
        FunctionName=function_name,
        Runtime='python3.11',
        Role=role_arn,
        Handler='lambda_function.lambda_handler',
        Code={'ZipFile': zip_content},
        Timeout=60,
        MemorySize=512,
        Description='API Gateway to Bedrock Agent'
    )
    print(f"✅ Lambda 생성 완료")
    print(f"📋 ARN: {response['FunctionArn']}")
except lambda_client.exceptions.ResourceConflictException:
    response = lambda_client.update_function_code(
        FunctionName=function_name,
        ZipFile=zip_content
    )
    print(f"✅ Lambda 업데이트 완료")
    print(f"📋 ARN: {response['FunctionArn']}")

print("\n다음: API Gateway 생성")
print("AWS Console → API Gateway → Create API → REST API")
print(f"Lambda 함수: {function_name}")
