/**
 * Admin panel — world management, turn processing, user management.
 * Only accessible to users with is_admin=true.
 */

import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { listWorlds, processTurn, initWorld } from "../api/game";
import { api } from "../api/client";
import type { World } from "../types";
import { useAuthStore } from "../store/auth";

interface AdminUser {
  id: string;
  username: string;
  email: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
}

type Tab = "worlds" | "users";

export function AdminPage() {
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const [tab, setTab] = useState<Tab>("worlds");
  const [worlds, setWorlds] = useState<World[]>([]);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [log, setLog] = useState<string[]>([]);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const [seed, setSeed] = useState("");

  useEffect(() => {
    if (user && !user.is_admin) navigate("/");
    listWorlds().then(setWorlds);
    loadUsers();
  }, [user, navigate]);

  async function loadUsers() {
    try {
      const res = await api.get<AdminUser[]>("/admin/users");
      setUsers(res.data);
    } catch {
      addLog("✗ Could not load users");
    }
  }

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

  async function handleUserAction(userId: string, action: "promote" | "demote" | "deactivate" | "activate") {
    try {
      await api.patch(`/admin/users/${userId}/${action}`);
      addLog(`✓ User ${action}d`);
      await loadUsers();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      addLog(`✗ ${action}: ${err?.response?.data?.detail ?? "error"}`);
    }
  }

  return (
    <div style={styles.page}>
      <header style={styles.header}>
        <button style={styles.back} onClick={() => navigate("/")}>← Home</button>
        <button style={{ ...styles.back, marginLeft: 4 }} onClick={() => navigate("/worlds")}>Worlds</button>
        <h2 style={styles.title}>Admin Panel</h2>
        <div style={styles.tabs}>
          <button style={tab === "worlds" ? styles.tabActive : styles.tab} onClick={() => setTab("worlds")}>
            Worlds
          </button>
          <button style={tab === "users" ? styles.tabActive : styles.tab} onClick={() => setTab("users")}>
            Users ({users.length})
          </button>
        </div>
        {tab === "worlds" && (
          <button style={styles.createBtn} onClick={() => setCreating(true)}>+ New World</button>
        )}
      </header>

      <div style={styles.body}>
        <div style={styles.main}>
          {/* Worlds tab */}
          {tab === "worlds" && (
            <>
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
            </>
          )}

          {/* Users tab */}
          {tab === "users" && (
            <>
              <h3 style={styles.sectionTitle}>User Accounts</h3>
              <table style={styles.table}>
                <thead>
                  <tr>
                    <th style={styles.th}>Username</th>
                    <th style={styles.th}>Email</th>
                    <th style={styles.th}>Status</th>
                    <th style={styles.th}>Role</th>
                    <th style={styles.th}>Joined</th>
                    <th style={styles.th}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id} style={{ opacity: u.is_active ? 1 : 0.5 }}>
                      <td style={styles.td}>{u.username}</td>
                      <td style={styles.td}>{u.email}</td>
                      <td style={styles.td}>
                        <span style={u.is_active ? styles.badgeGreen : styles.badgeRed}>
                          {u.is_active ? "Active" : "Banned"}
                        </span>
                      </td>
                      <td style={styles.td}>
                        <span style={u.is_admin ? styles.badgeGold : styles.badgeGray}>
                          {u.is_admin ? "Admin" : "Player"}
                        </span>
                      </td>
                      <td style={styles.td}>{new Date(u.created_at).toLocaleDateString()}</td>
                      <td style={styles.td}>
                        <div style={{ display: "flex", gap: 4 }}>
                          {!u.is_admin && u.id !== user?.id && (
                            <button style={styles.btnSmall} onClick={() => handleUserAction(u.id, "promote")}>
                              Promote
                            </button>
                          )}
                          {u.is_admin && u.id !== user?.id && (
                            <button style={styles.btnSmallWarn} onClick={() => handleUserAction(u.id, "demote")}>
                              Demote
                            </button>
                          )}
                          {u.is_active && u.id !== user?.id && (
                            <button style={styles.btnSmallDanger} onClick={() => handleUserAction(u.id, "deactivate")}>
                              Ban
                            </button>
                          )}
                          {!u.is_active && (
                            <button style={styles.btnSmall} onClick={() => handleUserAction(u.id, "activate")}>
                              Unban
                            </button>
                          )}
                          {u.id === user?.id && <span style={{ color: "#555", fontSize: 11 }}>(you)</span>}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {users.length === 0 && <p style={{ color: "#555" }}>No users registered yet</p>}
            </>
          )}
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
  title: { color: "#fff", margin: 0, fontSize: 18 },
  back: {
    background: "none", border: "1px solid #444", borderRadius: 4,
    color: "#aaa", cursor: "pointer", fontSize: 12, padding: "4px 8px",
  },
  tabs: { display: "flex", gap: 4, flex: 1 },
  tab: {
    padding: "5px 14px", background: "none", border: "1px solid #444",
    borderRadius: 4, color: "#888", cursor: "pointer", fontSize: 13,
  },
  tabActive: {
    padding: "5px 14px", background: "#2c3e50", border: "1px solid #4a6fa5",
    borderRadius: 4, color: "#fff", cursor: "pointer", fontSize: 13,
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
  table: { width: "100%", borderCollapse: "collapse", fontSize: 13 },
  th: {
    color: "#888", textAlign: "left", padding: "6px 10px",
    borderBottom: "1px solid #333", fontWeight: 500,
  },
  td: { color: "#ccc", padding: "8px 10px", borderBottom: "1px solid #1e1e30" },
  badgeGreen: {
    background: "#1a4a2a", color: "#5f9", fontSize: 11,
    padding: "2px 7px", borderRadius: 10,
  },
  badgeRed: {
    background: "#4a1a1a", color: "#f55", fontSize: 11,
    padding: "2px 7px", borderRadius: 10,
  },
  badgeGold: {
    background: "#4a3800", color: "#fc0", fontSize: 11,
    padding: "2px 7px", borderRadius: 10,
  },
  badgeGray: {
    background: "#222", color: "#888", fontSize: 11,
    padding: "2px 7px", borderRadius: 10,
  },
  btnSmall: {
    padding: "2px 8px", background: "#2c3e50", border: "1px solid #445",
    borderRadius: 3, color: "#adf", cursor: "pointer", fontSize: 11,
  },
  btnSmallWarn: {
    padding: "2px 8px", background: "#3a3000", border: "1px solid #665500",
    borderRadius: 3, color: "#fc0", cursor: "pointer", fontSize: 11,
  },
  btnSmallDanger: {
    padding: "2px 8px", background: "#3a1010", border: "1px solid #661111",
    borderRadius: 3, color: "#f88", cursor: "pointer", fontSize: 11,
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
