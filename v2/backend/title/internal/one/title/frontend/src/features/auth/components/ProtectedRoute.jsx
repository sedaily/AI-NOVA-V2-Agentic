import React from "react";

const ProtectedRoute = ({ children, requiredRole = null }) => {
  // 로그인 체크 없이 바로 children 렌더링
  return children;
};

export default ProtectedRoute;