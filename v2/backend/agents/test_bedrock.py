"""
Bedrock LLM 연결 테스트
실제 Claude Sonnet 4 호출
"""

import os
import json
import asyncio
import boto3
from datetime import datetime

# 환경 변수
AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2")
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "apac.anthropic.claude-3-5-sonnet-20241022-v2:0")

# Bedrock Runtime 클라이언트
bedrock_runtime = boto3.client("bedrock-runtime", region_name=AWS_REGION)


def test_bedrock_invoke():
    """Bedrock 직접 호출 테스트"""
    print(f"\n{'='*60}")
    print(f"Bedrock LLM 테스트")
    print(f"{'='*60}")
    print(f"Region: {AWS_REGION}")
    print(f"Model: {MODEL_ID}")
    print(f"{'='*60}\n")

    # 테스트 프롬프트 (W1 기사 작성 시뮬레이션)
    system_prompt = """당신은 서울경제신문의 AI 기자입니다.

[기업 보도자료 기사화 시스템 W1 v2.0]

역할: 기업 보도자료를 전문적인 경제 기사로 변환합니다.

핵심 원칙:
1. 팩트 기반 정확한 보도
2. 역피라미드 구조 (핵심 → 세부)
3. 첫 문장에 Who, What, When 포함

출력 형식:
- 제목: 50자 이내
- 본문: 300~500자"""

    user_message = """다음 보도자료를 온라인 기사로 작성해주세요:

삼성전자가 15일 차세대 AI 반도체 'Exynos AI 3000' 개발 계획을 발표했다.
이 반도체는 기존 대비 성능이 3배 향상되고 전력 소모는 40% 감소했다.
삼성전자 반도체 부문 김영한 사장은 "올해 4분기 양산을 목표로 하고 있다"며
"글로벌 AI 반도체 시장 1위를 탈환하겠다"고 밝혔다.
투자 규모는 약 5조원이며, 미국 텍사스 공장에서 생산될 예정이다."""

    # Bedrock API 호출
    try:
        print("📤 Bedrock API 호출 중...")
        start_time = datetime.now()

        response = bedrock_runtime.invoke_model(
            modelId=MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2048,
                "temperature": 0.81,
                "system": system_prompt,
                "messages": [
                    {"role": "user", "content": user_message}
                ]
            })
        )

        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()

        # 응답 파싱
        result = json.loads(response["body"].read())
        content = result["content"][0]["text"]

        print(f"✅ 응답 완료 ({elapsed:.2f}초)")
        print(f"\n{'='*60}")
        print("📰 생성된 기사:")
        print(f"{'='*60}\n")
        print(content)
        print(f"\n{'='*60}")

        # 토큰 사용량
        usage = result.get("usage", {})
        print(f"\n📊 토큰 사용량:")
        print(f"  - Input: {usage.get('input_tokens', 'N/A')}")
        print(f"  - Output: {usage.get('output_tokens', 'N/A')}")

        return True, content

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False, str(e)


def test_title_generation():
    """T1 제목 생성 테스트"""
    print(f"\n{'='*60}")
    print(f"TITLE-NOMICS 3.0 테스트")
    print(f"{'='*60}\n")

    system_prompt = """당신은 TITLE-NOMICS 3.0, 경제 저널리즘의 AI 협업 시스템입니다.

5가지 유형의 제목을 생성해주세요:
1. 저널리즘 충실형 - 정확한 팩트 전달
2. 균형잡힌 후킹형 - 팩트 + 호기심
3. 클릭유도형 - 감정적 임팩트
4. SEO/AEO 최적화형 - 검색 의도 최적화
5. 소셜미디어 공유형 - 확산 최적화

JSON 형식으로 응답:
{"titles": [{"type": "...", "title": "..."}]}"""

    article = """삼성전자, AI 반도체 'Exynos AI 3000' 개발 착수

삼성전자가 15일 차세대 AI 반도체 개발 계획을 발표했다.
성능 3배 향상, 전력 40% 감소가 목표다.
4분기 양산 예정이며 투자 규모는 5조원이다."""

    try:
        print("📤 제목 생성 중...")
        start_time = datetime.now()

        response = bedrock_runtime.invoke_model(
            modelId=MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1024,
                "temperature": 0.85,
                "system": system_prompt,
                "messages": [
                    {"role": "user", "content": f"다음 기사의 제목 5종을 생성해주세요:\n\n{article}"}
                ]
            })
        )

        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()

        result = json.loads(response["body"].read())
        content = result["content"][0]["text"]

        print(f"✅ 완료 ({elapsed:.2f}초)")
        print(f"\n🏷️ 생성된 제목들:")
        print(content)

        return True, content

    except Exception as e:
        print(f"❌ 오류: {e}")
        return False, str(e)


def test_embedding():
    """임베딩 생성 테스트 (Titan)"""
    print(f"\n{'='*60}")
    print(f"Titan Embedding 테스트")
    print(f"{'='*60}\n")

    text = "삼성전자 AI 반도체 개발 투자 5조원"

    try:
        print(f"📤 임베딩 생성 중: '{text}'")

        response = bedrock_runtime.invoke_model(
            modelId="amazon.titan-embed-text-v2:0",
            contentType="application/json",
            accept="application/json",
            body=json.dumps({"inputText": text})
        )

        result = json.loads(response["body"].read())
        embedding = result["embedding"]

        print(f"✅ 완료")
        print(f"  - 차원: {len(embedding)}")
        print(f"  - 샘플: {embedding[:5]}...")

        return True, embedding

    except Exception as e:
        print(f"❌ 오류: {e}")
        return False, str(e)


if __name__ == "__main__":
    print("\n" + "🚀" * 30)
    print("  Bedrock LLM 연결 테스트 시작")
    print("🚀" * 30)

    # 1. 기사 작성 테스트
    success1, _ = test_bedrock_invoke()

    # 2. 제목 생성 테스트
    success2, _ = test_title_generation()

    # 3. 임베딩 테스트
    success3, _ = test_embedding()

    print(f"\n{'='*60}")
    print("📋 테스트 결과 요약")
    print(f"{'='*60}")
    print(f"  1. 기사 작성 (W1): {'✅ 성공' if success1 else '❌ 실패'}")
    print(f"  2. 제목 생성 (T1): {'✅ 성공' if success2 else '❌ 실패'}")
    print(f"  3. 임베딩 생성:    {'✅ 성공' if success3 else '❌ 실패'}")
    print(f"{'='*60}\n")
