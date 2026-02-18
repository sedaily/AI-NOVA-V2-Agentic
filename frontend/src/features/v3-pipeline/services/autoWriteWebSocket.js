/**
 * WebSocket Service for NOVA v3 Auto Write
 * Connects to AWS WebSocket API Gateway for streaming responses
 */

const WS_URL = import.meta.env.VITE_V3_WS_URL || 'wss://v85klisu55.execute-api.us-east-1.amazonaws.com/prod';

/**
 * WebSocket connection manager for auto-write streaming
 */
class AutoWriteWebSocket {
  constructor() {
    this.ws = null;
    this.connectionId = null;
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 3;
    this.callbacks = {
      onStart: null,
      onChunk: null,
      onAgentUpdate: null,
      onComplete: null,
      onError: null,
      onClose: null,
    };
  }

  /**
   * Connect to WebSocket server
   * @returns {Promise<void>}
   */
  connect() {
    return new Promise((resolve, reject) => {
      if (this.isConnected && this.ws?.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      try {
        this.ws = new WebSocket(WS_URL);

        this.ws.onopen = () => {
          console.log('[AutoWriteWS] Connected');
          this.isConnected = true;
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          this.handleMessage(event.data);
        };

        this.ws.onerror = (error) => {
          console.error('[AutoWriteWS] Error:', error);
          if (this.callbacks.onError) {
            this.callbacks.onError({ type: 'connection', message: 'WebSocket connection error' });
          }
          reject(error);
        };

        this.ws.onclose = (event) => {
          console.log('[AutoWriteWS] Closed:', event.code, event.reason);
          this.isConnected = false;

          if (this.callbacks.onClose) {
            this.callbacks.onClose(event);
          }
        };

        // Connection timeout
        setTimeout(() => {
          if (this.ws?.readyState !== WebSocket.OPEN) {
            this.ws?.close();
            reject(new Error('Connection timeout'));
          }
        }, 10000);

      } catch (error) {
        console.error('[AutoWriteWS] Connection error:', error);
        reject(error);
      }
    });
  }

  /**
   * Handle incoming WebSocket messages
   * @param {string} data - Raw message data
   */
  handleMessage(data) {
    try {
      const message = JSON.parse(data);
      console.log('[AutoWriteWS] Received:', message.type);

      switch (message.type) {
        case 'start':
          if (this.callbacks.onStart) {
            this.callbacks.onStart(message);
          }
          break;

        case 'chunk':
          if (this.callbacks.onChunk) {
            this.callbacks.onChunk(message.text, message);
          }
          break;

        case 'agent_update':
          if (this.callbacks.onAgentUpdate) {
            this.callbacks.onAgentUpdate(message);
          }
          break;

        case 'complete':
          if (this.callbacks.onComplete) {
            this.callbacks.onComplete(message.result, message);
          }
          break;

        case 'error':
          if (this.callbacks.onError) {
            this.callbacks.onError(message);
          }
          break;

        default:
          console.log('[AutoWriteWS] Unknown message type:', message.type);
      }
    } catch (error) {
      console.error('[AutoWriteWS] Message parse error:', error);
    }
  }

  /**
   * Send auto-write request
   * @param {string} sourceText - Source text to process
   * @param {Object} options - Processing options
   */
  sendMessage(sourceText, options = {}) {
    if (!this.isConnected || this.ws?.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket is not connected');
    }

    const message = {
      action: 'sendMessage',
      sourceText,
      options: {
        mode: options.mode || 'full',
        articleType: options.articleType || 'corporate',
      },
    };

    console.log('[AutoWriteWS] Sending:', message.action);
    this.ws.send(JSON.stringify(message));
  }

  /**
   * Set callback handlers
   * @param {Object} callbacks - Callback functions
   */
  setCallbacks(callbacks) {
    this.callbacks = { ...this.callbacks, ...callbacks };
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
      this.isConnected = false;
    }
  }

  /**
   * Check if connected
   * @returns {boolean}
   */
  get connected() {
    return this.isConnected && this.ws?.readyState === WebSocket.OPEN;
  }
}

// Singleton instance
const autoWriteWS = new AutoWriteWebSocket();

/**
 * Auto-write with WebSocket streaming
 * @param {string} sourceText - Source text
 * @param {Object} options - Options (mode, articleType)
 * @param {Object} callbacks - Callback handlers
 *   - onStart: called when processing starts
 *   - onChunk: called for each text chunk (streaming)
 *   - onAgentUpdate: called when agent status changes
 *   - onComplete: called when processing completes
 *   - onError: called on error
 * @returns {Promise<Object>} - Final result
 */
export const autoWriteWithStreaming = async (sourceText, options = {}, callbacks = {}) => {
  return new Promise(async (resolve, reject) => {
    let result = '';
    let isCompleted = false;

    try {
      // Set callbacks
      autoWriteWS.setCallbacks({
        onStart: (message) => {
          if (callbacks.onStart) callbacks.onStart(message);
        },
        onChunk: (text, message) => {
          result += text;
          if (callbacks.onChunk) callbacks.onChunk(text, result, message);
        },
        onAgentUpdate: (message) => {
          if (callbacks.onAgentUpdate) callbacks.onAgentUpdate(message);
        },
        onComplete: (finalResult, message) => {
          isCompleted = true;
          if (callbacks.onComplete) callbacks.onComplete(finalResult, message);
          resolve({ success: true, result: finalResult || result });
        },
        onError: (error) => {
          if (callbacks.onError) callbacks.onError(error);
          reject(new Error(error.message || 'Processing failed'));
        },
        onClose: (event) => {
          if (!isCompleted) {
            reject(new Error('Connection closed unexpectedly'));
          }
        },
      });

      // Connect if not connected
      if (!autoWriteWS.connected) {
        await autoWriteWS.connect();
      }

      // Send message
      autoWriteWS.sendMessage(sourceText, options);

    } catch (error) {
      console.error('[AutoWriteWS] Error:', error);
      reject(error);
    }
  });
};

/**
 * Disconnect WebSocket
 */
export const disconnectAutoWrite = () => {
  autoWriteWS.disconnect();
};

/**
 * Check if WebSocket is connected
 * @returns {boolean}
 */
export const isAutoWriteConnected = () => {
  return autoWriteWS.connected;
};

export default {
  autoWriteWithStreaming,
  disconnectAutoWrite,
  isAutoWriteConnected,
};
