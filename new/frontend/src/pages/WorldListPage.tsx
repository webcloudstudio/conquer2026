/**
 * Game browser — lists open worlds a player can join or enter.
 */

import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { listWorlds } from "../api/game";
import type { World } from "../types";
import { useAuthStore } from "../store/auth";

export function WorldListPage() {
  const [worlds, setWorlds] = useState<World[]>([]);
  const [loading, setLoading] = useState(true);
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  useEffect(() => {
    listWorlds().then(setWorlds).finally(() => setLoading(false));
  }, []);

  return (
    <div style={styles.page}>
      <header style={styles.header}>
        <h1 style={styles.title}>Conquer v5</h1>
        <div style={styles.user}>
          <span style={{ color: "#aaa", fontSize: 13 }}>{user?.username}</span>
          {user?.is_admin && (
            <button style={styles.logoutBtn} onClick={() => navigate("/admin")}>Admin</button>
          )}
          <button style={styles.logoutBtn} onClick={logout}>Logout</button>
        </div>
      </header>

      <main style={styles.main}>
        <h2 style={styles.heading}>Open Games</h2>
        {loading && <p style={styles.info}>Loading…</p>}
        {!loading && worlds.length === 0 && (
          <p style={styles.info}>No active games. Ask an admin to create one.</p>
        )}
        <div style={styles.grid}>
          {worlds.map((w) => (
            <div key={w.id} style={styles.card}>
              <h3 style={styles.worldName}>{w.name}</h3>
              <p style={styles.meta}>Turn {w.turn} · {w.mapx}×{w.mapy} map</p>
              {w.is_maintenance && (
                <p style={{ color: "#e74c3c", fontSize: 12 }}>⚠ Maintenance Mode</p>
              )}
              <button
                style={styles.enterBtn}
                disabled={w.is_maintenance}
                onClick={() => navigate(`/game/${w.id}`)}
              >
                Enter World
              </button>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: { minHeight: "100vh", background: "#0d1117", color: "#fff" },
  header: {
    display: "flex", justifyContent: "space-between", alignItems: "center",
    padding: "12px 24px", background: "#1c1c2e", borderBottom: "1px solid #333",
  },
  title: { color: "#ffd700", margin: 0, fontSize: 22 },
  user: { display: "flex", alignItems: "center", gap: 12 },
  logoutBtn: {
    padding: "4px 12px", background: "none", border: "1px solid #555",
    borderRadius: 4, color: "#aaa", cursor: "pointer", fontSize: 12,
  },
  main: { maxWidth: 800, margin: "0 auto", padding: 32 },
  heading: { color: "#ccc", margin: "0 0 20px" },
  info: { color: "#666" },
  grid: { display: "flex", flexWrap: "wrap", gap: 16 },
  card: {
    background: "#1c1c2e", border: "1px solid #333", borderRadius: 8,
    padding: 20, width: 220,
  },
  worldName: { color: "#fff", margin: "0 0 4px", fontSize: 16 },
  meta: { color: "#888", fontSize: 12, margin: "0 0 12px" },
  enterBtn: {
    width: "100%", padding: "8px", background: "#2980b9",
    border: "none", borderRadius: 4, color: "#fff", fontSize: 13, cursor: "pointer",
  },
};
