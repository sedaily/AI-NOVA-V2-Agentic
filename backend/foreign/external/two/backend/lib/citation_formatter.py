"""
Citation Formatter for Web Search Results
출처 정보 추출 및 포맷팅 모듈
"""
import re
import logging
from typing import List, Dict, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class CitationFormatter:
    """웹 검색 결과에 대한 출처 표시 포맷터"""
    
    # 신뢰할 수 있는 언론사 도메인
    TRUSTED_NEWS_DOMAINS = {
        'ytn.co.kr', 'yna.co.kr', 'kbs.co.kr', 'mbc.co.kr', 'sbs.co.kr',
        'chosun.com', 'donga.com', 'joongang.co.kr', 'hani.co.kr', 'hankookilbo.com',
        'sedaily.com', 'hankyung.com', 'mk.co.kr', 'mt.co.kr', 'edaily.co.kr',
        'khan.co.kr', 'ohmynews.com', 'pressian.com', 'newsis.com', 'news1.kr'
    }
    
    # 정부/공공기관 도메인
    GOVERNMENT_DOMAINS = {
        'gov.kr', 'go.kr', 'or.kr', 're.kr', 'ac.kr',
        'korea.kr', 'mois.go.kr', 'mofa.go.kr', 'moe.go.kr',
        'mohw.go.kr', 'moj.go.kr', 'moef.go.kr', 'motie.go.kr'
    }
    
    @classmethod
    def format_response_with_citations(cls, text: str) -> str:
        """
        AI 응답에서 출처 정보를 추출하고 포맷팅
        
        Args:
            text: AI 응답 텍스트
            
        Returns:
            출처가 포맷팅된 응답
        """
        try:
            # 이미 출처 섹션이 있는지 확인
            if "📚 출처:" in text or "━━━" in text:
                return text
            
            # URL 패턴 찾기
            url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+(?:\.[^\s<>"{}|\\^`\[\]]+)*'
            urls = re.findall(url_pattern, text)
            
            if not urls:
                return text
            
            # 중복 제거 및 출처 정보 생성
            citations = []
            seen_domains = set()
            
            for i, url in enumerate(urls, 1):
                domain = cls._extract_domain(url)
                if domain not in seen_domains:
                    seen_domains.add(domain)
                    trust_icon = cls._get_trust_icon(domain)
                    site_name = cls._get_site_name(domain)
                    
                    # URL을 각주 번호로 대체
                    text = text.replace(url, f"[{i}]", 1)
                    
                    # 출처 정보 추가
                    citations.append(f"[{i}] {trust_icon} {site_name} - {url}")
            
            # 출처 섹션 추가
            if citations:
                citation_section = "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                citation_section += "📚 출처:\n"
                citation_section += "\n".join(citations)
                citation_section += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                
                text = text + citation_section
            
            return text
            
        except Exception as e:
            logger.error(f"Error formatting citations: {str(e)}")
            return text
    
    @classmethod
    def _extract_domain(cls, url: str) -> str:
        """URL에서 도메인 추출"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            # www. 제거
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return ""
    
    @classmethod
    def _get_trust_icon(cls, domain: str) -> str:
        """도메인 신뢰도에 따른 아이콘 반환"""
        # 정부/공공기관 체크
        for gov_domain in cls.GOVERNMENT_DOMAINS:
            if gov_domain in domain:
                return "🏛️"
        
        # 언론사 체크
        for news_domain in cls.TRUSTED_NEWS_DOMAINS:
            if news_domain in domain:
                return "✅"
        
        # 일반 웹사이트
        return "ℹ️"
    
    @classmethod
    def _get_site_name(cls, domain: str) -> str:
        """도메인에서 사이트명 추출"""
        # 주요 언론사 매핑
        site_names = {
            'ytn.co.kr': 'YTN',
            'yna.co.kr': '연합뉴스',
            'kbs.co.kr': 'KBS',
            'mbc.co.kr': 'MBC',
            'sbs.co.kr': 'SBS',
            'chosun.com': '조선일보',
            'donga.com': '동아일보',
            'joongang.co.kr': '중앙일보',
            'hani.co.kr': '한겨레',
            'hankookilbo.com': '한국일보',
            'sedaily.com': '서울경제',
            'hankyung.com': '한국경제',
            'mk.co.kr': '매일경제',
            'mt.co.kr': '머니투데이',
            'edaily.co.kr': '이데일리',
            'khan.co.kr': '경향신문',
            'ohmynews.com': '오마이뉴스',
            'pressian.com': '프레시안',
            'newsis.com': '뉴시스',
            'news1.kr': '뉴스1'
        }
        
        return site_names.get(domain, domain)
    
    @classmethod
    def extract_citations_from_response(cls, text: str) -> List[Dict[str, str]]:
        """
        응답에서 출처 정보를 구조화된 형태로 추출
        
        Returns:
            List of citation dictionaries with 'number', 'url', 'title', 'source'
        """
        citations = []
        
        # 출처 섹션 찾기
        citation_section_pattern = r'📚 출처:(.*?)(?:━━━|$)'
        citation_match = re.search(citation_section_pattern, text, re.DOTALL)
        
        if citation_match:
            citation_text = citation_match.group(1)
            
            # 각 출처 라인 파싱
            citation_lines = citation_text.strip().split('\n')
            for line in citation_lines:
                line = line.strip()
                if not line:
                    continue
                
                # [번호] 아이콘 사이트명 - URL 패턴 매칭
                citation_pattern = r'\[(\d+)\]\s*([🏛️✅ℹ️]?)\s*([^-]+)\s*-\s*(https?://[^\s]+)'
                match = re.match(citation_pattern, line)
                
                if match:
                    citations.append({
                        'number': match.group(1),
                        'trust_icon': match.group(2),
                        'source': match.group(3).strip(),
                        'url': match.group(4)
                    })
        
        return citations
    
    @classmethod
    def format_inline_citations(cls, text: str) -> str:
        """
        텍스트에서 인라인 출처 번호 포맷팅
        [1], [2] 형식을 상위첨자로 변환
        """
        # Markdown 상위첨자 형식으로 변환 (일부 클라이언트 지원)
        # 또는 그대로 유지 (대부분의 경우)
        return text