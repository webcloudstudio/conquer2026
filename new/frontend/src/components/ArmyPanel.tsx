/**
 * Army list panel — shows armies and queues move/attack orders.
 */

import React, { useState } from "react";
import type { Army } from "../types";
import { orderAttack, orderDisband, orderMove } from "../api/game";

interface Props {
  worldId: string;
  armies: Army[];
  selectedHex: { x: number; y: number } | null;
  onActionDone: () => void;
}

export function ArmyPanel({ worldId, armies, selectedHex, onActionDone }: Props) {
  const [selectedArmy, setSelectedArmy] = useState<string | null>(null);
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);

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
      <h4 style={styles.title}>Your Armies</h4>
      {armies.length === 0 && <p style={styles.empty}>No active armies</p>}
      {armies.map((a) => (
        <div
          key={a.id}
          style={{ ...styles.card, borderColor: selectedArmy === a.id ? "#ffd700" : "#333" }}
          onClick={() => setSelectedArmy(a.id === selectedArmy ? null : a.id)}
        >
          <div style={styles.row}>
            <span style={styles.strength}>⚔️ {a.strength}</span>
            <span style={styles.pos}>({a.x},{a.y})</span>
            <span style={styles.mv}>mv:{a.movement}</span>
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
      ))}
      {msg && <p style={styles.msg}>{msg}</p>}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: { padding: 12, overflowY: "auto", flex: 1 },
  title: { color: "#ccc", margin: "0 0 8px", fontSize: 13 },
  empty: { color: "#555", fontSize: 12 },
  card: {
    border: "1px solid #333", borderRadius: 4, padding: "6px 8px",
    marginBottom: 6, cursor: "pointer", background: "#12121f",
  },
  row: { display: "flex", gap: 8, alignItems: "center" },
  strength: { color: "#fff", fontSize: 13, fontWeight: "bold" },
  pos: { color: "#888", fontSize: 11 },
  mv: { color: "#3498db", fontSize: 11, marginLeft: "auto" },
  actions: { display: "flex", gap: 6, marginTop: 6 },
  btn: {
    padding: "2px 8px", fontSize: 11, background: "#1e2d3d",
    border: "1px solid #445", borderRadius: 3, cursor: "pointer", color: "#7fc",
  },
  msg: { color: "#7fc", fontSize: 11, marginTop: 8 },
};
