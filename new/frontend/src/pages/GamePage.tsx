/**
 * Main game page — hex map + side panels + army panel + resource bar.
 */

import React, { useCallback, useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { HexMap } from "../components/HexMap";
import { SectorPanel } from "../components/SectorPanel";
import { NationDashboard } from "../components/NationDashboard";
import { ArmyPanel } from "../components/ArmyPanel";
import { listSectors, listArmies, listMyArmies, listNations, getWorld } from "../api/game";
import type { Army, Nation, Sector, World } from "../types";
import { useAuthStore } from "../store/auth";

type Tab = "armies" | "nations";

export function GamePage() {
  const { worldId } = useParams<{ worldId: string }>();
  const navigate = useNavigate();
  const { user } = useAuthStore();

  const [world, setWorld] = useState<World | null>(null);
  const [sectors, setSectors] = useState<Sector[]>([]);
  const [armies, setArmies] = useState<Army[]>([]);
  const [myArmies, setMyArmies] = useState<Army[]>([]);
  const [nations, setNations] = useState<Nation[]>([]);
  const [myNation, setMyNation] = useState<Nation | null>(null);
  const [selectedHex, setSelectedHex] = useState<{ x: number; y: number } | null>(null);
  const [selectedSector, setSelectedSector] = useState<Sector | null>(null);
  const [tab, setTab] = useState<Tab>("armies");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!worldId) return;
    const [w, s, a, ma, n] = await Promise.all([
      getWorld(worldId),
      listSectors(worldId),
      listArmies(worldId),
      listMyArmies(worldId).catch(() => []),
      listNations(worldId),
    ]);
    setWorld(w);
    setSectors(s);
    setArmies(a);
    setMyArmies(ma);
    setNations(n);

    // Find player's nation
    if (user) {
      // myArmies endpoint 403s without a nation — we infer from nation list
      // Backend doesn't return user_id in NationOut yet, so we rely on /nations/mine if added
      setMyNation(null); // will be refined when we add GET /nations/mine
    }
    setLoading(false);
  }, [worldId, user]);

  useEffect(() => { load(); }, [load]);

  function handleSelectHex(x: number, y: number, sector: Sector | null) {
    setSelectedHex({ x, y });
    setSelectedSector(sector);
  }

  if (loading) {
    return (
      <div style={{ minHeight: "100vh", background: "#0d1117", display: "flex",
        alignItems: "center", justifyContent: "center", color: "#fff" }}>
        Loading world…
      </div>
    );
  }

  return (
    <div style={styles.root}>
      {/* Top bar */}
      <header style={styles.header}>
        <button style={styles.backBtn} onClick={() => navigate("/worlds")}>← Worlds</button>
        <span style={styles.worldName}>{world?.name ?? "..."}</span>
        <div style={styles.tabs}>
          {(["armies", "nations"] as Tab[]).map((t) => (
            <button
              key={t}
              style={{ ...styles.tabBtn, ...(tab === t ? styles.tabActive : {}) }}
              onClick={() => setTab(t)}
            >
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
          <button style={styles.tabBtn} onClick={() => navigate(`/game/${worldId}/inbox`)}>
            Inbox
          </button>
        </div>
      </header>

      {/* Map + side panel */}
      <div style={styles.body}>
        {/* Left sidebar */}
        <div style={styles.sidebar}>
          {tab === "armies" && worldId && (
            <ArmyPanel
              worldId={worldId}
              armies={myArmies}
              selectedHex={selectedHex}
              onActionDone={load}
            />
          )}
          {tab === "nations" && (
            <div style={{ padding: 12 }}>
              <h4 style={{ color: "#ccc", margin: "0 0 8px", fontSize: 13 }}>Nations</h4>
              {nations.map((n) => (
                <div key={n.id} style={styles.nationCard}>
                  <span style={{ color: "#fff", fontSize: 13 }}>{n.name}</span>
                  <span style={{ color: "#888", fontSize: 11 }}>{n.player_class}</span>
                  <span style={{ color: "#ffd700", fontSize: 11 }}>VP: {n.victory_points}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Map canvas */}
        <div style={styles.mapArea}>
          <HexMap
            sectors={sectors}
            armies={armies}
            nations={nations}
            selectedHex={selectedHex}
            onSelectHex={handleSelectHex}
          />
          {selectedSector && worldId && (
            <SectorPanel
              worldId={worldId}
              sector={selectedSector}
              playerNation={myNation}
              onClose={() => { setSelectedSector(null); setSelectedHex(null); }}
              onActionDone={load}
            />
          )}
        </div>
      </div>

      {/* Bottom resource bar */}
      {myNation && world && (
        <NationDashboard nation={myNation} worldTurn={world.turn} />
      )}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  root: {
    display: "flex", flexDirection: "column", height: "100vh",
    background: "#0d1117", color: "#fff", overflow: "hidden",
  },
  header: {
    display: "flex", alignItems: "center", gap: 16,
    padding: "8px 16px", background: "#1c1c2e", borderBottom: "1px solid #333",
    flexShrink: 0,
  },
  backBtn: {
    background: "none", border: "1px solid #444", borderRadius: 4,
    color: "#aaa", cursor: "pointer", fontSize: 12, padding: "4px 8px",
  },
  worldName: { color: "#ffd700", fontWeight: "bold", fontSize: 16, flex: 1 },
  tabs: { display: "flex", gap: 4 },
  tabBtn: {
    padding: "4px 12px", background: "none", border: "1px solid #333",
    borderRadius: 4, color: "#888", cursor: "pointer", fontSize: 12,
  },
  tabActive: { background: "#2c3e50", color: "#fff", borderColor: "#555" },
  body: { display: "flex", flex: 1, overflow: "hidden" },
  sidebar: {
    width: 220, background: "#12121f", borderRight: "1px solid #333",
    display: "flex", flexDirection: "column", overflowY: "auto", flexShrink: 0,
  },
  mapArea: {
    flex: 1, position: "relative", overflow: "hidden",
  },
  nationCard: {
    display: "flex", flexDirection: "column", padding: "6px 8px",
    borderBottom: "1px solid #222",
  },
};
