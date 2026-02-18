import json

def detect_category(text):
    """카테고리 감지 (경제/사회)"""
    
    # 경제 키워드
    economy_keywords = [
        '주가', '증시', '금리', '환율', '기업', '매출', '실적', '투자',
        '상장', '배당', '주주', '경영', '재무', '수익', '손실', '영업',
        '코스피', '코스닥', '삼성', 'LG', '현대', 'SK', '반도체',
        '수출', '수입', '무역', '경제', '산업', '시장', '거래'
    ]
    
    # 사회 키워드
    society_keywords = [
        '사건', '사고', '범죄', '경찰', '검찰', '법원', '재판',
        '교육', '학교', '학생', '교사', '대학', '입시',
        '복지', '연금', '의료', '병원', '환자',
        '문화', '예술', '공연', '전시', '영화',
        '정치', '국회', '의원', '선거', '정당',
        '환경', '기후', '재난', '안전'
    ]
    
    economy_score = sum(1 for kw in economy_keywords if kw in text)
    society_score = sum(1 for kw in society_keywords if kw in text)
    
    if economy_score == 0 and society_score == 0:
        return 'general'  # 일반
    
    return 'economy' if economy_score > society_score else 'society'

def lambda_handler(event, context):
    """카테고리 감지 에이전트"""
    # Bedrock Agent 요청 파싱
    action_group = event.get('actionGroup', '')
    function = event.get('function', '')
    parameters = event.get('parameters', [])
    
    text = ''
    for param in parameters:
        if param.get('name') == 'text':
            text = param.get('value', '')
            break
    
    category = detect_category(text)
    
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': action_group,
            'function': function,
            'functionResponse': {
                'responseBody': {
                    'TEXT': {
                        'body': json.dumps({'category': category})
                    }
                }
            }
        }
    }
