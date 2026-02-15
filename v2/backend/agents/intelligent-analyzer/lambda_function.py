"""
AI NOVA 지능형 콘텐츠 분석기
Claude Opus 4.5를 사용한 고품질 텍스트 분석

이 Lambda는 단순 키워드 매칭 대신 실제 LLM 추론을 수행합니다.
"""

import json
import boto3
from typing import Dict, Any, Optional

# Bedrock Runtime 클라이언트
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')

# Claude Opus 4.5 모델 ID
MODEL_ID = "us.anthropic.claude-opus-4-5-20251101-v1:0"

# 분석 프롬프트 템플릿
ANALYSIS_PROMPT = """당신은 서울경제신문의 AI 콘텐츠 분석 전문가입니다.

## 분석할 텍스트
<text>
{text}
</text>

## 분석 요청
위 텍스트를 다음 관점에서 심층 분석하세요:

### 1. 언어 분석
- 주요 사용 언어 식별 (korean, english, japanese, mixed)
- 외국어 비율 추정
- 번역 서비스 필요 여부

### 2. 콘텐츠 유형 분석
- 보도자료인지 일반 기사인지 판단
- 보도자료 판단 근거: 배포일시, 담당자 정보, 공식 발표 형식, "보도자료" 명시 등
- 보도자료인 경우 출처 분류: public(공공기관) 또는 corporate(기업)

### 3. 카테고리 분석
- 주제 분야: economy(경제), society(사회), tech(기술), international(국제), general(일반)
- 세부 토픽 식별
- 교열 시 주의사항

### 4. 문체/길이 분석
- 글자 수 추정
- 단문(600자 미만) vs 장문(600자 이상)
- 문체 특성: 뉴스체, 칼럼체, 보고서체 등

### 5. 서비스 라우팅 결정
아래 서비스 중 최적의 처리 경로를 결정하세요:
- f1: 외신 번역 (영어/일본어 텍스트)
- w1: 보도자료 작성 (engineType: 11=기업, 22=공공)
- b1: 기사 작성 (기사버디)
- p1: 교열 (경제/사회 분야)
- r1: 퇴고 (단문/장문)
- t1: 제목 생성

## 응답 형식
반드시 아래 JSON 형식으로만 응답하세요 (다른 텍스트 없이):

```json
{{
  "analysis": {{
    "language": {{
      "primary": "korean|english|japanese|mixed",
      "foreignRatio": 0.0,
      "needsTranslation": false
    }},
    "contentType": {{
      "type": "article|press_release",
      "pressType": "public|corporate|null",
      "indicators": ["발견된 보도자료 지표들"]
    }},
    "category": {{
      "primary": "economy|society|tech|international|general",
      "topics": ["세부 토픽들"],
      "proofreadingFocus": "교열 시 주의점"
    }},
    "style": {{
      "charCount": 0,
      "lengthType": "short|long",
      "tone": "news|column|report"
    }}
  }},
  "routing": {{
    "primary": {{
      "serviceCode": "b1|t1|p1|w1|f1|r1",
      "engineType": "11|22",
      "promptType": "economy|society|public|corporate|english|japanese|short|long"
    }},
    "pipeline": ["b1", "p1", "r1"],
    "confidence": 0.95
  }},
  "reasoning": "이 결정을 내린 상세한 이유"
}}
```"""


def invoke_claude(text: str) -> Dict[str, Any]:
    """Claude Opus 4.5를 호출하여 텍스트 분석"""

    prompt = ANALYSIS_PROMPT.format(text=text)

    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 2048,
        "temperature": 0.1,  # 일관된 분석을 위해 낮은 temperature
        "top_p": 0.9,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    response = bedrock_runtime.invoke_model(
        modelId=MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(request_body)
    )

    response_body = json.loads(response['body'].read())

    # Claude 응답에서 텍스트 추출
    assistant_message = response_body.get('content', [{}])[0].get('text', '')

    # JSON 파싱 시도
    try:
        # ```json ... ``` 블록 추출
        if '```json' in assistant_message:
            json_start = assistant_message.find('```json') + 7
            json_end = assistant_message.find('```', json_start)
            json_str = assistant_message[json_start:json_end].strip()
        elif '{' in assistant_message:
            # 직접 JSON인 경우
            json_start = assistant_message.find('{')
            json_end = assistant_message.rfind('}') + 1
            json_str = assistant_message[json_start:json_end]
        else:
            json_str = assistant_message

        return json.loads(json_str)
    except json.JSONDecodeError as e:
        # 파싱 실패 시 기본값 반환
        return {
            "error": "JSON 파싱 실패",
            "raw_response": assistant_message,
            "routing": {
                "primary": {
                    "serviceCode": "b1",
                    "engineType": "22",
                    "promptType": "general"
                },
                "pipeline": ["b1", "p1", "r1"],
                "confidence": 0.5
            }
        }


def lambda_handler(event, context):
    """
    지능형 콘텐츠 분석 Lambda 핸들러

    Claude Opus 4.5를 사용하여 텍스트를 심층 분석하고
    최적의 서비스 라우팅을 결정합니다.
    """

    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }

    # OPTIONS 요청 처리 (CORS preflight)
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }

    try:
        # 요청 파싱
        body = event.get('body', '{}')
        if isinstance(body, str):
            body = json.loads(body)

        text = body.get('text', '') or body.get('message', '')

        if not text:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'error': 'text 또는 message 파라미터가 필요합니다',
                    'required': ['text', 'message']
                })
            }

        # 텍스트가 너무 짧은 경우 처리
        if len(text.strip()) < 10:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'error': '분석할 텍스트가 너무 짧습니다 (최소 10자)',
                    'charCount': len(text.strip())
                })
            }

        # Claude를 사용한 지능형 분석
        analysis_result = invoke_claude(text)

        # 성공 응답
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'result': analysis_result,
                'model': MODEL_ID,
                'inputLength': len(text)
            }, ensure_ascii=False)
        }

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()

        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': str(e),
                'trace': error_trace
            })
        }


# Bedrock Agent 액션 그룹용 핸들러
def bedrock_agent_handler(event, context):
    """
    Bedrock Agent 액션 그룹에서 호출되는 핸들러
    """

    action_group = event.get('actionGroup', '')
    function = event.get('function', '')
    parameters = event.get('parameters', [])

    # 파라미터에서 text 추출
    text = ''
    for param in parameters:
        if param.get('name') == 'text':
            text = param.get('value', '')
            break

    if not text:
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': action_group,
                'function': function,
                'functionResponse': {
                    'responseBody': {
                        'TEXT': {
                            'body': json.dumps({'error': 'text 파라미터 필요'})
                        }
                    }
                }
            }
        }

    # Claude 분석 수행
    analysis_result = invoke_claude(text)

    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': action_group,
            'function': function,
            'functionResponse': {
                'responseBody': {
                    'TEXT': {
                        'body': json.dumps(analysis_result, ensure_ascii=False)
                    }
                }
            }
        }
    }
