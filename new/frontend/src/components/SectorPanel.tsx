/**
 * Side panel showing selected sector details and designation controls.
 */

import React, { useState } from "react";
import type { Nation, Sector } from "../types";
import { DesignationLabel } from "../types";
import { designateSector } from "../api/game";

interface SectorPanelProps {
  worldId: string;
  sector: Sector | null;
  playerNation: Nation | null;
  onClose: () => void;
  onActionDone: () => void;
}

const TERRAIN_NAMES = ["Water", "Lowland", "Plains", "Hills", "Highland", "Mountain Foot", "Mountain", "Peak"];
const VEG_NAMES = ["Barren", "Sparse", "Grassland", "Forest", "Dense Forest", "Jungle",
  "Tundra", "Desert", "Savanna", "Wetland", "Coast", "Ice"];

const DESIGNATABLE = [1, 2, 3, 5, 6, 7, 8, 9, 11, 12, 13, 14, 15];

export function SectorPanel({ worldId, sector, playerNation, onClose, onActionDone }: SectorPanelProps) {
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  if (!sector) return null;

  const owned = sector.owner_nation_id && playerNation
    && sector.owner_nation_id === playerNation.id;

  async function handleDesignate(d: number) {
    setBusy(true);
    setMsg("");
    try {
      await designateSector(worldId, sector!.x, sector!.y, d);
      setMsg(`Designation order queued for turn.`);
      onActionDone();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setMsg(err?.response?.data?.detail || "Error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={styles.panel}>
      <button onClick={onClose} style={styles.close}>✕</button>
      <h3 style={styles.title}>Sector ({sector.x}, {sector.y})</h3>

      <table style={styles.table}>
        <tbody>
          <Row label="Terrain" value={TERRAIN_NAMES[sector.altitude] ?? sector.altitude} />
          <Row label="Vegetation" value={VEG_NAMES[sector.vegetation] ?? sector.vegetation} />
          <Row label="Designation" value={DesignationLabel[sector.designation] ?? "Unknown"} />
          <Row label="Efficiency" value={`${sector.efficiency}%`} />
          <Row label="Population" value={sector.population.toLocaleString()} />
          {sector.minerals > 0 && <Row label="Minerals" value={sector.minerals} />}
          {sector.tradegood > 0 && <Row label="Trade Good" value={sector.tradegood} />}
        </tbody>
      </table>

      {owned && (
        <>
          <h4 style={{ color: "#aaa", marginTop: 12 }}>Designate Sector</h4>
          <div style={styles.btnGrid}>
            {DESIGNATABLE.map((d) => (
              <button
                key={d}
                style={styles.btn}
                disabled={busy || sector.designation === d}
                onClick={() => handleDesignate(d)}
              >
                {DesignationLabel[d]}
              </button>
            ))}
          </div>
        </>
      )}

      {msg && <p style={{ color: "#7fc", marginTop: 8, fontSize: 12 }}>{msg}</p>}
    </div>
  );
}

function Row({ label, value }: { label: string; value: string | number }) {
  return (
    <tr>
      <td style={{ color: "#888", paddingRight: 12, fontSize: 12 }}>{label}</td>
      <td style={{ color: "#ddd", fontSize: 12 }}>{value}</td>
    </tr>
  );
}

const styles: Record<string, React.CSSProperties> = {
  panel: {
    position: "absolute", right: 0, top: 0, bottom: 0,
    width: 240, background: "#1c1c2e", borderLeft: "1px solid #333",
    padding: "16px 12px", overflowY: "auto", zIndex: 10,
  },
  close: {
    position: "absolute", top: 8, right: 8, background: "none",
    border: "none", color: "#aaa", cursor: "pointer", fontSize: 16,
  },
  title: { color: "#fff", margin: "0 0 12px", fontSize: 16 },
  table: { width: "100%", borderCollapse: "collapse" },
  btnGrid: { display: "flex", flexWrap: "wrap", gap: 6 },
  btn: {
    padding: "4px 8px", fontSize: 11, background: "#2c3e50",
    color: "#ccc", border: "1px solid #555", borderRadius: 3, cursor: "pointer",
  },
};
