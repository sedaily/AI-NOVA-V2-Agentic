"""
Base Agent 클래스
모든 Agent의 공통 기능을 정의합니다.
AWS Bedrock + AgentCore Memory + pgvector 통합 + Tools

Tool 통합:
- bind_tools(): LLM에 도구 바인딩
- invoke_with_tools(): 도구 사용 가능한 LLM 호출
- parse_tool_calls(): 응답에서 도구 호출 추출
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable
import logging
import os

from langchain_aws import ChatBedrockConverse
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

# 프롬프트 로더
from ..prompts.prompt_loader import prompt_loader
from ..prompts.prompt_templates import PROMPT_TEMPLATES

# AgentCore Memory
from ..memory import get_memory_manager, AgentCoreMemoryManager

# pgvector 검색 (토큰 절약)
from ..database import search_kb_rules, search_stylebook, search_examples, get_reporter_style

# Tools
from ..tools import get_all_tools, get_research_tools, get_factcheck_tools

logger = logging.getLogger(__name__)

# AWS 설정
AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2")
# APAC Inference Profile 사용 (ap-northeast-2 리전)
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "apac.anthropic.claude-3-5-sonnet-20241022-v2:0")


class BaseAgent(ABC):
    """
    Agent 기본 클래스

    AgentCore Memory 통합:
    - 기자 스타일 학습
    - 세션 컨텍스트 유지
    - 작성 패턴 분석

    Tool 통합:
    - LLM에 도구 바인딩
    - 도구 사용 가능한 호출
    """

    def __init__(
        self,
        name: str,
        agent_id: str,
        model_id: str = "apac.anthropic.claude-3-5-sonnet-20241022-v2:0",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        use_memory: bool = True,
        tools: Optional[List[Callable]] = None,
    ):
        self.name = name
        self.agent_id = agent_id
        self.model_id = model_id
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.use_memory = use_memory

        # LLM 초기화
        self.llm = ChatBedrockConverse(
            model=model_id,
            region_name="ap-northeast-2",
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Tools
        self._tools = tools
        self._llm_with_tools = None

        # Memory Manager (lazy initialization)
        self._memory_manager: Optional[AgentCoreMemoryManager] = None

    @property
    def memory(self) -> AgentCoreMemoryManager:
        """AgentCore Memory Manager 반환"""
        if self._memory_manager is None:
            self._memory_manager = get_memory_manager()
        return self._memory_manager

    @property
    def tools(self) -> List[Callable]:
        """사용 가능한 도구 목록"""
        if self._tools is None:
            # 기본 도구 설정 (Agent 유형별)
            self._tools = self._get_default_tools()
        return self._tools

    @property
    def llm_with_tools(self):
        """도구가 바인딩된 LLM"""
        if self._llm_with_tools is None and self.tools:
            self._llm_with_tools = self.llm.bind_tools(self.tools)
        return self._llm_with_tools if self._llm_with_tools else self.llm

    def _get_default_tools(self) -> List[Callable]:
        """Agent 유형별 기본 도구 반환"""
        # Agent ID에 따라 다른 도구 세트 반환
        if self.agent_id in ["COLLECTOR", "SOURCE_ANALYZER"]:
            return get_research_tools()
        elif self.agent_id in ["FACT_CHECKER", "P1"]:
            return get_factcheck_tools()
        else:
            # 기본적으로 모든 도구 사용 가능
            return get_all_tools()

    def bind_tools(self, tools: List[Callable]) -> None:
        """도구 바인딩"""
        self._tools = tools
        self._llm_with_tools = self.llm.bind_tools(tools)
        logger.info(f"[{self.name}] Bound {len(tools)} tools")

    @abstractmethod
    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Agent 실행 (서브클래스에서 구현)"""
        pass

    async def get_kb_context(
        self,
        query: str,
        top_k: int = 5,
        engine_type: Optional[str] = None,
    ) -> str:
        """
        KB 규칙 검색 (pgvector)

        Args:
            query: 검색 쿼리 (기사 내용 일부)
            top_k: 상위 K개
            engine_type: 엔진 유형 (11: 기업, 22: 정부/공공)

        Returns:
            관련 KB 규칙 텍스트 (줄바꿈 구분)
        """
        try:
            rules = await search_kb_rules(
                agent_id=self.agent_id,
                query=query,
                top_k=top_k,
                engine_type=engine_type,
            )
            return "\n".join(rules) if rules else ""
        except Exception as e:
            logger.error(f"KB 검색 실패: {e}")
            return ""

    async def get_style_context(
        self,
        query: str,
        top_k: int = 3,
        category: Optional[str] = None,
    ) -> str:
        """
        스타일북 검색 (pgvector)

        Args:
            query: 검색 쿼리
            top_k: 상위 K개
            category: 카테고리 필터

        Returns:
            스타일 규칙 텍스트 (줄바꿈 구분)
        """
        try:
            styles = await search_stylebook(
                query=query,
                top_k=top_k,
                category=category,
            )
            return "\n".join(styles) if styles else ""
        except Exception as e:
            logger.error(f"스타일북 검색 실패: {e}")
            return ""

    async def get_examples(
        self,
        query: str,
        top_k: int = 3,
        article_type: Optional[str] = None,
        engine_type: Optional[str] = None,
    ) -> List[Dict]:
        """
        Few-shot 예시 검색 (pgvector)

        Args:
            query: 검색 쿼리
            top_k: 상위 K개
            article_type: 기사 유형 필터
            engine_type: 엔진 유형 필터

        Returns:
            예시 기사 리스트
        """
        try:
            return await search_examples(
                query=query,
                top_k=top_k,
                article_type=article_type,
                engine_type=engine_type,
            )
        except Exception as e:
            logger.error(f"예시 검색 실패: {e}")
            return []

    async def get_reporter_context(self, reporter_id: str) -> str:
        """
        기자 스타일 조회 (AgentCore Memory 통합)

        Args:
            reporter_id: 기자 ID

        Returns:
            기자 스타일 컨텍스트 문자열
        """
        if not reporter_id:
            return ""

        try:
            # AgentCore Memory에서 조회
            if self.use_memory:
                await self.memory.initialize()

                # 스타일 정보
                style = await self.memory.get_reporter_preference(reporter_id, "style")

                # 작성 패턴
                patterns = await self.memory.get_reporter_preference(reporter_id, "writing_patterns")

                if style or patterns:
                    context_parts = []

                    if style:
                        context_parts.append(f"선호 문체: {style.get('style_summary', '')}")
                        if style.get('preferred_tone'):
                            context_parts.append(f"선호 어조: {style.get('preferred_tone')}")

                    if patterns:
                        avg_length = patterns.get('avg_length', 0)
                        if avg_length:
                            context_parts.append(f"평균 기사 길이: {avg_length}자")

                        common_phrases = patterns.get('common_phrases', [])[:5]
                        if common_phrases:
                            context_parts.append(f"자주 사용하는 표현: {', '.join(common_phrases)}")

                    if context_parts:
                        return "\n".join(context_parts)

            # 폴백: 기존 방식
            return await self._get_reporter_style_legacy(reporter_id)

        except Exception as e:
            logger.error(f"기자 스타일 조회 실패: {e}")
            return ""

    async def _get_reporter_style_legacy(self, reporter_id: str) -> str:
        """기자 스타일 조회 (Legacy - DB 기반)"""
        try:
            # DB에서 기자 스타일 조회
            return await get_reporter_style(reporter_id)
        except Exception as e:
            logger.debug(f"Legacy reporter style lookup failed: {e}")
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

    async def invoke_with_tools(
        self,
        messages: List[Dict],
        max_iterations: int = 5,
    ) -> Dict[str, Any]:
        """
        도구 사용 가능한 LLM 호출

        Args:
            messages: 메시지 리스트
            max_iterations: 최대 도구 호출 반복 횟수

        Returns:
            {
                "content": 최종 응답,
                "tool_calls": 실행된 도구 호출 목록,
                "tool_results": 도구 실행 결과,
            }
        """
        from ..graph.tool_node import parse_tool_calls_from_response

        if not self.tools:
            # 도구 없으면 일반 호출
            response = await self.llm.ainvoke(messages)
            return {
                "content": response.content,
                "tool_calls": [],
                "tool_results": [],
            }

        all_tool_calls = []
        all_tool_results = []
        current_messages = list(messages)

        for iteration in range(max_iterations):
            # 도구 바인딩된 LLM 호출
            response = await self.llm_with_tools.ainvoke(current_messages)

            # 도구 호출 파싱
            tool_calls = parse_tool_calls_from_response(response)

            if not tool_calls:
                # 도구 호출 없음 - 최종 응답
                return {
                    "content": response.content if hasattr(response, 'content') else str(response),
                    "tool_calls": all_tool_calls,
                    "tool_results": all_tool_results,
                }

            # 도구 실행
            tool_results = []
            for tc in tool_calls:
                tool_name = tc["name"]
                tool_args = tc["args"]

                def get_tool_name(t):
                    if hasattr(t, 'name'):
                        return t.name
                    elif hasattr(t, '__name__'):
                        return t.__name__
                    return str(t)

                if tool_name in {get_tool_name(t) for t in self.tools}:
                    # 도구 찾기
                    tool = next(
                        (t for t in self.tools if get_tool_name(t) == tool_name),
                        None
                    )
                    if tool:
                        try:
                            if hasattr(tool, 'ainvoke'):
                                result = await tool.ainvoke(tool_args)
                            else:
                                result = await tool(**tool_args)
                            tool_results.append({
                                "tool_call_id": tc["id"],
                                "name": tool_name,
                                "result": result,
                            })
                        except Exception as e:
                            logger.error(f"Tool {tool_name} error: {e}")
                            tool_results.append({
                                "tool_call_id": tc["id"],
                                "name": tool_name,
                                "result": f"Error: {str(e)}",
                            })

            all_tool_calls.extend(tool_calls)
            all_tool_results.extend(tool_results)

            # 메시지에 AI 응답 추가
            current_messages.append({
                "role": "assistant",
                "content": response.content if hasattr(response, 'content') else "",
                "tool_calls": tool_calls,
            })

            # 도구 결과 메시지 추가
            for tr in tool_results:
                current_messages.append({
                    "role": "tool",
                    "tool_call_id": tr["tool_call_id"],
                    "name": tr["name"],
                    "content": str(tr["result"]),
                })

            self.log_step(f"도구 실행 완료 (iteration {iteration + 1}): {len(tool_results)}개")

        # 최대 반복 도달
        logger.warning(f"[{self.name}] Max tool iterations reached")
        return {
            "content": "",
            "tool_calls": all_tool_calls,
            "tool_results": all_tool_results,
        }

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

    # =========================================================================
    # AgentCore Memory 통합 메서드
    # =========================================================================

    async def learn_from_article(
        self,
        reporter_id: str,
        article_text: str,
        article_metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        기사에서 작성 패턴 학습

        Args:
            reporter_id: 기자 ID
            article_text: 기사 본문
            article_metadata: 기사 메타데이터 (유형, 주제 등)

        Returns:
            학습 성공 여부
        """
        if not self.use_memory or not reporter_id:
            return False

        try:
            await self.memory.initialize()
            return await self.memory.learn_writing_pattern(
                reporter_id=reporter_id,
                article_text=article_text,
                article_metadata=article_metadata or {},
            )
        except Exception as e:
            logger.error(f"Article pattern learning failed: {e}")
            return False

    async def update_reporter_style(
        self,
        reporter_id: str,
        style_data: Dict[str, Any],
    ) -> bool:
        """
        기자 스타일 정보 업데이트

        Args:
            reporter_id: 기자 ID
            style_data: 스타일 데이터

        Returns:
            성공 여부
        """
        if not self.use_memory or not reporter_id:
            return False

        try:
            await self.memory.initialize()
            return await self.memory.store_reporter_preference(
                reporter_id=reporter_id,
                preference_type="style",
                data=style_data,
            )
        except Exception as e:
            logger.error(f"Update reporter style failed: {e}")
            return False

    async def save_session_summary(
        self,
        reporter_id: str,
        session_id: str,
        summary: Dict[str, Any],
    ) -> bool:
        """
        세션 요약 저장

        Args:
            reporter_id: 기자 ID
            session_id: 세션 ID
            summary: 세션 요약 데이터

        Returns:
            성공 여부
        """
        if not self.use_memory:
            return False

        try:
            await self.memory.initialize()
            return await self.memory.store_session_summary(
                reporter_id=reporter_id,
                session_id=session_id,
                summary=summary,
            )
        except Exception as e:
            logger.error(f"Save session summary failed: {e}")
            return False

    async def get_recent_context(
        self,
        reporter_id: str,
        limit: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        최근 세션 컨텍스트 조회

        Args:
            reporter_id: 기자 ID
            limit: 최대 세션 수

        Returns:
            최근 세션 요약 리스트
        """
        if not self.use_memory or not reporter_id:
            return []

        try:
            await self.memory.initialize()
            return await self.memory.get_recent_sessions(reporter_id, limit)
        except Exception as e:
            logger.error(f"Get recent context failed: {e}")
            return []
