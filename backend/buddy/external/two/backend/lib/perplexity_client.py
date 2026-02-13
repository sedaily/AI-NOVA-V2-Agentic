"""
Perplexity API Client - 간단한 웹 검색 통합
"""
import os
import json
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

class PerplexityClient:
    """Perplexity API 클라이언트"""
    
    def __init__(self):
        self.api_key = os.environ.get('PERPLEXITY_API_KEY', '')
        self.api_url = "https://api.perplexity.ai/chat/completions"
        logger.info(f"PerplexityClient initialized with API key: {'Yes' if self.api_key else 'No'}")
        
    def search(self, query: str, enable: bool = True) -> Optional[str]:
        """웹 검색 수행"""
        if not enable or not self.api_key:
            return None
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "sonar-pro",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful search assistant. Provide concise, relevant search results in Korean."
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ],
                "temperature": 0.2,
                "max_tokens": 1000
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                search_result = result['choices'][0]['message']['content']
                logger.info(f"Perplexity search completed for: {query[:50]}...")
                return search_result
            else:
                logger.error(f"Perplexity API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error calling Perplexity API: {str(e)}")
            return None