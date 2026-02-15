"""
Aurora pgvector 검색 테스트

테스트 항목:
1. 임베딩 생성 (Titan v2)
2. KB 규칙 검색
3. 스타일북 검색
4. 예시 기사 검색
5. 토큰 절약 효과 측정
"""

import os
import asyncio
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_embedding():
    """Titan 임베딩 생성 테스트"""
    print(f"\n{'='*60}")
    print("1. Titan Embeddings v2 테스트")
    print(f"{'='*60}")

    from src.database.vector_store import VectorStore, EMBEDDING_DIMENSION

    store = VectorStore()
    print(f"임베딩 차원: {EMBEDDING_DIMENSION}")

    test_text = "삼성전자가 차세대 AI 반도체 개발 계획을 발표했다."

    start = datetime.now()
    embedding = await store.get_embedding(test_text)
    elapsed = (datetime.now() - start).total_seconds()

    if embedding:
        print(f"임베딩 생성 성공")
        print(f"  - 차원: {len(embedding)}")
        print(f"  - 소요시간: {elapsed:.3f}초")
        print(f"  - 샘플: [{embedding[0]:.4f}, {embedding[1]:.4f}, ...]")

        # 캐시 테스트
        start = datetime.now()
        embedding2 = await store.get_embedding(test_text)
        elapsed2 = (datetime.now() - start).total_seconds()
        print(f"\n캐시 히트 테스트:")
        print(f"  - 소요시간: {elapsed2:.6f}초 (캐시)")

        return True
    else:
        print("임베딩 생성 실패")
        return False


async def test_cache_stats():
    """캐시 통계 테스트"""
    print(f"\n{'='*60}")
    print("2. 임베딩 캐시 통계")
    print(f"{'='*60}")

    from src.database.vector_store import get_cache_stats, clear_embedding_cache

    stats = get_cache_stats()
    print(f"캐시 크기: {stats['size']}/{stats['max_size']}")

    return True


async def test_kb_search():
    """KB 규칙 검색 테스트"""
    print(f"\n{'='*60}")
    print("3. KB 규칙 검색 테스트")
    print(f"{'='*60}")

    from src.database import search_kb_rules

    query = "삼성전자 반도체 투자 5조원 발표"

    # W1 (기사 작성) 규칙 검색
    print(f"\n쿼리: {query}")
    print(f"\nW1 (기사 작성) 규칙:")

    try:
        rules = await search_kb_rules(
            agent_id="W1",
            query=query,
            top_k=3,
            engine_type="11",  # 기업
        )

        if rules:
            for i, rule in enumerate(rules, 1):
                print(f"  {i}. {rule[:100]}...")
        else:
            print("  (검색 결과 없음 - DB에 데이터가 없을 수 있음)")

        return True

    except Exception as e:
        print(f"검색 실패: {e}")
        return False


async def test_stylebook_search():
    """스타일북 검색 테스트"""
    print(f"\n{'='*60}")
    print("4. 스타일북 검색 테스트")
    print(f"{'='*60}")

    from src.database import search_stylebook

    query = "기업 실적 발표 기사 작성"

    print(f"쿼리: {query}")

    try:
        styles = await search_stylebook(
            query=query,
            top_k=3,
        )

        if styles:
            print(f"\n스타일 규칙:")
            for i, style in enumerate(styles, 1):
                print(f"  {i}. {style[:100]}...")
        else:
            print("  (검색 결과 없음 - DB에 데이터가 없을 수 있음)")

        return True

    except Exception as e:
        print(f"검색 실패: {e}")
        return False


async def test_example_search():
    """예시 기사 검색 테스트"""
    print(f"\n{'='*60}")
    print("5. 예시 기사 검색 테스트")
    print(f"{'='*60}")

    from src.database import search_examples

    query = "기업 실적 발표"

    print(f"쿼리: {query}")

    try:
        examples = await search_examples(
            query=query,
            top_k=2,
            article_type="online",
        )

        if examples:
            print(f"\n예시 기사:")
            for ex in examples:
                print(f"  - ID: {ex.get('article_id')}")
                print(f"    유사도: {ex.get('similarity', 0):.2%}")
                print(f"    내용: {ex.get('content', '')[:80]}...")
        else:
            print("  (검색 결과 없음 - DB에 데이터가 없을 수 있음)")

        return True

    except Exception as e:
        print(f"검색 실패: {e}")
        return False


async def test_token_savings():
    """토큰 절약 효과 측정"""
    print(f"\n{'='*60}")
    print("6. 토큰 절약 효과 측정")
    print(f"{'='*60}")

    # 기존 방식: 전체 프롬프트 로딩 (예상)
    full_prompt_tokens = 15000  # 예상 토큰

    # 새 방식: 관련 규칙만 검색 (예상)
    kb_rules_tokens = 500  # 상위 5개 규칙
    style_tokens = 300  # 상위 3개 스타일
    reporter_tokens = 100  # 기자 스타일

    optimized_tokens = kb_rules_tokens + style_tokens + reporter_tokens

    savings = (1 - optimized_tokens / full_prompt_tokens) * 100

    print(f"기존 방식 (전체 프롬프트): ~{full_prompt_tokens:,} 토큰")
    print(f"최적화 방식 (벡터 검색):")
    print(f"  - KB 규칙 (top 5): ~{kb_rules_tokens} 토큰")
    print(f"  - 스타일북 (top 3): ~{style_tokens} 토큰")
    print(f"  - 기자 스타일: ~{reporter_tokens} 토큰")
    print(f"  - 합계: ~{optimized_tokens} 토큰")
    print(f"\n토큰 절약: {savings:.0f}%")

    return True


async def test_vector_store_singleton():
    """VectorStore 싱글톤 테스트"""
    print(f"\n{'='*60}")
    print("7. VectorStore 싱글톤 테스트")
    print(f"{'='*60}")

    from src.database.vector_store import get_vector_store

    store1 = get_vector_store()
    store2 = get_vector_store()

    is_same = store1 is store2
    print(f"싱글톤 동일성: {is_same}")

    return is_same


async def main():
    """메인 테스트 실행"""
    print("\n" + "=" * 60)
    print("  Aurora pgvector 검색 테스트")
    print("=" * 60)

    results = {}

    # 1. 임베딩 테스트
    results["embedding"] = await test_embedding()

    # 2. 캐시 통계
    results["cache_stats"] = await test_cache_stats()

    # 3. KB 검색 테스트
    results["kb_search"] = await test_kb_search()

    # 4. 스타일북 검색 테스트
    results["stylebook_search"] = await test_stylebook_search()

    # 5. 예시 검색 테스트
    results["example_search"] = await test_example_search()

    # 6. 토큰 절약 측정
    results["token_savings"] = await test_token_savings()

    # 7. 싱글톤 테스트
    results["singleton"] = await test_vector_store_singleton()

    # 결과 요약
    print(f"\n{'='*60}")
    print("테스트 결과 요약")
    print(f"{'='*60}")

    for test_name, success in results.items():
        status = "Pass" if success else "Fail"
        print(f"  {test_name}: {status}")

    print(f"{'='*60}")

    # DB 연결 확인 안내
    print("\n참고:")
    print("  - KB/스타일북 검색은 DB에 데이터가 있어야 결과가 나옵니다.")
    print("  - 데이터 로딩: python scripts/load_kb_data.py")
    print("  - Docker 시작: ./scripts/start-local.sh")
    print()


if __name__ == "__main__":
    asyncio.run(main())
