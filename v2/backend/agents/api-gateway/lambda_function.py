import boto3
import json
import uuid
import traceback

bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
lambda_client = boto3.client('lambda', region_name='us-east-1')

AGENT_ID = 'JGEFIJJERA'
ALIAS_ID = '0U7GBBKCVR'

# 서비스 Lambda 매핑
SERVICE_LAMBDAS = {
    'b1': 'buddy-handler',
    't1': 'title-handler', 
    'p1': 'proofreading-handler',
    'w1': 'bodo-handler',
    'f1': 'foreign-handler',
    'r1': 'regression-handler'
}

def call_service(service_code, message):
    """Lambda 서비스 직접 호출"""
    lambda_name = SERVICE_LAMBDAS.get(service_code)
    if not lambda_name:
        return None
    
    try:
        response = lambda_client.invoke(
            FunctionName=lambda_name,
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'message': message,
                'serviceCode': service_code,
                'userId': 'agent-user'
            })
        )
        result = json.loads(response['Payload'].read())
        return result.get('body', result)
    except Exception as e:
        print(f"Service call error: {str(e)}")
        return None

def lambda_handler(event, context):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS'
    }
    
    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': headers, 'body': ''}
    
    try:
        body = json.loads(event.get('body', '{}'))
        user_message = body.get('message', '')
        session_id = body.get('sessionId', str(uuid.uuid4()))
        
        if not user_message:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'message is required'})
            }
        
        # Agent 호출
        response = bedrock_runtime.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=ALIAS_ID,
            sessionId=session_id,
            inputText=user_message
        )
        
        agent_result = ''
        for event_chunk in response['completion']:
            if 'chunk' in event_chunk:
                chunk = event_chunk['chunk']
                if 'bytes' in chunk:
                    agent_result += chunk['bytes'].decode('utf-8')
        
        # Agent 응답에서 서비스 코드 추출
        service_code = None
        for code in ['f1', 'p1', 'r1', 'w1', 'b1', 't1']:
            if code in agent_result.lower():
                service_code = code
                break
        
        # 서비스 호출
        if service_code:
            print(f"Calling service: {service_code}")
            service_result = call_service(service_code, user_message)
            
            if service_result:
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps({
                        'response': service_result,
                        'agentAnalysis': agent_result,
                        'serviceUsed': service_code,
                        'sessionId': session_id
                    })
                }
        
        # 서비스 호출 실패 시 Agent 분석만 반환
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'response': agent_result,
                'sessionId': session_id
            })
        }
        
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"Error: {error_msg}")
        print(f"Traceback: {error_trace}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': error_msg, 'trace': error_trace})
        }
