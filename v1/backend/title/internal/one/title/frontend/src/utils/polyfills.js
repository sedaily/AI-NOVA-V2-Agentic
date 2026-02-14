/**
 * crypto.randomUUID polyfill
 * crypto.randomUUID는 secure context (HTTPS)에서만 사용 가능
 * HTTP 환경을 위한 fallback 구현
 */

if (typeof crypto !== 'undefined' && !crypto.randomUUID) {
  crypto.randomUUID = function() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  };
}

// crypto 객체가 없는 경우
if (typeof window !== 'undefined' && typeof window.crypto === 'undefined') {
  window.crypto = {
    randomUUID: function() {
      return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
      });
    }
  };
}
