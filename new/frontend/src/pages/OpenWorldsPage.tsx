/**
 * Worlds List — shows all active worlds sorted admin → playing → other.
 * Admins get gold border, playing worlds get green, others are neutral.
 */

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { listWorlds, listMyWorlds, listPlayingWorlds } from "../api/game";
import type { World } from "../types";

const LAST_KEY = "lastPlayedWorldId";

export function OpenWorldsPage() {
  const [worlds, setWorlds] = useState<World[]>([]);
  const [adminIds, setAdminIds] = useState<Set<string>>(new Set());
  const [playingIds, setPlayingIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([listWorlds(), listMyWorlds(), listPlayingWorlds()])
      .then(([all, mine, playing]) => {
        const aIds = new Set(mine.map((w) => w.id));
        const pIds = new Set(playing.map((w) => w.id));
        setAdminIds(aIds);
        setPlayingIds(pIds);

        const adminWorlds = all.filter((w) => aIds.has(w.id)).sort((a, b) => a.name.localeCompare(b.name));
        const playingOnly = all.filter((w) => pIds.has(w.id) && !aIds.has(w.id)).sort((a, b) => a.name.localeCompare(b.name));
        const other = all.filter((w) => !aIds.has(w.id) && !pIds.has(w.id)).sort((a, b) => a.name.localeCompare(b.name));
        setWorlds([...adminWorlds, ...playingOnly, ...other]);
      })
      .finally(() => setLoading(false));
  }, []);

  function enterWorld(w: World) {
    localStorage.setItem(LAST_KEY, w.id);
    navigate(`/game/${w.id}`);
  }

  function cardStyle(w: World) {
    if (adminIds.has(w.id)) return { ...s.card, border: "2px solid #e3b341", boxShadow: "0 0 12px rgba(227,179,65,0.2)" };
    if (playingIds.has(w.id)) return { ...s.card, border: "2px solid #3fb950", boxShadow: "0 0 10px rgba(63,185,80,0.15)" };
    return s.card;
  }

  function badge(w: World) {
    if (adminIds.has(w.id)) return <div style={s.badgeGold}>⚙ Administering</div>;
    if (playingIds.has(w.id)) return <div style={s.badgeGreen}>▶ Currently Playing</div>;
    return null;
  }

  function actionBtn(w: World) {
    const isAdmin = adminIds.has(w.id);
    const isPlaying = playingIds.has(w.id);
    const full = w.player_count >= w.max_players;
    const disabled = !isAdmin && !isPlaying && (full || w.is_maintenance);

    let label = "Join";
    if (isAdmin) label = "Enter World";
    else if (isPlaying) label = "Continue";

    const btnStyle = isAdmin
      ? s.btnGold
      : isPlaying
      ? s.btnGreen
      : s.btnDefault;

    return (
      <button
        style={{ ...btnStyle, ...(disabled ? { opacity: 0.45, cursor: "not-allowed" } : {}) }}
        disabled={disabled}
        onClick={() => enterWorld(w)}
      >
        {label}
      </button>
    );
  }

  return (
    <div style={s.page}>
      <h2 style={s.title}>Worlds List</h2>

      {loading && <p style={s.info}>Loading…</p>}
      {!loading && worlds.length === 0 && (
        <div style={s.empty}>
          <p>No active worlds yet.</p>
          <p>Go to <button style={s.link} onClick={() => navigate("/manage")}>Manage Worlds</button> to create one.</p>
        </div>
      )}

      <div style={s.grid}>
        {worlds.map((w) => (
          <div key={w.id} style={cardStyle(w)}>
            {badge(w)}
            <h3 style={s.worldName}>{w.name}</h3>
            <p style={s.meta}>
              Turn {w.turn} · {w.mapx}×{w.mapy} map · {w.player_count}/{w.max_players} players
            </p>
            <p style={s.adminLine}>
              Admin{w.admins.length !== 1 ? "s" : ""}: {" "}
              <span style={s.adminNames}>
                {w.admins.length ? w.admins.map((a) => a.username).join(", ") : "—"}
              </span>
            </p>
            {w.is_maintenance && (
              <p style={s.maint}>⚠ Maintenance — temporarily closed</p>
            )}
            {!adminIds.has(w.id) && !playingIds.has(w.id) && w.player_count >= w.max_players && (
              <p style={s.maint}>World is full</p>
            )}
            {actionBtn(w)}
          </div>
        ))}
      </div>
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  page: { padding: "32px 40px", maxWidth: 960, margin: "0 auto", overflowY: "auto" },
  title: { color: "#c9d1d9", margin: "0 0 24px", fontSize: 22, fontWeight: 700 },
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
  badgeGold: { color: "#e3b341", fontSize: 11, fontWeight: 700, letterSpacing: 0.5, marginBottom: 4 },
  badgeGreen: { color: "#3fb950", fontSize: 11, fontWeight: 700, letterSpacing: 0.5, marginBottom: 4 },
  worldName: { color: "#fff", margin: 0, fontSize: 17, fontWeight: 600 },
  meta: { color: "#8b949e", fontSize: 12, margin: 0 },
  adminLine: { color: "#8b949e", fontSize: 12, margin: 0 },
  adminNames: { color: "#c9d1d9" },
  maint: { color: "#f85149", fontSize: 12, margin: 0 },
  btnDefault: {
    marginTop: 8, padding: "8px 0", background: "#238636",
    border: "none", borderRadius: 6, color: "#fff",
    fontSize: 14, cursor: "pointer", fontWeight: 600,
  },
  btnGold: {
    marginTop: 8, padding: "8px 0", background: "#7d5a00",
    border: "1px solid #e3b341", borderRadius: 6, color: "#e3b341",
    fontSize: 14, cursor: "pointer", fontWeight: 600,
  },
  btnGreen: {
    marginTop: 8, padding: "8px 0", background: "#1a4a2a",
    border: "1px solid #3fb950", borderRadius: 6, color: "#3fb950",
    fontSize: 14, cursor: "pointer", fontWeight: 600,
  },
};
