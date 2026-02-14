"""
Citation Formatter
웹 검색 결과의 출처 정보를 포맷팅하는 모듈
"""
import re
import logging
from typing import List, Dict, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class CitationFormatter:
    """출처 표시 및 포맷팅을 담당하는 클래스"""
    
    # 신뢰할 수 있는 언론사 도메인
    TRUSTED_NEWS_DOMAINS = {
        'ytn.co.kr': '✅ YTN',
        'joins.com': '✅ 중앙일보',
        'chosun.com': '✅ 조선일보',
        'donga.com': '✅ 동아일보',
        'hani.co.kr': '✅ 한겨레',
        'khan.co.kr': '✅ 경향신문',
        'mt.co.kr': '✅ 머니투데이',
        'hankyung.com': '✅ 한국경제',
        'mk.co.kr': '✅ 매일경제',
        'seoul.co.kr': '✅ 서울신문',
        'kbs.co.kr': '✅ KBS',
        'mbc.co.kr': '✅ MBC',
        'sbs.co.kr': '✅ SBS',
        'jtbc.joins.com': '✅ JTBC'
    }
    
    # 정부/공공기관 도메인
    GOVERNMENT_DOMAINS = {
        'go.kr': '🏛️',
        'korea.kr': '🏛️'
    }
    
    @staticmethod
    def format_response_with_citations(text: str, search_results: List[Dict] = None) -> str:
        """
        AI 응답에서 URL을 감지하고 출처 각주로 변환
        
        Args:
            text: AI 응답 텍스트
            search_results: 웹 검색 결과 (옵션)
        
        Returns:
            출처가 포함된 포맷팅된 텍스트
        """
        try:
            # URL 패턴 매칭
            url_pattern = r'https?://[^\s\])]+'
            urls = re.findall(url_pattern, text)
            
            if not urls and not search_results:
                return text
            
            # 각주 번호와 URL 매핑
            citations = []
            citation_map = {}
            
            # 텍스트에서 찾은 URL들 처리
            for i, url in enumerate(urls, 1):
                if url not in citation_map:
                    citation_info = CitationFormatter._extract_domain_info(url)
                    citations.append({
                        'number': i,
                        'url': url,
                        'domain': citation_info['domain'],
                        'trust_level': citation_info['trust_level'],
                        'title': f"참조 {i}"
                    })
                    citation_map[url] = i
            
            # 웹 검색 결과에서 추가 출처 처리
            if search_results:
                for result in search_results:
                    url = result.get('url', '')
                    if url and url not in citation_map:
                        next_num = len(citations) + 1
                        citation_info = CitationFormatter._extract_domain_info(url)
                        citations.append({
                            'number': next_num,
                            'url': url,
                            'domain': citation_info['domain'],
                            'trust_level': citation_info['trust_level'],
                            'title': result.get('title', f"참조 {next_num}")
                        })
                        citation_map[url] = next_num
            
            # 텍스트에서 URL을 각주 번호로 대체
            formatted_text = text
            for url, number in citation_map.items():
                formatted_text = formatted_text.replace(url, f"[{number}]")
            
            # 출처 섹션 생성
            if citations:
                sources_section = CitationFormatter._build_sources_section(citations)
                formatted_text += "\n\n" + sources_section
            
            return formatted_text
            
        except Exception as e:
            logger.error(f"Error formatting citations: {str(e)}")
            return text  # 오류 시 원본 텍스트 반환
    
    @staticmethod
    def _extract_domain_info(url: str) -> Dict[str, str]:
        """
        URL에서 도메인 정보 추출 및 신뢰도 판단
        
        Args:
            url: 분석할 URL
            
        Returns:
            도메인 정보와 신뢰도
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # 정확한 도메인 매칭
            if domain in CitationFormatter.TRUSTED_NEWS_DOMAINS:
                return {
                    'domain': domain,
                    'trust_level': CitationFormatter.TRUSTED_NEWS_DOMAINS[domain]
                }
            
            # 정부/공공기관 도메인 체크
            for gov_domain in CitationFormatter.GOVERNMENT_DOMAINS:
                if domain.endswith(gov_domain):
                    return {
                        'domain': domain,
                        'trust_level': f"{CitationFormatter.GOVERNMENT_DOMAINS[gov_domain]} 공공기관"
                    }
            
            # 일반 웹사이트
            return {
                'domain': domain,
                'trust_level': 'ℹ️ 일반'
            }
            
        except Exception as e:
            logger.error(f"Error parsing domain from {url}: {str(e)}")
            return {
                'domain': 'unknown',
                'trust_level': 'ℹ️ 일반'
            }
    
    @staticmethod
    def _build_sources_section(citations: List[Dict]) -> str:
        """
        출처 섹션을 마크다운 형식으로 생성
        
        Args:
            citations: 출처 정보 리스트
            
        Returns:
            포맷팅된 출처 섹션
        """
        if not citations:
            return ""
        
        lines = [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "📚 **출처:**"
        ]
        
        for citation in citations:
            line = f"[{citation['number']}] {citation['trust_level']} {citation['title']} - {citation['url']}"
            lines.append(line)
        
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        return "\n".join(lines)
    
    @staticmethod
    def extract_citations_from_web_search(search_response: str) -> List[Dict]:
        """
        웹 검색 응답에서 출처 정보 추출
        
        Args:
            search_response: 웹 검색 API 응답
            
        Returns:
            추출된 출처 정보 리스트
        """
        try:
            # Anthropic 웹 검색 응답에서 citation 정보 추출
            citations = []
            
            # URL 패턴으로 기본 추출
            url_pattern = r'https?://[^\s\])]+'
            urls = re.findall(url_pattern, search_response)
            
            for i, url in enumerate(set(urls), 1):  # 중복 제거
                citation_info = CitationFormatter._extract_domain_info(url)
                citations.append({
                    'number': i,
                    'url': url,
                    'domain': citation_info['domain'],
                    'trust_level': citation_info['trust_level'],
                    'title': f"웹 검색 결과 {i}"
                })
            
            return citations
            
        except Exception as e:
            logger.error(f"Error extracting citations from search response: {str(e)}")
            return []