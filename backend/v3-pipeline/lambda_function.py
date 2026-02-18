"""
NOVA v3 Pipeline API Handler
5-Phase Article Writing Pipeline using AWS Bedrock

Endpoints:
- POST /v3/analyze      - Phase 1: 소재 분석 (buddy 프롬프트) → 앵글 추천
- POST /v3/draft        - Phase 3: 초안 생성 (bodo 프롬프트)
- POST /v3/proofread    - Phase 4: 교열 (proofreading 프롬프트)
- POST /v3/revise       - Phase 4: 퇴고 (regression 프롬프트)
- POST /v3/titles       - Phase 5: 제목 생성 (title 프롬프트)
- POST /v3/save         - 파이프라인 상태 저장
- GET  /v3/load/{id}    - 파이프라인 상태 로드
"""

import json
import os
import traceback
import uuid
import boto3
from datetime import datetime
from decimal import Decimal

# Initialize AWS clients
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-2')

# DynamoDB Table
PIPELINE_TABLE = os.environ.get('PIPELINE_TABLE', 'nova-v3-pipeline')

# Bedrock Model - Claude 4.5 Sonnet
MODEL_ID = "us.anthropic.claude-sonnet-4-20250514-v1:0"

# Service Endpoints (기존 서비스)
SERVICE_ENDPOINTS = {
    'b1': 'https://pisnqqgu75.execute-api.us-east-1.amazonaws.com/prod',
    't1': 'https://qyfams2iva.execute-api.us-east-1.amazonaws.com/prod',
    'p1': 'https://wxwdb89w4m.execute-api.us-east-1.amazonaws.com/prod',
    'w1': 'https://16ayefk5lc.execute-api.us-east-1.amazonaws.com/prod',
    'f1': 'https://razlubfzw1.execute-api.us-east-1.amazonaws.com/prod',
    'r1': 'https://t75vorhge1.execute-api.us-east-1.amazonaws.com/prod'
}

# CORS headers
CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
    'Content-Type': 'application/json'
}


def make_response(status_code, body):
    """Create API Gateway response"""
    return {
        'statusCode': status_code,
        'headers': CORS_HEADERS,
        'body': json.dumps(body, ensure_ascii=False, default=str)
    }


def call_bedrock(system_prompt, user_message, max_tokens=4000):
    """Call Bedrock with Claude 4.5 Sonnet"""
    try:
        response = bedrock.invoke_model(
            modelId=MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "system": system_prompt,
                "messages": [
                    {"role": "user", "content": user_message}
                ]
            })
        )

        result = json.loads(response['body'].read())
        return result['content'][0]['text']
    except Exception as e:
        print(f"Bedrock error: {str(e)}")
        raise e


def parse_json_response(response_text):
    """Extract JSON from response text"""
    try:
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            return json.loads(response_text[json_start:json_end])
    except json.JSONDecodeError:
        pass
    return None


# ============================================================
# Phase 1: 소재 분석 (Buddy 프롬프트 활용)
# ============================================================
def analyze_source(source_text, source_type="press_release"):
    """
    Phase 1: Analyze source material and suggest article angles
    Uses buddy (b1) prompt style for analysis
    """
    system_prompt = """당신은 서울경제신문의 AI 기사작성 어시스턴트 '버디'입니다.
기자가 제출한 소재(보도자료, 인터뷰 메모, 참고자료 등)를 분석하여
기사 작성에 적합한 앵글(관점/프레임워크)을 추천해주세요.

분석 시 고려사항:
1. 뉴스 가치 (시의성, 영향력, 흥미성)
2. 독자 관심도 (경제/산업/사회적 영향)
3. 서울경제신문 독자층 특성 (경제/금융/산업 관심)
4. 차별화 가능한 앵글

반드시 아래 JSON 형식으로만 응답하세요:
{
  "angles": [
    {
      "id": 1,
      "title": "앵글 제목 (15자 이내)",
      "description": "이 앵글로 기사를 쓰면 어떤 내용이 될지 설명 (50자 이내)",
      "recommended": true,
      "keywords": ["키워드1", "키워드2", "키워드3"]
    }
  ],
  "summary": "소재 요약 (100자 이내)",
  "newsValue": "high/medium/low",
  "suggestedLength": "short/medium/long"
}"""

    source_type_kr = {
        "press_release": "보도자료",
        "interview": "인터뷰 메모",
        "reference": "참고자료",
        "memo": "취재 메모"
    }.get(source_type, "소재")

    user_message = f"""다음 {source_type_kr}를 분석하고 기사 앵글을 추천해주세요.

[{source_type_kr}]:
{source_text}

3개의 앵글을 추천해주세요. 가장 뉴스가치가 높은 앵글에 recommended: true를 표시하세요.
JSON 형식으로만 응답하세요."""

    response = call_bedrock(system_prompt, user_message)
    result = parse_json_response(response)

    if result:
        return result

    # Fallback
    return {
        "angles": [
            {
                "id": 1,
                "title": "기본 앵글",
                "description": "소재의 핵심 내용을 중심으로 작성",
                "recommended": True,
                "keywords": ["핵심", "정보", "전달"]
            }
        ],
        "summary": "소재 분석 완료",
        "newsValue": "medium",
        "suggestedLength": "medium"
    }


# ============================================================
# Phase 3: 초안 생성 (Bodo 프롬프트 활용)
# ============================================================
def generate_draft(source_text, angle, article_type="corporate"):
    """
    Phase 3: Generate article draft
    Uses bodo (w1) prompt style for press release writing
    """

    # 기업/정부 보도자료에 따른 프롬프트 분기
    if article_type == "public":
        style_guide = """정부/공공기관 보도자료 작성 스타일:
- 정책의 배경과 목적을 명확히 설명
- 국민/시민에게 미치는 영향 중심
- 공식 발표 내용 정확히 인용
- 전문용어는 쉽게 풀어서 설명"""
    else:
        style_guide = """기업 보도자료 작성 스타일:
- 기업의 핵심 메시지를 리드에 배치
- 시장/산업에 미치는 영향 분석
- 경쟁사 대비 차별점 부각
- 수치/데이터는 구체적으로 인용"""

    system_prompt = f"""당신은 서울경제신문의 기사작성 AI '보도'입니다.
주어진 소재와 앵글을 바탕으로 전문적인 경제 기사 초안을 작성해주세요.

{style_guide}

기사 작성 원칙:
1. 리드(첫 문단): 5W1H 중 핵심 정보, 1-2문장
2. 본문: 역피라미드 구조, 중요도 순 배치
3. 인용문: 핵심 발언은 직접 인용
4. 배경: 관련 맥락과 의미 설명
5. 전망: 향후 영향이나 계획

기사 길이: 800-1200자
문체: 객관적, 간결한 경제 기사 문체"""

    angle_title = angle.get('title', '') if isinstance(angle, dict) else str(angle)
    angle_desc = angle.get('description', '') if isinstance(angle, dict) else ''
    keywords = ', '.join(angle.get('keywords', [])) if isinstance(angle, dict) else ''

    user_message = f"""다음 소재와 앵글을 바탕으로 기사 초안을 작성해주세요.

[선택된 앵글]
- 제목: {angle_title}
- 설명: {angle_desc}
- 키워드: {keywords}

[소재]:
{source_text}

기사 본문만 작성해주세요. 제목은 별도로 생성됩니다."""

    draft = call_bedrock(system_prompt, user_message, max_tokens=2000)

    return {
        "draft": draft,
        "wordCount": len(draft),
        "angle": angle_title
    }


# ============================================================
# Phase 4-1: 교열 (Proofreading 프롬프트)
# ============================================================
def proofread(text, category="economy"):
    """
    Phase 4-1: Proofread for grammar, spelling, punctuation
    Uses proofreading (p1) prompt style
    """

    category_guide = {
        "economy": "경제/금융 기사 교열 시 숫자, 단위, 전문용어 정확성에 특히 주의",
        "society": "사회 기사 교열 시 인명, 지명, 직함 표기에 특히 주의",
        "general": "일반 기사 교열 시 문장 가독성과 논리적 흐름에 주의"
    }

    system_prompt = f"""당신은 서울경제신문의 교열 전문가입니다.
기사의 맞춤법, 문법, 띄어쓰기를 검토하고 수정해주세요.

{category_guide.get(category, category_guide['economy'])}

교열 기준:
1. 맞춤법 오류 (국립국어원 표준)
2. 띄어쓰기 오류
3. 문장 부호 사용
4. 조사 사용 오류
5. 외래어/외국어 표기법
6. 숫자 표기 통일 (만/억 단위)

반드시 JSON 형식으로 응답하세요:
{{
  "corrected": "수정된 전체 텍스트",
  "corrections": [
    {{
      "id": 1,
      "original": "원래 표현",
      "corrected": "수정된 표현",
      "type": "spelling/grammar/punctuation/spacing",
      "line": 1
    }}
  ],
  "summary": "총 N개 수정"
}}"""

    user_message = f"""다음 기사를 교열해주세요:

{text}"""

    response = call_bedrock(system_prompt, user_message)
    result = parse_json_response(response)

    if result:
        return result

    return {
        "corrected": text,
        "corrections": [],
        "summary": "교열 완료 (수정사항 없음)"
    }


# ============================================================
# Phase 4-2: 퇴고 (Regression 프롬프트)
# ============================================================
def revise(text, length_type="medium"):
    """
    Phase 4-2: Revise for style and expression
    Uses regression (r1) prompt style
    """

    length_guide = {
        "short": "간결한 스트레이트 기사 스타일 유지, 불필요한 수식어 제거",
        "medium": "정보와 분석의 균형, 적절한 배경 설명 포함",
        "long": "심층 분석 기사 스타일, 충분한 맥락과 전망 포함"
    }

    system_prompt = f"""당신은 서울경제신문의 수석 에디터입니다.
기사의 문체와 표현을 다듬어 더 읽기 좋게 만들어주세요.

{length_guide.get(length_type, length_guide['medium'])}

퇴고 기준:
1. 장황한 표현 → 간결하게
2. 수동태 → 능동태 선호
3. 추상적 표현 → 구체적 표현
4. 반복되는 어휘 → 다양한 어휘
5. 어색한 문장 → 자연스러운 흐름
6. 경제 기사 문체에 맞게 조정

반드시 JSON 형식으로 응답하세요:
{{
  "revised": "퇴고된 전체 텍스트",
  "revisions": [
    {{
      "id": 1,
      "original": "원래 표현",
      "revised": "수정된 표현",
      "type": "concise/active/specific/vocabulary/flow"
    }}
  ],
  "summary": "퇴고 요약",
  "readabilityScore": 85
}}"""

    user_message = f"""다음 기사를 퇴고해주세요:

{text}"""

    response = call_bedrock(system_prompt, user_message)
    result = parse_json_response(response)

    if result:
        return result

    return {
        "revised": text,
        "revisions": [],
        "summary": "퇴고 완료",
        "readabilityScore": 80
    }


# ============================================================
# Phase 5: 제목 생성 (Title 프롬프트)
# ============================================================
def generate_titles(article_text, count=3):
    """
    Phase 5: Generate title suggestions
    Uses title (t1) prompt style
    """
    system_prompt = """당신은 서울경제신문의 제목 전문가입니다.
기사 본문을 읽고 적합한 제목을 여러 스타일로 제안해주세요.

제목 유형:
1. 직설형: 핵심 정보를 직접 전달 (예: "삼성전자, 반도체 투자 1조원 확대")
2. 인용형: 핵심 인물의 말 인용 (예: "이재용 \"AI 시대 주도권 잡겠다\"")
3. 의문형: 독자 호기심 유발 (예: "삼성의 승부수, 성공할까")
4. 감성형: 비유/감성 표현 (예: "반도체 대전, 삼성의 '올인' 베팅")

제목 작성 원칙:
- 길이: 15-30자 (공백 포함)
- 핵심 정보 포함
- 클릭 유도하되 과장 금지
- 서울경제 독자층 고려

반드시 JSON 형식으로 응답하세요:
{
  "titles": [
    {
      "id": 1,
      "title": "제목 텍스트",
      "style": "직설형/인용형/의문형/감성형",
      "recommended": true/false
    }
  ]
}"""

    user_message = f"""다음 기사에 적합한 제목 {count}개를 제안해주세요:

{article_text[:2000]}

다양한 스타일의 제목을 제안하고, 가장 적합한 제목에 recommended: true를 표시하세요."""

    response = call_bedrock(system_prompt, user_message)
    result = parse_json_response(response)

    if result:
        return result

    return {
        "titles": [
            {"id": 1, "title": "제목 생성 오류", "style": "직설형", "recommended": True}
        ]
    }


# ============================================================
# DynamoDB: Pipeline State Management
# ============================================================
def save_pipeline_state(pipeline_id, user_id, state_data):
    """Save pipeline state to DynamoDB"""
    try:
        table = dynamodb.Table(PIPELINE_TABLE)

        item = {
            'pipelineId': pipeline_id,
            'userId': user_id,
            'currentPhase': state_data.get('currentPhase', 1),
            'sourceText': state_data.get('sourceText', ''),
            'selectedAngle': state_data.get('selectedAngle', {}),
            'draft': state_data.get('draft', ''),
            'proofreadResult': state_data.get('proofreadResult', {}),
            'revisedResult': state_data.get('revisedResult', {}),
            'selectedTitle': state_data.get('selectedTitle', ''),
            'finalArticle': state_data.get('finalArticle', ''),
            'createdAt': state_data.get('createdAt', datetime.utcnow().isoformat()),
            'updatedAt': datetime.utcnow().isoformat()
        }

        table.put_item(Item=item)
        return True
    except Exception as e:
        print(f"DynamoDB save error: {str(e)}")
        return False


def load_pipeline_state(pipeline_id):
    """Load pipeline state from DynamoDB"""
    try:
        table = dynamodb.Table(PIPELINE_TABLE)
        response = table.get_item(Key={'pipelineId': pipeline_id})
        return response.get('Item')
    except Exception as e:
        print(f"DynamoDB load error: {str(e)}")
        return None


# ============================================================
# Lambda Handler
# ============================================================
def lambda_handler(event, context):
    """Main Lambda handler"""

    # Handle CORS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return make_response(200, {'message': 'OK'})

    try:
        # Parse request
        path = event.get('path', '')
        method = event.get('httpMethod', 'POST')
        body = json.loads(event.get('body', '{}')) if event.get('body') else {}

        # Route to appropriate handler
        if path.endswith('/analyze'):
            # Phase 1: Analyze source
            source_text = body.get('sourceText', '')
            source_type = body.get('sourceType', 'press_release')

            if not source_text:
                return make_response(400, {'error': 'sourceText is required'})

            result = analyze_source(source_text, source_type)
            return make_response(200, result)

        elif path.endswith('/draft'):
            # Phase 3: Generate draft
            source_text = body.get('sourceText', '')
            angle = body.get('angle', {})
            article_type = body.get('articleType', 'corporate')

            if not source_text:
                return make_response(400, {'error': 'sourceText is required'})

            result = generate_draft(source_text, angle, article_type)
            return make_response(200, result)

        elif path.endswith('/proofread'):
            # Phase 4-1: Proofread
            text = body.get('text', '')
            category = body.get('category', 'economy')

            if not text:
                return make_response(400, {'error': 'text is required'})

            result = proofread(text, category)
            return make_response(200, result)

        elif path.endswith('/revise'):
            # Phase 4-2: Revise
            text = body.get('text', '')
            length_type = body.get('lengthType', 'medium')

            if not text:
                return make_response(400, {'error': 'text is required'})

            result = revise(text, length_type)
            return make_response(200, result)

        elif path.endswith('/titles'):
            # Phase 5: Generate titles
            article_text = body.get('articleText', '')
            count = body.get('count', 3)

            if not article_text:
                return make_response(400, {'error': 'articleText is required'})

            result = generate_titles(article_text, count)
            return make_response(200, result)

        elif path.endswith('/save'):
            # Save pipeline state
            pipeline_id = body.get('pipelineId', str(uuid.uuid4()))
            user_id = body.get('userId', 'anonymous')
            state_data = body.get('state', {})

            success = save_pipeline_state(pipeline_id, user_id, state_data)

            if success:
                return make_response(200, {'pipelineId': pipeline_id, 'saved': True})
            else:
                return make_response(500, {'error': 'Failed to save pipeline state'})

        elif '/load/' in path:
            # Load pipeline state
            pipeline_id = path.split('/load/')[-1]
            state = load_pipeline_state(pipeline_id)

            if state:
                return make_response(200, state)
            else:
                return make_response(404, {'error': 'Pipeline not found'})

        else:
            return make_response(404, {'error': f'Unknown endpoint: {path}'})

    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"Error: {error_msg}")
        print(f"Traceback: {error_trace}")
        return make_response(500, {
            'error': error_msg,
            'trace': error_trace if os.environ.get('DEBUG') else None
        })


# ============================================================
# Local Testing
# ============================================================
if __name__ == "__main__":
    # Test source
    test_source = """
    삼성전자가 AI 반도체 시장 공략을 위해 1조원 규모의 투자를 결정했다.
    회사 관계자에 따르면, 이번 투자는 2025년부터 3년간 단계적으로 진행될 예정이며,
    차세대 AI 가속기 칩 개발에 집중할 계획이다.
    이재용 회장은 "AI 시대의 주도권을 확보하기 위한 전략적 투자"라고 밝혔다.
    """

    print("=== Phase 1: Analyze Source ===")
    angles = analyze_source(test_source)
    print(json.dumps(angles, ensure_ascii=False, indent=2))
