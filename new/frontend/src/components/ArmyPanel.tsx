/**
 * Army list panel — shows armies and queues move/attack orders.
 */

import React, { useState } from "react";
import type { Army } from "../types";
import { UnitTypeName } from "../types";
import { orderAttack, orderDisband, orderMove } from "../api/game";

const GUIDE_KEY = "armyGuideCollapsed";

interface Props {
  worldId: string;
  armies: Army[];
  selectedHex: { x: number; y: number } | null;
  onActionDone: () => void;
  onSelectArmy: (army: Army | null) => void;
  onCenterMap: (x: number, y: number) => void;
}

export function ArmyPanel({
  worldId, armies, selectedHex, onActionDone, onSelectArmy, onCenterMap,
}: Props) {
  const [selectedArmy, setSelectedArmy] = useState<string | null>(null);
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);
  const [guideCollapsed, setGuideCollapsed] = useState(
    () => localStorage.getItem(GUIDE_KEY) === "1"
  );

  function toggleGuide() {
    const next = !guideCollapsed;
    setGuideCollapsed(next);
    localStorage.setItem(GUIDE_KEY, next ? "1" : "0");
  }

  function selectArmy(army: Army) {
    const newId = army.id === selectedArmy ? null : army.id;
    setSelectedArmy(newId);
    onSelectArmy(newId ? army : null);
  }

  async function doMove(armyId: string) {
    if (!selectedHex) { setMsg("Click a hex first"); return; }
    setBusy(true);
    try {
      await orderMove(worldId, armyId, selectedHex.x, selectedHex.y);
      setMsg(`Move order queued → (${selectedHex.x},${selectedHex.y})`);
      onActionDone();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setMsg(err?.response?.data?.detail || "Error");
    } finally { setBusy(false); }
  }

  async function doAttack(armyId: string) {
    if (!selectedHex) { setMsg("Click a target hex first"); return; }
    setBusy(true);
    try {
      await orderAttack(worldId, armyId, selectedHex.x, selectedHex.y);
      setMsg(`Attack order queued → (${selectedHex.x},${selectedHex.y})`);
      onActionDone();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setMsg(err?.response?.data?.detail || "Error");
    } finally { setBusy(false); }
  }

  async function doDisband(armyId: string) {
    if (!window.confirm("Disband this army?")) return;
    setBusy(true);
    try {
      await orderDisband(worldId, armyId);
      setMsg("Disband order queued");
      onActionDone();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setMsg(err?.response?.data?.detail || "Error");
    } finally { setBusy(false); }
  }

  return (
    <div style={styles.container}>
      {/* Collapsible how-to guide */}
      <div style={styles.guide}>
        <button style={styles.guideToggle} onClick={toggleGuide}>
          📋 How to give orders {guideCollapsed ? "▸" : "▾"}
        </button>
        {!guideCollapsed && (
          <ol style={styles.guideList}>
            <li>Click an army card to select it</li>
            <li>Click any hex on the map</li>
            <li>Press <strong>Move →</strong> or <strong>Attack</strong></li>
          </ol>
        )}
        {!guideCollapsed && (
          <p style={styles.guideNote}>
            Orders are queued — they execute when the admin processes the turn.
          </p>
        )}
      </div>

      <h4 style={styles.title}>Your Armies</h4>
      {armies.length === 0 && <p style={styles.empty}>No active armies</p>}
      {armies.map((a) => {
        const strPct = Math.min((a.strength / 3000) * 100, 100);
        const unitLabel = UnitTypeName[a.unit_type] ?? `Type ${a.unit_type}`;
        return (
          <div
            key={a.id}
            style={{ ...styles.card, borderColor: selectedArmy === a.id ? "#ffd700" : "#333" }}
            onClick={() => selectArmy(a)}
          >
            <div style={styles.unitType}>{unitLabel}</div>
            <div style={styles.row}>
              <span style={styles.strength}>⚔️ {a.strength.toLocaleString()}</span>
              <span style={styles.pos}>({a.x},{a.y})</span>
            </div>
            {/* Strength bar */}
            <div style={styles.barBg}>
              <div style={{ ...styles.barFill, width: `${strPct}%` }} />
            </div>
            <div style={styles.statsRow}>
              <span style={styles.stat}>Mv:{a.movement}</span>
              <span style={styles.stat}>Sply:{a.supply}</span>
              <span style={styles.stat}>Eff:{a.efficiency}%</span>
              <button
                style={styles.findBtn}
                onClick={(e) => { e.stopPropagation(); onCenterMap(a.x, a.y); }}
                title="Center map on this army"
              >
                📍 Find
              </button>
            </div>
            {selectedArmy === a.id && (
              <div style={styles.actions}>
                <button style={styles.btn} disabled={busy} onClick={(e) => { e.stopPropagation(); doMove(a.id); }}>
                  Move→
                </button>
                <button style={{ ...styles.btn, color: "#e74c3c" }} disabled={busy} onClick={(e) => { e.stopPropagation(); doAttack(a.id); }}>
                  Attack
                </button>
                <button style={{ ...styles.btn, color: "#888" }} disabled={busy} onClick={(e) => { e.stopPropagation(); doDisband(a.id); }}>
                  Disband
                </button>
              </div>
            )}
          </div>
        );
      })}
      {msg && <p style={styles.msg}>{msg}</p>}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: { padding: 12, overflowY: "auto", flex: 1 },
  guide: {
    background: "#1a1a2e", border: "1px solid #333", borderRadius: 4,
    padding: "6px 8px", marginBottom: 10, fontSize: 11,
  },
  guideToggle: {
    background: "none", border: "none", color: "#7fc", cursor: "pointer",
    fontSize: 11, padding: 0, fontWeight: "bold",
  },
  guideList: { color: "#aaa", margin: "6px 0 4px", paddingLeft: 18, lineHeight: 1.6 },
  guideNote: { color: "#666", margin: 0, fontSize: 10 },
  title: { color: "#ccc", margin: "0 0 8px", fontSize: 13 },
  empty: { color: "#555", fontSize: 12 },
  card: {
    border: "1px solid #333", borderRadius: 4, padding: "6px 8px",
    marginBottom: 6, cursor: "pointer", background: "#12121f",
  },
  unitType: { color: "#7fc", fontSize: 11, fontWeight: "bold", marginBottom: 3 },
  row: { display: "flex", gap: 8, alignItems: "center" },
  strength: { color: "#fff", fontSize: 13, fontWeight: "bold" },
  pos: { color: "#888", fontSize: 11, marginLeft: "auto" },
  barBg: { height: 4, background: "#333", borderRadius: 2, margin: "4px 0" },
  barFill: { height: 4, background: "#3fb950", borderRadius: 2, transition: "width 0.3s" },
  statsRow: { display: "flex", gap: 4, alignItems: "center", marginTop: 2 },
  stat: { color: "#888", fontSize: 10 },
  findBtn: {
    marginLeft: "auto", padding: "1px 6px", fontSize: 10, background: "#1e2d3d",
    border: "1px solid #445", borderRadius: 3, cursor: "pointer", color: "#79c0ff",
  },
  actions: { display: "flex", gap: 6, marginTop: 6 },
  btn: {
    padding: "2px 8px", fontSize: 11, background: "#1e2d3d",
    border: "1px solid #445", borderRadius: 3, cursor: "pointer", color: "#7fc",
  },
  msg: { color: "#7fc", fontSize: 11, marginTop: 8 },
};
