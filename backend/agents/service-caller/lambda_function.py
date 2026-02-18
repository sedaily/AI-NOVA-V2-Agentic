import json
import urllib3
import os

http = urllib3.PoolManager()

SERVICE_ENDPOINTS = {
    'b1': 'https://pisnqqgu75.execute-api.us-east-1.amazonaws.com/prod',
    't1': 'https://qyfams2iva.execute-api.us-east-1.amazonaws.com/prod',
    'p1': 'https://wxwdb89w4m.execute-api.us-east-1.amazonaws.com/prod',
    'w1': 'https://16ayefk5lc.execute-api.us-east-1.amazonaws.com/prod',
    'f1': 'https://razlubfzw1.execute-api.us-east-1.amazonaws.com/prod',
    'r1': 'https://t75vorhge1.execute-api.us-east-1.amazonaws.com/prod'
}

# WebSocket URLs
WS_ENDPOINTS = {
    'b1': 'wss://dwc2m51as4.execute-api.us-east-1.amazonaws.com/prod',
    't1': 'wss://hsdpbajz23.execute-api.us-east-1.amazonaws.com/prod',
    'p1': 'wss://p062xh167h.execute-api.us-east-1.amazonaws.com/prod',
    'w1': 'wss://prsebeg7ub.execute-api.us-east-1.amazonaws.com/prod',
    'f1': 'wss://5c6e29dg50.execute-api.us-east-1.amazonaws.com/prod',
    'r1': 'wss://ebqodb8ax9.execute-api.us-east-1.amazonaws.com/production'
}

def lambda_handler(event, context):
    """실제 백엔드 서비스 호출"""
    action_group = event.get('actionGroup', '')
    function = event.get('function', '')
    parameters = event.get('parameters', [])
    
    # 파라미터 추출
    service_code = ''
    user_message = ''
    
    for param in parameters:
        if param.get('name') == 'serviceCode':
            service_code = param.get('value', '')
        elif param.get('name') == 'message':
            user_message = param.get('value', '')
    
    # 서비스 호출
    endpoint = SERVICE_ENDPOINTS.get(service_code)
    if not endpoint:
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': action_group,
                'function': function,
                'functionResponse': {
                    'responseBody': {
                        'TEXT': {
                            'body': json.dumps({'error': f'Unknown service: {service_code}'})
                        }
                    }
                }
            }
        }
    
    try:
        # REST API 호출 (인증 토큰 없이)
        response = http.request(
            'POST',
            f'{endpoint}/invoke',
            body=json.dumps({
                'message': user_message,
                'serviceCode': service_code
            }),
            headers={
                'Content-Type': 'application/json'
            }
        )
        
        result = json.loads(response.data.decode('utf-8'))
        
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': action_group,
                'function': function,
                'functionResponse': {
                    'responseBody': {
                        'TEXT': {
                            'body': json.dumps({
                                'success': True,
                                'result': result,
                                'service': service_code
                            })
                        }
                    }
                }
            }
        }
    except Exception as e:
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': action_group,
                'function': function,
                'functionResponse': {
                    'responseBody': {
                        'TEXT': {
                            'body': json.dumps({'error': str(e)})
                        }
                    }
                }
            }
        }
