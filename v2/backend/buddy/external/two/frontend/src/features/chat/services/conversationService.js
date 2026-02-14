// 대화 저장 및 관리 서비스
import { API_BASE_URL } from '../../../config';

class ConversationService {
  constructor() {
    this.userId = this.getUserId();
  }

  // 사용자 ID 가져오기 (인증된 사용자 정보 사용) - UUID 기반
  getUserId() {
    const userInfo = JSON.parse(localStorage.getItem("userInfo") || "{}");
    // Cognito sub (UUID)를 우선 사용 - DynamoDB 데이터와 일치
    return (
      userInfo.userId || userInfo.username || userInfo.email || "anonymous"
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
      };
      
      // 저장할 데이터 로그 (필요시 주석 해제)
      // console.log("💾 저장할 데이터:", {
      //   conversationId: dataToSave.conversationId,
      //   userId: dataToSave.userId,
      //   engineType: dataToSave.engineType,
      //   messageCount: dataToSave.messages?.length
      // });
      
      const response = await fetch(`${API_BASE_URL}/conversations`, {
        method: "POST",
        headers: this.getAuthHeaders(),
        body: JSON.stringify(dataToSave),
      });

      if (!response.ok) {
        throw new Error(`Failed to save conversation: ${response.statusText}`);
      }

      const data = await response.json();
      // console.log("💾 대화 저장 성공:", data);
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
        params.append("engineType", engineType); // engineType 파라미터 사용 (백엔드 API 스펙에 맞춤)
      }
      
      // console.log("📋 대화 목록 조회 파라미터:", {
      //   userId: currentUserId,
      //   engineType: engineType
      // });

      const response = await fetch(`${API_BASE_URL}/conversations?${params}`, {
        method: "GET",
        headers: this.getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error(`Failed to list conversations: ${response.statusText}`);
      }

      const data = await response.json();
      // console.log("📋 대화 목록 조회 성공:", data);
      return data.conversations || [];
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
      // console.log("📖 대화 조회 성공:", data);
      return data;
    } catch (error) {
      console.error("대화 조회 실패:", error);
      // 오류 발생 시 localStorage에서 조회
      return this.getConversationFromLocalStorage(conversationId);
    }
  }

  // 대화 제목 수정 (PATCH 요청)
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
            title: newTitle,
          }),
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to update title: ${response.statusText}`);
      }

      const data = await response.json();
      console.log("✏️ 제목 수정 API 응답:", data);
      
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
        // localStorage에 없는 경우 서버에서 가져온 대화이므로 새로 생성
        const currentUserId = this.getUserId();
        const newKey = `conversation_${conversationId}`;
        conversations[newKey] = {
          conversationId: conversationId,
          userId: currentUserId,
          title: newTitle,
          messages: [],
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString()
        };
        localStorage.setItem("conversations", JSON.stringify(conversations));
        console.log("✏️ localStorage에 새 대화 생성 및 제목 설정");
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
        // console.log("🗑️ 서버에서 대화 삭제 성공");
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

      // 이미 존재하는 대화인지 확인 (conversationId와 userId로 검색)
      const existingKey = Object.keys(conversations).find(
        (k) => conversations[k].conversationId === conversationId && 
               conversations[k].userId === this.userId
      );

      if (existingKey) {
        // 기존 대화 업데이트 (중복 방지)
        conversations[existingKey] = {
          ...conversations[existingKey],
          ...conversationData,
          userId: this.userId,
          updatedAt: new Date().toISOString(),
        };
        console.log("💾 기존 대화 업데이트:", conversationId);
      } else {
        // 새로운 대화 생성 - 일관된 키 형식 사용
        const key = `conversation_${conversationId}`;
        conversations[key] = {
          ...conversationData,
          conversationId,
          userId: this.userId,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        };
        console.log("💾 새 대화 생성:", conversationId);
      }

      localStorage.setItem("conversations", JSON.stringify(conversations));
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
        // console.log("🗑️ localStorage에서 삭제");
      }
    } catch (error) {
      console.error("localStorage 삭제 실패:", error);
    }
  }

  // 중복 대화 정리 (localStorage 정리)
  cleanupDuplicateConversations() {
    try {
      const conversations = JSON.parse(
        localStorage.getItem("conversations") || "{}"
      );
      
      const conversationMap = new Map();
      const keysToDelete = [];
      
      // conversationId별로 그룹화하여 중복 찾기
      Object.entries(conversations).forEach(([key, conv]) => {
        const convId = conv.conversationId;
        const userId = conv.userId;
        const uniqueKey = `${userId}_${convId}`;
        
        if (conversationMap.has(uniqueKey)) {
          // 중복 발견 - 더 최신 것을 유지
          const existing = conversationMap.get(uniqueKey);
          const existingTime = new Date(existing.conversation.updatedAt || existing.conversation.createdAt || 0);
          const currentTime = new Date(conv.updatedAt || conv.createdAt || 0);
          
          if (currentTime > existingTime) {
            // 현재 것이 더 최신 - 기존 것 삭제 예약
            keysToDelete.push(existing.key);
            conversationMap.set(uniqueKey, { key, conversation: conv });
          } else {
            // 기존 것이 더 최신 - 현재 것 삭제 예약
            keysToDelete.push(key);
          }
        } else {
          conversationMap.set(uniqueKey, { key, conversation: conv });
        }
      });
      
      // 중복된 키들 삭제
      keysToDelete.forEach(key => {
        delete conversations[key];
      });
      
      localStorage.setItem("conversations", JSON.stringify(conversations));
      console.log(`🧹 ${keysToDelete.length}개의 중복 대화 정리 완료`);
      
      return keysToDelete.length;
    } catch (error) {
      console.error("중복 대화 정리 실패:", error);
      return 0;
    }
  }

  // 대화 동기화 (localStorage → DynamoDB)
  async syncConversations() {
    try {
      // 먼저 중복 대화 정리
      this.cleanupDuplicateConversations();
      
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
export const cleanupDuplicateConversations = () => conversationService.cleanupDuplicateConversations();
