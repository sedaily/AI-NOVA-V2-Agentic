// Claude API 직접 연동 서비스
class ClaudeService {
  constructor() {
    this.apiKey = import.meta.env.VITE_CLAUDE_API_KEY;
    this.baseURL = 'https://api.anthropic.com/v1/messages';
    this.model = 'claude-opus-4-5-20251101';
  }

  // API 키 확인
  hasApiKey() {
    return !!this.apiKey && this.apiKey !== 'your_claude_api_key_here';
  }

  // 스트리밍 채팅 응답
  async streamChat(message, selectedModel, onChunk, onComplete, onError) {
    if (!this.hasApiKey()) {
      onError(new Error('Claude API 키가 설정되지 않았습니다. .env.local 파일에 VITE_CLAUDE_API_KEY를 설정해주세요.'));
      return;
    }

    try {
      console.log('🤖 Claude API 호출 시작:', { messageLength: message.length, model: selectedModel });

      // 개발 환경: 프록시 서버 사용
      const apiUrl = import.meta.env.DEV 
        ? 'http://127.0.0.1:5000/api/claude/chat'
        : `${import.meta.env.VITE_API_BASE_URL || 'https://pinjzwk0qi.execute-api.us-east-1.amazonaws.com/prod'}/api/claude/chat`;

      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: message,
          model: selectedModel || 'claude-opus-4-5-20251101'
        })
      });

      if (!response.ok) {
        const errorData = await response.text();
        console.error('Claude API 오류:', response.status, errorData);
        throw new Error(`Claude API 오류: ${response.status} - ${errorData}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let chunkIndex = 0;

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          console.log('✅ Claude API 스트리밍 완료');
          onComplete(chunkIndex);
          break;
        }

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim();
            
            if (data === '[DONE]') {
              onComplete(chunkIndex);
              return;
            }

            try {
              const parsed = JSON.parse(data);
              
              if (parsed.type === 'content_block_delta' && parsed.delta?.text) {
                onChunk(parsed.delta.text, chunkIndex);
                chunkIndex++;
              }
            } catch (parseError) {
              continue;
            }
          }
        }
      }
    } catch (error) {
      console.error('Claude API 스트리밍 오류:', error);
      onError(error);
    }
  }

  // 모의 스트리밍 응답 (개발용)
  simulateStreamingResponse(message, onChunk, onComplete) {
    const mockResponse = `안녕하세요! 업로드하신 파일을 확인했습니다.

파일 내용을 분석한 결과:
- 파일 형식: ${message.includes('pdf') ? 'PDF' : message.includes('image') ? '이미지' : '텍스트'}
- 내용 요약: 업로드된 파일의 주요 내용을 분석하여 답변드리겠습니다.

추가로 궁금한 점이 있으시면 언제든 말씀해 주세요!`;

    let index = 0;
    const words = mockResponse.split('');
    
    const interval = setInterval(() => {
      if (index < words.length) {
        onChunk(words[index], index);
        index++;
      } else {
        clearInterval(interval);
        onComplete(index);
      }
    }, 50); // 50ms마다 한 글자씩
  }

  // 일반 채팅 응답 (스트리밍 없음)
  async chat(message) {
    if (!this.hasApiKey()) {
      throw new Error('Claude API 키가 설정되지 않았습니다.');
    }

    try {
      const response = await fetch(this.baseURL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': this.apiKey,
          'anthropic-version': '2023-06-01'
        },
        body: JSON.stringify({
          model: this.model,
          max_tokens: 4000,
          messages: [
            {
              role: 'user',
              content: message
            }
          ]
        })
      });

      if (!response.ok) {
        const errorData = await response.text();
        throw new Error(`Claude API 오류: ${response.status} - ${errorData}`);
      }

      const data = await response.json();
      return data.content[0].text;
    } catch (error) {
      console.error('Claude API 오류:', error);
      throw error;
    }
  }
}

// 싱글톤 인스턴스
const claudeService = new ClaudeService();

export default claudeService;