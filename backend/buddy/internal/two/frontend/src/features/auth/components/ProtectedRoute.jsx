import React from "react";

// ProtectedRoute를 비활성화하고 바로 children을 렌더링
const ProtectedRoute = ({ children }) => {
  // 인증 체크 없이 바로 children 렌더링
  return children;
};

export default ProtectedRoute;