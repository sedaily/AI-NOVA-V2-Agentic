"""
Citation Formatter
웹 검색 결과의 출처를 자동으로 포맷팅하는 모듈
"""
import re
import logging
from typing import List, Dict, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class CitationFormatter:
    """AI 응답에서 출처 정보를 추출하고 포맷팅하는 클래스"""
    
    # 신뢰도 표시 이모지
    TRUST_INDICATORS = {
        'government': '🏛️',  # 정부/공공기관
        'news': '✅',        # 공식 언론사
        'general': 'ℹ️'      # 일반 웹사이트
    }
    
    # 공식 언론사 도메인
    NEWS_DOMAINS = {
        'yna.co.kr', 'yonhapnews.co.kr',  # 연합뉴스
        'chosun.com', 'joins.com', 'donga.com',  # 조선, 중앙, 동아
        'khan.co.kr', 'hani.co.kr',  # 경향, 한겨레
        'seoul.co.kr', 'mk.co.kr',  # 서울신문, 매일경제
        'ytn.co.kr', 'kbs.co.kr', 'sbs.co.kr', 'mbc.co.kr',  # 방송사
        'newsis.com', 'news1.kr', 'newspim.com',  # 뉴시스, 뉴스1, 뉴스핌
        'edaily.co.kr', 'hankyung.com', 'etnews.com',  # 이데일리, 한국경제, 전자신문
        'bloter.net', 'zdnet.co.kr', 'itworld.co.kr'  # IT 전문지
    }
    
    # 정부/공공기관 도메인
    GOV_DOMAINS = {
        'gov.kr', 'go.kr',  # 정부 도메인
        'molit.go.kr', 'mosf.go.kr', 'moe.go.kr',  # 각 부처
        'bok.or.kr', 'kostat.go.kr',  # 한국은행, 통계청
        'kdi.re.kr', 'kiep.go.kr',  # 정부 연구기관
        'nts.go.kr', 'customs.go.kr'  # 국세청, 관세청
    }
    
    @staticmethod
    def format_response_with_citations(text: str) -> str:
        """
        AI 응답에서 출처 정보를 추출하고 포맷팅
        
        Args:
            text: AI 응답 텍스트
            
        Returns:
            출처가 포맷팅된 텍스트
        """
        try:
            # URL 패턴 찾기
            url_pattern = r'https?://[^\s\)]+(?=[\s\)\]\n]|$)'
            urls = re.findall(url_pattern, text)
            
            if not urls:
                logger.info("No URLs found in response")
                return text
            
            # 중복 제거
            unique_urls = list(dict.fromkeys(urls))
            
            # 이미 출처 섹션이 있는지 확인
            if "📚 출처:" in text:
                logger.info("Citations already formatted")
                return text
            
            # 출처 섹션 생성
            citations = []
            for i, url in enumerate(unique_urls, 1):
                domain = CitationFormatter._extract_domain(url)
                trust_indicator = CitationFormatter._get_trust_indicator(domain)
                
                # 간단한 제목 추출 (실제로는 더 정교한 로직 필요)
                title = CitationFormatter._extract_title_from_url(url)
                
                citations.append(f"[{i}] {trust_indicator} {domain} - {title} ({url})")
            
            # 출처 섹션 추가
            citation_section = f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 출처:
{chr(10).join(citations)}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
            
            # 인라인 각주 추가 (간단한 버전)
            formatted_text = CitationFormatter._add_inline_citations(text, unique_urls)
            
            return formatted_text + citation_section
            
        except Exception as e:
            logger.error(f"Error formatting citations: {str(e)}")
            return text
    
    @staticmethod
    def _extract_domain(url: str) -> str:
        """URL에서 도메인 추출"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # www 제거
            if domain.startswith('www.'):
                domain = domain[4:]
                
            return domain
        except:
            return "알 수 없는 사이트"
    
    @staticmethod
    def _get_trust_indicator(domain: str) -> str:
        """도메인별 신뢰도 표시 이모지 반환"""
        # 정부/공공기관 확인
        for gov_domain in CitationFormatter.GOV_DOMAINS:
            if gov_domain in domain:
                return CitationFormatter.TRUST_INDICATORS['government']
        
        # 언론사 확인
        if domain in CitationFormatter.NEWS_DOMAINS:
            return CitationFormatter.TRUST_INDICATORS['news']
        
        # 기타 언론사 패턴 확인
        news_patterns = ['news', 'media', '신문', '방송', 'tv', 'radio']
        for pattern in news_patterns:
            if pattern in domain:
                return CitationFormatter.TRUST_INDICATORS['news']
        
        # 일반 웹사이트
        return CitationFormatter.TRUST_INDICATORS['general']
    
    @staticmethod
    def _extract_title_from_url(url: str) -> str:
        """URL에서 간단한 제목 추출 (실제로는 HTTP 요청으로 <title> 태그 추출 필요)"""
        try:
            # URL에서 파일명 추출
            parsed = urlparse(url)
            path = parsed.path
            
            if path and path != '/':
                # 마지막 경로 요소를 제목으로 사용
                title = path.split('/')[-1]
                if title:
                    # 파일 확장자 제거
                    if '.' in title:
                        title = title.rsplit('.', 1)[0]
                    
                    # URL 인코딩된 문자 간단히 처리
                    title = title.replace('%20', ' ').replace('_', ' ').replace('-', ' ')
                    
                    # 길이 제한
                    if len(title) > 50:
                        title = title[:47] + '...'
                    
                    return title
            
            # 도메인명을 제목으로 사용
            domain = CitationFormatter._extract_domain(url)
            return f"{domain} 페이지"
            
        except:
            return "웹 페이지"
    
    @staticmethod
    def _add_inline_citations(text: str, urls: List[str]) -> str:
        """텍스트에 인라인 각주 추가"""
        try:
            # 간단한 구현: 각 URL 뒤에 [숫자] 추가
            for i, url in enumerate(urls, 1):
                # URL 바로 뒤에 [숫자] 추가 (이미 있는 경우 건너뛰기)
                pattern = re.escape(url) + r'(?!\[\d+\])'
                replacement = f"{url}[{i}]"
                text = re.sub(pattern, replacement, text)
            
            return text
            
        except Exception as e:
            logger.error(f"Error adding inline citations: {str(e)}")
            return text


def format_citations(text: str) -> str:
    """편의 함수: 출처 포맷팅"""
    formatter = CitationFormatter()
    return formatter.format_response_with_citations(text)


# 사용 예시
if __name__ == "__main__":
    sample_text = """
    최근 대한민국의 경제 성장률은 2.5%를 기록했습니다. 
    이는 한국은행 https://bok.or.kr/news/2024/economic-report의 발표에 따른 것입니다.
    또한 연합뉴스 https://yna.co.kr/news/economy/latest에서도 관련 뉴스를 확인할 수 있습니다.
    """
    
    formatted = format_citations(sample_text)
    print(formatted)