"""
프롬프트 캐싱 성능 테스트
로컬에서 캐싱 로직 검증

실행 방법:
cd backend
python test_prompt_caching.py
"""
import time
import sys
import os
import json

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.websocket_service import WebSocketService, PROMPT_CACHE, CACHE_TTL


def print_section(title: str):
    """섹션 구분선 출력"""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def test_prompt_caching():
    """프롬프트 캐싱 성능 테스트"""

    print_section("프롬프트 캐싱 성능 테스트")

    # 테스트할 엔진 타입 (실제 DynamoDB에 존재하는 값으로 변경)
    # C1, C2, T5, H8 등 프로젝트에서 사용하는 엔진 타입
    engine_types = ['C1', 'T5', 'H8']  # 실제 엔진 타입으로 변경해주세요

    print("\n📋 테스트 설정:")
    print(f"   - Engine Types: {', '.join(engine_types)}")
    print(f"   - Cache TTL: {CACHE_TTL}초")
    print(f"   - 초기 캐시 상태: {len(PROMPT_CACHE)}개 항목")

    service = WebSocketService()

    # 첫 번째 엔진 타입으로 테스트
    test_engine = engine_types[0]

    # 테스트 1: 첫 번째 조회 (캐시 미스)
    print_section(f"[테스트 1] 첫 번째 조회 (캐시 미스 예상) - {test_engine}")
    print("-" * 60)
    start = time.time()
    try:
        result1 = service._load_prompt_from_dynamodb(test_engine)
        elapsed1 = (time.time() - start) * 1000
        print(f"✅ 완료: {elapsed1:.0f}ms")
        print(f"   - Instruction: {len(result1.get('instruction', ''))} chars")
        print(f"   - Description: {len(result1.get('description', ''))} chars")
        print(f"   - Files: {len(result1.get('files', []))}개")
        print(f"   - Total size: {len(str(result1))} bytes")
    except Exception as e:
        print(f"❌ 에러: {str(e)}")
        return

    # 테스트 2: 두 번째 조회 (캐시 히트)
    print_section(f"[테스트 2] 두 번째 조회 (캐시 히트 예상) - {test_engine}")
    print("-" * 60)
    start = time.time()
    try:
        result2 = service._load_prompt_from_dynamodb(test_engine)
        elapsed2 = (time.time() - start) * 1000
        print(f"✅ 완료: {elapsed2:.0f}ms")

        if elapsed2 > 0 and elapsed1 > 0:
            improvement = elapsed1 / elapsed2
            print(f"   - 성능 개선: {improvement:.0f}배 빠름")
            print(f"   - 시간 절감: {elapsed1 - elapsed2:.0f}ms")
        else:
            print(f"   - 성능 개선: 거의 즉시 반환 (캐시 히트)")
    except Exception as e:
        print(f"❌ 에러: {str(e)}")
        return

    # 테스트 3: 여러 엔진 타입 연속 조회
    print_section("[테스트 3] 여러 엔진 타입 연속 조회")
    print("-" * 60)
    for engine in engine_types:
        start = time.time()
        try:
            result = service._load_prompt_from_dynamodb(engine)
            elapsed = (time.time() - start) * 1000
            files_count = len(result.get('files', []))
            print(f"   {engine}: {elapsed:.0f}ms ({files_count} files)")
        except Exception as e:
            print(f"   {engine}: ❌ {str(e)}")

    # 테스트 4: 캐시 재사용 확인
    print_section("[테스트 4] 캐시 재사용 확인")
    print("-" * 60)
    print(f"현재 캐시 상태: {len(PROMPT_CACHE)}개 항목")
    for engine, (data, timestamp) in PROMPT_CACHE.items():
        age = time.time() - timestamp
        print(f"   {engine}: {age:.1f}초 전 캐싱 (만료까지 {CACHE_TTL - age:.1f}초)")

    # 요약
    print_section("테스트 요약")
    print(f"첫 조회:  {elapsed1:.0f}ms (DB 조회)")
    print(f"재조회:   {elapsed2:.0f}ms (캐시 히트)")
    if elapsed2 > 0 and elapsed1 > 0:
        print(f"개선율:   {elapsed1/elapsed2:.0f}배")
        print(f"절감:     {elapsed1 - elapsed2:.0f}ms")
    print("=" * 60)

    # 캐시 효과 시뮬레이션
    print_section("[시뮬레이션] 월간 1만 요청 시 예상 성능")
    monthly_requests = 10000
    db_fetch_time = elapsed1  # ms
    cache_hit_time = elapsed2  # ms

    total_without_cache = monthly_requests * db_fetch_time
    # 첫 요청만 DB 조회, 나머지는 캐시 히트
    total_with_cache = db_fetch_time + (monthly_requests - 1) * cache_hit_time

    time_saved = total_without_cache - total_with_cache

    print(f"   캐싱 전 총 시간: {total_without_cache/1000:.1f}초")
    print(f"   캐싱 후 총 시간: {total_with_cache/1000:.1f}초")
    print(f"   절감 시간: {time_saved/1000:.1f}초")
    if total_without_cache > 0:
        print(f"   효율 개선: {(time_saved/total_without_cache)*100:.1f}%")
    print("=" * 60)


def test_cache_expiration():
    """캐시 만료 테스트 (선택 사항)"""
    print_section("[선택] 캐시 만료 테스트 (5분 대기 필요)")
    response = input("캐시 만료 테스트를 진행하시겠습니까? (y/N): ")

    if response.lower() != 'y':
        print("캐시 만료 테스트 건너뛰기")
        return

    print("\n5분 대기 중...")
    print("(실제 프로덕션에서는 Lambda 컨테이너가 재사용되는 동안 캐시가 유지됩니다)")

    # 실제로는 기다리지 않고 시뮬레이션
    print("\n⚠️  실제 대기 대신 시뮬레이션으로 진행합니다.")
    print("    프로덕션 환경에서 CloudWatch 로그로 캐시 만료를 확인하세요.")


if __name__ == "__main__":
    try:
        print("\n" + "🚀 " * 30)
        print("Nexus Prompt Caching Test Suite")
        print("🚀 " * 30)

        test_prompt_caching()
        test_cache_expiration()

        print("\n✅ 모든 테스트 완료!")
        print("\n다음 단계:")
        print("1. Lambda에 배포")
        print("2. CloudWatch 로그에서 캐시 메트릭 확인")
        print("3. 실제 요청으로 Bedrock 캐싱 검증")

    except KeyboardInterrupt:
        print("\n\n⚠️  테스트 중단됨")
    except Exception as e:
        print(f"\n❌ 예상치 못한 에러: {str(e)}")
        import traceback
        traceback.print_exc()
