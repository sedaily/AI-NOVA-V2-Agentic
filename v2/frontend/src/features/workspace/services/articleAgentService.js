/**
 * Article AI Agent Service
 * ArticleEditor 워크플로우를 위한 AI Agent 통합 서비스
 *
 * 프롬프트 매핑:
 * - W1: 보도자료 기사화 (Engine 11: 기업, Engine 22: 정부/공공)
 * - T1: TITLE-NOMICS 3.0 (제목 생성)
 * - P1: 교정 AI
 * - R1: 퇴고 시스템
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';
const CLAUDE_API_KEY = import.meta.env.VITE_CLAUDE_API_KEY;

// Agent 타입 정의
const AGENT_TYPES = {
  W1: 'press-release', // 보도자료 기사화
  T1: 'title-gen',     // 제목 생성
  P1: 'proofread',     // 교정
  R1: 'revise',        // 퇴고
};

// 기사 유형별 설정
const ARTICLE_TYPE_CONFIG = {
  daily: {
    name: '일보 작성',
    wordCount: '300~500자',
    style: '핵심 팩트 위주, 간결한 문체',
    prompt: `일보 기사를 작성해주세요.
- 분량: 300~500자
- 스타일: 핵심 팩트 위주, 간결한 문체
- 구조: 제목 + 리드문 + 본문 1~2문단`,
  },
  print: {
    name: '지면 기사',
    wordCount: '1000~1500자',
    style: '배경 설명 포함, 깊이있는 분석',
    prompt: `지면 기사를 작성해주세요.
- 분량: 1000~1500자
- 스타일: 배경 설명 포함, 깊이있는 분석
- 구조: 제목 + 부제 + 리드문 + 본문 + 전망`,
  },
  online: {
    name: '온라인 기사',
    wordCount: '800~1200자',
    style: 'SEO 최적화, 모바일 친화적',
    prompt: `온라인 기사를 작성해주세요.
- 분량: 800~1200자
- 스타일: SEO 최적화, 모바일 친화적
- 구조: 제목(50자 이내) + 리드문 + 소제목 포함 본문`,
  },
};

class ArticleAgentService {
  constructor() {
    this.apiKey = CLAUDE_API_KEY;
    this.baseURL = API_BASE_URL;
  }

  /**
   * API 키 확인
   */
  hasApiKey() {
    return !!this.apiKey && this.apiKey !== 'your_claude_api_key_here';
  }

  /**
   * Step 2: 보도자료 분석
   * W1 Agent를 사용하여 보도자료의 핵심 정보 추출
   */
  async analyzePressRelease(pressReleaseText, engineType = '11') {
    const systemPrompt = `당신은 서울경제신문의 AI 보도자료 분석 전문가입니다.

보도자료를 분석하여 다음 정보를 JSON 형식으로 추출해주세요:
1. summary: 핵심 요약 (2~3문장)
2. keyFacts: 주요 팩트 (배열, 최대 5개)
3. stakeholders: 관련 이해관계자 (배열)
4. economicImpact: 경제적 영향 분석
5. suggestedAngles: 추천 기사 관점 (배열, 최대 3개)
6. keywords: SEO 키워드 (배열, 최대 5개)

${engineType === '22' ? '정부/공공 보도자료입니다. 정치적 중립성을 유지하고 정치인 실명을 배제하세요.' : '기업 보도자료입니다. 투자자와 기업 관계자 관점에서 분석하세요.'}`;

    try {
      const response = await this._callClaudeAPI(systemPrompt, pressReleaseText);

      // JSON 파싱 시도
      try {
        const jsonMatch = response.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
          return JSON.parse(jsonMatch[0]);
        }
      } catch (e) {
        console.warn('JSON 파싱 실패, 원본 텍스트 반환');
      }

      return { rawAnalysis: response };
    } catch (error) {
      console.error('보도자료 분석 실패:', error);
      throw error;
    }
  }

  /**
   * Step 2: 트렌딩 토픽 관련 뉴스 검색
   * Perplexity API를 통한 웹 검색
   */
  async searchRelatedNews(topic) {
    try {
      const response = await fetch(`${this.baseURL}/api/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: `${topic} 최신 뉴스 동향`,
          enable: true,
        }),
      });

      if (!response.ok) {
        throw new Error(`검색 실패: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('관련 뉴스 검색 실패:', error);
      // 폴백: 모의 데이터 반환
      return {
        success: false,
        content: '검색 결과를 가져올 수 없습니다.',
        citations: [],
      };
    }
  }

  /**
   * Step 4: 기사 생성
   * W1 Agent를 사용하여 실제 기사 작성
   */
  async generateArticle(params) {
    const {
      pressRelease,
      topic,
      articleType,
      engineType = '11',
      additionalContext = '',
    } = params;

    const typeConfig = ARTICLE_TYPE_CONFIG[articleType];

    const systemPrompt = `당신은 서울경제신문의 AI 기자입니다.

${engineType === '22'
  ? `[정부/공공 보도자료 기사화 시스템 v2.0]
절대 규칙:
- 정치인(대통령, 장관, 국회의원) 실명 사용 금지
- 여당, 야당, 정당명 언급 금지
- 정치적 가치판단 표현 금지
- 경제적 영향 중심으로 분석`
  : `[기업 보도자료 기사화 시스템]
- 투자자와 기업 관계자 관점
- 경제/금융/산업 전문성
- 팩트 기반 정확한 분석`
}

${typeConfig.prompt}`;

    const userMessage = pressRelease
      ? `다음 보도자료를 기사로 작성해주세요:\n\n${pressRelease}${additionalContext ? `\n\n추가 컨텍스트:\n${additionalContext}` : ''}`
      : `다음 주제로 기사를 작성해주세요: ${topic}${additionalContext ? `\n\n추가 컨텍스트:\n${additionalContext}` : ''}`;

    try {
      return await this._callClaudeAPI(systemPrompt, userMessage);
    } catch (error) {
      console.error('기사 생성 실패:', error);
      throw error;
    }
  }

  /**
   * Step 4: 제목 생성
   * T1 TITLE-NOMICS Agent 사용
   */
  async generateTitles(articleContent, count = 5) {
    const systemPrompt = `당신은 TITLE-NOMICS 3.0, 경제 저널리즘의 창의적 혁명을 이끄는 AI 협업 시스템입니다.

기사 내용을 분석하여 ${count}가지 유형의 제목을 생성해주세요:

1. 저널리즘 충실형 - 핵심 팩트의 의외성과 전문적 함의
2. 균형잡힌 후킹형 - 정확한 분석과 호기심 자극의 균형
3. 클릭유도형 - 참신한 앵글과 감정적 임팩트
4. SEO/AEO 최적화형 - 검색 의도 최적화
5. 소셜미디어 공유형 - 공감과 확산을 위한 감성적 연결

각 제목은 다음 형식으로 출력해주세요:
1. [유형]: 제목 내용
2. [유형]: 제목 내용
...`;

    try {
      const response = await this._callClaudeAPI(systemPrompt, `다음 기사의 제목을 생성해주세요:\n\n${articleContent}`);
      return this._parseTitles(response);
    } catch (error) {
      console.error('제목 생성 실패:', error);
      throw error;
    }
  }

  /**
   * Step 4: 기사 교정
   * P1 교정 AI Agent 사용
   */
  async proofreadArticle(articleContent) {
    const systemPrompt = `당신은 서울경제신문의 AI 교정 전문가입니다.

기사를 검토하여 다음을 확인해주세요:
1. 맞춤법 및 문법 오류
2. 문장 구조 개선점
3. 팩트 체크 필요 항목
4. 서울경제 스타일 가이드 준수 여부

결과를 다음 JSON 형식으로 반환해주세요:
{
  "corrections": [{ "original": "원문", "corrected": "수정안", "reason": "이유" }],
  "suggestions": ["개선 제안 목록"],
  "factCheckItems": ["확인 필요 항목"],
  "styleIssues": ["스타일 이슈"],
  "overallScore": 85
}`;

    try {
      const response = await this._callClaudeAPI(systemPrompt, articleContent);

      try {
        const jsonMatch = response.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
          return JSON.parse(jsonMatch[0]);
        }
      } catch (e) {
        console.warn('JSON 파싱 실패');
      }

      return { rawFeedback: response };
    } catch (error) {
      console.error('교정 실패:', error);
      throw error;
    }
  }

  /**
   * Step 4: 기사 퇴고
   * R1 퇴고 Agent 사용
   */
  async reviseArticle(articleContent, feedback) {
    const systemPrompt = `당신은 서울경제신문의 AI 퇴고 전문가입니다.

기사를 다음 기준으로 개선해주세요:
1. 문장의 간결성과 명확성
2. 논리적 흐름 강화
3. 독자 가독성 향상
4. 서울경제 톤앤매너 적용

수정된 기사 전문을 반환해주세요.`;

    const userMessage = `기사 원문:\n${articleContent}\n\n${feedback ? `피드백:\n${feedback}` : ''}`;

    try {
      return await this._callClaudeAPI(systemPrompt, userMessage);
    } catch (error) {
      console.error('퇴고 실패:', error);
      throw error;
    }
  }

  /**
   * 스트리밍 기사 생성
   */
  async streamGenerateArticle(params, onChunk, onComplete, onError) {
    const {
      pressRelease,
      topic,
      articleType,
      engineType = '11',
      additionalContext = '',
    } = params;

    const typeConfig = ARTICLE_TYPE_CONFIG[articleType];

    const systemPrompt = `당신은 서울경제신문의 AI 기자입니다.
${typeConfig.prompt}`;

    const userMessage = pressRelease
      ? `다음 보도자료를 기사로 작성해주세요:\n\n${pressRelease}`
      : `다음 주제로 기사를 작성해주세요: ${topic}`;

    try {
      await this._streamClaudeAPI(systemPrompt, userMessage, onChunk, onComplete, onError);
    } catch (error) {
      onError(error);
    }
  }

  /**
   * Claude API 직접 호출 (비스트리밍)
   */
  async _callClaudeAPI(systemPrompt, userMessage) {
    if (!this.hasApiKey()) {
      throw new Error('Claude API 키가 설정되지 않았습니다.');
    }

    // 백엔드 프록시를 통한 호출
    const response = await fetch(`${this.baseURL}/api/claude/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: userMessage,
        systemPrompt: systemPrompt,
        model: 'claude-opus-4-5-20251101',
        apiKey: this.apiKey,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API 오류: ${response.status} - ${errorText}`);
    }

    const data = await response.json();
    return data.content?.[0]?.text || data.response || '';
  }

  /**
   * Claude API 스트리밍 호출
   */
  async _streamClaudeAPI(systemPrompt, userMessage, onChunk, onComplete, onError) {
    try {
      const response = await fetch(`${this.baseURL}/api/claude/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          systemPrompt: systemPrompt,
          model: 'claude-opus-4-5-20251101',
          apiKey: this.apiKey,
          stream: true,
        }),
      });

      if (!response.ok) {
        throw new Error(`API 오류: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let index = 0;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        onChunk(chunk, index);
        index++;
      }

      onComplete(index);
    } catch (error) {
      onError(error);
    }
  }

  /**
   * 제목 파싱 헬퍼
   */
  _parseTitles(response) {
    const titles = [];
    const lines = response.split('\n').filter(line => line.trim());

    for (const line of lines) {
      const match = line.match(/^\d+\.\s*\[([^\]]+)\]:\s*(.+)$/);
      if (match) {
        titles.push({
          type: match[1],
          title: match[2].trim(),
        });
      }
    }

    return titles.length > 0 ? titles : [{ type: 'default', title: response }];
  }
}

// 싱글톤 인스턴스
const articleAgentService = new ArticleAgentService();

export default articleAgentService;
export { ARTICLE_TYPE_CONFIG, AGENT_TYPES };
