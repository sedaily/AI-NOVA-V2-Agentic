"""
KB 규칙 및 스타일북 데이터 로딩 스크립트
Aurora PostgreSQL (pgvector)에 초기 데이터 삽입
"""

import os
import json
import asyncio
import asyncpg
from typing import List, Dict, Any
import logging

# Bedrock for embeddings
import boto3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 환경 변수
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://nexus_user:nexus_dev_password@localhost:5432/nexus_kb"
)
AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2")

# Bedrock Embeddings (Titan)
bedrock_runtime = boto3.client("bedrock-runtime", region_name=AWS_REGION)


async def get_embedding(text: str) -> List[float]:
    """Bedrock Titan으로 임베딩 생성"""
    try:
        response = bedrock_runtime.invoke_model(
            modelId="amazon.titan-embed-text-v2:0",
            body=json.dumps({"inputText": text[:8000]}),
            contentType="application/json",
            accept="application/json"
        )
        result = json.loads(response["body"].read())
        return result["embedding"]
    except Exception as e:
        logger.error(f"임베딩 생성 실패: {e}")
        # 1536차원 제로 벡터 반환 (폴백)
        return [0.0] * 1536


# ====================================================
# KB 규칙 초기 데이터
# ====================================================
KB_RULES_DATA = [
    # W1 - 기사 작성 규칙
    {
        "agent_id": "W1",
        "rule_type": "structure",
        "title": "역피라미드 구조",
        "content": "기사는 역피라미드 구조로 작성합니다. 첫 문단에 핵심 내용(5W1H)을 배치하고, 중요도 순으로 내용을 전개합니다. 독자가 첫 문단만 읽어도 기사의 핵심을 파악할 수 있어야 합니다.",
        "priority": 10
    },
    {
        "agent_id": "W1",
        "rule_type": "style",
        "title": "첫 문장 규칙",
        "content": "기사의 첫 문장은 50자 이내로 작성합니다. Who(누가), What(무엇을), When(언제)을 반드시 포함해야 합니다. 예: '삼성전자가 15일 차세대 반도체 공장 건설 계획을 발표했다.'",
        "priority": 9
    },
    {
        "agent_id": "W1",
        "rule_type": "policy",
        "title": "정치 중립성 원칙",
        "content": "정부/공공 보도자료(Engine 22) 기사화 시 정치적 중립을 엄격히 유지합니다. 대통령, 장관, 국회의원 등 정치인 실명을 사용하지 않습니다. '정부', '당국', '관계자' 등 중립적 표현을 사용합니다.",
        "priority": 10
    },
    {
        "agent_id": "W1",
        "rule_type": "term",
        "title": "경제 전문용어 사용",
        "content": "경제/금융 전문용어는 정확하게 사용합니다. 일반 독자를 위해 필요시 괄호 안에 간단한 설명을 추가합니다. 예: 'PER(주가수익비율)이 15배를 넘어섰다.'",
        "priority": 7
    },

    # T1 - 제목 생성 규칙
    {
        "agent_id": "T1",
        "rule_type": "format",
        "title": "제목 글자 수",
        "content": "온라인 기사 제목은 50자 이내로 작성합니다. 모바일 화면에서 2줄 이내로 표시되어야 합니다. 핵심 키워드는 앞쪽에 배치합니다.",
        "priority": 10
    },
    {
        "agent_id": "T1",
        "rule_type": "style",
        "title": "제목 문체",
        "content": "제목은 현재형으로 작성합니다. 동사형 어미를 선호합니다. 예: '삼성전자, AI 반도체 개발 착수' (O), '삼성전자가 AI 반도체를 개발하기로 했다' (X)",
        "priority": 9
    },
    {
        "agent_id": "T1",
        "rule_type": "seo",
        "title": "SEO 최적화",
        "content": "검색 최적화를 위해 핵심 키워드를 제목 앞부분에 배치합니다. 기업명, 인물명, 숫자 등 구체적 정보를 포함합니다. 질문형 제목도 효과적입니다.",
        "priority": 8
    },

    # P1 - 교정 규칙
    {
        "agent_id": "P1",
        "rule_type": "grammar",
        "title": "주어-서술어 호응",
        "content": "주어와 서술어의 호응을 확인합니다. 복문에서 주어가 생략되어 의미가 모호해지지 않도록 합니다.",
        "priority": 9
    },
    {
        "agent_id": "P1",
        "rule_type": "spelling",
        "title": "띄어쓰기",
        "content": "복합명사의 띄어쓰기를 확인합니다. '주가수익비율'(O), '주가 수익 비율'(X). 단위 앞 숫자는 붙여 씁니다. '100억원'(O), '100억 원'(X)",
        "priority": 8
    },
    {
        "agent_id": "P1",
        "rule_type": "format",
        "title": "숫자 표기",
        "content": "만 단위 이상의 숫자는 한글을 혼용합니다. 예: '1억5000만원', '23조4000억원'. 퍼센트는 '%' 기호를 사용합니다.",
        "priority": 8
    },

    # R1 - 퇴고 규칙
    {
        "agent_id": "R1",
        "rule_type": "style",
        "title": "간결한 문장",
        "content": "한 문장은 60자 이내로 작성합니다. 긴 문장은 두 문장으로 분리합니다. 접속사 '그리고', '그래서'의 남용을 피합니다.",
        "priority": 9
    },
    {
        "agent_id": "R1",
        "rule_type": "style",
        "title": "피동 → 능동",
        "content": "피동형 표현을 능동형으로 변환합니다. '~되었다'보다 '~했다'를 선호합니다. 예: '계획이 발표되었다' → '(회사가) 계획을 발표했다'",
        "priority": 8
    },
    {
        "agent_id": "R1",
        "rule_type": "structure",
        "title": "문단 구성",
        "content": "한 문단은 3~4개 문장으로 구성합니다. 문단마다 하나의 핵심 아이디어를 담습니다. 소제목을 활용하여 가독성을 높입니다.",
        "priority": 7
    },
]


# ====================================================
# 스타일북 초기 데이터
# ====================================================
STYLEBOOK_DATA = [
    # 표기법
    {
        "category": "표기법",
        "subcategory": "숫자",
        "rule_name": "금액 표기",
        "description": "만 단위 이상의 금액은 한글을 혼용하여 표기합니다.",
        "correct_example": "1억5000만원, 23조원, 500만달러",
        "incorrect_example": "150,000,000원, 23,000,000,000,000원"
    },
    {
        "category": "표기법",
        "subcategory": "숫자",
        "rule_name": "퍼센트 표기",
        "description": "비율은 '%' 기호를 사용합니다. 소수점 이하는 필요시 1자리까지만 표기합니다.",
        "correct_example": "23.5%, 전년 대비 10% 증가",
        "incorrect_example": "23.456퍼센트, 십퍼센트 증가"
    },
    {
        "category": "표기법",
        "subcategory": "날짜",
        "rule_name": "날짜 표기",
        "description": "날짜는 '일' 단위까지 표기합니다. 연도는 필요시만 표기합니다.",
        "correct_example": "15일, 3월 15일, 2024년 3월 15일",
        "incorrect_example": "03/15, 2024.03.15"
    },

    # 용어
    {
        "category": "용어",
        "subcategory": "경제",
        "rule_name": "주식 관련 용어",
        "description": "주식시장 관련 전문용어는 통일된 표기를 사용합니다.",
        "correct_example": "코스피, 코스닥, PER, PBR, 시가총액",
        "incorrect_example": "KOSPI, kosdaq, P/E ratio"
    },
    {
        "category": "용어",
        "subcategory": "금융",
        "rule_name": "금리 관련 용어",
        "description": "금리 관련 용어는 정확한 명칭을 사용합니다.",
        "correct_example": "기준금리, 대출금리, 예금금리, 시장금리",
        "incorrect_example": "베이스 레이트, 이자율"
    },

    # 문체
    {
        "category": "문체",
        "subcategory": "어미",
        "rule_name": "서술어 어미",
        "description": "기사는 '~다' 어미의 평서문으로 작성합니다.",
        "correct_example": "발표했다, 밝혔다, 전망이다",
        "incorrect_example": "발표했습니다, 밝혔어요"
    },
    {
        "category": "문체",
        "subcategory": "시제",
        "rule_name": "시제 통일",
        "description": "기사 본문은 과거형을 기본으로 하되, 현재 진행 상황은 현재형을 사용합니다.",
        "correct_example": "발표했다 (과거 사건), 추진 중이다 (현재 진행)",
        "incorrect_example": "발표한다 (과거 사건에 현재형 사용)"
    },

    # 인용
    {
        "category": "인용",
        "subcategory": "직접인용",
        "rule_name": "인용문 형식",
        "description": "직접 인용은 큰따옴표를 사용하고, 출처를 명시합니다.",
        "correct_example": '"올해 매출 목표는 100억원"이라고 김 대표는 밝혔다.',
        "incorrect_example": '올해 매출 목표는 100억원이라고 김 대표가 말했다.'
    },
    {
        "category": "인용",
        "subcategory": "간접인용",
        "rule_name": "간접인용 표현",
        "description": "간접 인용 시 '~라고 했다', '~라고 밝혔다' 형태를 사용합니다.",
        "correct_example": "김 대표는 올해 매출 목표가 100억원이라고 밝혔다.",
        "incorrect_example": "김 대표는 올해 매출 목표가 100억원이라고."
    },
]


# ====================================================
# Few-shot 예시 데이터
# ====================================================
EXAMPLES_DATA = [
    # P1 교정 예시
    {
        "agent_id": "P1",
        "example_type": "correction",
        "wrong_text": "삼성전자가 새로운 반도체 개발에 착수 했다.",
        "correct_text": "삼성전자가 새로운 반도체 개발에 착수했다.",
        "explanation": "동사와 보조동사 사이 띄어쓰기 오류. '착수하다'는 한 단어입니다."
    },
    {
        "agent_id": "P1",
        "example_type": "correction",
        "wrong_text": "주가가 10% 상승 되었다.",
        "correct_text": "주가가 10% 상승했다.",
        "explanation": "불필요한 피동 표현. '상승되다' → '상승하다'로 능동형 변환."
    },
    {
        "agent_id": "P1",
        "example_type": "correction",
        "wrong_text": "150,000,000원의 투자를 유치했다.",
        "correct_text": "1억5000만원의 투자를 유치했다.",
        "explanation": "금액 표기 규칙. 만 단위 이상은 한글 혼용."
    },

    # T1 제목 예시
    {
        "agent_id": "T1",
        "example_type": "title",
        "wrong_text": "삼성전자가 새로운 AI 반도체를 개발하기로 결정했다고 15일 발표",
        "correct_text": "삼성전자, AI 반도체 개발 착수…\"내년 양산\"",
        "explanation": "제목 간결화. 핵심만 추출하고, 인용구로 포인트 추가."
    },

    # W1 작성 예시
    {
        "agent_id": "W1",
        "example_type": "writing",
        "wrong_text": "오늘 삼성전자에서 발표한 내용에 따르면...",
        "correct_text": "삼성전자가 15일 차세대 AI 반도체 개발 계획을 발표했다.",
        "explanation": "첫 문장은 구체적 정보(Who, What, When) 포함."
    },
]


async def load_data():
    """데이터 로딩 실행"""
    logger.info("데이터 로딩 시작...")

    # 데이터베이스 연결
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        # KB 규칙 로딩
        logger.info(f"KB 규칙 {len(KB_RULES_DATA)}건 로딩...")
        for rule in KB_RULES_DATA:
            # 임베딩 생성
            embedding = await get_embedding(f"{rule['title']} {rule['content']}")

            await conn.execute("""
                INSERT INTO kb_rules (agent_id, rule_type, title, content, embedding, priority)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT DO NOTHING
            """, rule["agent_id"], rule["rule_type"], rule["title"],
                rule["content"], embedding, rule["priority"])

        logger.info("KB 규칙 로딩 완료")

        # 스타일북 로딩
        logger.info(f"스타일북 {len(STYLEBOOK_DATA)}건 로딩...")
        for style in STYLEBOOK_DATA:
            # 임베딩 생성
            text = f"{style['category']} {style['rule_name']} {style['description']}"
            embedding = await get_embedding(text)

            await conn.execute("""
                INSERT INTO stylebook
                (category, subcategory, rule_name, description, correct_example, incorrect_example, embedding)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT DO NOTHING
            """, style["category"], style.get("subcategory"), style["rule_name"],
                style["description"], style.get("correct_example"),
                style.get("incorrect_example"), embedding)

        logger.info("스타일북 로딩 완료")

        # 예시 로딩
        logger.info(f"예시 {len(EXAMPLES_DATA)}건 로딩...")
        for ex in EXAMPLES_DATA:
            # 임베딩 생성 (잘못된 예시 기준)
            embedding = await get_embedding(ex.get("wrong_text", ex["correct_text"]))

            await conn.execute("""
                INSERT INTO examples
                (agent_id, example_type, wrong_text, correct_text, explanation, embedding)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT DO NOTHING
            """, ex["agent_id"], ex["example_type"], ex.get("wrong_text"),
                ex["correct_text"], ex.get("explanation"), embedding)

        logger.info("예시 로딩 완료")

        # 통계 출력
        kb_count = await conn.fetchval("SELECT COUNT(*) FROM kb_rules")
        style_count = await conn.fetchval("SELECT COUNT(*) FROM stylebook")
        example_count = await conn.fetchval("SELECT COUNT(*) FROM examples")

        logger.info(f"""
============================================
데이터 로딩 완료!
============================================
- KB 규칙: {kb_count}건
- 스타일북: {style_count}건
- 예시: {example_count}건
============================================
        """)

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(load_data())
