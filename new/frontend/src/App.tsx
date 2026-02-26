import { useEffect } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { WorldListPage } from "./pages/WorldListPage";
import { GamePage } from "./pages/GamePage";
import { InboxPage } from "./pages/InboxPage";
import { AdminPage } from "./pages/AdminPage";
import { useAuthStore } from "./store/auth";

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { token } = useAuthStore();
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  const { token, loadMe } = useAuthStore();

  useEffect(() => {
    if (token) loadMe();
  }, [token, loadMe]);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/" element={<RequireAuth><WorldListPage /></RequireAuth>} />
        <Route path="/game/:worldId" element={<RequireAuth><GamePage /></RequireAuth>} />
        <Route path="/game/:worldId/inbox" element={<RequireAuth><InboxPage /></RequireAuth>} />
        <Route path="/admin" element={<RequireAuth><AdminPage /></RequireAuth>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
