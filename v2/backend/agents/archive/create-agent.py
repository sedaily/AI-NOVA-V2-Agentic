import boto3
import json
import time

bedrock = boto3.client('bedrock-agent', region_name='us-east-1')
lambda_client = boto3.client('lambda', region_name='us-east-1')
sts = boto3.client('sts')

account_id = sts.get_caller_identity()['Account']
role_arn = f"arn:aws:iam::{account_id}:role/BedrockAgentExecutionRole"

print("🚀 Bedrock Agent 생성 시작...\n")

# 1. Agent 생성
print("📋 Agent 생성 중...")
agent_instruction = """You are a service routing assistant for Seoul Economic Daily's AI platform.

Your job is to analyze user requests and determine:
1. Language (ko/en/ja)
2. Category (economy/society/public/corporate)
3. Content length (short/long)
4. Content type (article/press_release)

Based on these, route to the appropriate service:
- b1: 일보버디, 기사버디
- t1: 제목생성, 제목창의
- p1: 교열 (경제/사회)
- w1: 보도자료 (기업/공공)
- f1: 외신 (영어/일어)
- r1: 퇴고 (단문/장문)

Always respond in Korean."""

try:
    agent_response = bedrock.create_agent(
        agentName='ServiceRouterAgent',
        agentResourceRoleArn=role_arn,
        description='Routes user requests to appropriate AI services',
        foundationModel='anthropic.claude-opus-4-5-20251101-v1:0',
        instruction=agent_instruction,
        idleSessionTTLInSeconds=600
    )
    agent_id = agent_response['agent']['agentId']
    print(f"✅ Agent 생성 완료: {agent_id}\n")
except Exception as e:
    print(f"❌ Agent 생성 실패: {e}")
    exit(1)

# 2. Action Groups 정의
action_groups = [
    {
        'name': 'LanguageDetector',
        'description': 'Detects language of user input',
        'lambda': 'bedrock-language-detector',
        'function': 'detectLanguage',
        'function_desc': 'Detect language (ko/en/ja)',
        'parameters': [
            {'name': 'text', 'type': 'string', 'description': 'Text to analyze', 'required': True}
        ]
    },
    {
        'name': 'CategoryDetector',
        'description': 'Detects content category',
        'lambda': 'bedrock-category-detector',
        'function': 'detectCategory',
        'function_desc': 'Detect category (economy/society/public/corporate)',
        'parameters': [
            {'name': 'text', 'type': 'string', 'description': 'Text to analyze', 'required': True}
        ]
    },
    {
        'name': 'LengthDetector',
        'description': 'Detects content length',
        'lambda': 'bedrock-length-detector',
        'function': 'detectLength',
        'function_desc': 'Detect length (short/long)',
        'parameters': [
            {'name': 'text', 'type': 'string', 'description': 'Text to analyze', 'required': True}
        ]
    },
    {
        'name': 'ContentTypeDetector',
        'description': 'Detects content type',
        'lambda': 'bedrock-content-type-detector',
        'function': 'detectContentType',
        'function_desc': 'Detect content type (article/press_release)',
        'parameters': [
            {'name': 'text', 'type': 'string', 'description': 'Text to analyze', 'required': True}
        ]
    }
]

# 3. Action Groups 생성
for ag in action_groups:
    print(f"📦 {ag['name']} Action Group 생성 중...")
    
    lambda_arn = f"arn:aws:lambda:us-east-1:{account_id}:function:{ag['lambda']}"
    
    # Lambda 권한 추가
    try:
        lambda_client.add_permission(
            FunctionName=ag['lambda'],
            StatementId=f'bedrock-agent-{agent_id}',
            Action='lambda:InvokeFunction',
            Principal='bedrock.amazonaws.com',
            SourceArn=f"arn:aws:bedrock:us-east-1:{account_id}:agent/{agent_id}"
        )
    except lambda_client.exceptions.ResourceConflictException:
        pass
    
    # Action Group 생성
    try:
        bedrock.create_agent_action_group(
            agentId=agent_id,
            agentVersion='DRAFT',
            actionGroupName=ag['name'],
            description=ag['description'],
            actionGroupExecutor={
                'lambda': lambda_arn
            },
            functionSchema={
                'functions': [
                    {
                        'name': ag['function'],
                        'description': ag['function_desc'],
                        'parameters': {
                            param['name']: {
                                'type': param['type'],
                                'description': param['description'],
                                'required': param['required']
                            }
                            for param in ag['parameters']
                        }
                    }
                ]
            }
        )
        print(f"✅ {ag['name']} 생성 완료")
    except Exception as e:
        print(f"❌ {ag['name']} 생성 실패: {e}")

# 4. Agent Prepare
print("\n🔧 Agent 준비 중...")
try:
    bedrock.prepare_agent(agentId=agent_id)
    print("✅ Agent 준비 완료")
except Exception as e:
    print(f"❌ Agent 준비 실패: {e}")

print(f"\n🎉 완료!")
print(f"\nAgent ID: {agent_id}")
print(f"Agent ARN: arn:aws:bedrock:us-east-1:{account_id}:agent/{agent_id}")
print(f"\nAWS Console에서 테스트:")
print(f"https://us-east-1.console.aws.amazon.com/bedrock/home?region=us-east-1#/agents/{agent_id}")
