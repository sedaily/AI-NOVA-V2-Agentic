// HTTP 기반 채팅 서비스
import { API_BASE_URL } from '../../../config';

class HttpChatService {
  constructor() {
    this.messageHandlers = new Set();
    this.connectionHandlers = new Set();
    this.conversationHistory = [];
    this.currentConversationId = null;
    this.baseUrl = API_BASE_URL;
  }

  async connect() {
    console.log("HTTP 채팅 서비스 연결");
    this.connectionHandlers.forEach((handler) => handler(true));
    return Promise.resolve();
  }

  async sendMessage(
    message,
    engineType = "T5",
    conversationId = null,
    conversationHistory = null,
    idempotencyKey = null
  ) {
    try {
      console.log("HTTP 메시지 전송:", { message, engineType });

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
          }, index * 50);
        });

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

  requestTitleSuggestions(conversation, engineType = "T5") {
    return Promise.resolve();
  }

  updateConversationHistory(messages) {
    this.conversationHistory = messages;
    console.log("대화 기록 업데이트:", messages.length, "개 메시지");
  }

  setConversationId(id) {
    this.currentConversationId = id;
    console.log("대화 ID 설정:", id);
  }

  addMessageHandler(handler) {
    this.messageHandlers.add(handler);
  }

  removeMessageHandler(handler) {
    this.messageHandlers.delete(handler);
  }

  addConnectionHandler(handler) {
    this.connectionHandlers.add(handler);
  }

  removeConnectionHandler(handler) {
    this.connectionHandlers.delete(handler);
  }

  isWebSocketConnected() {
    return true;
  }

  disconnect() {
    console.log("HTTP 채팅 서비스 연결 종료");
    this.messageHandlers.clear();
    this.connectionHandlers.clear();
    this.conversationHistory = [];
    this.currentConversationId = null;
    this.connectionHandlers.forEach((handler) => handler(false));
  }
}

const httpChatService = new HttpChatService();

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
