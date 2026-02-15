"""
Session Memory
세션 기반 임시 메모리 (Redis 또는 In-Memory)
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

# Redis 설정 (선택적)
REDIS_URL = os.getenv("REDIS_URL", "")


class SessionMemory:
    """세션 메모리 관리"""

    def __init__(self):
        self._local_store: Dict[str, Dict[str, Any]] = {}
        self._redis_client = None

        if REDIS_URL:
            try:
                import redis
                self._redis_client = redis.from_url(REDIS_URL)
                logger.info("Redis session memory initialized")
            except Exception as e:
                logger.warning(f"Redis init failed, using local: {e}")

    def _get_key(self, session_id: str, key: str) -> str:
        return f"session:{session_id}:{key}"

    async def set(
        self,
        session_id: str,
        key: str,
        value: Any,
        ttl_seconds: int = 3600,
    ) -> bool:
        """값 저장"""
        full_key = self._get_key(session_id, key)
        data = json.dumps(value, default=str)

        if self._redis_client:
            try:
                self._redis_client.setex(full_key, ttl_seconds, data)
                return True
            except Exception as e:
                logger.error(f"Redis set error: {e}")

        # 로컬 폴백
        if session_id not in self._local_store:
            self._local_store[session_id] = {}
        self._local_store[session_id][key] = {
            "value": value,
            "expires": datetime.utcnow() + timedelta(seconds=ttl_seconds),
        }
        return True

    async def get(
        self,
        session_id: str,
        key: str,
    ) -> Optional[Any]:
        """값 조회"""
        full_key = self._get_key(session_id, key)

        if self._redis_client:
            try:
                data = self._redis_client.get(full_key)
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.error(f"Redis get error: {e}")

        # 로컬 폴백
        if session_id in self._local_store:
            entry = self._local_store[session_id].get(key)
            if entry and entry["expires"] > datetime.utcnow():
                return entry["value"]

        return None

    async def delete(self, session_id: str, key: str) -> bool:
        """값 삭제"""
        full_key = self._get_key(session_id, key)

        if self._redis_client:
            try:
                self._redis_client.delete(full_key)
            except Exception as e:
                logger.error(f"Redis delete error: {e}")

        if session_id in self._local_store:
            self._local_store[session_id].pop(key, None)

        return True

    async def get_session_state(self, session_id: str) -> Dict[str, Any]:
        """전체 세션 상태 조회"""
        state = await self.get(session_id, "state")
        return state or {}

    async def save_session_state(
        self,
        session_id: str,
        state: Dict[str, Any],
    ) -> bool:
        """세션 상태 저장"""
        return await self.set(session_id, "state", state, ttl_seconds=7200)

    async def clear_session(self, session_id: str) -> bool:
        """세션 초기화"""
        if self._redis_client:
            try:
                keys = self._redis_client.keys(f"session:{session_id}:*")
                if keys:
                    self._redis_client.delete(*keys)
            except Exception as e:
                logger.error(f"Redis clear error: {e}")

        self._local_store.pop(session_id, None)
        return True
