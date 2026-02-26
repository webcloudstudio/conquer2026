/**
 * Main game page — hex map + side panels + army panel + resource bar.
 */

import React, { useCallback, useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { HexMap } from "../components/HexMap";
import { SectorPanel } from "../components/SectorPanel";
import { NationDashboard } from "../components/NationDashboard";
import { ArmyPanel } from "../components/ArmyPanel";
import { JoinWorldPanel } from "../components/JoinWorldPanel";
import {
  listSectors, listArmies, listMyArmies, listNations, getWorld, getMyNation,
} from "../api/game";
import type { Army, Nation, Sector, World } from "../types";
import { useAuthStore } from "../store/auth";

type Tab = "armies" | "nations";

// BFS to compute reachable hexes (even-r offset)
function computeReachable(
  army: Army,
  sectors: Sector[],
): { x: number; y: number }[] {
  const sectorMap = new Map(sectors.map((s) => [`${s.x},${s.y}`, s]));
  const visited = new Set<string>();
  const queue: { x: number; y: number; steps: number }[] = [
    { x: army.x, y: army.y, steps: 0 },
  ];
  visited.add(`${army.x},${army.y}`);
  const result: { x: number; y: number }[] = [];

  // Even-r offset neighbors
  function neighbors(x: number, y: number): { x: number; y: number }[] {
    const even = y % 2 === 0;
    return [
      { x: x + 1, y },
      { x: x - 1, y },
      { x: x, y: y - 1 },
      { x: x, y: y + 1 },
      { x: even ? x - 1 : x + 1, y: y - 1 },
      { x: even ? x - 1 : x + 1, y: y + 1 },
    ];
  }

  while (queue.length > 0) {
    const cur = queue.shift()!;
    for (const nb of neighbors(cur.x, cur.y)) {
      const key = `${nb.x},${nb.y}`;
      if (visited.has(key)) continue;
      const sec = sectorMap.get(key);
      if (!sec || sec.altitude === 0) continue; // skip water
      visited.add(key);
      if (cur.steps + 1 <= army.movement) {
        result.push({ x: nb.x, y: nb.y });
        queue.push({ x: nb.x, y: nb.y, steps: cur.steps + 1 });
      }
    }
  }
  return result;
}

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
  const [selectedArmy, setSelectedArmy] = useState<Army | null>(null);
  const [movementRange, setMovementRange] = useState<{ x: number; y: number }[] | null>(null);
  const [centerHex, setCenterHex] = useState<{ x: number; y: number } | null>(null);
  const [tab, setTab] = useState<Tab>("armies");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!worldId) return;
    const [w, s, a, ma, n, mn] = await Promise.all([
      getWorld(worldId),
      listSectors(worldId),
      listArmies(worldId),
      listMyArmies(worldId).catch(() => [] as Army[]),
      listNations(worldId),
      getMyNation(worldId).catch(() => null),
    ]);
    setWorld(w);
    setSectors(s);
    setArmies(a);
    setMyArmies(ma);
    setNations(n);
    setMyNation(mn);
    setLoading(false);
  }, [worldId]);

  useEffect(() => { load(); }, [load]);

  function handleSelectHex(x: number, y: number, sector: Sector | null) {
    setSelectedHex({ x, y });
    setSelectedSector(sector);
  }

  function handleSelectArmy(army: Army | null) {
    setSelectedArmy(army);
    if (army) {
      setMovementRange(computeReachable(army, sectors));
    } else {
      setMovementRange(null);
    }
  }

  function handleCenterMap(x: number, y: number) {
    setCenterHex({ x, y });
  }

  if (loading) {
    return (
      <div style={{ minHeight: "100vh", background: "#0d1117", display: "flex",
        alignItems: "center", justifyContent: "center", color: "#fff" }}>
        Loading world…
      </div>
    );
  }

  const showJoinPanel = !myNation;

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
          {showJoinPanel && worldId && (
            <JoinWorldPanel worldId={worldId} onJoined={load} />
          )}
          {!showJoinPanel && tab === "armies" && worldId && (
            <ArmyPanel
              worldId={worldId}
              armies={myArmies}
              selectedHex={selectedHex}
              onActionDone={load}
              onSelectArmy={handleSelectArmy}
              onCenterMap={handleCenterMap}
            />
          )}
          {!showJoinPanel && tab === "nations" && (
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
            myNation={myNation}
            selectedHex={selectedHex}
            movementRange={movementRange}
            centerHex={centerHex}
            onSelectHex={handleSelectHex}
          />
          {selectedSector && worldId && (
            <SectorPanel
              worldId={worldId}
              sector={selectedSector}
              playerNation={myNation}
              nations={nations}
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
