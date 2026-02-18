import boto3
import json
import zipfile
import io

lambda_client = boto3.client('lambda', region_name='us-east-1')
sfn_client = boto3.client('stepfunctions', region_name='us-east-1')
iam = boto3.client('iam', region_name='us-east-1')
sts = boto3.client('sts')

account_id = sts.get_caller_identity()['Account']
role_arn = f"arn:aws:iam::{account_id}:role/BedrockAgentExecutionRole"

print("🚀 Step Functions 파이프라인 배포 시작...\n")

# 1. Service Router Lambda 배포
print("📦 service-router Lambda 배포 중...")
zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
    zip_file.write('service-router/lambda_function.py', 'lambda_function.py')

zip_buffer.seek(0)

try:
    lambda_client.create_function(
        FunctionName='bedrock-service-router',
        Runtime='python3.11',
        Role=role_arn,
        Handler='lambda_function.lambda_handler',
        Code={'ZipFile': zip_buffer.read()},
        Timeout=30,
        MemorySize=256
    )
    print("✅ Lambda 생성 완료\n")
except lambda_client.exceptions.ResourceConflictException:
    zip_buffer.seek(0)
    lambda_client.update_function_code(
        FunctionName='bedrock-service-router',
        ZipFile=zip_buffer.read()
    )
    print("✅ Lambda 업데이트 완료\n")

# 2. Step Functions State Machine 생성
print("📦 Step Functions State Machine 생성 중...")

with open('step-functions-definition.json', 'r') as f:
    definition = f.read()

state_machine_name = 'AINovaServicePipeline'

try:
    response = sfn_client.create_state_machine(
        name=state_machine_name,
        definition=definition,
        roleArn=role_arn,
        type='EXPRESS'
    )
    print(f"✅ State Machine 생성 완료")
    print(f"📋 ARN: {response['stateMachineArn']}")
except sfn_client.exceptions.StateMachineAlreadyExists:
    state_machines = sfn_client.list_state_machines()
    sm_arn = next(sm['stateMachineArn'] for sm in state_machines['stateMachines'] if sm['name'] == state_machine_name)
    
    sfn_client.update_state_machine(
        stateMachineArn=sm_arn,
        definition=definition
    )
    print(f"✅ State Machine 업데이트 완료")
    print(f"📋 ARN: {sm_arn}")

print("\n🎉 Step Functions 파이프라인 배포 완료!")
print("\n다음: API Gateway에서 Step Functions 호출")
