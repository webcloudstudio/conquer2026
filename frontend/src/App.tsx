import { useEffect } from "react";
import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { HomePage } from "./pages/HomePage";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { OpenWorldsPage } from "./pages/OpenWorldsPage";
import { ManageWorldsPage } from "./pages/ManageWorldsPage";
import { GamePage } from "./pages/GamePage";
import { InboxPage } from "./pages/InboxPage";
import { useAuthStore } from "./store/auth";

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { token } = useAuthStore();
  const location = useLocation();
  if (!token) return <Navigate to={`/login?next=${encodeURIComponent(location.pathname)}`} replace />;
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
        {/* Public routes outside AppShell */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* All app pages inside AppShell */}
        <Route element={<AppShell />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/worlds" element={<RequireAuth><OpenWorldsPage /></RequireAuth>} />
          <Route path="/manage" element={<RequireAuth><ManageWorldsPage /></RequireAuth>} />
          <Route path="/game/:worldId" element={<RequireAuth><GamePage /></RequireAuth>} />
          <Route path="/game/:worldId/inbox" element={<RequireAuth><InboxPage /></RequireAuth>} />
        </Route>

        {/* Legacy redirect */}
        <Route path="/admin" element={<Navigate to="/manage" replace />} />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
