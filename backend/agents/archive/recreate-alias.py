import boto3

bedrock = boto3.client('bedrock-agent', region_name='us-east-1')

agent_id = 'JGEFIJJERA'
alias_id = 'MVYJQAKXAZ'

print("🗑️  기존 Alias 삭제 중...\n")

try:
    bedrock.delete_agent_alias(
        agentId=agent_id,
        agentAliasId=alias_id
    )
    print("✅ 삭제 완료\n")
except Exception as e:
    print(f"⚠️  삭제 실패 (무시): {e}\n")

print("🚀 새 Alias 생성 중...\n")

try:
    response = bedrock.create_agent_alias(
        agentId=agent_id,
        agentAliasName='prod',
        description='Production alias for ServiceRouterAgent'
    )
    
    new_alias_id = response['agentAlias']['agentAliasId']
    print(f"✅ Alias 생성 완료!")
    print(f"\nAlias ID: {new_alias_id}")
    print(f"Alias ARN: {response['agentAlias']['agentAliasArn']}")
    
except Exception as e:
    print(f"❌ 생성 실패: {e}")
