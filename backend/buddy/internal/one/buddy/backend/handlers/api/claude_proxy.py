import json
import os
import urllib3
from typing import Dict, Any

http = urllib3.PoolManager()

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Claude API 프록시 Lambda 핸들러"""
    
    try:
        # CORS 헤더
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'POST,OPTIONS',
            'Content-Type': 'application/json'
        }
        
        # OPTIONS 요청 처리
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': ''
            }
        
        # 요청 본문 파싱
        body = json.loads(event.get('body', '{}'))
        message = body.get('message')
        model = body.get('model', 'claude-opus-4-20250514')
        api_key = body.get('apiKey') or os.environ.get('CLAUDE_API_KEY')
        
        if not api_key:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'API 키가 필요합니다.'})
            }
        
        if not message:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': '메시지가 필요합니다.'})
            }
        
        # Claude API 요청
        claude_response = http.request(
            'POST',
            'https://api.anthropic.com/v1/messages',
            headers={
                'Content-Type': 'application/json',
                'x-api-key': api_key,
                'anthropic-version': '2023-06-01'
            },
            body=json.dumps({
                'model': model,
                'max_tokens': 4096,
                'messages': [{'role': 'user', 'content': message}]
            }).encode('utf-8')
        )
        
        if claude_response.status != 200:
            return {
                'statusCode': claude_response.status,
                'headers': headers,
                'body': json.dumps({
                    'error': f'Claude API 오류: {claude_response.status}',
                    'details': claude_response.data.decode('utf-8')
                })
            }
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': claude_response.data.decode('utf-8')
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': '서버 오류가 발생했습니다.',
                'details': str(e)
            })
        }
