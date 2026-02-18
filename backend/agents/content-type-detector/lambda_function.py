import json

def detect_press_release(text):
    """보도자료 여부 감지"""
    # 보도자료 특징 키워드
    press_indicators = [
        '보도자료',
        '배포일시',
        '배포 일시',
        '문의:',
        '담당자:',
        '※',
        '붙임:',
        '[별첨]',
        '보도 참고',
        '즉시 배포',
        '엠바고',
        '보도 배포',
        '자료 배포',
        '참고자료',
        '첨부파일',
        '문의처',
        '연락처:'
    ]
    
    # 1개 이상 특징이 있으면 보도자료 (기준 완화)
    press_score = sum(1 for indicator in press_indicators if indicator in text)
    return press_score >= 1

def detect_press_type(text):
    """보도자료 타입 감지 (공공/기업)"""
    
    # 공공기관 키워드 (강화)
    public_keywords = [
        '정부', '부처', '청', '시청', '구청', '도청', '군청',
        '국회', '의회', '위원회',
        '공공기관', '공단', '공사', '재단',
        '교육청', '경찰청', '소방서', '소방본부',
        '발표했다', '밝혔다', '전했다',
        '장관', '차관', '국장', '과장',
        '시장', '도지사', '구청장',
        '행정', '정책', '제도', '법안',
        '국민', '시민', '주민',
        '예산', '지원금', '보조금',
        '공공', '행정안전부', '기획재정부'
    ]
    
    # 기업 키워드
    corporate_keywords = [
        '주식회사', '(주)', '㈜', 'Co.', 'Ltd',
        '대표이사', 'CEO', '경영진',
        '출시', '론칭', '신제품',
        '매출', '영업이익', '실적',
        '투자', '제휴', '협약',
        '삼성', 'LG', '현대', 'SK', '롯데', '한화'
    ]
    
    public_score = sum(1 for kw in public_keywords if kw in text)
    corporate_score = sum(1 for kw in corporate_keywords if kw in text)
    
    if public_score > corporate_score:
        return 'public'
    elif corporate_score > public_score:
        return 'corporate'
    else:
        return 'public'  # 기본값을 public으로 변경

def lambda_handler(event, context):
    """콘텐츠 타입 감지 에이전트"""
    action_group = event.get('actionGroup', '')
    function = event.get('function', '')
    parameters = event.get('parameters', [])
    
    text = ''
    for param in parameters:
        if param.get('name') == 'text':
            text = param.get('value', '')
            break
    
    is_press_release = detect_press_release(text)
    press_type = detect_press_type(text) if is_press_release else None
    
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': action_group,
            'function': function,
            'functionResponse': {
                'responseBody': {
                    'TEXT': {
                        'body': json.dumps({
                            'isPressRelease': is_press_release,
                            'pressType': press_type
                        })
                    }
                }
            }
        }
    }
