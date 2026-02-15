"""
AI NOVA API Gateway Lambda v2
Claude Opus 4.5 기반 고품질 Agent 시스템

기존 키워드 매칭 방식 → 실제 LLM 추론 방식으로 업그레이드
"""

import boto3
import json
import uuid
import traceback
from typing import Dict, Any, Optional

# AWS 클라이언트
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
lambda_client = boto3.client('lambda', region_name='us-east-1')

# Claude Opus 4.5 모델
MODEL_ID = "us.anthropic.claude-opus-4-5-20251101-v1:0"

# 서비스 Lambda 매핑
SERVICE_LAMBDAS = {
    'b1': 'buddy-handler',
    't1': 'title-handler',
    'p1': 'proofreading-handler',
    'w1': 'bodo-handler',
    'f1': 'foreign-handler',
    'r1': 'regression-handler'
}

# 고품질 분석 프롬프트
INTELLIGENT_ANALYSIS_PROMPT = """당신은 서울경제신문 AI NOVA 시스템의 핵심 분석 엔진입니다.

## 분석 대상 텍스트
<input>
{text}
</input>

## 분석 및 라우팅 결정

위 텍스트를 분석하여 최적의 AI 서비스를 결정하세요.

### 서비스 옵션
| 코드 | 서비스 | 용도 |
|------|--------|------|
| f1 | 외신 번역 | 영어/일본어 텍스트 번역 |
| w1 | 보도자료 | 보도자료 기반 기사 작성 |
| b1 | 기사버디 | 일반 기사 작성 |
| t1 | 제목생성 | 기사 제목 생성 |
| p1 | 교열 | 문법/맞춤법 교정 |
| r1 | 퇴고 | 문장 다듬기 |

### 분석 포인트
1. **언어**: 한국어가 아니면 f1
2. **보도자료 여부**: "보도자료", "배포일시", "담당자" 등 키워드 + 공식 발표 형식
3. **사용자 의도**:
   - "제목" 언급 → t1
   - "교정", "맞춤법" → p1
   - "퇴고", "다듬어" → r1
   - 기사 작성 요청 → b1

### 응답 형식 (JSON만)
```json
{{
  "serviceCode": "b1|t1|p1|w1|f1|r1",
  "engineType": "11|22",
  "promptType": "economy|society|public|corporate|english|japanese|short|long",
  "pipeline": ["b1", "p1", "r1"],
  "confidence": 0.95,
  "reasoning": "이 서비스를 선택한 이유"
}}
```

JSON만 출력하세요. 다른 설명은 불필요합니다."""


def analyze_with_claude(text: str) -> Dict[str, Any]:
    """Claude Opus 4.5로 텍스트 분석 및 서비스 결정"""

    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "temperature": 0.1,
        "messages": [
            {
                "role": "user",
                "content": INTELLIGENT_ANALYSIS_PROMPT.format(text=text[:3000])  # 토큰 제한
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
    assistant_message = response_body.get('content', [{}])[0].get('text', '')

    # JSON 추출
    try:
        if '```json' in assistant_message:
            json_start = assistant_message.find('```json') + 7
            json_end = assistant_message.find('```', json_start)
            json_str = assistant_message[json_start:json_end].strip()
        elif '{' in assistant_message:
            json_start = assistant_message.find('{')
            json_end = assistant_message.rfind('}') + 1
            json_str = assistant_message[json_start:json_end]
        else:
            raise ValueError("No JSON found")

        return json.loads(json_str)

    except (json.JSONDecodeError, ValueError):
        # 폴백: 기본값
        return {
            "serviceCode": "b1",
            "engineType": "22",
            "promptType": "general",
            "pipeline": ["b1", "p1", "r1"],
            "confidence": 0.5,
            "reasoning": "JSON 파싱 실패로 기본값 사용"
        }


def call_service_lambda(service_code: str, message: str, routing_info: Dict) -> Optional[Dict]:
    """서비스 Lambda 호출"""

    lambda_name = SERVICE_LAMBDAS.get(service_code)
    if not lambda_name:
        return None

    try:
        payload = {
            'message': message,
            'serviceCode': service_code,
            'engineType': routing_info.get('engineType', '22'),
            'promptType': routing_info.get('promptType', 'general'),
            'userId': 'agent-system'
        }

        response = lambda_client.invoke(
            FunctionName=lambda_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )

        result = json.loads(response['Payload'].read())
        return result.get('body', result)

    except Exception as e:
        print(f"Service call error ({service_code}): {str(e)}")
        return None


def lambda_handler(event, context):
    """
    API Gateway Lambda 핸들러 v2

    1. Claude Opus 4.5로 텍스트 분석
    2. 최적 서비스 결정
    3. 해당 서비스 Lambda 호출
    4. 결과 반환
    """

    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }

    # CORS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': headers, 'body': ''}

    try:
        # 요청 파싱
        body = json.loads(event.get('body', '{}'))
        user_message = body.get('message', '') or body.get('text', '')
        session_id = body.get('sessionId', str(uuid.uuid4()))

        if not user_message:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'message is required'})
            }

        print(f"📥 입력: {user_message[:100]}...")

        # Step 1: Claude로 지능형 분석
        print("🧠 Claude Opus 4.5 분석 시작...")
        routing_info = analyze_with_claude(user_message)
        print(f"📊 분석 결과: {json.dumps(routing_info, ensure_ascii=False)}")

        service_code = routing_info.get('serviceCode', 'b1')
        confidence = routing_info.get('confidence', 0.5)

        # Step 2: 서비스 Lambda 호출
        print(f"🚀 서비스 호출: {service_code} (confidence: {confidence})")
        service_result = call_service_lambda(service_code, user_message, routing_info)

        # Step 3: 응답 구성
        response_data = {
            'success': True,
            'sessionId': session_id,
            'analysis': {
                'serviceCode': service_code,
                'engineType': routing_info.get('engineType'),
                'promptType': routing_info.get('promptType'),
                'confidence': confidence,
                'reasoning': routing_info.get('reasoning', '')
            },
            'pipeline': routing_info.get('pipeline', [service_code]),
            'model': MODEL_ID
        }

        if service_result:
            response_data['serviceResult'] = service_result
            response_data['message'] = f"✅ {service_code} 서비스 처리 완료"
        else:
            response_data['message'] = f"⚠️ {service_code} 서비스 응답 대기 중"

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(response_data, ensure_ascii=False)
        }

    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"❌ 오류: {str(e)}")
        print(f"📋 트레이스: {error_trace}")

        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': str(e),
                'trace': error_trace
            })
        }
