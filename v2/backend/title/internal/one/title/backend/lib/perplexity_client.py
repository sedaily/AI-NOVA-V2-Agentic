"""
Perplexity API Client
웹 검색 기능을 위한 Perplexity API 통합
"""
import os
import json
import logging
import boto3
import re
import html
from typing import Generator, Optional, Dict, List, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

# 상수
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
DEFAULT_MODEL = "sonar"  # Perplexity 온라인 검색 모델 (2025년 업데이트)


def get_perplexity_api_key() -> Optional[str]:
    """
    Perplexity API 키 가져오기
    1. 환경 변수에서 먼저 확인
    2. AWS Secrets Manager에서 가져오기
    """
    # 환경 변수에서 먼저 확인
    api_key = os.environ.get('PERPLEXITY_API_KEY')
    if api_key:
        logger.info("Using Perplexity API key from environment variable")
        return api_key

    # Secrets Manager에서 가져오기
    secret_name = os.environ.get('PERPLEXITY_SECRET_NAME', 'nexus/perplexity-api-key')
    region = os.environ.get('AWS_REGION', 'us-east-1')

    try:
        client = boto3.client('secretsmanager', region_name=region)
        response = client.get_secret_value(SecretId=secret_name)

        if 'SecretString' in response:
            secret = json.loads(response['SecretString'])
            api_key = secret.get('PERPLEXITY_API_KEY') or secret.get('api_key')

            if api_key:
                logger.info(f"Perplexity API key loaded from Secrets Manager: {secret_name}")
                return api_key

    except Exception as e:
        logger.error(f"Failed to get Perplexity API key from Secrets Manager: {str(e)}")

    return None


class PerplexityClient:
    """Perplexity API 클라이언트"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or get_perplexity_api_key()
        if not self.api_key:
            logger.warning("Perplexity API key not found - web search will be disabled")

    def is_available(self) -> bool:
        """API 사용 가능 여부 확인"""
        return self.api_key is not None

    def _fetch_url_metadata(self, url: str, timeout: int = 3) -> Dict[str, Optional[str]]:
        """
        URL에서 페이지 메타데이터 추출 (제목, 날짜)

        Args:
            url: 대상 URL
            timeout: 요청 타임아웃 (초)

        Returns:
            {'title': 제목, 'date': 날짜} 또는 빈 dict
        """
        result = {'title': None, 'date': None}
        try:
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (compatible; NewsBot/1.0)',
                    'Accept': 'text/html'
                }
            )
            with urllib.request.urlopen(req, timeout=timeout) as response:
                # 처음 16KB 읽기 (날짜 메타데이터 포함을 위해 조금 더 읽음)
                content = response.read(16384).decode('utf-8', errors='ignore')

                # <title> 태그 추출
                title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
                if title_match:
                    title = html.unescape(title_match.group(1).strip())
                    if len(title) > 100:
                        title = title[:97] + "..."
                    result['title'] = title

                # Open Graph title 시도 (title이 없을 경우)
                if not result['title']:
                    og_title = re.search(r'<meta[^>]*property=["\']og:title["\'][^>]*content=["\']([^"\']+)["\']', content, re.IGNORECASE)
                    if og_title:
                        result['title'] = html.unescape(og_title.group(1).strip())

                # 날짜 추출 시도 (여러 메타 태그 패턴)
                date_patterns = [
                    r'<meta[^>]*property=["\']article:published_time["\'][^>]*content=["\']([^"\']+)["\']',
                    r'<meta[^>]*name=["\']date["\'][^>]*content=["\']([^"\']+)["\']',
                    r'<meta[^>]*name=["\']pubdate["\'][^>]*content=["\']([^"\']+)["\']',
                    r'<time[^>]*datetime=["\']([^"\']+)["\']',
                    r'"datePublished":\s*"([^"]+)"',
                    r'"publishedDate":\s*"([^"]+)"'
                ]
                for pattern in date_patterns:
                    date_match = re.search(pattern, content, re.IGNORECASE)
                    if date_match:
                        date_str = date_match.group(1)
                        # ISO 날짜를 간단한 형식으로 변환 (YYYY-MM-DD)
                        if 'T' in date_str:
                            date_str = date_str.split('T')[0]
                        if len(date_str) >= 10:
                            result['date'] = date_str[:10]
                        break

        except Exception as e:
            logger.debug(f"Failed to fetch metadata for {url}: {str(e)}")

        return result

    def _enrich_citations_with_metadata(self, citations: List[Any], max_workers: int = 5) -> List[Dict[str, Any]]:
        """
        Citations에 제목과 날짜 추가 (병렬 처리)

        Args:
            citations: URL 목록 또는 citation 객체 목록
            max_workers: 최대 병렬 작업 수

        Returns:
            메타데이터가 추가된 citation 객체 목록
        """
        enriched = []
        urls_to_fetch = []

        # citation 형식 정규화
        for citation in citations:
            if isinstance(citation, str):
                enriched.append({'url': citation, 'title': None, 'date': None})
                urls_to_fetch.append((len(enriched) - 1, citation))
            elif isinstance(citation, dict):
                url = citation.get('url', citation.get('link', ''))
                title = citation.get('title', '')
                date = citation.get('date', '')
                enriched.append({'url': url, 'title': title if title else None, 'date': date if date else None})
                if (not title or not date) and url:
                    urls_to_fetch.append((len(enriched) - 1, url))
            else:
                continue

        # 메타데이터가 없는 URL들에 대해 병렬로 가져오기
        if urls_to_fetch:
            with ThreadPoolExecutor(max_workers=min(max_workers, len(urls_to_fetch))) as executor:
                future_to_idx = {
                    executor.submit(self._fetch_url_metadata, url): idx
                    for idx, url in urls_to_fetch
                }

                for future in as_completed(future_to_idx, timeout=10):
                    idx = future_to_idx[future]
                    try:
                        metadata = future.result()
                        if metadata:
                            if metadata.get('title') and not enriched[idx]['title']:
                                enriched[idx]['title'] = metadata['title']
                            if metadata.get('date') and not enriched[idx]['date']:
                                enriched[idx]['date'] = metadata['date']
                    except Exception:
                        pass

        return enriched

    def optimize_search_query(self, user_message: str) -> Dict[str, str]:
        """
        사용자 질문을 분석해 최적화된 검색 쿼리 생성

        Args:
            user_message: 사용자 원본 메시지

        Returns:
            {'query': 최적화된 쿼리, 'display': 표시용 짧은 쿼리}
        """
        if not self.api_key:
            return {'query': user_message[:500], 'display': user_message[:50]}

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            body = {
                "model": "sonar",
                "messages": [
                    {
                        "role": "system",
                        "content": """You are a search query optimizer. Given a user's question or message:
1. Extract the core search intent
2. Generate an optimized search query (max 100 chars)
3. Generate a short display label (max 30 chars, Korean preferred)

Respond ONLY in this exact JSON format, no other text:
{"query": "optimized search query", "display": "짧은 표시용 라벨"}"""
                    },
                    {
                        "role": "user",
                        "content": user_message[:1000]
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 150
            }

            req = urllib.request.Request(
                PERPLEXITY_API_URL,
                data=json.dumps(body).encode('utf-8'),
                headers=headers,
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))

            if result.get('choices') and len(result['choices']) > 0:
                content = result['choices'][0].get('message', {}).get('content', '')
                # JSON 파싱 시도
                try:
                    parsed = json.loads(content.strip())
                    return {
                        'query': parsed.get('query', user_message[:500]),
                        'display': parsed.get('display', user_message[:30])
                    }
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse optimized query response: {content}")

        except Exception as e:
            logger.warning(f"Query optimization failed: {str(e)}")

        # 기본값: 사용자 메시지에서 핵심 부분 추출
        return {
            'query': user_message[:500],
            'display': user_message[:30] + ('...' if len(user_message) > 30 else '')
        }

    # 블랙리스트: 저품질 소스 제외 (블로그, 카페, 위키 등)
    EXCLUDED_DOMAINS = [
        '-blog.naver.com',    # 네이버 블로그
        '-tistory.com',       # 티스토리
        '-brunch.co.kr',      # 브런치
        '-cafe.naver.com',    # 네이버 카페
        '-cafe.daum.net',     # 다음 카페
        '-namu.wiki',         # 나무위키
        '-namuwiki.kr',       # 나무위키 (구)
        '-kin.naver.com',     # 지식인
    ]

    def search(
        self,
        query: str,
        system_prompt: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        recency_filter: Optional[str] = "day",  # day(24시간), week, month, year
        use_domain_filter: bool = True  # 도메인 필터 사용 여부
    ) -> Dict[str, Any]:
        """
        Perplexity API를 사용한 웹 검색

        Args:
            query: 검색 쿼리
            system_prompt: 시스템 프롬프트 (선택)
            model: 사용할 모델
            recency_filter: 최신성 필터
            use_domain_filter: 블랙리스트 도메인 필터 사용 여부

        Returns:
            검색 결과 및 응답
        """
        if not self.api_key:
            return {
                'success': False,
                'error': 'Perplexity API key not configured',
                'content': '',
                'citations': []
            }

        try:
            # 요청 헤더
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            # 요청 본문
            messages = []

            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })

            messages.append({
                "role": "user",
                "content": query
            })

            body = {
                "model": model,
                "messages": messages,
                "temperature": 0.2,
                "top_p": 0.9,
                "return_citations": True,
                "return_images": False,
                "return_related_questions": False
            }

            # 최신성 필터 추가 (day, week, month, year)
            if recency_filter:
                body["search_recency_filter"] = recency_filter
                logger.info(f"🕐 검색 최신성 필터 적용: {recency_filter}")

            # 도메인 필터 추가 (블랙리스트: 블로그/카페 등 제외)
            if use_domain_filter and self.EXCLUDED_DOMAINS:
                body["search_domain_filter"] = self.EXCLUDED_DOMAINS
                logger.info(f"🚫 도메인 필터 적용: {len(self.EXCLUDED_DOMAINS)}개 제외")

            # API 호출
            req = urllib.request.Request(
                PERPLEXITY_API_URL,
                data=json.dumps(body).encode('utf-8'),
                headers=headers,
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))

            # 응답 파싱
            content = ""
            citations = []

            if result.get('choices') and len(result['choices']) > 0:
                message = result['choices'][0].get('message', {})
                content = message.get('content', '')

            # citations 추출 및 제목 추가
            if 'citations' in result:
                raw_citations = result['citations']
                # 제목이 포함된 enriched citations으로 변환
                citations = self._enrich_citations_with_metadata(raw_citations)
                logger.info(f"📚 Citations enriched with titles: {len(citations)} items")

            logger.info(f"Perplexity search completed: {len(content)} chars, {len(citations)} citations")

            return {
                'success': True,
                'content': content,
                'citations': citations,
                'model': model,
                'usage': result.get('usage', {})
            }

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else str(e)
            logger.error(f"Perplexity API HTTP error: {e.code} - {error_body}")
            return {
                'success': False,
                'error': f"HTTP {e.code}: {error_body}",
                'content': '',
                'citations': []
            }

        except Exception as e:
            logger.error(f"Perplexity API error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'content': '',
                'citations': []
            }

    def search_for_article(
        self,
        article_content: str,
        search_type: str = 'context',
        recency_filter: Optional[str] = "day",  # day(24시간), week, month, year
        use_domain_filter: bool = True  # 블랙리스트 도메인 필터 사용
    ) -> Dict[str, Any]:
        """
        기사 내용 기반 웹 검색 (Perplexity 자체 의도 파악 활용)

        Args:
            article_content: 기사 본문 또는 사용자 질문
            search_type: 검색 유형 ('context', 'fact_check', 'related')
            recency_filter: 검색 최신성 필터 ('day', 'week', 'month', 'year')
            use_domain_filter: 블랙리스트 도메인 필터 사용 여부

        Returns:
            검색 결과 (display_query 포함)
        """
        # Perplexity가 자체적으로 의도 파악하므로 원본 질문 그대로 사용
        user_query = article_content[:500]  # 최대 500자
        display_query = article_content[:50] + ('...' if len(article_content) > 50 else '')
        logger.info(f"🔍 웹검색 시작: '{display_query}'")

        # 검색 유형에 따른 시스템 프롬프트 설정 (Perplexity가 의도 파악)
        if search_type == 'context':
            system_prompt = """You are a helpful research assistant for Korean news.
Search for the most recent and relevant information. Focus on factual, up-to-date content.
Always respond in Korean."""
            query = user_query

        elif search_type == 'fact_check':
            system_prompt = """You are a fact-checking assistant. Verify claims with reliable sources.
Respond in Korean."""
            query = user_query

        elif search_type == 'related':
            system_prompt = """You are a news research assistant. Find related recent news.
Respond in Korean."""
            query = user_query

        else:
            system_prompt = "You are a helpful research assistant. Respond in Korean."
            query = user_query

        # 3. 검색 실행 (최신성 필터 + 도메인 필터 적용)
        result = self.search(
            query=query,
            system_prompt=system_prompt,
            recency_filter=recency_filter,
            use_domain_filter=use_domain_filter
        )

        # 4. display_query 추가 (프론트엔드에서 표시용)
        result['display_query'] = display_query

        return result

    def format_search_results_for_prompt(
        self,
        search_result: Dict[str, Any]
    ) -> str:
        """
        검색 결과를 프롬프트에 포함할 형식으로 변환

        Args:
            search_result: search() 메서드의 반환값

        Returns:
            프롬프트에 포함할 수 있는 문자열
        """
        if not search_result.get('success'):
            return ""

        parts = []

        # 검색 내용
        content = search_result.get('content', '')
        if content:
            parts.append("=== 웹 검색 결과 ===")
            parts.append(content)

        # 출처 정보
        citations = search_result.get('citations', [])
        if citations:
            parts.append("\n=== 참고 출처 ===")
            for i, citation in enumerate(citations[:5], 1):  # 최대 5개 출처
                if isinstance(citation, str):
                    parts.append(f"{i}. {citation}")
                elif isinstance(citation, dict):
                    url = citation.get('url', citation.get('link', ''))
                    title = citation.get('title', '')
                    if url:
                        parts.append(f"{i}. {title}: {url}" if title else f"{i}. {url}")

        return "\n".join(parts)


# 싱글톤 인스턴스
_perplexity_client = None


def get_perplexity_client() -> PerplexityClient:
    """Perplexity 클라이언트 싱글톤 인스턴스 반환"""
    global _perplexity_client
    if _perplexity_client is None:
        _perplexity_client = PerplexityClient()
    return _perplexity_client
