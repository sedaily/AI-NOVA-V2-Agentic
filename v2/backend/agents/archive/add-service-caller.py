import boto3
import zipfile
import io
import os

lambda_client = boto3.client('lambda', region_name='us-east-1')
bedrock = boto3.client('bedrock-agent', region_name='us-east-1')
sts = boto3.client('sts')

account_id = sts.get_caller_identity()['Account']
role_arn = f"arn:aws:iam::{account_id}:role/BedrockAgentExecutionRole"
agent_id = 'JGEFIJJERA'

# 1. Lambda 배포
function_name = 'bedrock-service-caller'

print(f"📦 {function_name} Lambda 배포 중...\n")

zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
    zip_file.write('service-caller/lambda_function.py', 'lambda_function.py')

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
        MemorySize=512
    )
    print(f"✅ Lambda 생성 완료")
except lambda_client.exceptions.ResourceConflictException:
    response = lambda_client.update_function_code(
        FunctionName=function_name,
        ZipFile=zip_content
    )
    print(f"✅ Lambda 업데이트 완료")

lambda_arn = f"arn:aws:lambda:us-east-1:{account_id}:function:{function_name}"

# 2. Lambda 권한 추가
try:
    lambda_client.add_permission(
        FunctionName=function_name,
        StatementId=f'bedrock-agent-{agent_id}',
        Action='lambda:InvokeFunction',
        Principal='bedrock.amazonaws.com',
        SourceArn=f"arn:aws:bedrock:us-east-1:{account_id}:agent/{agent_id}"
    )
except:
    pass

# 3. Action Group 추가
print("\n📦 ServiceCaller Action Group 추가 중...")

try:
    bedrock.create_agent_action_group(
        agentId=agent_id,
        agentVersion='DRAFT',
        actionGroupName='ServiceCaller',
        description='Calls actual backend services',
        actionGroupExecutor={'lambda': lambda_arn},
        functionSchema={
            'functions': [
                {
                    'name': 'callService',
                    'description': 'Call backend service with user message',
                    'parameters': {
                        'serviceCode': {
                            'type': 'string',
                            'description': 'Service code (b1/t1/p1/w1/f1/r1)',
                            'required': True
                        },
                        'message': {
                            'type': 'string',
                            'description': 'User message to send to service',
                            'required': True
                        }
                    }
                }
            ]
        }
    )
    print("✅ Action Group 추가 완료")
except Exception as e:
    print(f"❌ Action Group 추가 실패: {e}")

# 4. Agent Prepare
print("\n🔧 Agent 준비 중...")
bedrock.prepare_agent(agentId=agent_id)
print("✅ Agent 준비 완료")

print("\n🎉 완료! AWS Console에서 테스트하세요:")
print("https://us-east-1.console.aws.amazon.com/bedrock/home?region=us-east-1#/agents/JGEFIJJERA")
