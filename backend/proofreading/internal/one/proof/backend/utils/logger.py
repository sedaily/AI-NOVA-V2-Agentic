"""
Logging Utilities
통합 로깅 설정 및 헬퍼 함수
"""
import logging
import json
from typing import Any, Dict


def setup_logger(name: str, level: str = 'INFO') -> logging.Logger:
    """로거 설정"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    return logger


def log_lambda_event(logger: logging.Logger, event: Dict[str, Any]) -> None:
    """Lambda 이벤트 로깅"""
    logger.info(f"Lambda Event: {json.dumps(event, default=str)}")
    
    # 주요 정보 추출 로깅
    http_method = event.get('httpMethod', 'N/A')
    path = event.get('path', event.get('rawPath', 'N/A'))
    logger.info(f"Request: {http_method} {path}")