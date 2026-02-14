import React, { useState, useEffect, Suspense, lazy } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  useNavigate,
  useLocation,
} from "react-router-dom";

const ChatPage = lazy(() =>
  import("./features/chat/containers/ChatPageContainer")
);

function ChatOnlyApp() {
  const navigate = useNavigate();
  const location = useLocation();

  const [userRole] = useState("user");
  const [selectedEngine, setSelectedEngine] = useState(() => {
    if (location.pathname.includes("/11")) return "11";
    if (location.pathname.includes("/22")) return "22";
    return "11";
  });

  const handleLogout = () => {
    navigate("/11/chat");
  };

  const handleBackToLanding = () => {
    navigate("/11/chat");
  };

  return (
    <div className="flex w-full overflow-x-clip" style={{ minHeight: "100dvh" }}>
      <div className="min-h-full w-full min-w-0 flex-1">
        <Suspense fallback={<div>Loading...</div>}>
          <Routes>
            <Route path="/" element={<Navigate to="/11/chat" replace />} />
            <Route
              path="/11/chat/:conversationId?"
              element={
                <ChatPage
                  userRole={userRole}
                  selectedEngine="11"
                  onLogout={handleLogout}
                  onBackToLanding={handleBackToLanding}
                  onTitleUpdate={() => {}}
                  onToggleSidebar={() => {}}
                  isSidebarOpen={false}
                  onNewConversation={() => {}}
                  onDashboard={() => {}}
                />
              }
            />
            <Route
              path="/22/chat/:conversationId?"
              element={
                <ChatPage
                  userRole={userRole}
                  selectedEngine="22"
                  onLogout={handleLogout}
                  onBackToLanding={handleBackToLanding}
                  onTitleUpdate={() => {}}
                  onToggleSidebar={() => {}}
                  isSidebarOpen={false}
                  onNewConversation={() => {}}
                  onDashboard={() => {}}
                />
              }
            />
            <Route path="*" element={<Navigate to="/11/chat" replace />} />
          </Routes>
        </Suspense>
      </div>
    </div>
  );
}

function ChatOnlyAppWrapper() {
  return (
    <Router>
      <ChatOnlyApp />
    </Router>
  );
}

export default ChatOnlyAppWrapper;