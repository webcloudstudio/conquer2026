/**
 * Panel shown in sidebar when player has not yet joined the world.
 */

import React, { useState } from "react";
import { joinWorld } from "../api/game";

const RACES = [
  "human", "elf", "dwarf", "orc", "halfling", "lizard", "pirate", "savage", "nomad",
];

const CLASSES: { value: string; label: string; desc: string }[] = [
  { value: "empire_builder", label: "Empire Builder", desc: "Bonus to sector growth and production" },
  { value: "warlord",        label: "Warlord",        desc: "Stronger armies, attack bonus" },
  { value: "trader",         label: "Trader",         desc: "Caravan income multiplier" },
  { value: "theocrat",       label: "Theocrat",       desc: "Magic power regen bonus" },
  { value: "diplomat",       label: "Diplomat",       desc: "Alliance and relations bonuses" },
  { value: "artifact_hunter",label: "Artifact Hunter",desc: "Bonus to artifact discovery" },
  { value: "pathfinder",     label: "Pathfinder",     desc: "Extended army movement range" },
  { value: "monster_lord",   label: "Monster Lord",   desc: "Command NPC monsters in battle" },
];

interface Props {
  worldId: string;
  onJoined: () => void;
}

export function JoinWorldPanel({ worldId, onJoined }: Props) {
  const [name, setName] = useState("");
  const [race, setRace] = useState("human");
  const [playerClass, setPlayerClass] = useState("empire_builder");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleJoin() {
    const trimmed = name.trim();
    if (!trimmed) { setError("Nation name is required"); return; }
    if (trimmed.length > 10) { setError("Name must be 10 characters or fewer"); return; }
    setBusy(true);
    setError("");
    try {
      await joinWorld(worldId, {
        name: trimmed,
        leader_title: "Leader",
        race,
        player_class: playerClass,
      });
      onJoined();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setError(err?.response?.data?.detail || "Failed to join world");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={styles.container}>
      <h4 style={styles.title}>Join This World</h4>
      <p style={styles.sub}>Create your nation to start playing.</p>

      <label style={styles.label}>Nation Name (max 10 chars)</label>
      <input
        style={styles.input}
        maxLength={10}
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="e.g. Khazadum"
      />

      <label style={styles.label}>Race</label>
      <select style={styles.select} value={race} onChange={(e) => setRace(e.target.value)}>
        {RACES.map((r) => (
          <option key={r} value={r}>
            {r.charAt(0).toUpperCase() + r.slice(1)}
          </option>
        ))}
      </select>

      <label style={styles.label}>Class</label>
      <select style={styles.select} value={playerClass} onChange={(e) => setPlayerClass(e.target.value)}>
        {CLASSES.map((c) => (
          <option key={c.value} value={c.value}>{c.label}</option>
        ))}
      </select>

      {playerClass && (
        <p style={styles.classDesc}>
          {CLASSES.find((c) => c.value === playerClass)?.desc}
        </p>
      )}

      {error && <p style={styles.error}>{error}</p>}

      <button style={styles.joinBtn} disabled={busy} onClick={handleJoin}>
        {busy ? "Joining…" : "Join World"}
      </button>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: { padding: 14, display: "flex", flexDirection: "column", gap: 6 },
  title: { color: "#ffd700", margin: "0 0 4px", fontSize: 14 },
  sub: { color: "#888", fontSize: 11, margin: "0 0 8px" },
  label: { color: "#aaa", fontSize: 11 },
  input: {
    background: "#0d1117", border: "1px solid #444", borderRadius: 4,
    color: "#fff", fontSize: 12, padding: "5px 8px", width: "100%",
  },
  select: {
    background: "#0d1117", border: "1px solid #444", borderRadius: 4,
    color: "#fff", fontSize: 12, padding: "5px 8px", width: "100%",
  },
  classDesc: { color: "#666", fontSize: 10, margin: "0 0 4px", fontStyle: "italic" },
  error: { color: "#f85149", fontSize: 11, margin: 0 },
  joinBtn: {
    marginTop: 8, padding: "8px 16px", background: "#238636", border: "1px solid #2ea043",
    borderRadius: 4, color: "#fff", fontSize: 13, cursor: "pointer", fontWeight: "bold",
  },
};
