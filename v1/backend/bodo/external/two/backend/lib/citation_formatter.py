"""
Citation Formatter
웹 검색 결과의 출처를 포맷팅하고 관리하는 모듈
"""
import re
import logging
from typing import List, Dict, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class CitationFormatter:
    """웹 검색 결과의 출처 정보를 포맷팅"""
    
    # 신뢰도 표시를 위한 도메인 분류
    TRUSTED_NEWS_DOMAINS = [
        'yna.co.kr', 'ytn.co.kr', 'sbs.co.kr', 'kbs.co.kr', 'mbc.co.kr',
        'sedaily.com', 'mk.co.kr', 'hankyung.com', 'mt.co.kr', 'edaily.co.kr',
        'chosun.com', 'joongang.co.kr', 'donga.com', 'hani.co.kr', 'khan.co.kr',
        'hankookilbo.com', 'etnews.com', 'zdnet.co.kr', 'bloter.net', 'newsis.com'
    ]
    
    GOVERNMENT_DOMAINS = [
        '.go.kr', '.gov.kr', '.or.kr', 'korea.kr', 'kosis.kr', 
        'bok.or.kr', 'fss.or.kr', 'kofia.or.kr', 'kdi.re.kr'
    ]
    
    @staticmethod
    def format_response_with_citations(text: str) -> str:
        """
        AI 응답에서 출처 정보를 추출하고 포맷팅
        
        Args:
            text: AI의 원본 응답
            
        Returns:
            출처가 포맷팅된 응답
        """
        try:
            # 이미 포맷팅된 경우 그대로 반환
            if "📚 출처:" in text:
                return text
            
            # URL 패턴 찾기
            url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+(?:[.,;!?](?=\s)|(?=[.,;!?\s]|$))'
            urls = re.findall(url_pattern, text)
            
            if not urls:
                return text
            
            # 중복 제거 및 순서 유지
            seen = set()
            unique_urls = []
            for url in urls:
                # URL 끝의 구두점 제거
                url = re.sub(r'[.,;!?]+$', '', url)
                if url not in seen:
                    seen.add(url)
                    unique_urls.append(url)
            
            # 본문에서 URL을 번호로 치환
            formatted_text = text
            citations = []
            
            for idx, url in enumerate(unique_urls, 1):
                # URL을 각주 번호로 치환
                formatted_text = formatted_text.replace(url, f"[{idx}]")
                
                # 출처 정보 생성
                domain = CitationFormatter._extract_domain(url)
                trust_icon = CitationFormatter._get_trust_icon(domain)
                
                # 도메인에서 사이트명 추출
                site_name = CitationFormatter._get_site_name(domain)
                
                citations.append(f"[{idx}] {trust_icon} {site_name} - {url}")
            
            # 출처 섹션 추가
            if citations:
                citation_section = "\n\n" + "━" * 50
                citation_section += "\n📚 출처:\n"
                citation_section += "\n".join(citations)
                citation_section += "\n" + "━" * 50
                
                formatted_text += citation_section
            
            return formatted_text
            
        except Exception as e:
            logger.error(f"Error formatting citations: {str(e)}")
            return text
    
    @staticmethod
    def _extract_domain(url: str) -> str:
        """URL에서 도메인 추출"""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except:
            return ""
    
    @staticmethod
    def _get_trust_icon(domain: str) -> str:
        """도메인별 신뢰도 아이콘 반환"""
        # 공식 언론사
        for news_domain in CitationFormatter.TRUSTED_NEWS_DOMAINS:
            if news_domain in domain:
                return "✅"
        
        # 정부/공공기관
        for gov_domain in CitationFormatter.GOVERNMENT_DOMAINS:
            if gov_domain in domain:
                return "🏛️"
        
        # 일반 웹사이트
        return "ℹ️"
    
    @staticmethod
    def _get_site_name(domain: str) -> str:
        """도메인에서 사이트명 추출"""
        # 주요 언론사 매핑
        site_names = {
            'yna.co.kr': '연합뉴스',
            'ytn.co.kr': 'YTN',
            'sbs.co.kr': 'SBS',
            'kbs.co.kr': 'KBS',
            'mbc.co.kr': 'MBC',
            'sedaily.com': '서울경제',
            'mk.co.kr': '매일경제',
            'hankyung.com': '한국경제',
            'mt.co.kr': '머니투데이',
            'edaily.co.kr': '이데일리',
            'chosun.com': '조선일보',
            'joongang.co.kr': '중앙일보',
            'donga.com': '동아일보',
            'hani.co.kr': '한겨레',
            'khan.co.kr': '경향신문',
            'hankookilbo.com': '한국일보',
            'etnews.com': '전자신문',
            'zdnet.co.kr': 'ZDNet Korea',
            'bloter.net': '블로터',
            'newsis.com': '뉴시스'
        }
        
        for key, name in site_names.items():
            if key in domain:
                return name
        
        # 정부 기관
        if '.go.kr' in domain or '.gov.kr' in domain:
            return '정부기관'
        
        # 도메인에서 첫 부분 추출
        parts = domain.split('.')
        if len(parts) > 1:
            # www 제거
            if parts[0] == 'www' and len(parts) > 2:
                return parts[1].capitalize()
            return parts[0].capitalize()
        
        return domain
    
    @staticmethod
    def extract_citations_from_response(text: str) -> List[Dict[str, str]]:
        """
        응답에서 출처 정보 추출
        
        Returns:
            List of dictionaries with 'url', 'title', 'domain' keys
        """
        citations = []
        
        # URL 패턴 찾기
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+(?:[.,;!?](?=\s)|(?=[.,;!?\s]|$))'
        urls = re.findall(url_pattern, text)
        
        for url in urls:
            url = re.sub(r'[.,;!?]+$', '', url)
            domain = CitationFormatter._extract_domain(url)
            site_name = CitationFormatter._get_site_name(domain)
            
            citations.append({
                'url': url,
                'domain': domain,
                'site_name': site_name,
                'trust_level': CitationFormatter._get_trust_icon(domain)
            })
        
        return citations
    
    @staticmethod
    def format_inline_citations(text: str, citations: List[str]) -> str:
        """
        텍스트에 인라인 각주 추가
        
        Args:
            text: 원본 텍스트
            citations: 출처 URL 리스트
            
        Returns:
            각주가 추가된 텍스트
        """
        formatted_text = text
        
        for idx, url in enumerate(citations, 1):
            # URL을 각주 번호로 치환
            formatted_text = formatted_text.replace(url, f"[{idx}]")
        
        return formatted_text