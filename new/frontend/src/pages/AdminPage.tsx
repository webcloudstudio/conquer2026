/**
 * Admin panel — world management, turn processing, world initialization.
 * Only accessible to users with is_admin=true.
 */

import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { listWorlds, processTurn, initWorld } from "../api/game";
import { api } from "../api/client";
import type { World } from "../types";
import { useAuthStore } from "../store/auth";

export function AdminPage() {
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const [worlds, setWorlds] = useState<World[]>([]);
  const [log, setLog] = useState<string[]>([]);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const [seed, setSeed] = useState("");

  useEffect(() => {
    if (user && !user.is_admin) navigate("/");
    listWorlds().then(setWorlds);
  }, [user, navigate]);

  function addLog(msg: string) {
    setLog((prev) => [`[${new Date().toLocaleTimeString()}] ${msg}`, ...prev.slice(0, 49)]);
  }

  async function handleProcessTurn(worldId: string, name: string) {
    addLog(`Processing turn for ${name}…`);
    try {
      const res = await processTurn(worldId);
      addLog(`✓ ${name}: turn ${res.new_turn} complete (${res.nations_processed} nations)`);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      addLog(`✗ ${name}: ${err?.response?.data?.detail ?? "error"}`);
    }
  }

  async function handleInitWorld(worldId: string, name: string) {
    addLog(`Initializing ${name}…`);
    try {
      const res = await initWorld(worldId, { seed: seed ? parseInt(seed) : undefined });
      addLog(`✓ ${name}: ${res.sectors} sectors, ${res.npc_nations} NPC nations`);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      addLog(`✗ ${name}: ${err?.response?.data?.detail ?? "error"}`);
    }
  }

  async function handleCreateWorld(e: React.FormEvent) {
    e.preventDefault();
    try {
      await api.post("/worlds/", { name: newName, mapx: 79, mapy: 49 });
      addLog(`✓ World "${newName}" created`);
      setCreating(false);
      setNewName("");
      const updated = await listWorlds();
      setWorlds(updated);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      addLog(`✗ Create world: ${err?.response?.data?.detail ?? "error"}`);
    }
  }

  return (
    <div style={styles.page}>
      <header style={styles.header}>
        <button style={styles.back} onClick={() => navigate("/")}>← Worlds</button>
        <h2 style={styles.title}>Admin Panel</h2>
        <button style={styles.createBtn} onClick={() => setCreating(true)}>+ New World</button>
      </header>

      <div style={styles.body}>
        {/* World list */}
        <div style={styles.main}>
          <h3 style={styles.sectionTitle}>Worlds</h3>
          {worlds.map((w) => (
            <div key={w.id} style={styles.card}>
              <div style={styles.cardHeader}>
                <span style={styles.worldName}>{w.name}</span>
                <span style={styles.meta}>Turn {w.turn} · {w.mapx}×{w.mapy}</span>
                {w.is_maintenance && <span style={styles.maint}>MAINT</span>}
              </div>
              <div style={styles.cardActions}>
                <button style={styles.btn} onClick={() => handleInitWorld(w.id, w.name)}>
                  Initialize Map
                </button>
                <button style={styles.btnDanger} onClick={() => handleProcessTurn(w.id, w.name)}>
                  Process Turn
                </button>
                <input
                  style={styles.seedInput}
                  placeholder="seed (opt)"
                  value={seed}
                  onChange={(e) => setSeed(e.target.value)}
                />
              </div>
            </div>
          ))}
          {worlds.length === 0 && <p style={{ color: "#555" }}>No worlds yet</p>}
        </div>

        {/* Log */}
        <div style={styles.logPanel}>
          <h3 style={styles.sectionTitle}>Activity Log</h3>
          <div style={styles.logBody}>
            {log.length === 0 && <p style={{ color: "#555", fontSize: 12 }}>No activity yet</p>}
            {log.map((l, i) => (
              <p key={i} style={styles.logLine}>{l}</p>
            ))}
          </div>
        </div>
      </div>

      {/* Create world modal */}
      {creating && (
        <div style={styles.overlay}>
          <div style={styles.modal}>
            <h3 style={{ color: "#fff", margin: "0 0 16px" }}>Create New World</h3>
            <form onSubmit={handleCreateWorld} style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              <input
                style={styles.input} placeholder="World name"
                value={newName} onChange={(e) => setNewName(e.target.value)} required
              />
              <div style={{ display: "flex", gap: 8 }}>
                <button type="submit" style={styles.createBtn}>Create</button>
                <button type="button" style={styles.cancelBtn} onClick={() => setCreating(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: { display: "flex", flexDirection: "column", height: "100vh", background: "#0d1117" },
  header: {
    display: "flex", alignItems: "center", gap: 16,
    padding: "10px 20px", background: "#1c1c2e", borderBottom: "1px solid #333",
  },
  title: { color: "#fff", margin: 0, flex: 1, fontSize: 18 },
  back: {
    background: "none", border: "1px solid #444", borderRadius: 4,
    color: "#aaa", cursor: "pointer", fontSize: 12, padding: "4px 8px",
  },
  createBtn: {
    padding: "6px 14px", background: "#27ae60", border: "none",
    borderRadius: 4, color: "#fff", cursor: "pointer", fontSize: 13,
  },
  body: { display: "flex", flex: 1, overflow: "hidden" },
  main: { flex: 1, padding: 24, overflowY: "auto" },
  logPanel: {
    width: 320, background: "#0a0a14", borderLeft: "1px solid #222",
    display: "flex", flexDirection: "column",
  },
  sectionTitle: { color: "#aaa", margin: "0 0 12px", fontSize: 14 },
  card: {
    background: "#1c1c2e", border: "1px solid #333", borderRadius: 6,
    padding: 16, marginBottom: 12,
  },
  cardHeader: { display: "flex", alignItems: "center", gap: 12, marginBottom: 10 },
  worldName: { color: "#fff", fontWeight: "bold", fontSize: 14 },
  meta: { color: "#666", fontSize: 12 },
  maint: {
    background: "#c0392b", color: "#fff", fontSize: 10,
    padding: "2px 6px", borderRadius: 3,
  },
  cardActions: { display: "flex", alignItems: "center", gap: 8 },
  btn: {
    padding: "4px 12px", background: "#2c3e50", border: "1px solid #445",
    borderRadius: 4, color: "#ccc", cursor: "pointer", fontSize: 12,
  },
  btnDanger: {
    padding: "4px 12px", background: "#7b2020", border: "1px solid #a33",
    borderRadius: 4, color: "#faa", cursor: "pointer", fontSize: 12,
  },
  seedInput: {
    padding: "4px 8px", background: "#12121f", border: "1px solid #444",
    borderRadius: 4, color: "#fff", fontSize: 12, width: 80,
  },
  logBody: { flex: 1, overflowY: "auto", padding: "0 12px 12px" },
  logLine: { color: "#7fc", fontSize: 11, margin: "2px 0", fontFamily: "monospace" },
  overlay: {
    position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)",
    display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100,
  },
  modal: {
    background: "#1c1c2e", border: "1px solid #333", borderRadius: 8, padding: 24, width: 360,
  },
  input: {
    padding: "8px 10px", background: "#12121f", border: "1px solid #444",
    borderRadius: 4, color: "#fff", fontSize: 13, width: "100%",
  },
  cancelBtn: {
    padding: "6px 14px", background: "none", border: "1px solid #555",
    borderRadius: 4, color: "#aaa", cursor: "pointer",
  },
};
