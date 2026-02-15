"""
TTSAgent
TTS 음성 생성 Agent (제미나이 API)
"""

from typing import Dict, Any
import logging

from .base_agent import BaseAgent
from ..tools.gemini_tts import generate_tts

logger = logging.getLogger(__name__)


class TTSAgent(BaseAgent):
    """TTS 생성 Agent"""

    def __init__(self):
        super().__init__(
            name="TTSAgent",
            agent_id="TTS",
            temperature=0.3,
            max_tokens=2048,
        )

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        TTS 음성 생성

        처리:
        1. 기사 텍스트 정제 (읽기용)
        2. 제미나이 TTS API 호출
        3. 음성 파일 URL 반환
        """
        self.log_step("TTS 생성 시작")

        draft = state.get("final_article", state.get("draft", ""))
        if not draft:
            return state

        # 텍스트 정제 (마크다운 제거 등)
        clean_text = self._clean_for_tts(draft)

        # 너무 길면 요약
        if len(clean_text) > 3000:
            system_prompt = "다음 기사를 TTS 낭독용으로 1500자 이내로 요약해주세요. 핵심만 유지하세요."
            messages = self.build_messages(system_prompt, clean_text)
            try:
                clean_text = await self.invoke(messages)
            except:
                clean_text = clean_text[:3000]

        # TTS 생성
        try:
            tts_url = await generate_tts(clean_text)
            state["tts_url"] = tts_url
            state["tts_text"] = clean_text
            self.log_step("TTS 생성 완료")
        except Exception as e:
            logger.error(f"TTS 생성 실패: {e}")
            state["tts_url"] = None

        state["current_step"] = "tts_agent"

        return state

    def _clean_for_tts(self, text: str) -> str:
        """TTS용 텍스트 정제"""
        import re

        # 마크다운 제거
        text = re.sub(r'#+\s*', '', text)  # 헤딩
        text = re.sub(r'\*+', '', text)     # 볼드/이탤릭
        text = re.sub(r'>\s*', '', text)    # 인용
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # 링크

        # 특수문자 정리
        text = text.replace('■', '')
        text = text.replace('●', '')
        text = text.replace('※', '참고로')

        return text.strip()


agent = TTSAgent()

async def run(state: Dict[str, Any]) -> Dict[str, Any]:
    return await agent.run(state)
