/**
 * Open Worlds — lists all active game worlds with their admin usernames.
 * The user's last-played world is shown first with a gold border.
 */

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { listWorlds } from "../api/game";
import type { World } from "../types";
import { useAuthStore } from "../store/auth";

const LAST_KEY = "lastPlayedWorldId";

export function OpenWorldsPage() {
  const [worlds, setWorlds] = useState<World[]>([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const lastPlayed = localStorage.getItem(LAST_KEY);

  useEffect(() => {
    listWorlds()
      .then((ws) => {
        // Sort: last-played world first
        const sorted = [...ws].sort((a, b) => {
          if (a.id === lastPlayed) return -1;
          if (b.id === lastPlayed) return 1;
          return 0;
        });
        setWorlds(sorted);
      })
      .finally(() => setLoading(false));
  }, [lastPlayed]);

  function enterWorld(w: World) {
    localStorage.setItem(LAST_KEY, w.id);
    navigate(`/game/${w.id}`);
  }

  return (
    <div style={s.page}>
      <div style={s.header}>
        <h2 style={s.title}>Open Worlds</h2>
        {user?.is_admin && (
          <button style={s.adminBtn} onClick={() => navigate("/manage")}>Manage Worlds</button>
        )}
      </div>

      {loading && <p style={s.info}>Loading…</p>}
      {!loading && worlds.length === 0 && (
        <div style={s.empty}>
          <p>No active worlds yet.</p>
          <p>Go to <button style={s.link} onClick={() => navigate("/manage")}>Manage Worlds</button> to create one.</p>
        </div>
      )}

      <div style={s.grid}>
        {worlds.map((w) => {
          const isLast = w.id === lastPlayed;
          return (
            <div key={w.id} style={{ ...s.card, ...(isLast ? s.cardActive : {}) }}>
              {isLast && <div style={s.activeBadge}>▶ Currently Playing</div>}
              <h3 style={s.worldName}>{w.name}</h3>
              <p style={s.meta}>Turn {w.turn} · {w.mapx}×{w.mapy} map</p>
              <p style={s.adminLine}>
                Admin{w.admins.length !== 1 ? "s" : ""}: {" "}
                <span style={s.adminNames}>
                  {w.admins.length ? w.admins.map((a) => a.username).join(", ") : "—"}
                </span>
              </p>
              {w.is_maintenance && (
                <p style={s.maint}>⚠ Maintenance — temporarily closed</p>
              )}
              <button
                style={s.enterBtn}
                disabled={w.is_maintenance}
                onClick={() => enterWorld(w)}
              >
                {isLast ? "Continue" : "Enter World"}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  page: { padding: "32px 40px", maxWidth: 960, margin: "0 auto" },
  header: { display: "flex", alignItems: "center", marginBottom: 24, gap: 16 },
  title: { color: "#c9d1d9", margin: 0, fontSize: 22, fontWeight: 700 },
  adminBtn: {
    padding: "5px 14px", background: "#1f6feb", border: "none",
    borderRadius: 6, color: "#fff", fontSize: 13, cursor: "pointer",
  },
  info: { color: "#666" },
  empty: { color: "#8b949e", padding: "40px 0", textAlign: "center" },
  link: {
    background: "none", border: "none", color: "#58a6ff",
    cursor: "pointer", fontSize: "inherit", padding: 0,
  },
  grid: { display: "flex", flexWrap: "wrap", gap: 20 },
  card: {
    background: "#161b22", border: "1px solid #30363d",
    borderRadius: 10, padding: "20px 22px", width: 260,
    display: "flex", flexDirection: "column", gap: 6,
  },
  cardActive: {
    border: "2px solid #e3b341",
    boxShadow: "0 0 12px rgba(227,179,65,0.2)",
  },
  activeBadge: {
    color: "#e3b341", fontSize: 11, fontWeight: 700,
    letterSpacing: 0.5, marginBottom: 4,
  },
  worldName: { color: "#fff", margin: 0, fontSize: 17, fontWeight: 600 },
  meta: { color: "#8b949e", fontSize: 12, margin: 0 },
  adminLine: { color: "#8b949e", fontSize: 12, margin: 0 },
  adminNames: { color: "#c9d1d9" },
  maint: { color: "#f85149", fontSize: 12, margin: 0 },
  enterBtn: {
    marginTop: 8, padding: "8px 0", background: "#238636",
    border: "none", borderRadius: 6, color: "#fff",
    fontSize: 14, cursor: "pointer", fontWeight: 600,
  },
};
