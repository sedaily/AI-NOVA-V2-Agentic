"""
Memory Module
AWS AgentCore Memory 연동

LangGraph Checkpoint + Memory Store 통합
- AgentCoreMemoryManager: 통합 메모리 관리자
- AgentCoreMemory: Legacy 호환 클래스
"""

from .agent_core import (
    AgentCoreMemory,
    AgentCoreMemoryManager,
    get_memory_manager,
    initialize_memory,
    create_memory_resource,
    MEMORY_STRATEGIES,
)
from .session_memory import SessionMemory
from .reporter_memory import ReporterMemory

__all__ = [
    # 신규 (권장)
    "AgentCoreMemoryManager",
    "get_memory_manager",
    "initialize_memory",
    "create_memory_resource",
    "MEMORY_STRATEGIES",
    # Legacy 호환
    "AgentCoreMemory",
    "SessionMemory",
    "ReporterMemory",
]
