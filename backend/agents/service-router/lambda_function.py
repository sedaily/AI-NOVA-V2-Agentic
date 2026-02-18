import json

def lambda_handler(event, context):
    """분석 결과를 기반으로 호출할 서비스 결정"""
    
    results = event
    language_result = results[0]
    category_result = results[1]
    length_result = results[2]
    content_type_result = results[3]
    
    language = json.loads(language_result['body'])['language']
    category = json.loads(category_result['body'])['category']
    is_long = json.loads(length_result['body'])['isLongForm']
    is_press = json.loads(content_type_result['body'])['isPressRelease']
    press_type = json.loads(content_type_result['body']).get('pressType')
    
    pipeline = []
    
    if language in ['en', 'ja']:
        pipeline.append({'service': 'f1', 'type': language})
    elif is_press:
        pipeline.append({'service': 'w1', 'type': press_type})
    else:
        pipeline.append({'service': 'b1', 'type': 'article'})
    
    if language in ['en', 'ja'] or is_press:
        pipeline.append({'service': 'p1', 'type': category})
    
    pipeline.append({'service': 't1', 'type': 'title'})
    
    return {
        'pipeline': pipeline,
        'originalMessage': event.get('originalMessage', ''),
        'currentStep': 0
    }
