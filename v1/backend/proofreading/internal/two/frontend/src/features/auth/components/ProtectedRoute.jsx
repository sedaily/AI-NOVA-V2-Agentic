import React, { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import authService from "../services/authService";

const ProtectedRoute = ({ children, requiredRole = null }) => {
  // 로그인 기능 비활성화 - 모든 요청 통과
  return children;
};

export default ProtectedRoute;