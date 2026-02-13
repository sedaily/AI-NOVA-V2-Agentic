import React from "react";

const ProtectedRoute = ({ children, requiredRole = null }) => {
  // 인증 체크 비활성화 - 항상 children 반환
  return children;
};

export default ProtectedRoute;
