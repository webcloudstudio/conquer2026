/**
 * Manage Worlds — any authenticated user can create worlds and manage
 * the ones they administer.
 * World admins can: initialize map, process turns, toggle maintenance, add co-admins.
 * Global admins additionally see the Users tab for server-level user management.
 */

import React, { useEffect, useState } from "react";
import { listMyWorlds, processTurn, initWorld, toggleMaintenance, addWorldAdmin } from "../api/game";
import { api } from "../api/client";
import type { World } from "../types";
import { useAuthStore } from "../store/auth";

interface AdminUser {
  id: string; username: string; email: string;
  is_active: boolean; is_admin: boolean; created_at: string;
}

type Tab = "worlds" | "users";

export function ManageWorldsPage() {
  const { user } = useAuthStore();
  const [tab, setTab] = useState<Tab>("worlds");
  const [worlds, setWorlds] = useState<World[]>([]);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [log, setLog] = useState<string[]>([]);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const [seed, setSeed] = useState("");
  const [coAdminInputs, setCoAdminInputs] = useState<Record<string, string>>({});

  useEffect(() => {
    loadWorlds();
    if (user?.is_admin) loadUsers();
  }, [user]);

  async function loadWorlds() {
    try { setWorlds(await listMyWorlds()); }
    catch { addLog("✗ Could not load worlds"); }
  }
  async function loadUsers() {
    try {
      const r = await api.get<AdminUser[]>("/admin/users");
      setUsers(r.data);
    } catch { addLog("✗ Could not load users"); }
  }

  function addLog(msg: string) {
    setLog((prev) => [`[${new Date().toLocaleTimeString()}] ${msg}`, ...prev.slice(0, 49)]);
  }

  async function handleCreateWorld(e: React.FormEvent) {
    e.preventDefault();
    try {
      await api.post("/worlds/", { name: newName, mapx: 79, mapy: 49 });
      addLog(`✓ World "${newName}" created — you are its admin`);
      setCreating(false); setNewName("");
      await loadWorlds();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      addLog(`✗ Create: ${err?.response?.data?.detail ?? "error"}`);
    }
  }

  async function handleInit(w: World) {
    addLog(`Initializing ${w.name}…`);
    try {
      const r = await initWorld(w.id, { seed: seed ? parseInt(seed) : undefined });
      addLog(`✓ ${w.name}: ${r.sectors} sectors, ${r.npc_nations} NPC nations`);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      addLog(`✗ ${w.name} init: ${err?.response?.data?.detail ?? "error"}`);
    }
  }

  async function handleTurn(w: World) {
    addLog(`Processing turn for ${w.name}…`);
    try {
      const r = await processTurn(w.id);
      addLog(`✓ ${w.name}: turn ${r.new_turn} (${r.nations_processed} nations)`);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      addLog(`✗ ${w.name} turn: ${err?.response?.data?.detail ?? "error"}`);
    }
  }

  async function handleMaint(w: World) {
    try {
      const r = await toggleMaintenance(w.id);
      addLog(`✓ ${w.name}: maintenance ${r.maintenance ? "ON" : "OFF"}`);
      await loadWorlds();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      addLog(`✗ ${w.name} maint: ${err?.response?.data?.detail ?? "error"}`);
    }
  }

  async function handleAddAdmin(worldId: string) {
    const username = coAdminInputs[worldId]?.trim();
    if (!username) return;
    try {
      await addWorldAdmin(worldId, username);
      addLog(`✓ Added ${username} as co-admin`);
      setCoAdminInputs((p) => ({ ...p, [worldId]: "" }));
      await loadWorlds();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      addLog(`✗ Add co-admin: ${err?.response?.data?.detail ?? "error"}`);
    }
  }

  async function handleUserAction(userId: string, action: string) {
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
    <div style={s.page}>
      <div style={s.topRow}>
        <div style={s.tabs}>
          <button style={tab === "worlds" ? s.tabActive : s.tab} onClick={() => setTab("worlds")}>
            My Worlds
          </button>
          {user?.is_admin && (
            <button style={tab === "users" ? s.tabActive : s.tab} onClick={() => setTab("users")}>
              All Users
            </button>
          )}
        </div>
        {tab === "worlds" && (
          <button style={s.createBtn} onClick={() => setCreating(true)}>+ New World</button>
        )}
      </div>

      <div style={s.body}>
        <div style={s.main}>

          {/* ── My Worlds tab ── */}
          {tab === "worlds" && (
            <>
              {worlds.length === 0 && (
                <div style={s.empty}>
                  <p>You don't administer any worlds yet.</p>
                  <p>Click <strong>+ New World</strong> to create one — you'll automatically become its admin.</p>
                </div>
              )}
              {worlds.map((w) => (
                <div key={w.id} style={s.card}>
                  <div style={s.cardTop}>
                    <div>
                      <span style={s.worldName}>{w.name}</span>
                      <span style={s.meta}> · Turn {w.turn} · {w.mapx}×{w.mapy}</span>
                      {w.is_maintenance && <span style={s.maintBadge}>MAINT</span>}
                    </div>
                    <div style={s.adminList}>
                      Admins: {w.admins.map((a) => a.username).join(", ") || "—"}
                    </div>
                  </div>
                  <div style={s.actions}>
                    <button style={s.btn} onClick={() => handleInit(w)}>Init Map</button>
                    <button style={s.btnWarn} onClick={() => handleTurn(w)}>Process Turn</button>
                    <button style={s.btnGhost} onClick={() => handleMaint(w)}>
                      {w.is_maintenance ? "Disable Maint" : "Enable Maint"}
                    </button>
                    <input
                      style={s.seedIn}
                      placeholder="seed (opt)"
                      value={seed}
                      onChange={(e) => setSeed(e.target.value)}
                    />
                  </div>
                  <div style={s.coAdminRow}>
                    <input
                      style={s.coAdminIn}
                      placeholder="Add co-admin by username…"
                      value={coAdminInputs[w.id] ?? ""}
                      onChange={(e) => setCoAdminInputs((p) => ({ ...p, [w.id]: e.target.value }))}
                      onKeyDown={(e) => e.key === "Enter" && handleAddAdmin(w.id)}
                    />
                    <button style={s.btn} onClick={() => handleAddAdmin(w.id)}>Add</button>
                  </div>
                </div>
              ))}
            </>
          )}

          {/* ── All Users tab (global admin only) ── */}
          {tab === "users" && (
            <>
              <table style={s.table}>
                <thead>
                  <tr>
                    {["Username", "Email", "Status", "Role", "Joined", "Actions"].map((h) => (
                      <th key={h} style={s.th}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id} style={{ opacity: u.is_active ? 1 : 0.5 }}>
                      <td style={s.td}>{u.username}</td>
                      <td style={s.td}>{u.email}</td>
                      <td style={s.td}>
                        <span style={u.is_active ? s.badgeGreen : s.badgeRed}>
                          {u.is_active ? "Active" : "Banned"}
                        </span>
                      </td>
                      <td style={s.td}>
                        <span style={u.is_admin ? s.badgeGold : s.badgeGray}>
                          {u.is_admin ? "Admin" : "Player"}
                        </span>
                      </td>
                      <td style={s.td}>{new Date(u.created_at).toLocaleDateString()}</td>
                      <td style={s.td}>
                        <div style={{ display: "flex", gap: 4 }}>
                          {!u.is_admin && u.id !== user?.id && (
                            <button style={s.btnSm} onClick={() => handleUserAction(u.id, "promote")}>Promote</button>
                          )}
                          {u.is_admin && u.id !== user?.id && (
                            <button style={s.btnSmWarn} onClick={() => handleUserAction(u.id, "demote")}>Demote</button>
                          )}
                          {u.is_active && u.id !== user?.id && (
                            <button style={s.btnSmDanger} onClick={() => handleUserAction(u.id, "deactivate")}>Ban</button>
                          )}
                          {!u.is_active && (
                            <button style={s.btnSm} onClick={() => handleUserAction(u.id, "activate")}>Unban</button>
                          )}
                          {u.id === user?.id && <span style={{ color: "#555", fontSize: 11 }}>(you)</span>}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </div>

        {/* Activity log */}
        <div style={s.logPanel}>
          <p style={s.logTitle}>Activity Log</p>
          <div style={s.logBody}>
            {log.length === 0 && <p style={{ color: "#555", fontSize: 11 }}>No activity yet</p>}
            {log.map((l, i) => <p key={i} style={s.logLine}>{l}</p>)}
          </div>
        </div>
      </div>

      {/* Create world modal */}
      {creating && (
        <div style={s.overlay}>
          <div style={s.modal}>
            <h3 style={{ color: "#fff", margin: "0 0 16px" }}>Create New World</h3>
            <form onSubmit={handleCreateWorld} style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              <input style={s.input} placeholder="World name" value={newName}
                onChange={(e) => setNewName(e.target.value)} required autoFocus />
              <div style={{ display: "flex", gap: 8 }}>
                <button type="submit" style={s.createBtn}>Create</button>
                <button type="button" style={s.cancelBtn} onClick={() => setCreating(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  page: { display: "flex", flexDirection: "column", height: "100%", background: "#0d1117" },
  topRow: {
    display: "flex", alignItems: "center", gap: 16, justifyContent: "space-between",
    padding: "16px 24px", borderBottom: "1px solid #21262d",
  },
  tabs: { display: "flex", gap: 4 },
  tab: {
    padding: "5px 16px", background: "none", border: "1px solid #30363d",
    borderRadius: 6, color: "#8b949e", cursor: "pointer", fontSize: 13,
  },
  tabActive: {
    padding: "5px 16px", background: "#21262d", border: "1px solid #4a6fa5",
    borderRadius: 6, color: "#fff", cursor: "pointer", fontSize: 13, fontWeight: 600,
  },
  createBtn: {
    padding: "6px 16px", background: "#238636", border: "none",
    borderRadius: 6, color: "#fff", cursor: "pointer", fontSize: 13, fontWeight: 600,
  },
  body: { display: "flex", flex: 1, overflow: "hidden" },
  main: { flex: 1, padding: 24, overflowY: "auto" },
  empty: { color: "#8b949e", padding: "32px 0" },
  card: {
    background: "#161b22", border: "1px solid #30363d",
    borderRadius: 8, padding: 18, marginBottom: 14,
  },
  cardTop: { marginBottom: 10 },
  worldName: { color: "#fff", fontWeight: 700, fontSize: 15 },
  meta: { color: "#8b949e", fontSize: 12 },
  maintBadge: {
    marginLeft: 8, background: "#b91c1c", color: "#fff",
    fontSize: 10, padding: "2px 6px", borderRadius: 3,
  },
  adminList: { color: "#8b949e", fontSize: 12, marginTop: 4 },
  actions: { display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" },
  coAdminRow: { display: "flex", gap: 8, marginTop: 10 },
  btn: {
    padding: "4px 12px", background: "#21262d", border: "1px solid #30363d",
    borderRadius: 5, color: "#c9d1d9", cursor: "pointer", fontSize: 12,
  },
  btnWarn: {
    padding: "4px 12px", background: "#7b2020", border: "1px solid #a33",
    borderRadius: 5, color: "#faa", cursor: "pointer", fontSize: 12,
  },
  btnGhost: {
    padding: "4px 12px", background: "none", border: "1px solid #30363d",
    borderRadius: 5, color: "#8b949e", cursor: "pointer", fontSize: 12,
  },
  seedIn: {
    padding: "4px 8px", background: "#0d1117", border: "1px solid #30363d",
    borderRadius: 5, color: "#fff", fontSize: 12, width: 80,
  },
  coAdminIn: {
    flex: 1, padding: "5px 10px", background: "#0d1117", border: "1px solid #30363d",
    borderRadius: 5, color: "#fff", fontSize: 12,
  },
  logPanel: {
    width: 300, background: "#0a0a14", borderLeft: "1px solid #21262d",
    display: "flex", flexDirection: "column",
  },
  logTitle: { color: "#8b949e", margin: "12px 12px 8px", fontSize: 12, fontWeight: 600 },
  logBody: { flex: 1, overflowY: "auto", padding: "0 12px 12px" },
  logLine: { color: "#7fc", fontSize: 11, margin: "2px 0", fontFamily: "monospace" },
  table: { width: "100%", borderCollapse: "collapse", fontSize: 13 },
  th: {
    color: "#8b949e", textAlign: "left", padding: "6px 10px",
    borderBottom: "1px solid #21262d", fontWeight: 500,
  },
  td: { color: "#c9d1d9", padding: "8px 10px", borderBottom: "1px solid #1e1e30" },
  badgeGreen: { background: "#1a4a2a", color: "#5f9", fontSize: 11, padding: "2px 7px", borderRadius: 10 },
  badgeRed: { background: "#4a1a1a", color: "#f55", fontSize: 11, padding: "2px 7px", borderRadius: 10 },
  badgeGold: { background: "#4a3800", color: "#fc0", fontSize: 11, padding: "2px 7px", borderRadius: 10 },
  badgeGray: { background: "#222", color: "#888", fontSize: 11, padding: "2px 7px", borderRadius: 10 },
  btnSm: {
    padding: "2px 8px", background: "#21262d", border: "1px solid #30363d",
    borderRadius: 3, color: "#adf", cursor: "pointer", fontSize: 11,
  },
  btnSmWarn: {
    padding: "2px 8px", background: "#3a3000", border: "1px solid #665500",
    borderRadius: 3, color: "#fc0", cursor: "pointer", fontSize: 11,
  },
  btnSmDanger: {
    padding: "2px 8px", background: "#3a1010", border: "1px solid #661111",
    borderRadius: 3, color: "#f88", cursor: "pointer", fontSize: 11,
  },
  overlay: {
    position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)",
    display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100,
  },
  modal: {
    background: "#161b22", border: "1px solid #30363d", borderRadius: 8, padding: 24, width: 360,
  },
  input: {
    padding: "8px 10px", background: "#0d1117", border: "1px solid #30363d",
    borderRadius: 5, color: "#fff", fontSize: 13, width: "100%",
  },
  cancelBtn: {
    padding: "6px 14px", background: "none", border: "1px solid #555",
    borderRadius: 5, color: "#aaa", cursor: "pointer",
  },
};
