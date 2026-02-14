// HTTP 기반 채팅 서비스
import { HTTP_CHAT_URL } from '../../../config';

class HttpChatService {
  constructor() {
    this.messageHandlers = new Set();
    this.connectionHandlers = new Set();
    this.conversationHistory = [];
    this.currentConversationId = null;
    this.baseUrl = HTTP_CHAT_URL;
  }

  // 연결 시뮬레이션
  async connect() {
    console.log("HTTP 채팅 서비스 연결");
    this.connectionHandlers.forEach((handler) => handler(true));
    return Promise.resolve();
  }

  // 메시지 전송
  async sendMessage(
    message,
    engineType = "11",
    conversationId = null,
    conversationHistory = null,
    idempotencyKey = null
  ) {
    try {
      console.log("📤 HTTP 메시지 전송:", { message, engineType });
      
      // AI 시작 신호
      this.messageHandlers.forEach((handler) => {
        handler({
          type: "ai_start",
          timestamp: new Date().toISOString()
        });
      });

      const response = await fetch(`${this.baseUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message,
          engineType: engineType,
          conversationId: conversationId
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.type === 'error') {
        this.messageHandlers.forEach((handler) => {
          handler({
            type: "error",
            message: data.message
          });
        });
      } else {
        // 응답을 청크로 시뮬레이션
        const responseText = data.message;
        const words = responseText.split(' ');
        
        words.forEach((word, index) => {
          setTimeout(() => {
            this.messageHandlers.forEach((handler) => {
              handler({
                type: "ai_chunk",
                chunk: word + ' ',
                chunk_index: index
              });
            });
          }, index * 50); // 50ms 간격으로 단어별 출력
        });

        // 완료 신호
        setTimeout(() => {
          this.messageHandlers.forEach((handler) => {
            handler({
              type: "chat_end",
              total_chunks: words.length,
              engine: engineType
            });
          });
        }, words.length * 50 + 100);
      }

    } catch (error) {
      console.error("HTTP 요청 실패:", error);
      this.messageHandlers.forEach((handler) => {
        handler({
          type: "error",
          message: `연결 오류: ${error.message}`
        });
      });
    }
  }

  // 제목 제안 요청
  requestTitleSuggestions(conversation, engineType = "11") {
    return Promise.resolve();
  }

  // 대화 기록 업데이트
  updateConversationHistory(messages) {
    this.conversationHistory = messages;
    console.log("💬 대화 기록 업데이트:", messages.length, "개 메시지");
  }

  // 대화 ID 설정
  setConversationId(id) {
    this.currentConversationId = id;
    console.log("🆔 대화 ID 설정:", id);
  }

  // 메시지 핸들러 등록
  addMessageHandler(handler) {
    this.messageHandlers.add(handler);
  }

  // 메시지 핸들러 제거
  removeMessageHandler(handler) {
    this.messageHandlers.delete(handler);
  }

  // 연결 상태 핸들러 등록
  addConnectionHandler(handler) {
    this.connectionHandlers.add(handler);
  }

  // 연결 상태 핸들러 제거
  removeConnectionHandler(handler) {
    this.connectionHandlers.delete(handler);
  }

  // 연결 상태 확인
  isWebSocketConnected() {
    return true; // HTTP는 항상 연결된 것으로 간주
  }

  // 연결 종료
  disconnect() {
    console.log("HTTP 채팅 서비스 연결 종료");
    this.messageHandlers.clear();
    this.connectionHandlers.clear();
    this.conversationHistory = [];
    this.currentConversationId = null;
    this.connectionHandlers.forEach((handler) => handler(false));
  }
}

// 싱글톤 인스턴스
const httpChatService = new HttpChatService();

// 내보낼 함수들
export const connectWebSocket = () => httpChatService.connect();
export const disconnectWebSocket = () => httpChatService.disconnect();
export const sendChatMessage = (
  message,
  engineType,
  conversationHistory,
  conversationId,
  idempotencyKey
) =>
  httpChatService.sendMessage(
    message,
    engineType,
    conversationId,
    conversationHistory,
    idempotencyKey
  );
export const isWebSocketConnected = () =>
  httpChatService.isWebSocketConnected();
export const addMessageHandler = (handler) =>
  httpChatService.addMessageHandler(handler);
export const removeMessageHandler = (handler) =>
  httpChatService.removeMessageHandler(handler);
export const addConnectionHandler = (handler) =>
  httpChatService.addConnectionHandler(handler);
export const removeConnectionHandler = (handler) =>
  httpChatService.removeConnectionHandler(handler);
export const requestTitleSuggestions = (conversation, engineType) =>
  httpChatService.requestTitleSuggestions(conversation, engineType);
export const updateConversationHistory = (messages) =>
  httpChatService.updateConversationHistory(messages);
export const setConversationId = (id) => httpChatService.setConversationId(id);

export default httpChatService;