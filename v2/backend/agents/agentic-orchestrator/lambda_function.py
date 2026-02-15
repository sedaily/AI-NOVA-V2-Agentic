"""
AI NOVA Agentic Orchestrator
Claude Opus 4.5 Tool Use 기반 자율적 AI Agent

기자가 "삼성전자 HBM4 기사 써줘"라고 하면
Agent가 알아서 분석 → 초안 작성 → 교열 → 제목 생성까지 자동 수행
"""

import boto3
import json
import uuid
import traceback
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

# AWS 클라이언트
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')

# Claude Opus 4.5 모델
MODEL_ID = "us.anthropic.claude-opus-4-5-20251101-v1:0"

# ============================================================
# TOOL DEFINITIONS (Claude Tool Use 스펙)
# ============================================================

TOOLS = [
    {
        "name": "analyze_content",
        "description": "보도자료나 텍스트를 분석하여 핵심 정보를 추출합니다. 언어, 콘텐츠 유형, 카테고리, 핵심 팩트를 파악합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "분석할 텍스트 (보도자료, 기사 등)"
                }
            },
            "required": ["text"]
        }
    },
    {
        "name": "write_article",
        "description": "분석된 정보를 바탕으로 기사 초안을 작성합니다. 뉴스 기사 형식으로 작성됩니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "기사 작성의 기반이 될 내용"
                },
                "style": {
                    "type": "string",
                    "enum": ["economy", "society", "tech", "politics", "culture"],
                    "description": "기사 스타일/카테고리"
                },
                "length": {
                    "type": "string",
                    "enum": ["short", "medium", "long"],
                    "description": "기사 길이 (short: 300자, medium: 500자, long: 800자)"
                }
            },
            "required": ["content"]
        }
    },
    {
        "name": "generate_titles",
        "description": "기사 내용을 바탕으로 클릭을 유도하는 제목 5개를 생성합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "article": {
                    "type": "string",
                    "description": "제목을 생성할 기사 본문"
                },
                "style": {
                    "type": "string",
                    "enum": ["formal", "casual", "breaking", "analysis"],
                    "description": "제목 스타일"
                }
            },
            "required": ["article"]
        }
    },
    {
        "name": "proofread",
        "description": "기사의 맞춤법, 문법, 어색한 표현을 교정합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "교정할 텍스트"
                }
            },
            "required": ["text"]
        }
    },
    {
        "name": "polish_writing",
        "description": "기사의 문장을 더 매끄럽고 읽기 좋게 퇴고합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "퇴고할 텍스트"
                }
            },
            "required": ["text"]
        }
    },
    {
        "name": "translate_foreign",
        "description": "외국어(영어/일본어) 텍스트를 자연스러운 한국어로 번역합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "번역할 외국어 텍스트"
                },
                "source_language": {
                    "type": "string",
                    "enum": ["english", "japanese", "auto"],
                    "description": "원문 언어 (auto: 자동 감지)"
                }
            },
            "required": ["text"]
        }
    },
    {
        "name": "search_related",
        "description": "관련 기사나 배경 정보를 검색합니다. (시뮬레이션)",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "검색할 키워드나 주제"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "fact_check",
        "description": "기사 내용의 팩트체크가 필요한 부분을 표시합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "article": {
                    "type": "string",
                    "description": "팩트체크할 기사"
                }
            },
            "required": ["article"]
        }
    }
]


# ============================================================
# TOOL IMPLEMENTATIONS
# ============================================================

def execute_tool(tool_name: str, tool_input: Dict[str, Any]) -> str:
    """도구 실행"""

    if tool_name == "analyze_content":
        return _analyze_content(tool_input.get("text", ""))

    elif tool_name == "write_article":
        return _write_article(
            tool_input.get("content", ""),
            tool_input.get("style", "economy"),
            tool_input.get("length", "medium")
        )

    elif tool_name == "generate_titles":
        return _generate_titles(
            tool_input.get("article", ""),
            tool_input.get("style", "formal")
        )

    elif tool_name == "proofread":
        return _proofread(tool_input.get("text", ""))

    elif tool_name == "polish_writing":
        return _polish_writing(tool_input.get("text", ""))

    elif tool_name == "translate_foreign":
        return _translate_foreign(
            tool_input.get("text", ""),
            tool_input.get("source_language", "auto")
        )

    elif tool_name == "search_related":
        return _search_related(tool_input.get("query", ""))

    elif tool_name == "fact_check":
        return _fact_check(tool_input.get("article", ""))

    else:
        return f"알 수 없는 도구: {tool_name}"


def _call_claude(system_prompt: str, user_prompt: str, max_tokens: int = 2048) -> str:
    """Claude API 호출 헬퍼"""

    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "temperature": 0.3,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": user_prompt}
        ]
    }

    response = bedrock_runtime.invoke_model(
        modelId=MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(request_body)
    )

    response_body = json.loads(response['body'].read())
    return response_body.get('content', [{}])[0].get('text', '')


def _analyze_content(text: str) -> str:
    """콘텐츠 분석"""

    system = """당신은 뉴스 콘텐츠 분석 전문가입니다.
주어진 텍스트를 분석하여 다음 정보를 JSON 형식으로 추출하세요:
- language: 언어 (korean/english/japanese)
- content_type: 콘텐츠 유형 (press_release/news_article/report/other)
- category: 카테고리 (economy/tech/politics/society/culture)
- key_facts: 핵심 팩트 배열 (최대 5개)
- entities: 언급된 기업/기관/인물
- numbers: 중요 숫자 데이터
- summary: 한 줄 요약"""

    result = _call_claude(system, f"다음 텍스트를 분석하세요:\n\n{text[:3000]}")
    return result


def _write_article(content: str, style: str, length: str) -> str:
    """기사 작성"""

    length_guide = {
        "short": "300자 내외로 간결하게",
        "medium": "500자 내외로",
        "long": "800자 이상 상세하게"
    }

    system = f"""당신은 서울경제신문의 숙련된 기자입니다.
다음 원칙에 따라 {style} 분야 기사를 작성하세요:

1. 역피라미드 구조 (가장 중요한 정보 먼저)
2. 6하원칙 준수 (누가, 언제, 어디서, 무엇을, 어떻게, 왜)
3. 객관적이고 중립적인 톤
4. {length_guide.get(length, '500자 내외로')} 작성
5. 직접 인용문 활용
6. 수치는 정확하게 표기"""

    result = _call_claude(system, f"다음 내용을 바탕으로 뉴스 기사를 작성하세요:\n\n{content}")
    return result


def _generate_titles(article: str, style: str) -> str:
    """제목 생성"""

    style_guide = {
        "formal": "공식적이고 정중한 톤",
        "casual": "친근하고 쉬운 톤",
        "breaking": "긴박하고 속보성 있는 톤",
        "analysis": "분석적이고 심층적인 톤"
    }

    system = f"""당신은 뉴스 헤드라인 전문가입니다.
{style_guide.get(style, '공식적인 톤')}으로 제목 5개를 생성하세요.

제목 작성 원칙:
1. 15자 내외로 간결하게
2. 핵심 키워드 포함
3. 호기심 유발
4. 과장/선정적 표현 금지
5. 숫자, 따옴표 활용

형식:
1. [제목1]
2. [제목2]
3. [제목3]
4. [제목4]
5. [제목5]"""

    result = _call_claude(system, f"다음 기사의 제목 5개를 생성하세요:\n\n{article[:2000]}")
    return result


def _proofread(text: str) -> str:
    """교열"""

    system = """당신은 한국어 교열 전문가입니다.
다음 항목을 검토하고 수정하세요:
1. 맞춤법 오류
2. 띄어쓰기 오류
3. 문법 오류
4. 어색한 표현
5. 중복 표현

수정된 텍스트와 함께 주요 수정 사항을 설명해주세요."""

    result = _call_claude(system, f"다음 텍스트를 교열하세요:\n\n{text}")
    return result


def _polish_writing(text: str) -> str:
    """퇴고"""

    system = """당신은 문장 다듬기 전문가입니다.
문장의 의미는 유지하면서 더 읽기 좋게 다듬으세요:
1. 긴 문장 분리
2. 능동태로 전환
3. 불필요한 수식어 제거
4. 전문 용어 쉽게 풀기
5. 문장 간 연결 자연스럽게"""

    result = _call_claude(system, f"다음 텍스트를 퇴고하세요:\n\n{text}")
    return result


def _translate_foreign(text: str, source_language: str) -> str:
    """외국어 번역"""

    system = """당신은 뉴스 전문 번역가입니다.
외국어 뉴스를 자연스러운 한국어 기사로 번역하세요:
1. 기계 번역 느낌 제거
2. 한국 독자에게 맞는 맥락 추가
3. 고유명사 한국어 표기
4. 문화적 차이 설명
5. 뉴스 기사 형식 유지"""

    result = _call_claude(system, f"다음 {source_language} 텍스트를 한국어로 번역하세요:\n\n{text}")
    return result


def _search_related(query: str) -> str:
    """관련 정보 검색 (시뮬레이션)"""

    # 실제로는 외부 검색 API 호출
    return f"""[관련 정보 검색 결과 - '{query}']

⚠️ 시뮬레이션 데이터입니다. 실제 서비스에서는 웹 검색 API 연동 필요.

관련 기사:
1. [경제] {query} 관련 최신 동향 분석 - 2024.01.15
2. [산업] {query} 시장 전망 리포트 - 2024.01.10
3. [기업] {query} 관련 기업 실적 발표 - 2024.01.08

배경 정보:
- 해당 주제의 최근 3개월 기사 수: 127건
- 주요 관련 키워드: 반도체, AI, 투자, 실적
- 관련 기업: 삼성전자, SK하이닉스, NVIDIA"""


def _fact_check(article: str) -> str:
    """팩트체크"""

    system = """당신은 팩트체크 전문가입니다.
기사에서 확인이 필요한 팩트를 찾아 표시하세요:
1. 수치/통계 데이터
2. 인용문
3. 날짜/시간
4. 고유명사
5. 역사적 사실

각 항목에 대해 [확인 필요] 태그와 확인 방법을 제안하세요."""

    result = _call_claude(system, f"다음 기사를 팩트체크하세요:\n\n{article}")
    return result


# ============================================================
# AGENT ORCHESTRATOR
# ============================================================

def run_agent(user_request: str, max_iterations: int = 10) -> Dict[str, Any]:
    """
    Agentic AI 메인 실행 함수
    Claude가 스스로 도구를 선택하고 실행하면서 목표를 달성
    """

    execution_log = []
    final_result = None

    # 시스템 프롬프트
    system_prompt = """당신은 AI NOVA, 서울경제신문의 AI 기자 어시스턴트입니다.

당신의 목표는 사용자의 요청을 완전히 수행하는 것입니다.
사용 가능한 도구들을 활용하여 자율적으로 작업을 수행하세요.

## 작업 흐름 예시

### 기사 작성 요청 시:
1. analyze_content: 입력 텍스트 분석
2. write_article: 기사 초안 작성
3. proofread: 교열
4. polish_writing: 퇴고
5. generate_titles: 제목 생성
6. fact_check: 팩트체크 포인트 표시

### 번역 요청 시:
1. translate_foreign: 번역
2. proofread: 교열
3. polish_writing: 퇴고

### 제목만 요청 시:
1. analyze_content: 기사 분석
2. generate_titles: 제목 생성

작업이 완료되면 최종 결과를 사용자에게 전달하세요.
중간 과정도 간략히 설명해주세요."""

    messages = [
        {"role": "user", "content": user_request}
    ]

    for iteration in range(max_iterations):
        print(f"🔄 Iteration {iteration + 1}")

        # Claude 호출 (with tools)
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "temperature": 0.3,
            "system": system_prompt,
            "tools": TOOLS,
            "messages": messages
        }

        response = bedrock_runtime.invoke_model(
            modelId=MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(request_body)
        )

        response_body = json.loads(response['body'].read())
        stop_reason = response_body.get('stop_reason')
        content_blocks = response_body.get('content', [])

        # 응답 처리
        tool_use_blocks = []
        text_blocks = []

        for block in content_blocks:
            if block.get('type') == 'tool_use':
                tool_use_blocks.append(block)
            elif block.get('type') == 'text':
                text_blocks.append(block.get('text', ''))

        # 텍스트 응답 로깅
        if text_blocks:
            execution_log.append({
                "type": "thinking",
                "content": "\n".join(text_blocks)
            })

        # 종료 조건: tool_use가 없으면 완료
        if stop_reason == 'end_turn' or not tool_use_blocks:
            final_result = "\n".join(text_blocks)
            break

        # Tool 실행
        messages.append({"role": "assistant", "content": content_blocks})

        tool_results = []
        for tool_block in tool_use_blocks:
            tool_name = tool_block.get('name')
            tool_input = tool_block.get('input', {})
            tool_id = tool_block.get('id')

            print(f"  🔧 Tool: {tool_name}")
            execution_log.append({
                "type": "tool_call",
                "tool": tool_name,
                "input": tool_input
            })

            # 도구 실행
            result = execute_tool(tool_name, tool_input)

            execution_log.append({
                "type": "tool_result",
                "tool": tool_name,
                "result": result[:500] + "..." if len(result) > 500 else result
            })

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_id,
                "content": result
            })

        messages.append({"role": "user", "content": tool_results})

    return {
        "success": True,
        "result": final_result,
        "execution_log": execution_log,
        "iterations": iteration + 1
    }


# ============================================================
# LAMBDA HANDLER
# ============================================================

def lambda_handler(event, context):
    """
    Agentic AI Lambda 핸들러

    요청 형식:
    {
        "message": "삼성전자 HBM4 보도자료로 IT면 기사 써줘",
        "context": "optional context"
    }
    """

    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
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

        print(f"📥 Agentic Request: {user_message[:100]}...")

        # Agent 실행
        result = run_agent(user_message)

        response_data = {
            'success': True,
            'sessionId': session_id,
            'agentResult': result.get('result'),
            'executionLog': result.get('execution_log'),
            'iterations': result.get('iterations'),
            'model': MODEL_ID,
            'mode': 'agentic'
        }

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(response_data, ensure_ascii=False)
        }

    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"❌ Error: {str(e)}")
        print(f"📋 Trace: {error_trace}")

        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': str(e),
                'trace': error_trace
            })
        }
