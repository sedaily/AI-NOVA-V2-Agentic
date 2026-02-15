"""
Tool Node
LangGraph 워크플로우에서 도구 실행을 담당하는 노드

주요 기능:
- Tool 호출 파싱
- 병렬 도구 실행
- 결과 상태 업데이트
"""

import asyncio
import logging
from typing import Dict, Any, List, Callable

from .state import ArticleState, ToolCall, ToolResult

logger = logging.getLogger(__name__)


class ToolNode:
    """
    LangGraph용 Tool 실행 노드

    Agent가 tool_calls를 생성하면 이 노드가 실행하고
    결과를 tool_results에 저장
    """

    def __init__(self, tools: List[Callable], name: str = "tool_node"):
        """
        Args:
            tools: LangChain Tool 리스트 (@tool 데코레이터 함수)
            name: 노드 이름
        """
        self.name = name
        self.tools_by_name = {}

        for tool in tools:
            # LangChain Tool의 name 속성 또는 함수명 사용
            if hasattr(tool, 'name'):
                tool_name = tool.name
            elif hasattr(tool, '__name__'):
                tool_name = tool.__name__
            else:
                tool_name = str(tool)
            self.tools_by_name[tool_name] = tool

        logger.info(f"ToolNode initialized with {len(self.tools_by_name)} tools: {list(self.tools_by_name.keys())}")

    async def __call__(self, state: ArticleState) -> ArticleState:
        """
        도구 실행 노드

        1. state.tool_calls에서 실행할 도구 목록 가져오기
        2. 병렬로 도구 실행
        3. 결과를 state.tool_results에 저장
        """
        tool_calls = state.get("tool_calls", [])

        if not tool_calls:
            logger.debug("No tool calls to execute")
            state["pending_tool_calls"] = False
            return state

        logger.info(f"Executing {len(tool_calls)} tool calls")

        # 병렬 실행
        tasks = []
        for tool_call in tool_calls:
            task = self._execute_tool(tool_call)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 결과 처리
        tool_results = []
        for tool_call, result in zip(tool_calls, results):
            if isinstance(result, Exception):
                logger.error(f"Tool {tool_call['name']} failed: {result}")
                tool_results.append({
                    "tool_call_id": tool_call["id"],
                    "name": tool_call["name"],
                    "result": f"Error: {str(result)}",
                })
                state["errors"] = state.get("errors", []) + [f"Tool error: {tool_call['name']}: {result}"]
            else:
                tool_results.append({
                    "tool_call_id": tool_call["id"],
                    "name": tool_call["name"],
                    "result": result,
                })

        # 상태 업데이트
        state["tool_results"] = tool_results
        state["tool_calls"] = []  # 처리 완료
        state["pending_tool_calls"] = False

        logger.info(f"Tool execution complete: {len(tool_results)} results")

        return state

    async def _execute_tool(self, tool_call: ToolCall) -> Any:
        """개별 도구 실행"""
        tool_name = tool_call["name"]
        tool_args = tool_call.get("args", {})

        if tool_name not in self.tools_by_name:
            raise ValueError(f"Unknown tool: {tool_name}")

        tool = self.tools_by_name[tool_name]

        logger.debug(f"Executing tool: {tool_name} with args: {tool_args}")

        # LangChain Tool은 ainvoke 사용
        if hasattr(tool, 'ainvoke'):
            result = await tool.ainvoke(tool_args)
        elif hasattr(tool, 'invoke'):
            result = tool.invoke(tool_args)
        elif asyncio.iscoroutinefunction(tool):
            result = await tool(**tool_args)
        else:
            result = tool(**tool_args)

        return result

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """LLM에 전달할 도구 스키마 반환"""
        schemas = []
        for name, tool in self.tools_by_name.items():
            if hasattr(tool, 'args_schema') and tool.args_schema:
                schema = {
                    "name": name,
                    "description": getattr(tool, 'description', ''),
                    "parameters": tool.args_schema.model_json_schema(),
                }
            else:
                schema = {
                    "name": name,
                    "description": getattr(tool, 'description', ''),
                }
            schemas.append(schema)
        return schemas


def create_tool_node(tools: List[Callable], name: str = "tool_node") -> ToolNode:
    """ToolNode 팩토리 함수"""
    return ToolNode(tools, name)


def should_use_tools(state: ArticleState) -> str:
    """
    조건부 라우팅: 도구 사용 여부 결정

    Returns:
        "tools" - 도구 실행 필요
        "continue" - 다음 노드로 진행
    """
    if state.get("pending_tool_calls") and state.get("tool_calls"):
        return "tools"
    return "continue"


def parse_tool_calls_from_response(response: Any) -> List[ToolCall]:
    """
    LLM 응답에서 tool_calls 파싱

    Args:
        response: LLM 응답 (AIMessage 또는 dict)

    Returns:
        ToolCall 리스트
    """
    tool_calls = []

    # LangChain AIMessage 형식
    if hasattr(response, 'tool_calls') and response.tool_calls:
        for tc in response.tool_calls:
            tool_calls.append({
                "id": tc.get("id", f"call_{len(tool_calls)}"),
                "name": tc.get("name", ""),
                "args": tc.get("args", {}),
            })

    # Bedrock/Anthropic 형식
    elif hasattr(response, 'content'):
        content = response.content
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    tool_calls.append({
                        "id": block.get("id", f"call_{len(tool_calls)}"),
                        "name": block.get("name", ""),
                        "args": block.get("input", {}),
                    })

    # Dict 형식
    elif isinstance(response, dict):
        if "tool_calls" in response:
            for tc in response["tool_calls"]:
                tool_calls.append({
                    "id": tc.get("id", f"call_{len(tool_calls)}"),
                    "name": tc.get("name", ""),
                    "args": tc.get("args", tc.get("arguments", {})),
                })

    return tool_calls


def format_tool_results_for_llm(tool_results: List[ToolResult]) -> List[Dict[str, Any]]:
    """
    도구 결과를 LLM 메시지 형식으로 변환

    Args:
        tool_results: 도구 실행 결과 리스트

    Returns:
        LLM에 전달할 메시지 형식
    """
    messages = []
    for result in tool_results:
        messages.append({
            "role": "tool",
            "tool_call_id": result["tool_call_id"],
            "name": result["name"],
            "content": str(result["result"]),
        })
    return messages
