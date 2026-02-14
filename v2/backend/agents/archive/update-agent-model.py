import boto3

bedrock = boto3.client('bedrock-agent', region_name='us-east-1')
sts = boto3.client('sts')

account_id = sts.get_caller_identity()['Account']
role_arn = f"arn:aws:iam::{account_id}:role/BedrockAgentExecutionRole"
agent_id = 'JGEFIJJERA'

print("🔄 Agent 모델 업데이트 중...\n")

try:
    bedrock.update_agent(
        agentId=agent_id,
        agentName='ServiceRouterAgent',
        agentResourceRoleArn=role_arn,
        foundationModel='us.anthropic.claude-opus-4-5-20251101-v1:0',
        instruction="""You are an AI service router for Seoul Economic Daily.

When user provides content:
1. Use detectLanguage, detectCategory, detectLength, detectContentType to analyze
2. Determine the service code (b1/t1/p1/w1/f1/r1)
3. IMMEDIATELY call callService function with the service code and original user message
4. Return the actual service response to the user

Service mapping:
- Foreign language (en/ja) → f1
- Press release (public) → w1 (public)
- Press release (corporate) → w1 (corporate)  
- Economy article → p1 (economy)
- Society article → p1 (society)
- Long article (>1000 chars) → r1 (long)
- Short article → r1 (short)
- Title generation → t1
- General article → b1

DO NOT just explain. ALWAYS call callService and return the actual result.

Respond in Korean."""
    )
    print("✅ 모델 업데이트 완료: Claude Opus 4.5 (Cross-region)")
    
    # Prepare 필요
    bedrock.prepare_agent(agentId=agent_id)
    print("✅ Agent 준비 완료")
    
except Exception as e:
    print(f"❌ 업데이트 실패: {e}")
