// 사용량 추적 서비스 (DynamoDB 연동)
// Shared service for chat and dashboard features
import { API_BASE_URL } from "../../config";

// Usage API 전용 엔드포인트 (DynamoDB 연동)
const USAGE_API_BASE_URL = import.meta.env.VITE_USAGE_API_URL || '';

// 사용자 정보 가져오기 헬퍼 함수
const getCurrentUser = () => {
  try {
    const userInfo = JSON.parse(localStorage.getItem("userInfo") || "{}");
    let userPlan = localStorage.getItem("userPlan");
    if (!userPlan) {
      userPlan = localStorage.getItem("userRole") === "admin" ? "premium" : "free";
    }

    return {
      userId: userInfo.username || userInfo.email || "anonymous",
      plan: userPlan,
    };
  } catch (error) {
    console.error("사용자 정보 파싱 실패:", error);
    return { userId: "anonymous", plan: "free" };
  }
};

// 인증 헤더 생성
const getAuthHeaders = () => {
  const token = localStorage.getItem("authToken");
  const headers = { "Content-Type": "application/json" };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
};

// 플랜별 제한 설정
const PLAN_LIMITS = {
  free: {
    T5: {
      monthlyTokens: 10000,
      dailyMessages: 20,
      maxTokensPerMessage: 1000,
    },
    H8: {
      monthlyTokens: 10000,
      dailyMessages: 20,
      maxTokensPerMessage: 1000,
    },
  },
  basic: {
    T5: {
      monthlyTokens: 100000,
      dailyMessages: 100,
      maxTokensPerMessage: 2000,
    },
    H8: {
      monthlyTokens: 100000,
      dailyMessages: 100,
      maxTokensPerMessage: 2000,
    },
  },
  premium: {
    T5: {
      monthlyTokens: 500000,
      dailyMessages: 500,
      maxTokensPerMessage: 4000,
    },
    H8: {
      monthlyTokens: 500000,
      dailyMessages: 500,
      maxTokensPerMessage: 4000,
    },
  },
};

// 토큰 계산 유틸리티 (간단한 추정치)
export const estimateTokens = (text) => {
  if (!text) return 0;

  const koreanChars = (text.match(/[가-힣]/g) || []).length;
  const englishChars = (text.match(/[a-zA-Z]/g) || []).length;
  const otherChars = text.length - koreanChars - englishChars;

  const koreanTokens = Math.ceil(koreanChars / 2.5);
  const englishTokens = Math.ceil(englishChars / 4);
  const otherTokens = Math.ceil(otherChars / 3);

  return koreanTokens + englishTokens + otherTokens;
};

// 글자 수 계산
export const countCharacters = (text) => {
  return text ? text.length : 0;
};

// 로컬 스토리지 키
const USAGE_KEY = "user_usage_data";
const USER_PROFILE_KEY = "user_profile";

// 사용자 프로필 가져오기
export const getUserProfile = () => {
  try {
    const stored = localStorage.getItem(USER_PROFILE_KEY);
    if (!stored) {
      return {
        userId: localStorage.getItem("userId") || "anonymous",
        currentPlan: "free",
        signupDate: new Date().toISOString(),
        planStartDate: new Date().toISOString(),
      };
    }
    return JSON.parse(stored);
  } catch (error) {
    console.error("프로필 로드 실패:", error);
    return {
      currentPlan: "free",
    };
  }
};

// 사용자 플랜 설정
export const setUserPlan = (plan) => {
  const profile = getUserProfile();
  profile.currentPlan = plan;
  profile.planStartDate = new Date().toISOString();
  localStorage.setItem(USER_PROFILE_KEY, JSON.stringify(profile));
  return profile;
};

// 사용량 데이터 초기화
const initializeUsageData = () => {
  const currentMonth = new Date().toISOString().slice(0, 7);
  const today = new Date().toISOString().slice(0, 10);
  const userProfile = getUserProfile();
  const planLimits = PLAN_LIMITS[userProfile.currentPlan] || PLAN_LIMITS.free;

  return {
    T5: {
      period: currentMonth,
      planType: userProfile.currentPlan,
      tokens: { input: 0, output: 0, total: 0 },
      characters: { input: 0, output: 0 },
      messageCount: 0,
      dailyUsage: { [today]: { tokens: 0, messages: 0 } },
      limits: planLimits.T5,
      firstUsedAt: null,
      lastUsedAt: null,
    },
    H8: {
      period: currentMonth,
      planType: userProfile.currentPlan,
      tokens: { input: 0, output: 0, total: 0 },
      characters: { input: 0, output: 0 },
      messageCount: 0,
      dailyUsage: { [today]: { tokens: 0, messages: 0 } },
      limits: planLimits.H8,
      firstUsedAt: null,
      lastUsedAt: null,
    },
  };
};

// 로컬 사용량 데이터 가져오기
export const getLocalUsageData = () => {
  try {
    const backup = localStorage.getItem(USAGE_KEY + "_backup");
    if (backup) {
      try {
        return JSON.parse(backup);
      } catch (e) {
        // 백업 파싱 실패
      }
    }

    const stored = localStorage.getItem(USAGE_KEY);
    if (!stored) {
      const existingBackup = localStorage.getItem(USAGE_KEY + "_backup");
      if (existingBackup) {
        return JSON.parse(existingBackup);
      }

      const initialData = initializeUsageData();
      localStorage.setItem(USAGE_KEY, JSON.stringify(initialData));
      return initialData;
    }

    const data = JSON.parse(stored);
    const currentMonth = new Date().toISOString().slice(0, 7);

    if (data.T5?.period !== currentMonth) {
      const newData = initializeUsageData();
      localStorage.setItem(USAGE_KEY, JSON.stringify(newData));
      return newData;
    }

    const userProfile = getUserProfile();
    const planLimits = PLAN_LIMITS[userProfile.currentPlan] || PLAN_LIMITS.free;

    if (data.T5) {
      data.T5.planType = userProfile.currentPlan;
      data.T5.limits = planLimits.T5;
    }
    if (data.H8) {
      data.H8.planType = userProfile.currentPlan;
      data.H8.limits = planLimits.H8;
    }

    return data;
  } catch (error) {
    console.error("사용량 데이터 로드 실패:", error);
    return initializeUsageData();
  }
};

// 사용량 제한 체크
export const checkUsageLimit = (engineType, additionalTokens = 0) => {
  const usageData = getLocalUsageData();
  const engine = usageData[engineType];
  const today = new Date().toISOString().slice(0, 10);

  if (!engine) return { allowed: false, reason: "잘못된 엔진 타입" };

  if (engine.tokens.total + additionalTokens > engine.limits.monthlyTokens) {
    return {
      allowed: false,
      reason: "월간 토큰 한도 초과",
      remaining: Math.max(0, engine.limits.monthlyTokens - engine.tokens.total),
    };
  }

  const todayUsage = engine.dailyUsage[today] || { messages: 0 };
  if (todayUsage.messages >= engine.limits.dailyMessages) {
    return {
      allowed: false,
      reason: "일일 메시지 한도 초과",
      dailyRemaining: 0,
    };
  }

  if (additionalTokens > engine.limits.maxTokensPerMessage) {
    return {
      allowed: false,
      reason: "메시지당 토큰 한도 초과",
      maxAllowed: engine.limits.maxTokensPerMessage,
    };
  }

  return {
    allowed: true,
    remaining: engine.limits.monthlyTokens - engine.tokens.total,
    dailyRemaining: engine.limits.dailyMessages - todayUsage.messages,
  };
};

// 사용량 업데이트 (DynamoDB API 호출)
export const updateLocalUsage = async (engineType, inputText, outputText) => {
  try {
    const user = getCurrentUser();

    const response = await fetch(`${USAGE_API_BASE_URL}/usage/update`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        userId: user.userId,
        engineType: engineType,
        inputText: inputText || "",
        outputText: outputText || "",
        userPlan: user.plan,
      }),
    });

    if (!response.ok) {
      throw new Error(`API 오류: ${response.status}`);
    }

    const result = await response.json();

    if (result.success) {
      const backupData = getLocalUsageData();
      if (result.usage) {
        backupData[engineType] = {
          period: result.usage.yearMonth || new Date().toISOString().slice(0, 7),
          planType: result.usage.userPlan || user.plan,
          tokens: {
            input: result.usage.inputTokens || 0,
            output: result.usage.outputTokens || 0,
            total: result.usage.totalTokens || 0,
          },
          characters: {
            input: result.usage.characters?.input || 0,
            output: result.usage.characters?.output || 0,
          },
          messageCount: result.usage.messageCount || 0,
          dailyUsage: result.usage.dailyUsage || {},
          limits:
            result.usage.limits ||
            PLAN_LIMITS[user.plan]?.[engineType] ||
            PLAN_LIMITS.free[engineType],
          firstUsedAt: result.usage.createdAt || result.usage.firstUsedAt,
          lastUsedAt: result.usage.lastUsedAt || result.usage.updatedAt,
        };

        localStorage.setItem(USAGE_KEY, JSON.stringify(backupData));
        localStorage.setItem(USAGE_KEY + "_backup", JSON.stringify(backupData));
      }

      const actualPercentage =
        result.percentage !== undefined
          ? result.percentage
          : Math.round(
              ((result.usage?.totalTokens || 0) /
                (result.usage?.limits?.monthlyTokens || 500000)) *
                100
            );

      return {
        success: true,
        percentage: actualPercentage,
        remaining: result.remaining,
        usage: result.usage,
      };
    } else {
      return {
        success: false,
        reason: result.error,
        remaining: result.remaining || 0,
      };
    }
  } catch (error) {
    console.error("사용량 업데이트 실패:", error);
    return updateLocalUsageBackup(engineType, inputText, outputText);
  }
};

// API 실패 시 로컬 백업 함수
const updateLocalUsageBackup = (engineType, inputText, outputText) => {
  try {
    const usageData = getLocalUsageData();
    const engine = usageData[engineType];
    const today = new Date().toISOString().slice(0, 10);

    if (!engine) {
      return { success: false, reason: "잘못된 엔진 타입" };
    }

    const inputTokens = estimateTokens(inputText);
    const outputTokens = estimateTokens(outputText);
    const totalTokens = inputTokens + outputTokens;
    const inputChars = countCharacters(inputText);
    const outputChars = countCharacters(outputText);

    const limitCheck = checkUsageLimit(engineType, totalTokens);
    if (!limitCheck.allowed) {
      return {
        success: false,
        reason: limitCheck.reason,
        ...limitCheck,
      };
    }

    engine.tokens.input += inputTokens;
    engine.tokens.output += outputTokens;
    engine.tokens.total += totalTokens;
    engine.characters.input += inputChars;
    engine.characters.output += outputChars;
    engine.messageCount += 1;

    if (!engine.dailyUsage[today]) {
      engine.dailyUsage[today] = { tokens: 0, messages: 0 };
    }
    engine.dailyUsage[today].tokens += totalTokens;
    engine.dailyUsage[today].messages += 1;

    const now = new Date().toISOString();
    if (!engine.firstUsedAt) {
      engine.firstUsedAt = now;
    }
    engine.lastUsedAt = now;

    localStorage.setItem(USAGE_KEY + "_backup", JSON.stringify(usageData));

    const percentage = Math.round(
      (engine.tokens.total / engine.limits.monthlyTokens) * 100
    );

    return {
      success: true,
      usage: engine,
      percentage: Math.min(percentage, 100),
      remaining: limitCheck.remaining,
      isBackup: true,
    };
  } catch (error) {
    console.error("로컬 백업 업데이트 실패:", error);
    return { success: false, reason: "업데이트 실패" };
  }
};

// 사용량 퍼센티지 계산 (async - 서버 데이터 우선)
export const getUsagePercentage = async (engineType, forceRefresh = false) => {
  try {
    const cacheKey = `usage_percentage_${engineType}`;
    const cacheTime = `usage_percentage_time_${engineType}`;
    const cachedValue = localStorage.getItem(cacheKey);
    const cachedTime = localStorage.getItem(cacheTime);

    if (!forceRefresh && cachedValue && cachedTime) {
      const timeDiff = Date.now() - parseInt(cachedTime);
      if (timeDiff < 5000) {
        return parseInt(cachedValue);
      }
    }

    const user = getCurrentUser();
    const response = await fetch(
      `${USAGE_API_BASE_URL}/usage/${user.userId}/${engineType}`,
      {
        headers: getAuthHeaders(),
      }
    );

    if (response.ok) {
      const result = await response.json();
      if (result.success && result.data) {
        const totalTokens = result.data.totalTokens || 0;
        const limits = PLAN_LIMITS[user.plan]?.[engineType] || PLAN_LIMITS.free[engineType];

        const percentage = Math.round(
          (totalTokens / limits.monthlyTokens) * 100
        );
        const finalPercentage = Math.min(percentage, 100);

        localStorage.setItem(cacheKey, finalPercentage.toString());
        localStorage.setItem(cacheTime, Date.now().toString());

        return finalPercentage;
      }
    }

    const usageData = getLocalUsageData();
    const engine = usageData[engineType];

    if (!engine || !engine.limits) return 0;

    const percentage = Math.round(
      (engine.tokens.total / engine.limits.monthlyTokens) * 100
    );
    return Math.min(percentage, 100);
  } catch (error) {
    console.error('사용량 퍼센티지 조회 실패:', error);

    const usageData = getLocalUsageData();
    const engine = usageData[engineType];

    if (!engine || !engine.limits) return 0;

    const percentage = Math.round(
      (engine.tokens.total / engine.limits.monthlyTokens) * 100
    );
    return Math.min(percentage, 100);
  }
};

// 사용량 요약 정보 가져오기 (async)
export const getUsageSummary = async (engineType) => {
  const usageData = getLocalUsageData();
  const engine = usageData[engineType];
  const today = new Date().toISOString().slice(0, 10);

  if (!engine) return null;

  const todayUsage = engine.dailyUsage[today] || { tokens: 0, messages: 0 };
  const percentage = await getUsagePercentage(engineType);

  return {
    percentage,
    tokens: {
      used: engine.tokens.total,
      limit: engine.limits.monthlyTokens,
      remaining: Math.max(0, engine.limits.monthlyTokens - engine.tokens.total),
      input: engine.tokens.input,
      output: engine.tokens.output,
    },
    characters: {
      input: engine.characters.input,
      output: engine.characters.output,
      total: engine.characters.input + engine.characters.output,
    },
    messages: {
      total: engine.messageCount,
      todayCount: todayUsage.messages,
      todayLimit: engine.limits.dailyMessages,
      todayRemaining: Math.max(
        0,
        engine.limits.dailyMessages - todayUsage.messages
      ),
    },
    plan: {
      type: engine.planType,
      limits: engine.limits,
    },
    period: engine.period,
    lastUsed: engine.lastUsedAt,
    firstUsed: engine.firstUsedAt,
  };
};

// 모든 엔진의 사용량 통계 가져오기
export const getAllUsageStats = () => {
  const usageData = getLocalUsageData();
  const userProfile = getUserProfile();

  return {
    user: {
      userId: userProfile.userId,
      plan: userProfile.currentPlan,
      signupDate: userProfile.signupDate,
      planStartDate: userProfile.planStartDate,
    },
    engines: {
      T5: getUsageSummary("Basic"),
      H8: getUsageSummary("Pro"),
    },
    total: {
      tokens: {
        total:
          (usageData.T5?.tokens.total || 0) + (usageData.H8?.tokens.total || 0),
        input:
          (usageData.T5?.tokens.input || 0) + (usageData.H8?.tokens.input || 0),
        output:
          (usageData.T5?.tokens.output || 0) +
          (usageData.H8?.tokens.output || 0),
      },
      characters: {
        input:
          (usageData.T5?.characters.input || 0) +
          (usageData.H8?.characters.input || 0),
        output:
          (usageData.T5?.characters.output || 0) +
          (usageData.H8?.characters.output || 0),
      },
      messages:
        (usageData.T5?.messageCount || 0) + (usageData.H8?.messageCount || 0),
    },
  };
};

// 서버에서 사용량 데이터 가져오기 (API 호출)
export const fetchUsageFromServer = async (userId, engineType) => {
  try {
    const token = localStorage.getItem("access_token");
    const response = await fetch(
      `${USAGE_API_BASE_URL}/usage/${userId}/${engineType}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    if (!response.ok) {
      throw new Error("사용량 데이터 조회 실패");
    }

    const data = await response.json();

    const localData = getLocalUsageData();
    localData[engineType] = {
      ...localData[engineType],
      ...data,
    };
    localStorage.setItem(USAGE_KEY, JSON.stringify(localData));

    return data;
  } catch (error) {
    console.error("서버 사용량 조회 실패:", error);
    return getLocalUsageData()[engineType];
  }
};

// 서버에 사용량 업데이트 (API 호출)
export const updateUsageOnServer = async (userId, engineType, usageData) => {
  try {
    const token = localStorage.getItem("access_token");
    const response = await fetch(`${USAGE_API_BASE_URL}/usage/update`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        userId,
        engineType,
        ...usageData,
      }),
    });

    if (!response.ok) {
      throw new Error("사용량 업데이트 실패");
    }

    return await response.json();
  } catch (error) {
    console.error("서버 사용량 업데이트 실패:", error);
    return null;
  }
};

// 로컬 스토리지 사용량 캐시 정리
export const clearUsageCache = () => {
  localStorage.removeItem('user_usage_data');
  localStorage.removeItem('usage_data_timestamp');
  localStorage.removeItem('usage_percentage_T5');
  localStorage.removeItem('usage_percentage_time_T5');
  localStorage.removeItem('usage_percentage_H8');
  localStorage.removeItem('usage_percentage_time_H8');
};

// 플랜 변경
export const changePlan = async (newPlan) => {
  try {
    const token = localStorage.getItem("access_token");
    const userId = localStorage.getItem("userId");

    const response = await fetch(`${USAGE_API_BASE_URL}/user/plan`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        userId,
        newPlan,
        changeDate: new Date().toISOString(),
      }),
    });

    if (!response.ok) {
      throw new Error("플랜 변경 실패");
    }

    setUserPlan(newPlan);

    const usageData = getLocalUsageData();
    localStorage.setItem(USAGE_KEY, JSON.stringify(usageData));

    return await response.json();
  } catch (error) {
    console.error("플랜 변경 실패:", error);
    return null;
  }
};

// 사용량 초기화 (월별 리셋)
export const resetMonthlyUsage = () => {
  const initialData = initializeUsageData();
  localStorage.setItem(USAGE_KEY, JSON.stringify(initialData));
  return initialData;
};

// Dashboard에서 사용하는 전체 사용량 데이터 가져오기 (DynamoDB API)
export const getAllUsageData = async (forceRefresh = false) => {
  try {
    const user = getCurrentUser();

    const [basicResponse, proResponse] = await Promise.all([
      fetch(
        `${USAGE_API_BASE_URL}/usage/${encodeURIComponent(user.userId)}/T5`,
        {
          method: "GET",
          headers: getAuthHeaders(),
        }
      ),
      fetch(
        `${USAGE_API_BASE_URL}/usage/${encodeURIComponent(user.userId)}/H8`,
        {
          method: "GET",
          headers: getAuthHeaders(),
        }
      ),
    ]);

    const basicResult = await basicResponse.json();
    const proResult = await proResponse.json();

    const basicData = basicResult.success ? basicResult.data : null;
    const proData = proResult.success ? proResult.data : null;

    return {
      userId: user.userId,
      userPlan: user.plan,
      signupDate: new Date().toISOString(),
      T5: {
        monthlyTokensUsed: basicData?.totalTokens || 0,
        inputTokens: basicData?.inputTokens || 0,
        outputTokens: basicData?.outputTokens || 0,
        charactersProcessed: 0,
        messageCount: basicData?.messageCount || 0,
        lastUsedAt: basicData?.lastUsedAt,
        limits: PLAN_LIMITS[user.plan]?.T5 || PLAN_LIMITS.free.T5,
      },
      H8: {
        monthlyTokensUsed: proData?.totalTokens || 0,
        inputTokens: proData?.inputTokens || 0,
        outputTokens: proData?.outputTokens || 0,
        charactersProcessed: 0,
        messageCount: proData?.messageCount || 0,
        lastUsedAt: proData?.lastUsedAt,
        limits: PLAN_LIMITS[user.plan]?.H8 || PLAN_LIMITS.free.H8,
      },
    };
  } catch (error) {
    console.error("사용량 데이터 조회 실패:", error);
    const user = getCurrentUser();
    return {
      userId: user.userId,
      userPlan: user.plan,
      signupDate: new Date().toISOString(),
      T5: {
        monthlyTokensUsed: 0,
        inputTokens: 0,
        outputTokens: 0,
        charactersProcessed: 0,
        messageCount: 0,
        lastUsedAt: null,
        limits: PLAN_LIMITS[user.plan]?.T5 || PLAN_LIMITS.free.T5,
      },
      H8: {
        monthlyTokensUsed: 0,
        inputTokens: 0,
        outputTokens: 0,
        charactersProcessed: 0,
        messageCount: 0,
        lastUsedAt: null,
        limits: PLAN_LIMITS[user.plan]?.H8 || PLAN_LIMITS.free.H8,
      },
    };
  }
};

// 플랜별 제한 가져오기
export const getPlanLimits = (plan) => {
  return PLAN_LIMITS[plan] || PLAN_LIMITS.free;
};

export default {
  estimateTokens,
  countCharacters,
  getUserProfile,
  setUserPlan,
  getLocalUsageData,
  checkUsageLimit,
  updateLocalUsage,
  getUsagePercentage,
  getUsageSummary,
  getAllUsageStats,
  fetchUsageFromServer,
  updateUsageOnServer,
  changePlan,
  resetMonthlyUsage,
  getAllUsageData,
  getPlanLimits,
  clearUsageCache,
  PLAN_LIMITS,
};
