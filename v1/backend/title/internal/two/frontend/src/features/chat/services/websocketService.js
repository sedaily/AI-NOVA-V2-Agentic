// WebSocket 서비스
class WebSocketService {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 3000;
    this.messageHandlers = new Set();
    this.connectionHandlers = new Set();
    this.isConnecting = false;
    this.messageQueue = [];
    this.isReconnecting = false;
    this.conversationHistory = [];
    this.currentConversationId = null;
  }

  // WebSocket 연결
  async connect() {
    if (
      this.isConnecting ||
      (this.ws && this.ws.readyState === WebSocket.OPEN)
    ) {
      console.log("이미 연결되어 있거나 연결 중입니다.");
      return Promise.resolve();
    }

    this.isConnecting = true;

    return new Promise(async (resolve, reject) => {
      try {
        // JWT 토큰 가져오기
        const authService = (await import("../../auth/services/authService")).default;
        const token = await authService.getAuthToken();

        let wsUrl = import.meta.env.VITE_WEBSOCKET_URL || '';

        // 토큰이 있으면 쿼리 파라미터로 추가
        if (token) {
          wsUrl += `?token=${encodeURIComponent(token)}`;
        }

        console.log("WebSocket 연결 시도:", wsUrl.split("?")[0]); // URL만 로그 (토큰 제외)

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log("WebSocket 연결 성공");
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.isReconnecting = false;

          // 연결 핸들러 호출
          this.connectionHandlers.forEach((handler) => handler(true));

          // 큐에 있는 메시지 전송
          this.processMessageQueue();

          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log("WebSocket 메시지 수신:", data);

            // 모든 메시지 핸들러에 전달
            this.messageHandlers.forEach((handler) => {
              try {
                handler(data);
              } catch (error) {
                console.error("메시지 핸들러 오류:", error);
              }
            });
          } catch (error) {
            console.error("메시지 파싱 오류:", error, event.data);
          }
        };

        this.ws.onerror = (error) => {
          console.error("WebSocket 오류:", error);
          this.isConnecting = false;
        };

        this.ws.onclose = (event) => {
          console.log("WebSocket 연결 종료:", event.code, event.reason);
          this.isConnecting = false;

          // 연결 핸들러 호출
          this.connectionHandlers.forEach((handler) => handler(false));

          // 자동 재연결 (정상 종료가 아닌 경우)
          if (event.code !== 1000 && event.code !== 1001) {
            this.handleReconnect();
          }
        };

        // 30초 타임아웃
        setTimeout(() => {
          if (this.isConnecting) {
            console.error("WebSocket 연결 타임아웃");
            this.isConnecting = false;
            this.ws?.close();
            reject(new Error("Connection timeout"));
          }
        }, 30000);
      } catch (error) {
        console.error("WebSocket 연결 실패:", error);
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  // 재연결 처리
  handleReconnect() {
    if (
      this.isReconnecting ||
      this.reconnectAttempts >= this.maxReconnectAttempts
    ) {
      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        console.error("최대 재연결 시도 횟수 초과");
      }
      return;
    }

    this.isReconnecting = true;
    this.reconnectAttempts++;

    console.log(
      `재연결 시도 ${this.reconnectAttempts}/${this.maxReconnectAttempts} (${
        this.reconnectDelay / 1000
      }초 후)`
    );

    setTimeout(() => {
      this.connect()
        .then(() => {
          console.log("재연결 성공");
          this.isReconnecting = false;
        })
        .catch(() => {
          console.error("재연결 실패");
          this.isReconnecting = false;
          this.handleReconnect();
        });
    }, this.reconnectDelay);
  }

  // 메시지 청크 분할 함수
  chunkMessage(message, maxSize = 100000) {
    // 100KB 단위로 분할
    const chunks = [];
    const messageBytes = new TextEncoder().encode(message);

    if (messageBytes.length <= maxSize) {
      return [message];
    }

    // UTF-8 안전하게 분할
    let currentChunk = "";
    let currentSize = 0;
    const lines = message.split("\n");

    for (const line of lines) {
      const lineBytes = new TextEncoder().encode(line + "\n");
      if (currentSize + lineBytes.length > maxSize && currentChunk) {
        chunks.push(currentChunk);
        currentChunk = line + "\n";
        currentSize = lineBytes.length;
      } else {
        currentChunk += line + "\n";
        currentSize += lineBytes.length;
      }
    }

    if (currentChunk) {
      chunks.push(currentChunk);
    }

    return chunks;
  }

  // 메시지 전송 (청크 지원)
  sendMessage(
    message,
    engineType = "T5",
    conversationId = null,
    conversationHistory = null,
    idempotencyKey = null
  ) {
    return new Promise((resolve, reject) => {
      if (!this.isWebSocketConnected()) {
        console.error("WebSocket이 연결되지 않았습니다.");
        this.messageQueue.push({
          message,
          engineType,
          conversationId,
          conversationHistory,
          idempotencyKey,
          resolve,
          reject,
        });
        this.connect();
        return;
      }

      try {
        // 사용자 정보 가져오기
        const userInfo = JSON.parse(localStorage.getItem("userInfo") || "{}");
        // userId를 우선 사용하되, 없으면 email 또는 username 사용
        const userId =
          userInfo.userId || userInfo.email || userInfo.username || "anonymous";

        // 사용자 역할 가져오기
        const userRole = localStorage.getItem("userRole") || "user";

        // idempotencyKey가 없으면 생성
        const messageIdempotencyKey = idempotencyKey || crypto.randomUUID();

        // 대화 기록 처리 - 전달받은 히스토리를 우선 사용
        const historyToUse = conversationHistory || this.conversationHistory;
        console.log("대화 히스토리 처리:", {
          receivedHistory: conversationHistory ? conversationHistory.length : 0,
          internalHistory: this.conversationHistory.length,
          usingWhich: conversationHistory ? "received" : "internal",
        });

        const processedHistory = historyToUse.map((msg) => {
          const content =
            typeof msg.content === "object" && msg.content.text
              ? msg.content.text
              : typeof msg.content === "string"
              ? msg.content
              : "";

          return {
            role: msg.type === "user" ? "user" : "assistant",
            content: content,
            timestamp: msg.timestamp,
          };
        });

        // 메시지가 너무 큰 경우 청크로 분할
        const messageChunks = this.chunkMessage(message);

        if (messageChunks.length > 1) {
          console.log(
            `대용량 메시지를 ${messageChunks.length}개 청크로 분할 전송`
          );

          // 청크 전송
          messageChunks.forEach((chunk, index) => {
            const payload = {
              action: "sendMessage",
              message: chunk,
              engineType: engineType,
              conversationId: conversationId,
              userId: userId,
              userRole: userRole,
              idempotencyKey: messageIdempotencyKey,
              timestamp: new Date().toISOString(),
              conversationHistory: index === 0 ? processedHistory : [], // 첫 청크에만 히스토리 포함
              chunkInfo: {
                total: messageChunks.length,
                current: index + 1,
                isFirst: index === 0,
                isLast: index === messageChunks.length - 1,
              },
            };

            console.log(
              `청크 ${index + 1}/${messageChunks.length} 전송 (${
                chunk.length
              } 문자)`
            );
            this.ws.send(JSON.stringify(payload));
          });
        } else {
          // 일반 전송
          const payload = {
            action: "sendMessage",
            message: message,
            engineType: engineType,
            conversationId: conversationId,
            userId: userId,
            userRole: userRole,
            idempotencyKey: messageIdempotencyKey,
            timestamp: new Date().toISOString(),
            conversationHistory: processedHistory,
          };

          console.log("📤 WebSocket 메시지 전송:", {
            messageLength: message.length,
            engineType,
            conversationId: conversationId || "new_conversation",
            historyLength: processedHistory.length,
            history: processedHistory.slice(-3).map((h) => ({
              role: h.role,
              preview: h.content.substring(0, 50) + "...",
            })),
          });

          this.ws.send(JSON.stringify(payload));
        }

        resolve();
      } catch (error) {
        console.error("메시지 전송 실패:", error);
        reject(error);
      }
    });
  }

  // 제목 제안 요청
  requestTitleSuggestions(conversation, engineType = "T5") {
    return new Promise((resolve, reject) => {
      if (!this.isWebSocketConnected()) {
        reject(new Error("WebSocket not connected"));
        return;
      }

      try {
        const payload = {
          action: "generateTitles",
          conversation: conversation,
          engineType: engineType,
          timestamp: new Date().toISOString(),
        };

        console.log("📤 제목 생성 요청:", payload);
        this.ws.send(JSON.stringify(payload));
        resolve();
      } catch (error) {
        console.error("제목 요청 전송 실패:", error);
        reject(error);
      }
    });
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

  // 메시지 큐 처리
  processMessageQueue() {
    while (this.messageQueue.length > 0) {
      const { message, engineType, conversationId, resolve, reject } =
        this.messageQueue.shift();
      this.sendMessage(message, engineType, conversationId)
        .then(resolve)
        .catch(reject);
    }
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

  // WebSocket 연결 상태 확인
  isWebSocketConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN;
  }

  // WebSocket 연결 종료
  disconnect() {
    if (this.ws) {
      console.log("WebSocket 연결 종료 요청");
      this.ws.close(1000, "Normal closure");
      this.ws = null;
    }
    this.messageHandlers.clear();
    this.connectionHandlers.clear();
    this.messageQueue = [];
    this.conversationHistory = [];
    this.currentConversationId = null;
  }
}

// 싱글톤 인스턴스
const webSocketService = new WebSocketService();

// 내보낼 함수들
export const connectWebSocket = () => webSocketService.connect();
export const disconnectWebSocket = () => webSocketService.disconnect();
export const sendChatMessage = (
  message,
  engineType,
  conversationHistory,
  conversationId,
  idempotencyKey
) =>
  webSocketService.sendMessage(
    message,
    engineType,
    conversationId,
    conversationHistory,
    idempotencyKey
  );
export const isWebSocketConnected = () =>
  webSocketService.isWebSocketConnected();
export const addMessageHandler = (handler) =>
  webSocketService.addMessageHandler(handler);
export const removeMessageHandler = (handler) =>
  webSocketService.removeMessageHandler(handler);
export const addConnectionHandler = (handler) =>
  webSocketService.addConnectionHandler(handler);
export const removeConnectionHandler = (handler) =>
  webSocketService.removeConnectionHandler(handler);
export const requestTitleSuggestions = (conversation, engineType) =>
  webSocketService.requestTitleSuggestions(conversation, engineType);
export const updateConversationHistory = (messages) =>
  webSocketService.updateConversationHistory(messages);
export const setConversationId = (id) => webSocketService.setConversationId(id);

export default webSocketService;
