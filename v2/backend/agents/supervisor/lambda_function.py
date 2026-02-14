import json
import boto3

lambda_client = boto3.client('lambda')

def quick_language_check(text):
    """빠른 한글 체크 (무료, Agent 호출 없음)"""
    if not text:
        return 'korean'
    
    korean_chars = sum(1 for c in text if '가' <= c <= '힣')
    total_chars = len(text.replace(' ', '').replace('\n', ''))
    
    if total_chars == 0:
        return 'korean'
    
    korean_ratio = korean_chars / total_chars
    
    # 30% 이상 한글이면 한글로 판단
    if korean_ratio > 0.3:
        return 'korean'
    else:
        return 'foreign'

def invoke_agent(agent_name, payload):
    """Agent Lambda 함수 호출"""
    try:
        response = lambda_client.invoke(
            FunctionName=f'agent-{agent_name}',
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        
        # Lambda 응답에서 body 추출
        if 'body' in result:
            return json.loads(result['body'])
        return result
        
    except Exception as e:
        print(f"Error invoking {agent_name}: {str(e)}")
        return None

def lambda_handler(event, context):
    """
    Supervisor Agent - 오케스트레이터
    
    플로우:
    1. 빠른 언어 체크 (무료)
    2. 외국어면 → Language Agent → Foreign (f1)
    3. 한글이면 → Content Type Agent
       - 보도자료 → Bodo (w1)
       - 기사 → Category Agent → Proofreading (p1) → Length Agent → Regression (r1)
    """
    
    text = event.get('text', '')
    
    # 결과 추적
    orchestration_log = {
        'steps': [],
        'agents_called': []
    }
    
    # Step 1: 빠른 언어 체크 (무료)
    quick_lang = quick_language_check(text)
    orchestration_log['steps'].append({
        'step': 1,
        'action': 'quick_language_check',
        'result': quick_lang,
        'cost': 0
    })
    
    # Step 2: 외국어 처리
    if quick_lang == 'foreign':
        orchestration_log['steps'].append({
            'step': 2,
            'action': 'foreign_detected',
            'message': 'Calling Language Agent'
        })
        
        # Language Agent 호출
        language_result = invoke_agent('language-detector', {'text': text})
        orchestration_log['agents_called'].append('language-detector')
        
        if language_result and language_result.get('language') in ['english', 'japanese']:
            # 외신 서비스로 라우팅
            final_routing = {
                'serviceCode': 'f1',
                'promptType': language_result['language'],
                'engineType': '22',
                'contentType': f"foreign_{language_result['language']}",
                'language': language_result['language']
            }
            
            orchestration_log['steps'].append({
                'step': 3,
                'action': 'route_to_foreign',
                'result': final_routing
            })
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'routing': final_routing,
                    'orchestration': orchestration_log
                })
            }
    
    # Step 3: 한글 처리 - Content Type Agent
    orchestration_log['steps'].append({
        'step': 3,
        'action': 'korean_detected',
        'message': 'Calling Content Type Agent'
    })
    
    content_type_result = invoke_agent('content-type-detector', {'text': text})
    orchestration_log['agents_called'].append('content-type-detector')
    
    # Step 4: 보도자료 체크
    if content_type_result and content_type_result.get('isPressRelease'):
        # 보도자료 → w1 서비스
        final_routing = content_type_result['writerConfig']
        
        orchestration_log['steps'].append({
            'step': 4,
            'action': 'route_to_bodo',
            'result': final_routing
        })
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'routing': final_routing,
                'orchestration': orchestration_log
            })
        }
    
    # Step 5: 일반 기사 → Category Agent
    orchestration_log['steps'].append({
        'step': 5,
        'action': 'article_detected',
        'message': 'Calling Category Agent'
    })
    
    category_result = invoke_agent('category-detector', {'text': text})
    orchestration_log['agents_called'].append('category-detector')
    
    # Step 6: 교열 (p1) - Category 결과 사용
    proofreading_config = {
        'serviceCode': 'p1',
        'promptType': category_result.get('category', 'economy') if category_result else 'economy',
        'engineType': '22',
        'contentType': 'proofreading'
    }
    
    orchestration_log['steps'].append({
        'step': 6,
        'action': 'proofreading_ready',
        'config': proofreading_config
    })
    
    # Step 7: 퇴고 (r1) - Length Agent 호출
    orchestration_log['steps'].append({
        'step': 7,
        'action': 'calling_length_agent',
        'message': 'Determining article length for regression'
    })
    
    length_result = invoke_agent('length-detector', {'text': text})
    orchestration_log['agents_called'].append('length-detector')
    
    regression_config = {
        'serviceCode': 'r1',
        'promptType': length_result.get('lengthType', 'short') if length_result else 'short',
        'engineType': '22',
        'contentType': 'regression'
    }
    
    orchestration_log['steps'].append({
        'step': 8,
        'action': 'regression_ready',
        'config': regression_config
    })
    
    # 최종 라우팅: 기사버디 → 교열 → 퇴고
    final_routing = {
        'primary': content_type_result['writerConfig'] if content_type_result else {
            'serviceCode': 'b1',
            'promptType': 'article',
            'engineType': '22',
            'contentType': 'article'
        },
        'proofreading': proofreading_config,
        'regression': regression_config,
        'pipeline': ['b1', 'p1', 'r1']
    }
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'routing': final_routing,
            'orchestration': orchestration_log
        })
    }
