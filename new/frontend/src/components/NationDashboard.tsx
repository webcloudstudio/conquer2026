/**
 * Nation resource dashboard — displayed at the bottom of the game screen.
 */

import React from "react";
import type { Nation } from "../types";

interface Props {
  nation: Nation;
  worldTurn: number;
}

export function NationDashboard({ nation, worldTurn }: Props) {
  const resources = [
    { icon: "🪙", label: "Talons", value: nation.talons, produced: nation.talons_produced },
    { icon: "💎", label: "Jewels", value: nation.jewels, produced: nation.jewels_produced },
    { icon: "⚙️", label: "Metals", value: nation.metals, produced: nation.metals_produced },
    { icon: "🌾", label: "Food", value: nation.food, produced: nation.food_produced },
    { icon: "🪵", label: "Wood", value: nation.wood, produced: nation.wood_produced },
  ];

  const powers = [
    { label: "🔥 Military", value: nation.power_fire, colour: "#e74c3c" },
    { label: "💧 Civilian", value: nation.power_water, colour: "#3498db" },
    { label: "🌍 Wizardry", value: nation.power_earth, colour: "#9b59b6" },
  ];

  return (
    <div style={styles.bar}>
      {/* Nation info */}
      <div style={styles.section}>
        <span style={styles.name}>{nation.name}</span>
        <span style={styles.sub}>{nation.player_class} · Turn {worldTurn}</span>
      </div>

      {/* Resources */}
      {resources.map(({ icon, label, value, produced }) => (
        <div key={label} style={styles.res}>
          <span style={styles.icon}>{icon}</span>
          <div style={{ display: "flex", alignItems: "baseline", gap: 3 }}>
            <span style={styles.val}>{value.toLocaleString()}</span>
            {produced > 0 && (
              <span style={{ color: "#3fb950", fontSize: 10 }}>+{produced.toLocaleString()}</span>
            )}
          </div>
          <span style={styles.lbl}>{label}</span>
        </div>
      ))}

      {/* Divider */}
      <div style={styles.divider} />

      {/* Magic powers */}
      {powers.map(({ label, value, colour }) => (
        <div key={label} style={styles.res}>
          <div style={{ ...styles.powerBar, width: Math.min(value / 2, 60) + "px", background: colour }} />
          <span style={{ ...styles.lbl, color: colour }}>{label}: {value}</span>
        </div>
      ))}

      {/* Morale + VP */}
      <div style={styles.res}>
        <span style={styles.icon}>⚔️</span>
        <span style={styles.val}>{nation.attr_morale}%</span>
        <span style={styles.lbl}>Morale</span>
      </div>
      <div style={styles.res}>
        <span style={styles.icon}>🏆</span>
        <span style={styles.val}>{nation.victory_points}</span>
        <span style={styles.lbl}>VP</span>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  bar: {
    display: "flex", alignItems: "center", gap: 20,
    background: "#0d1117", borderTop: "1px solid #333",
    padding: "8px 16px", flexShrink: 0,
  },
  section: { display: "flex", flexDirection: "column", minWidth: 120 },
  name: { color: "#fff", fontWeight: "bold", fontSize: 14 },
  sub: { color: "#888", fontSize: 11 },
  res: { display: "flex", flexDirection: "column", alignItems: "center", minWidth: 56 },
  icon: { fontSize: 16 },
  val: { color: "#fff", fontSize: 13, fontWeight: "bold" },
  lbl: { color: "#666", fontSize: 10 },
  divider: { width: 1, height: 40, background: "#333" },
  powerBar: { height: 6, borderRadius: 3, minWidth: 4 },
};
