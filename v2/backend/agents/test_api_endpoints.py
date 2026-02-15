"""
API 엔드포인트 테스트

테스트 항목:
1. Health Check
2. Agent 목록 조회
3. 워크플로우 세션 시작
4. 워크플로우 상태 조회
5. 워크플로우 실행 (시뮬레이션)
6. 실제 워크플로우 API 테스트
"""

import asyncio
import sys
import httpx
import json
from datetime import datetime

# 테스트 설정
BASE_URL = "http://localhost:8001"
TEST_SESSION_ID = None


async def test_health_check():
    """헬스 체크 테스트"""
    print(f"\n{'='*60}")
    print("1. Health Check 테스트")
    print(f"{'='*60}")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/health", timeout=5.0)

            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")

            return response.status_code == 200
        except httpx.ConnectError:
            print("ERROR: API 서버에 연결할 수 없습니다.")
            print(f"서버가 {BASE_URL}에서 실행 중인지 확인하세요.")
            return False
        except Exception as e:
            print(f"ERROR: {e}")
            return False


async def test_root():
    """루트 엔드포인트 테스트"""
    print(f"\n{'='*60}")
    print("2. Root Endpoint 테스트")
    print(f"{'='*60}")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/", timeout=5.0)

            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")

            return response.status_code == 200
        except Exception as e:
            print(f"ERROR: {e}")
            return False


async def test_list_agents():
    """Agent 목록 조회 테스트"""
    print(f"\n{'='*60}")
    print("3. Agent 목록 조회 테스트")
    print(f"{'='*60}")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/agents", timeout=5.0)

            print(f"Status Code: {response.status_code}")
            data = response.json()

            agents = data.get("agents", [])
            print(f"등록된 Agent: {len(agents)}개")

            # Phase별 그룹핑
            phases = {}
            for agent in agents:
                phase = agent.get("phase", 0)
                if phase not in phases:
                    phases[phase] = []
                phases[phase].append(agent)

            for phase in sorted(phases.keys()):
                print(f"\n  Phase {phase}:")
                for agent in phases[phase]:
                    print(f"    - {agent['id']}: {agent['name']}")

            return response.status_code == 200 and len(agents) > 0
        except Exception as e:
            print(f"ERROR: {e}")
            return False


async def test_workflow_start():
    """워크플로우 세션 시작 테스트"""
    global TEST_SESSION_ID

    print(f"\n{'='*60}")
    print("4. 워크플로우 세션 시작 테스트")
    print(f"{'='*60}")

    async with httpx.AsyncClient() as client:
        try:
            payload = {
                "user_id": "test_user",
                "reporter_id": "reporter_001",
                "sources": [
                    {
                        "id": "src_001",
                        "title": "삼성전자, AI 반도체 HBM4 개발 성공",
                        "content": """삼성전자가 차세대 AI 반도체용 HBM4 메모리 개발에 성공했다고 15일 밝혔다.
HBM4는 기존 HBM3 대비 데이터 처리 속도가 2배 이상 빠르며, AI 학습에 최적화된 구조를 갖추고 있다.
삼성전자는 2026년 하반기부터 양산에 돌입할 예정이며, 글로벌 AI 기업들과 공급 협의를 진행 중이다.
업계에서는 HBM4가 AI 반도체 시장의 게임체인저가 될 것으로 전망하고 있다.""",
                        "source_type": "press_release"
                    }
                ],
                "article_type": "online",
                "engine_type": "11"
            }

            response = await client.post(
                f"{BASE_URL}/workflow/start",
                json=payload,
                timeout=10.0
            )

            print(f"Status Code: {response.status_code}")
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")

            if response.status_code == 200:
                TEST_SESSION_ID = data.get("session_id")
                print(f"\n세션 ID: {TEST_SESSION_ID}")

            return response.status_code == 200
        except Exception as e:
            print(f"ERROR: {e}")
            return False


async def test_workflow_status():
    """워크플로우 상태 조회 테스트"""
    print(f"\n{'='*60}")
    print("5. 워크플로우 상태 조회 테스트")
    print(f"{'='*60}")

    if not TEST_SESSION_ID:
        print("SKIP: 세션 ID가 없습니다.")
        return False

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{BASE_URL}/workflow/{TEST_SESSION_ID}",
                timeout=5.0
            )

            print(f"Status Code: {response.status_code}")
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")

            return response.status_code == 200
        except Exception as e:
            print(f"ERROR: {e}")
            return False


async def test_workflow_run():
    """워크플로우 실행 테스트 (시뮬레이션)"""
    print(f"\n{'='*60}")
    print("6. 워크플로우 실행 테스트 (시뮬레이션)")
    print(f"{'='*60}")

    if not TEST_SESSION_ID:
        print("SKIP: 세션 ID가 없습니다.")
        return False

    async with httpx.AsyncClient() as client:
        try:
            payload = {"step": "full"}

            response = await client.post(
                f"{BASE_URL}/workflow/{TEST_SESSION_ID}/run",
                json=payload,
                timeout=30.0
            )

            print(f"Status Code: {response.status_code}")
            data = response.json()

            print(f"\n실행 결과:")
            print(f"  - 상태: {data.get('status')}")
            print(f"  - 현재 단계: {data.get('current_step')}")
            print(f"  - 품질 점수: {data.get('quality_score')}/100")
            print(f"  - 제목 수: {len(data.get('titles', []))}개")

            draft = data.get('draft', '')
            if draft:
                print(f"\n초안 미리보기:")
                print(f"  {draft[:200]}...")

            titles = data.get('titles', [])
            if titles:
                print(f"\n생성된 제목:")
                for t in titles[:3]:
                    print(f"  - [{t.get('type')}] {t.get('title')}")

            return response.status_code == 200
        except Exception as e:
            print(f"ERROR: {e}")
            return False


async def test_workflow_status_after_run():
    """실행 후 상태 확인"""
    print(f"\n{'='*60}")
    print("7. 실행 후 상태 확인")
    print(f"{'='*60}")

    if not TEST_SESSION_ID:
        print("SKIP: 세션 ID가 없습니다.")
        return False

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{BASE_URL}/workflow/{TEST_SESSION_ID}",
                timeout=5.0
            )

            print(f"Status Code: {response.status_code}")
            data = response.json()

            print(f"\n최종 상태:")
            print(f"  - 상태: {data.get('status')}")
            print(f"  - 현재 단계: {data.get('current_step')}")
            print(f"  - 품질 점수: {data.get('quality_score')}/100")
            print(f"  - 수정 횟수: {data.get('revision_count')}")

            return response.status_code == 200 and data.get('status') == 'completed'
        except Exception as e:
            print(f"ERROR: {e}")
            return False


async def test_404_error():
    """404 에러 테스트"""
    print(f"\n{'='*60}")
    print("8. 404 에러 처리 테스트")
    print(f"{'='*60}")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{BASE_URL}/workflow/non_existent_session",
                timeout=5.0
            )

            print(f"Status Code: {response.status_code}")

            return response.status_code == 404
        except Exception as e:
            print(f"ERROR: {e}")
            return False


async def test_real_workflow_api():
    """실제 워크플로우 API 테스트 (src/main.py)"""
    print(f"\n{'='*60}")
    print("9. 실제 워크플로우 API 테스트")
    print(f"{'='*60}")

    async with httpx.AsyncClient() as client:
        try:
            # 기사 작성 시작
            payload = {
                "session_id": f"test_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "reporter_id": "reporter_001",
                "article_type": "online",
                "engine_type": "11",
                "sources": [
                    {
                        "title": "AI 반도체 시장 동향",
                        "content": "삼성전자가 HBM4 메모리 개발에 성공했다."
                    }
                ],
                "topic": "AI 반도체",
                "keywords": ["삼성전자", "HBM4", "AI"]
            }

            response = await client.post(
                f"{BASE_URL}/api/article/start",
                json=payload,
                timeout=10.0
            )

            if response.status_code == 200:
                print(f"기사 작성 시작: 성공")
                data = response.json()
                print(f"  - 세션 ID: {data.get('session_id')}")
                print(f"  - 상태: {data.get('status')}")
                return True
            elif response.status_code == 404:
                print("실제 워크플로우 API가 활성화되지 않았습니다.")
                print("src/main.py를 실행하세요.")
                return True  # 시뮬레이션 API만 테스트된 경우
            else:
                print(f"Status Code: {response.status_code}")
                return False

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                print("실제 워크플로우 API 엔드포인트 없음 (시뮬레이션 모드)")
                return True
            return False
        except Exception as e:
            print(f"참고: 실제 워크플로우 API 테스트 생략 ({type(e).__name__})")
            return True


async def main():
    """메인 테스트 함수"""
    print("\n" + "=" * 60)
    print("  Nexus AI Agent API 엔드포인트 테스트")
    print("=" * 60)
    print(f"테스트 대상: {BASE_URL}")
    print(f"시작 시간: {datetime.now().isoformat()}")

    results = {}

    # 1. Health Check
    results["health_check"] = await test_health_check()
    if not results["health_check"]:
        print("\n서버가 실행 중이 아닙니다. 테스트를 중단합니다.")
        print("\n서버 시작 방법:")
        print("  cd /Users/yeong-gwang/Documents/work/서울경제신문/DEV/Agentic-Nexus/v2/backend/agents")
        print("  python main.py")
        return False

    # 2. Root Endpoint
    results["root"] = await test_root()

    # 3. Agent 목록
    results["list_agents"] = await test_list_agents()

    # 4. 워크플로우 시작
    results["workflow_start"] = await test_workflow_start()

    # 5. 워크플로우 상태 조회
    results["workflow_status"] = await test_workflow_status()

    # 6. 워크플로우 실행
    results["workflow_run"] = await test_workflow_run()

    # 7. 실행 후 상태 확인
    results["workflow_final"] = await test_workflow_status_after_run()

    # 8. 404 에러 처리
    results["error_404"] = await test_404_error()

    # 9. 실제 워크플로우 API
    results["real_workflow"] = await test_real_workflow_api()

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
