import React from "react";

const ProtectedRoute = ({ children, requiredRole = null }) => {
  // 로그인 체크를 비활성화하고 항상 children을 렌더링
  return children;
};

export default ProtectedRoute;