import React from "react";

// 로그인 체크 없이 모든 접근 허용
const DummyProtectedRoute = ({ children }) => {
  return children;
};

export default DummyProtectedRoute;