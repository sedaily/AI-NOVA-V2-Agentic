import boto3

bedrock = boto3.client('bedrock-agent', region_name='us-east-1')

agent_id = 'JGEFIJJERA'

print("🔍 Agent Alias 조회 중...\n")

try:
    response = bedrock.list_agent_aliases(agentId=agent_id)
    
    if response['agentAliasSummaries']:
        for alias in response['agentAliasSummaries']:
            print(f"Alias Name: {alias['agentAliasName']}")
            print(f"Alias ID: {alias['agentAliasId']}")
            print(f"Status: {alias['agentAliasStatus']}\n")
    else:
        print("❌ Alias가 없습니다. recreate-alias.py를 실행하세요.")
        
except Exception as e:
    print(f"❌ 오류: {e}")
