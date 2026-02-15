"""
Base Agent 클래스
모든 Agent의 공통 기능을 정의합니다.
AWS Bedrock 사용
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging
import os

from langchain_aws import ChatBedrockConverse

# 프롬프트 로더
from ..prompts.prompt_loader import prompt_loader
from ..prompts.prompt_templates import PROMPT_TEMPLATES

logger = logging.getLogger(__name__)

# AWS 설정
AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2")
# APAC Inference Profile 사용 (ap-northeast-2 리전)
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "apac.anthropic.claude-3-5-sonnet-20241022-v2:0")


class BaseAgent(ABC):
    """Agent 기본 클래스"""

    def __init__(
        self,
        name: str,
        agent_id: str,
        model_id: str = "apac.anthropic.claude-3-5-sonnet-20241022-v2:0",
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

    def get_system_prompt(
        self,
        prompt_type: str,
        engine_type: Optional[str] = None,
    ) -> str:
        """
        DynamoDB에서 시스템 프롬프트 로딩

        Args:
            prompt_type: W1, T1, P1, R1 등
            engine_type: 11 (기업) 또는 22 (정부/공공)

        Returns:
            시스템 프롬프트 문자열
        """
        try:
            return prompt_loader.get_system_prompt(prompt_type, engine_type)
        except Exception as e:
            logger.warning(f"프롬프트 로딩 실패, 폴백 사용: {e}")
            # 폴백: 템플릿에서 로딩
            template = PROMPT_TEMPLATES.get(prompt_type, {})
            if engine_type and engine_type in template:
                return template[engine_type].get("instruction", "")
            return template.get("default", {}).get("instruction", "")

    def get_prompt_with_context(
        self,
        prompt_type: str,
        engine_type: Optional[str] = None,
        kb_context: str = "",
        style_context: str = "",
        reporter_context: str = "",
    ) -> str:
        """
        프롬프트 + KB 컨텍스트 조합

        Args:
            prompt_type: W1, T1, P1, R1 등
            engine_type: 11 또는 22
            kb_context: KB 규칙 컨텍스트
            style_context: 스타일북 컨텍스트
            reporter_context: 기자 스타일 컨텍스트

        Returns:
            최종 시스템 프롬프트
        """
        base_prompt = self.get_system_prompt(prompt_type, engine_type)

        context_parts = []

        if kb_context:
            context_parts.append(f"\n\n[KB 규칙]\n{kb_context}")

        if style_context:
            context_parts.append(f"\n\n[스타일 가이드]\n{style_context}")

        if reporter_context:
            context_parts.append(f"\n\n[기자 스타일]\n{reporter_context}")

        return base_prompt + "".join(context_parts)
