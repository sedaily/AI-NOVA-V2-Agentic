"""
Base Agent 클래스
모든 Agent의 공통 기능을 정의합니다.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging

from langchain_aws import ChatBedrockConverse
from ..database.aurora import search_kb_rules, search_stylebook, search_examples
from ..memory.agentcore import get_reporter_style

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Agent 기본 클래스"""

    def __init__(
        self,
        name: str,
        agent_id: str,
        model_id: str = "anthropic.claude-sonnet-4-20250514",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        self.name = name
        self.agent_id = agent_id
        self.model_id = model_id
        self.temperature = temperature
        self.max_tokens = max_tokens

        # LLM 초기화
        self.llm = ChatBedrockConverse(
            model=model_id,
            region_name="ap-northeast-2",
            temperature=temperature,
            max_tokens=max_tokens,
        )

    @abstractmethod
    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Agent 실행 (서브클래스에서 구현)"""
        pass

    async def get_kb_context(self, query: str, top_k: int = 5) -> str:
        """KB 규칙 검색"""
        try:
            rules = await search_kb_rules(self.agent_id, query, top_k)
            return "\n".join(rules) if rules else ""
        except Exception as e:
            logger.error(f"KB 검색 실패: {e}")
            return ""

    async def get_style_context(self, query: str, top_k: int = 3) -> str:
        """스타일북 검색"""
        try:
            styles = await search_stylebook(query, top_k)
            return "\n".join(styles) if styles else ""
        except Exception as e:
            logger.error(f"스타일북 검색 실패: {e}")
            return ""

    async def get_examples(self, query: str, top_k: int = 3) -> List[Dict]:
        """Few-shot 예시 검색"""
        try:
            return await search_examples(query, top_k)
        except Exception as e:
            logger.error(f"예시 검색 실패: {e}")
            return []

    async def get_reporter_context(self, reporter_id: str) -> str:
        """기자 스타일 조회"""
        try:
            return await get_reporter_style(reporter_id)
        except Exception as e:
            logger.error(f"기자 스타일 조회 실패: {e}")
            return ""

    def build_messages(
        self,
        system_prompt: str,
        user_message: str,
        history: Optional[List[Dict]] = None,
    ) -> List[Dict]:
        """메시지 구성"""
        messages = [{"role": "system", "content": system_prompt}]

        if history:
            messages.extend(history)

        messages.append({"role": "user", "content": user_message})

        return messages

    async def invoke(self, messages: List[Dict]) -> str:
        """LLM 호출"""
        try:
            response = await self.llm.ainvoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"LLM 호출 실패: {e}")
            raise

    def log_step(self, step: str, details: Optional[Dict] = None):
        """단계 로깅"""
        logger.info(f"[{self.name}] {step}")
        if details:
            logger.debug(f"[{self.name}] Details: {details}")
