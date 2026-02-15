"""
ImageAgent
대표 이미지 생성 Agent (나노바나나 API)
"""

from typing import Dict, Any
import logging

from .base_agent import BaseAgent
from ..tools.nanobanana import generate_image

logger = logging.getLogger(__name__)


class ImageAgent(BaseAgent):
    """이미지 생성 Agent"""

    def __init__(self):
        super().__init__(
            name="ImageAgent",
            agent_id="IMAGE",
            temperature=0.7,
            max_tokens=1024,
        )

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        대표 이미지 생성

        처리:
        1. 기사 핵심 내용 분석
        2. 이미지 프롬프트 생성
        3. 나노바나나 API로 이미지 생성
        """
        self.log_step("이미지 생성 시작")

        draft = state.get("final_article", state.get("draft", ""))
        titles = state.get("titles", [])

        if not draft:
            return state

        # 제목이 있으면 사용, 없으면 기사 첫 문장
        title = ""
        if titles and len(titles) > 0:
            title = titles[0].get("title", "")
        else:
            title = draft.split("\n")[0][:50]

        # 이미지 프롬프트 생성
        system_prompt = """기사 내용을 바탕으로 대표 이미지 생성용 프롬프트를 작성해주세요.

규칙:
1. 영문으로 작성
2. 뉴스 기사에 적합한 전문적 이미지
3. 추상적이거나 상징적인 표현 가능
4. 인물 사진은 피할 것

예시: "Professional business concept, Korean economy growth, digital transformation, blue and white corporate colors, clean modern design"

프롬프트만 반환하세요."""

        user_message = f"제목: {title}\n\n기사 내용:\n{draft[:1000]}"

        messages = self.build_messages(system_prompt, user_message)

        try:
            prompt = await self.invoke(messages)
            prompt = prompt.strip().strip('"')

            # 나노바나나 API 호출
            try:
                image_url = await generate_image(prompt)
                state["image_url"] = image_url
                state["image_prompt"] = prompt
                self.log_step("이미지 생성 완료")
            except Exception as e:
                logger.error(f"이미지 API 호출 실패: {e}")
                state["image_url"] = None

        except Exception as e:
            logger.error(f"이미지 프롬프트 생성 실패: {e}")

        state["current_step"] = "image_agent"

        return state


agent = ImageAgent()

async def run(state: Dict[str, Any]) -> Dict[str, Any]:
    return await agent.run(state)
