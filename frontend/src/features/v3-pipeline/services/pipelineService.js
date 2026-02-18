/**
 * NOVA v3 Pipeline API Service
 * Connects to AWS Lambda + Bedrock backend
 */

const API_BASE_URL = import.meta.env.VITE_V3_API_URL || 'https://uhovbribz8.execute-api.ap-northeast-2.amazonaws.com/prod/v3';

// Auto mode API (us-east-1 - Multi-Agent Supervisor)
const AUTO_API_URL = import.meta.env.VITE_V3_AUTO_API_URL || 'https://9p43ghstlg.execute-api.us-east-1.amazonaws.com/prod/v3';

/**
 * Helper function to make API calls
 */
const apiCall = async (endpoint, method = 'POST', data = null) => {
  const options = {
    method,
    headers: {
      'Content-Type': 'application/json',
    },
  };

  if (data) {
    options.body = JSON.stringify(data);
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, options);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'API Error' }));
    throw new Error(error.error || `HTTP ${response.status}`);
  }

  return response.json();
};

/**
 * Phase 1: Analyze source material
 * @param {string} sourceText - Source text to analyze
 * @param {string} sourceType - Type: press_release, interview, memo, reference
 * @returns {Promise<{angles: Array, summary: string, newsValue: string}>}
 */
export const analyzeSource = async (sourceText, sourceType = 'press_release') => {
  try {
    const result = await apiCall('/analyze', 'POST', {
      sourceText,
      sourceType,
    });
    return result;
  } catch (error) {
    console.error('Analyze source error:', error);
    throw error;
  }
};

/**
 * Phase 3: Generate article draft
 * @param {string} sourceText - Original source text
 * @param {Object} angle - Selected angle from Phase 2
 * @param {string} articleType - 'corporate' or 'public'
 * @returns {Promise<{draft: string, wordCount: number, angle: string}>}
 */
export const generateDraft = async (sourceText, angle, articleType = 'corporate') => {
  try {
    const result = await apiCall('/draft', 'POST', {
      sourceText,
      angle,
      articleType,
    });
    return result;
  } catch (error) {
    console.error('Generate draft error:', error);
    throw error;
  }
};

/**
 * Phase 4-1: Proofread article
 * @param {string} text - Draft text to proofread
 * @param {string} category - economy, society, general
 * @returns {Promise<{corrected: string, corrections: Array, summary: string}>}
 */
export const proofreadArticle = async (text, category = 'economy') => {
  try {
    const result = await apiCall('/proofread', 'POST', {
      text,
      category,
    });
    return result;
  } catch (error) {
    console.error('Proofread error:', error);
    throw error;
  }
};

/**
 * Phase 4-2: Revise article
 * @param {string} text - Text to revise
 * @param {string} lengthType - short, medium, long
 * @returns {Promise<{revised: string, revisions: Array, summary: string, readabilityScore: number}>}
 */
export const reviseArticle = async (text, lengthType = 'medium') => {
  try {
    const result = await apiCall('/revise', 'POST', {
      text,
      lengthType,
    });
    return result;
  } catch (error) {
    console.error('Revise error:', error);
    throw error;
  }
};

/**
 * Phase 5: Generate title suggestions
 * @param {string} articleText - Article text
 * @param {number} count - Number of titles to generate
 * @returns {Promise<{titles: Array}>}
 */
export const generateTitles = async (articleText, count = 3) => {
  try {
    const result = await apiCall('/titles', 'POST', {
      articleText,
      count,
    });
    return result;
  } catch (error) {
    console.error('Generate titles error:', error);
    throw error;
  }
};

/**
 * Save pipeline state
 * @param {string} pipelineId - Pipeline ID (optional, will be generated if not provided)
 * @param {string} userId - User ID
 * @param {Object} state - Pipeline state data
 * @returns {Promise<{pipelineId: string, saved: boolean}>}
 */
export const savePipelineState = async (pipelineId, userId, state) => {
  try {
    const result = await apiCall('/save', 'POST', {
      pipelineId,
      userId,
      state,
    });
    return result;
  } catch (error) {
    console.error('Save pipeline error:', error);
    throw error;
  }
};

/**
 * Load pipeline state
 * @param {string} pipelineId - Pipeline ID to load
 * @returns {Promise<Object>}
 */
export const loadPipelineState = async (pipelineId) => {
  try {
    const result = await apiCall(`/load/${pipelineId}`, 'GET');
    return result;
  } catch (error) {
    console.error('Load pipeline error:', error);
    throw error;
  }
};

/**
 * Auto Write Mode - Multi-Agent Supervisor
 * Automatically analyzes source and generates complete article
 * @param {string} sourceText - Source text (press release, memo, etc.)
 * @param {Object} options - Additional options
 *   - mode: 'full' (complete pipeline) | 'analyze' (analysis only)
 *   - articleType: 'corporate' | 'public'
 * @returns {Promise<{success: boolean, sessionId: string, result: string, mode: string}>}
 */
export const autoWriteArticle = async (sourceText, options = {}) => {
  try {
    const response = await fetch(`${AUTO_API_URL}/auto`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        sourceText,
        options: {
          mode: options.mode || 'full',
          articleType: options.articleType || 'corporate',
        },
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'API Error' }));
      throw new Error(error.error || `HTTP ${response.status}`);
    }

    return response.json();
  } catch (error) {
    console.error('Auto write article error:', error);
    throw error;
  }
};

export default {
  analyzeSource,
  generateDraft,
  proofreadArticle,
  reviseArticle,
  generateTitles,
  savePipelineState,
  loadPipelineState,
  autoWriteArticle,
};
