import json
import re

def detect_language(text):
    """언어 감지"""
    english = len(re.findall(r'[a-zA-Z]', text))
    japanese = len(re.findall(r'[\u3040-\u309F\u30A0-\u30FF]', text))
    korean = len(re.findall(r'[가-힣]', text))
    
    total = english + japanese + korean
    if total == 0:
        return 'unknown'
    
    if english / total > 0.3:
        return 'en'
    if japanese / total > 0.3:
        return 'ja'
    return 'ko'

def lambda_handler(event, context):
    """언어 감지 에이전트"""
    # Bedrock Agent 요청 파싱
    agent = event.get('agent', '')
    action_group = event.get('actionGroup', '')
    function = event.get('function', '')
    parameters = event.get('parameters', [])
    
    # 파라미터에서 text 추출
    text = ''
    for param in parameters:
        if param.get('name') == 'text':
            text = param.get('value', '')
            break
    
    language = detect_language(text)
    needs_foreign_agent = language in ['en', 'ja']
    
    # Bedrock Agent 응답 형식
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': action_group,
            'function': function,
            'functionResponse': {
                'responseBody': {
                    'TEXT': {
                        'body': json.dumps({
                            'language': language,
                            'needsForeignAgent': needs_foreign_agent
                        })
                    }
                }
            }
        }
    }
