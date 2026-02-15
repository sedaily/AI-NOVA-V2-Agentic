"""
실제 워크플로우 API 테스트 (src/main.py)

테스트 항목:
1. Health Check
2. 기사 작성 시작 (/api/article/start)
3. 워크플로우 실행 (/api/article/run)
4. 기사 상태 조회 (/api/article/{session_id})
"""

import asyncio
import sys
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8001"


async def test_health():
    """Health Check"""
    print(f"\n{'='*60}")
    print("1. Health Check")
    print(f"{'='*60}")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/health", timeout=5.0)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"ERROR: {e}")
            return False


async def test_article_start():
    """기사 작성 시작"""
    print(f"\n{'='*60}")
    print("2. 기사 작성 시작 (/api/article/start)")
    print(f"{'='*60}")

    session_id = f"test_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    async with httpx.AsyncClient() as client:
        try:
            payload = {
                "session_id": session_id,
                "reporter_id": "reporter_001",
                "article_type": "online",
                "engine_type": "11",
                "sources": [
                    {
                        "title": "삼성전자, AI 반도체 HBM4 개발 성공",
                        "content": """삼성전자가 차세대 AI 반도체용 HBM4 메모리 개발에 성공했다고 15일 밝혔다.
HBM4는 기존 HBM3 대비 데이터 처리 속도가 2배 이상 빠르며, AI 학습에 최적화된 구조를 갖추고 있다.
삼성전자는 2026년 하반기부터 양산에 돌입할 예정이다.""",
                        "source": "삼성전자 보도자료"
                    }
                ],
                "topic": "AI 반도체",
                "keywords": ["삼성전자", "HBM4", "AI반도체"]
            }

            response = await client.post(
                f"{BASE_URL}/api/article/start",
                json=payload,
                timeout=10.0
            )

            print(f"Status Code: {response.status_code}")
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")

            if response.status_code == 200:
                return True, session_id
            return False, None

        except Exception as e:
            print(f"ERROR: {e}")
            return False, None


async def test_article_run(session_id: str):
    """워크플로우 실행"""
    print(f"\n{'='*60}")
    print("3. 워크플로우 실행 (/api/article/run)")
    print(f"{'='*60}")

    if not session_id:
        print("SKIP: 세션 ID 없음")
        return False

    async with httpx.AsyncClient() as client:
        try:
            payload = {
                "session_id": session_id,
                "step": "full"
            }

            print(f"세션 ID: {session_id}")
            print("워크플로우 실행 중... (최대 120초)")

            response = await client.post(
                f"{BASE_URL}/api/article/run",
                json=payload,
                timeout=120.0
            )

            print(f"\nStatus Code: {response.status_code}")
            data = response.json()

            if response.status_code == 200:
                print(f"\n실행 결과:")
                print(f"  - 상태: {data.get('status')}")
                print(f"  - 현재 단계: {data.get('current_step')}")
                print(f"  - 품질 점수: {data.get('quality_score')}/100")
                print(f"  - 제목 수: {len(data.get('titles', []))}개")

                draft = data.get('draft', '')
                if draft:
                    print(f"\n기사 미리보기:")
                    print(f"  {draft[:300]}...")

                titles = data.get('titles', [])
                if titles:
                    print(f"\n생성된 제목:")
                    for i, t in enumerate(titles[:3], 1):
                        title_text = t.get('title', t) if isinstance(t, dict) else t
                        print(f"  {i}. {title_text}")

                return True
            else:
                print(f"Response: {data}")
                return False

        except httpx.ReadTimeout:
            print("TIMEOUT: 워크플로우 실행 시간 초과 (120초)")
            return False
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False


async def test_article_status(session_id: str):
    """기사 상태 조회"""
    print(f"\n{'='*60}")
    print("4. 기사 상태 조회 (/api/article/{session_id})")
    print(f"{'='*60}")

    if not session_id:
        print("SKIP: 세션 ID 없음")
        return False

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{BASE_URL}/api/article/{session_id}",
                timeout=10.0
            )

            print(f"Status Code: {response.status_code}")
            data = response.json()

            if response.status_code == 200:
                print(f"\n기사 상태:")
                print(f"  - 세션 ID: {data.get('session_id')}")
                print(f"  - 상태: {data.get('status')}")
                print(f"  - 현재 단계: {data.get('current_step')}")
                print(f"  - 품질 점수: {data.get('quality_score')}/100")

                final_report = data.get('final_report', {})
                if final_report:
                    print(f"\n최종 리포트:")
                    print(f"  - 발행 준비: {'완료' if final_report.get('status', {}).get('is_ready_to_publish') else '미완료'}")
                return True
            else:
                print(f"Response: {data}")
                return False

        except Exception as e:
            print(f"ERROR: {e}")
            return False


async def main():
    """메인 테스트"""
    print("\n" + "=" * 60)
    print("  실제 워크플로우 API 테스트 (src/main.py)")
    print("=" * 60)
    print(f"테스트 대상: {BASE_URL}")
    print(f"시작 시간: {datetime.now().isoformat()}")

    results = {}

    # 1. Health Check
    results["health"] = await test_health()
    if not results["health"]:
        print("\n실제 워크플로우 API 서버가 실행 중이 아닙니다.")
        return False

    # 2. 기사 작성 시작
    success, session_id = await test_article_start()
    results["article_start"] = success

    # 3. 워크플로우 실행
    results["article_run"] = await test_article_run(session_id)

    # 4. 기사 상태 조회
    results["article_status"] = await test_article_status(session_id)

    # 결과 요약
    print(f"\n{'='*60}")
    print("테스트 결과 요약")
    print(f"{'='*60}")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, success in results.items():
        status = "PASS" if success else "FAIL"
        icon = "✓" if success else "✗"
        print(f"  {icon} {test_name}: {status}")

    print(f"\n총 결과: {passed}/{total} 통과")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
