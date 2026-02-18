import json

def lambda_handler(event, context):
    """글자수 감지 에이전트"""
    action_group = event.get('actionGroup', '')
    function = event.get('function', '')
    parameters = event.get('parameters', [])
    
    text = ''
    for param in parameters:
        if param.get('name') == 'text':
            text = param.get('value', '')
            break
    
    char_count = len(text)
    is_long_form = char_count >= 1000
    
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': action_group,
            'function': function,
            'functionResponse': {
                'responseBody': {
                    'TEXT': {
                        'body': json.dumps({
                            'charCount': char_count,
                            'isLongForm': is_long_form
                        })
                    }
                }
            }
        }
    }
