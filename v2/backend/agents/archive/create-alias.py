import boto3

bedrock = boto3.client('bedrock-agent', region_name='us-east-1')

agent_id = 'JGEFIJJERA'

print("🚀 Agent Alias 생성 중...\n")

try:
    response = bedrock.create_agent_alias(
        agentId=agent_id,
        agentAliasName='prod',
        description='Production alias for ServiceRouterAgent'
    )
    
    alias_id = response['agentAlias']['agentAliasId']
    print(f"✅ Alias 생성 완료!")
    print(f"\nAlias ID: {alias_id}")
    print(f"Alias ARN: {response['agentAlias']['agentAliasArn']}")
    
except Exception as e:
    print(f"❌ 생성 실패: {e}")
