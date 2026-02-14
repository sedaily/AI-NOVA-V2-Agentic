"""
Tavily Web Search Client
Bedrock과 함께 사용하기 위한 실시간 웹검색 클라이언트
"""
import os
import json
import boto3
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional
from functools import lru_cache
from botocore.exceptions import ClientError

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Secrets Manager 클라이언트
secrets_client = boto3.client('secretsmanager', region_name='us-east-1')

# Tavily API 설정
TAVILY_API_URL = "https://api.tavily.com/search"
DEFAULT_MAX_RESULTS = 5


@lru_cache(maxsize=1)
def get_tavily_api_key() -> Optional[str]:
    """Secrets Manager에서 Tavily API 키 가져오기"""
    try:
        secret_name = os.environ.get('TAVILY_SECRET_NAME', 'tavily-api-key')
        response = secrets_client.get_secret_value(SecretId=secret_name)
        secret = json.loads(response['SecretString'])
        api_key = secret.get('TAVILY_API_KEY', '')
        if api_key:
            logger.info("Tavily API key loaded from Secrets Manager")
        return api_key
    except Exception as e:
        logger.error(f"Failed to get Tavily API key: {str(e)}")
        return os.environ.get('TAVILY_API_KEY', '')


def search(query: str, max_results: int = DEFAULT_MAX_RESULTS, days: int = 1) -> Dict[str, Any]:
    """
    Tavily 웹검색 실행

    Args:
        query: 검색 쿼리
        max_results: 최대 결과 수
        days: 최근 N일 이내 결과만 (실시간 뉴스를 위해 기본값 1)

    Returns:
        {
            'success': bool,
            'answer': str,
            'results': [{'title', 'url', 'content'}],
            'query': str
        }
    """
    api_key = get_tavily_api_key()
    if not api_key:
        return {'success': False, 'error': 'API key not configured', 'results': [], 'query': query}

    try:
        response = requests.post(
            TAVILY_API_URL,
            json={
                'api_key': api_key,
                'query': query,
                'max_results': max_results,
                'search_depth': 'advanced',  # 고급 검색 (더 정확한 결과)
                'include_answer': True,
                'days': days,  # 최근 N일 이내 결과만 (실시간 뉴스)
                'topic': 'news'  # 뉴스 토픽 우선
            },
            timeout=15
        )

        if response.status_code != 200:
            logger.error(f"Tavily error: {response.status_code}")
            return {'success': False, 'error': f'API error: {response.status_code}', 'results': [], 'query': query}

        data = response.json()
        results = [{
            'title': r.get('title', ''),
            'url': r.get('url', ''),
            'content': r.get('content', '')[:500],
            'published_date': r.get('published_date', '')  # 게시일 추가
        } for r in data.get('results', [])]

        logger.info(f"🌐 Tavily search: '{query}' → {len(results)} results")
        return {
            'success': True,
            'answer': data.get('answer', ''),
            'results': results,
            'query': query,
            'search_date': datetime.now().strftime('%Y-%m-%d')  # 검색 시점 날짜
        }

    except Exception as e:
        logger.error(f"Tavily search error: {str(e)}")
        return {'success': False, 'error': str(e), 'results': [], 'query': query}


def format_context(search_result: Dict[str, Any]) -> str:
    """검색 결과를 LLM 컨텍스트로 포맷"""
    if not search_result.get('success') or not search_result.get('results'):
        return ""

    search_date = search_result.get('search_date', datetime.now().strftime('%Y-%m-%d'))

    parts = [
        f"\n[WEB_SEARCH_RESULT date=\"{search_date}\"]",
    ]

    if search_result.get('answer'):
        parts.append(f"요약: {search_result['answer']}")

    parts.append("\n[SOURCES]")
    for idx, r in enumerate(search_result.get('results', [])[:5], 1):
        title = r.get('title', '')
        url = r.get('url', '')
        content = r.get('content', '')
        pub_date = r.get('published_date', '')

        parts.append(f"[{idx}] {title}")
        if pub_date:
            parts.append(f"    게시일: {pub_date}")
        parts.append(f"    URL: {url}")
        parts.append(f"    내용: {content}")

    parts.append("[/SOURCES]")
    parts.append(f"\n오늘 날짜는 {search_date}입니다. 답변 시 출처를 [제목](URL) 마크다운 링크로 표시하세요.")
    parts.append("[/WEB_SEARCH_RESULT]\n")

    return '\n'.join(parts)


def search_and_format(query: str, max_results: int = DEFAULT_MAX_RESULTS) -> str:
    """웹검색 + 컨텍스트 포맷팅 한번에"""
    result = search(query, max_results)
    return format_context(result)
