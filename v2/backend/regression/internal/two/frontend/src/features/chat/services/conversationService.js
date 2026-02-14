// 대화 저장 및 관리 서비스

// Conversation API 엔드포인트 - API Gateway 사용
// 환경 변수를 사용하거나 기본값 사용
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

class ConversationService {
  constructor() {
    this.userId = this.getUserId();
  }

  // 프론트엔드 엔진 타입을 백엔드 엔진 타입으로 매핑
  mapEngineTypeForAPI(frontendEngineType) {
    const engineMapping = {
      '11': 'C1',
      '22': 'C2'
    };
    return engineMapping[frontendEngineType] || frontendEngineType;
  }

  // 백엔드 엔진 타입을 프론트엔드 엔진 타입으로 매핑
  mapEngineTypeFromAPI(backendEngineType) {
    const engineMapping = {
      'C1': '11',
      'C2': '22'
    };
    return engineMapping[backendEngineType] || backendEngineType;
  }

  // 사용자 ID 가져오기 (인증된 사용자 정보 사용)
  getUserId() {
    const userInfo = JSON.parse(localStorage.getItem("userInfo") || "{}");
    // UUID(username)를 우선 사용하되, 없으면 userId 또는 email 사용
    return (
      userInfo.username || userInfo.userId || userInfo.email || "anonymous"
    );
  }

  // 인증 헤더 생성
  getAuthHeaders() {
    const token = localStorage.getItem("authToken");
    const headers = {
      "Content-Type": "application/json",
    };

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    return headers;
  }

  // 대화 저장
  async saveConversation(conversationData) {
    try {
      // conversationData에 이미 userId가 있으면 그것을 사용, 없으면 this.userId 사용
      const dataToSave = {
        ...conversationData,
        userId: conversationData.userId || this.getUserId(), // getUserId() 호출하여 최신 userId 가져오기
        engineType: this.mapEngineTypeForAPI(conversationData.engineType), // 백엔드용 엔진 타입으로 변환
      };
      
      console.log("💾 저장할 데이터:", {
        conversationId: dataToSave.conversationId,
        userId: dataToSave.userId,
        engineType: dataToSave.engineType,
        messageCount: dataToSave.messages?.length
      });
      
      const response = await fetch(`${API_BASE_URL}/conversations`, {
        method: "POST",
        headers: this.getAuthHeaders(),
        body: JSON.stringify(dataToSave),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('💥 API 응답 에러:', {
          status: response.status,
          statusText: response.statusText,
          body: errorText
        });
        throw new Error(`Failed to save conversation: ${response.statusText} - ${errorText}`);
      }

      const data = await response.json();
      console.log("💾 대화 저장 성공:", data);
      return data;
    } catch (error) {
      console.error("대화 저장 실패:", error);
      // 오류 발생 시 localStorage에 백업
      this.saveToLocalStorage(conversationData);
      throw error;
    }
  }

  // 대화 목록 조회
  async listConversations(engineType = null) {
    try {
      const currentUserId = this.getUserId(); // 최신 userId 가져오기
      const params = new URLSearchParams({
        userId: currentUserId,
      });

      if (engineType) {
        params.append("engineType", this.mapEngineTypeForAPI(engineType)); // 백엔드용 엔진 타입으로 변환
      }
      
      console.log("📋 대화 목록 조회 파라미터:", {
        userId: currentUserId,
        engineType: engineType
      });

      const response = await fetch(`${API_BASE_URL}/conversations?${params}`, {
        method: "GET",
        headers: this.getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error(`Failed to list conversations: ${response.statusText}`);
      }

      const data = await response.json();
      console.log("📋 대화 목록 조회 성공:", data);

      // 백엔드에서 받은 데이터의 엔진 타입을 프론트엔드용으로 변환
      const conversations = (data.conversations || []).map(conv => ({
        ...conv,
        engineType: this.mapEngineTypeFromAPI(conv.engineType)
      }));

      return conversations;
    } catch (error) {
      console.error("대화 목록 조회 실패:", error);
      // 오류 발생 시 localStorage에서 조회
      return this.getFromLocalStorage(engineType);
    }
  }

  // 특정 대화 조회
  async getConversation(conversationId) {
    try {
      const response = await fetch(
        `${API_BASE_URL}/conversations/${conversationId}`,
        {
          method: "GET",
          headers: this.getAuthHeaders(),
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to get conversation: ${response.statusText}`);
      }

      const data = await response.json();
      console.log("📖 대화 조회 성공:", data);

      // 엔진 타입을 프론트엔드용으로 변환
      if (data && data.engineType) {
        data.engineType = this.mapEngineTypeFromAPI(data.engineType);
      }

      return data;
    } catch (error) {
      console.error("대화 조회 실패:", error);
      // 오류 발생 시 localStorage에서 조회
      return this.getConversationFromLocalStorage(conversationId);
    }
  }

  // 대화 제목 수정
  async updateConversationTitle(conversationId, newTitle) {
    try {
      const response = await fetch(
        `${API_BASE_URL}/conversations/${conversationId}`,
        {
          method: "PATCH",
          headers: {
            ...this.getAuthHeaders(),
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            userId: this.userId,
            title: newTitle,
          }),
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to update title: ${response.statusText}`);
      }

      const data = await response.json();
      console.log("✏️ 제목 수정 성공:", data);
      
      // localStorage도 업데이트
      this.updateLocalStorageTitle(conversationId, newTitle);
      
      return data;
    } catch (error) {
      console.error("제목 수정 실패:", error);
      // 오류 발생 시 localStorage만 업데이트
      this.updateLocalStorageTitle(conversationId, newTitle);
      throw error;
    }
  }

  // localStorage 제목 업데이트
  updateLocalStorageTitle(conversationId, newTitle) {
    try {
      // conversations는 object 형태로 저장되어 있음
      const conversations = JSON.parse(localStorage.getItem("conversations") || "{}");
      
      // conversationId로 해당 대화를 찾음
      const key = Object.keys(conversations).find(
        k => conversations[k].conversationId === conversationId
      );
      
      if (key && conversations[key]) {
        conversations[key].title = newTitle;
        conversations[key].updatedAt = new Date().toISOString();
        localStorage.setItem("conversations", JSON.stringify(conversations));
        console.log("✏️ localStorage 제목 업데이트 성공");
      } else {
        console.warn("localStorage에서 해당 대화를 찾을 수 없음:", conversationId);
      }
    } catch (error) {
      console.error("localStorage 제목 업데이트 실패:", error);
    }
  }

  // 대화 삭제
  async deleteConversation(conversationId) {
    try {
      const params = new URLSearchParams({
        userId: this.userId,
      });

      const response = await fetch(
        `${API_BASE_URL}/conversations/${conversationId}?${params}`,
        {
          method: "DELETE",
          headers: this.getAuthHeaders(),
        }
      );

      if (!response.ok) {
        console.warn("서버에서 삭제 실패, localStorage에서만 삭제 시도");
      } else {
        console.log("🗑️ 서버에서 대화 삭제 성공");
      }

      // localStorage에서도 삭제 (서버 삭제 실패해도 로컬은 삭제)
      this.deleteFromLocalStorage(conversationId);

      // 대화 히스토리도 삭제
      const conversations = JSON.parse(
        localStorage.getItem("conversations") || "{}"
      );
      const conv = Object.values(conversations).find(
        (c) => c.conversationId === conversationId
      );
      if (conv && conv.engineType) {
        const historyKey = `chat_history_${conv.engineType}`;
        const history = localStorage.getItem(historyKey);
        if (history) {
          const messages = JSON.parse(history);
          // 해당 대화의 메시지만 제거
          const filteredMessages = messages.filter(
            (m) => !m.conversationId || m.conversationId !== conversationId
          );
          if (filteredMessages.length === 0) {
            localStorage.removeItem(historyKey);
          } else {
            localStorage.setItem(historyKey, JSON.stringify(filteredMessages));
          }
        }
      }

      return true;
    } catch (error) {
      console.error("대화 삭제 중 오류:", error);
      // 서버 오류여도 localStorage는 삭제
      this.deleteFromLocalStorage(conversationId);
      return true;
    }
  }

  // 자동 저장 (debounced)
  autoSave(conversationData) {
    // 이전 타이머가 있으면 취소
    if (this.saveTimer) {
      clearTimeout(this.saveTimer);
    }

    // 3초 후에 저장 (localStorage만 사용)
    this.saveTimer = setTimeout(() => {
      // API 호출 대신 localStorage에만 저장
      this.saveToLocalStorage(conversationData);
    }, 3000);
  }

  // === localStorage 백업 메서드들 ===

  saveToLocalStorage(conversationData) {
    try {
      const conversations = JSON.parse(
        localStorage.getItem("conversations") || "{}"
      );
      const conversationId =
        conversationData.conversationId || crypto.randomUUID();
      const key = `conversation_${conversationData.engineType}_${conversationId}`;

      // 이미 존재하는 대화인지 확인
      const existingKey = Object.keys(conversations).find(
        (k) => conversations[k].conversationId === conversationId
      );

      if (existingKey) {
        // 기존 대화 업데이트 (중복 방지)
        conversations[existingKey] = {
          ...conversations[existingKey],
          ...conversationData,
          userId: this.userId,
          updatedAt: new Date().toISOString(),
        };
      } else {
        // 새로운 대화 생성
        conversations[key] = {
          ...conversationData,
          conversationId,
          userId: this.userId,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        };
      }

      localStorage.setItem("conversations", JSON.stringify(conversations));
      console.log("💾 localStorage에 저장:", existingKey ? "업데이트" : "신규");
    } catch (error) {
      console.error("localStorage 저장 실패:", error);
    }
  }

  getFromLocalStorage(engineType = null) {
    try {
      const conversations = JSON.parse(
        localStorage.getItem("conversations") || "{}"
      );
      let conversationList = Object.values(conversations);

      // 사용자 필터링
      conversationList = conversationList.filter(
        (conv) => conv.userId === this.userId
      );

      // 엔진 타입 필터링
      if (engineType) {
        conversationList = conversationList.filter(
          (conv) => conv.engineType === engineType
        );
      }

      // 최신순 정렬
      conversationList.sort(
        (a, b) => new Date(b.updatedAt) - new Date(a.updatedAt)
      );

      return conversationList;
    } catch (error) {
      console.error("localStorage 조회 실패:", error);
      return [];
    }
  }

  getConversationFromLocalStorage(conversationId) {
    try {
      const conversations = JSON.parse(
        localStorage.getItem("conversations") || "{}"
      );
      const conversation = Object.values(conversations).find(
        (conv) =>
          conv.conversationId === conversationId && conv.userId === this.userId
      );
      return conversation || null;
    } catch (error) {
      console.error("localStorage 조회 실패:", error);
      return null;
    }
  }

  deleteFromLocalStorage(conversationId) {
    try {
      const conversations = JSON.parse(
        localStorage.getItem("conversations") || "{}"
      );
      const key = Object.keys(conversations).find(
        (k) =>
          conversations[k].conversationId === conversationId &&
          conversations[k].userId === this.userId
      );
      if (key) {
        delete conversations[key];
        localStorage.setItem("conversations", JSON.stringify(conversations));
        console.log("🗑️ localStorage에서 삭제");
      }
    } catch (error) {
      console.error("localStorage 삭제 실패:", error);
    }
  }

  // 대화 동기화 (localStorage → DynamoDB)
  async syncConversations() {
    try {
      const localConversations = this.getFromLocalStorage();
      console.log(`🔄 ${localConversations.length}개 대화 동기화 시작`);

      for (const conversation of localConversations) {
        try {
          await this.saveConversation(conversation);
        } catch (error) {
          console.error(
            "대화 동기화 실패:",
            conversation.conversationId,
            error
          );
        }
      }

      console.log("✅ 대화 동기화 완료");
    } catch (error) {
      console.error("대화 동기화 실패:", error);
    }
  }
}

// 싱글톤 인스턴스
const conversationService = new ConversationService();

export default conversationService;

// 편의 함수들
export const saveConversation = (data) =>
  conversationService.saveConversation(data);
export const listConversations = (engineType) =>
  conversationService.listConversations(engineType);
export const getConversation = (id) => conversationService.getConversation(id);
export const deleteConversation = (id) =>
  conversationService.deleteConversation(id);
export const updateConversationTitle = (id, title) =>
  conversationService.updateConversationTitle(id, title);
export const autoSaveConversation = (data) =>
  conversationService.autoSave(data);
export const syncConversations = () => conversationService.syncConversations();
