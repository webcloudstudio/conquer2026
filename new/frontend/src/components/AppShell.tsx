/**
 * AppShell — persistent top navbar for all authenticated app pages.
 * Wraps children (or <Outlet/> for layout routes) with a sticky header.
 */

import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { useAuthStore } from "../store/auth";

export function AppShell() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const { pathname } = useLocation();

  function tab(label: string, path: string) {
    const active = pathname.startsWith(path);
    return (
      <button
        style={active ? s.tabActive : s.tab}
        onClick={() => navigate(path)}
      >
        {label}
      </button>
    );
  }

  return (
    <div style={s.shell}>
      <header style={s.bar}>
        <button style={s.logo} onClick={() => navigate("/")}>⚔️ Conquer v5</button>
        <nav style={s.tabs}>
          {tab("Open Worlds", "/worlds")}
          {tab("Manage Worlds", "/manage")}
        </nav>
        <div style={s.right}>
          {user && <span style={s.username}>{user.username}</span>}
          <button style={s.ghost} onClick={logout}>Sign Out</button>
        </div>
      </header>
      <div style={s.body}>
        <Outlet />
      </div>
    </div>
  );
}

const BAR_H = 48;

const s: Record<string, React.CSSProperties> = {
  shell: { display: "flex", flexDirection: "column", minHeight: "100vh", background: "#0d1117" },
  bar: {
    position: "sticky", top: 0, zIndex: 20, height: BAR_H,
    display: "flex", alignItems: "center", gap: 8, padding: "0 20px",
    background: "#161b22", borderBottom: "1px solid #30363d",
  },
  logo: {
    background: "none", border: "none", color: "#e3b341",
    fontWeight: "bold", fontSize: 16, cursor: "pointer", padding: "0 8px 0 0",
  },
  tabs: { display: "flex", gap: 4, flex: 1 },
  tab: {
    padding: "5px 14px", background: "none", border: "1px solid transparent",
    borderRadius: 6, color: "#8b949e", cursor: "pointer", fontSize: 13,
  },
  tabActive: {
    padding: "5px 14px", background: "#21262d", border: "1px solid #30363d",
    borderRadius: 6, color: "#c9d1d9", cursor: "pointer", fontSize: 13,
    fontWeight: 600,
  },
  right: { display: "flex", alignItems: "center", gap: 10 },
  username: { color: "#8b949e", fontSize: 13 },
  ghost: {
    padding: "4px 12px", background: "none", border: "1px solid #30363d",
    borderRadius: 6, color: "#8b949e", fontSize: 13, cursor: "pointer",
  },
  body: { flex: 1, overflowY: "auto" },
};
