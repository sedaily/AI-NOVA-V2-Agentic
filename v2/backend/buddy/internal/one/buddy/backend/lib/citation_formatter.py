"""
Citation Formatter for Web Search Results
웹 검색 결과의 출처를 포맷팅하는 유틸리티
"""

import re
import logging
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)


class CitationFormatter:
    """웹 검색 출처 포맷터"""
    
    @staticmethod
    def format_response_with_citations(text: str) -> str:
        """
        AI 응답에서 출처 정보를 추출하고 포맷팅
        
        Args:
            text: AI 응답 텍스트
            
        Returns:
            포맷팅된 응답 텍스트
        """
        # URL 패턴 찾기
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+(?:[.,;]\s|$)?'
        
        # 이미 포맷팅된 출처 섹션이 있는지 확인
        if "📚 출처:" in text:
            return text
            
        # URL들을 찾아서 각주로 변환
        urls = re.findall(url_pattern, text)
        if not urls:
            return text
            
        # 중복 URL 제거
        unique_urls = []
        seen = set()
        for url in urls:
            # 끝에 있는 구두점 제거
            clean_url = url.rstrip('.,;')
            if clean_url not in seen:
                seen.add(clean_url)
                unique_urls.append(clean_url)
        
        if not unique_urls:
            return text
            
        # 본문에서 URL을 각주 번호로 교체
        modified_text = text
        citations = []
        
        for i, url in enumerate(unique_urls, 1):
            # URL을 각주 번호로 교체
            modified_text = modified_text.replace(url, f"[{i}]")
            
            # 도메인 추출
            domain = CitationFormatter._extract_domain(url)
            citations.append(f"[{i}] {domain} - {url}")
        
        # 출처 섹션 추가
        citation_section = "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        citation_section += "📚 출처:\n"
        citation_section += "\n".join(citations)
        citation_section += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        return modified_text + citation_section
    
    @staticmethod
    def _extract_domain(url: str) -> str:
        """URL에서 도메인 추출"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc
            
            # www. 제거
            if domain.startswith('www.'):
                domain = domain[4:]
                
            # 알려진 도메인 매핑
            domain_map = {
                'naver.com': '네이버',
                'daum.net': '다음',
                'ytn.co.kr': 'YTN',
                'yna.co.kr': '연합뉴스',
                'kbs.co.kr': 'KBS',
                'mbc.co.kr': 'MBC',
                'sbs.co.kr': 'SBS',
                'jtbc.co.kr': 'JTBC',
                'chosun.com': '조선일보',
                'donga.com': '동아일보',
                'joongang.co.kr': '중앙일보',
                'hani.co.kr': '한겨레',
                'khan.co.kr': '경향신문',
                'seoul.co.kr': '서울신문',
                'mk.co.kr': '매일경제',
                'hankyung.com': '한국경제',
                'mt.co.kr': '머니투데이',
                'fnnews.com': '파이낸셜뉴스',
                'sedaily.com': '서울경제',
                'gov.kr': '정부기관',
                'go.kr': '정부기관',
                'or.kr': '공공기관'
            }
            
            # 도메인 매핑 확인
            for key, value in domain_map.items():
                if key in domain:
                    return f"✅ {value}"
            
            # 정부/공공기관
            if domain.endswith(('.gov.kr', '.go.kr', '.or.kr')):
                return f"🏛️ {domain}"
            
            # 일반 웹사이트
            return f"ℹ️ {domain}"
            
        except Exception as e:
            logger.error(f"Error extracting domain from {url}: {str(e)}")
            return "웹사이트"
    
    @staticmethod
    def extract_citations_from_response(response: Dict) -> List[Dict]:
        """
        API 응답에서 citation 정보 추출
        
        Args:
            response: Anthropic API 응답
            
        Returns:
            Citation 정보 리스트
        """
        citations = []
        
        # content 배열에서 citation 정보 찾기
        if 'content' in response:
            for content in response['content']:
                if content.get('type') == 'text':
                    text = content.get('text', '')
                    # URL 패턴 찾기
                    urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', text)
                    for url in urls:
                        citations.append({
                            'url': url,
                            'domain': CitationFormatter._extract_domain(url)
                        })
        
        # 직접적인 citations 필드가 있는 경우 (미래 API 업데이트 대비)
        if 'citations' in response:
            for citation in response['citations']:
                citations.append({
                    'url': citation.get('url', ''),
                    'title': citation.get('title', ''),
                    'cited_text': citation.get('cited_text', ''),
                    'domain': CitationFormatter._extract_domain(citation.get('url', ''))
                })
        
        return citations
    
    @staticmethod
    def format_markdown_citations(text: str) -> str:
        """
        마크다운 형식으로 출처를 포맷팅
        
        Args:
            text: AI 응답 텍스트
            
        Returns:
            마크다운 포맷팅된 텍스트
        """
        # URL을 마크다운 링크로 변환
        url_pattern = r'(https?://[^\s<>"{}|\\^`\[\]]+)'
        
        def replace_url(match):
            url = match.group(1).rstrip('.,;')
            domain = CitationFormatter._extract_domain(url)
            return f"[{domain}]({url})"
        
        formatted_text = re.sub(url_pattern, replace_url, text)
        
        return formatted_text


# 사용 예시
if __name__ == "__main__":
    sample_text = """
    오늘의 주요 뉴스입니다.
    
    1. 광주 도서관 붕괴 사고가 발생했습니다. https://www.ytn.co.kr/news/12345
    
    2. 대설주의보가 해제되었습니다. https://www.kma.go.kr/weather/alert
    
    자세한 내용은 각 링크를 참조하세요.
    """
    
    formatter = CitationFormatter()
    formatted = formatter.format_response_with_citations(sample_text)
    print(formatted)