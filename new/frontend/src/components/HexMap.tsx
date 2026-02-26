/**
 * SVG hex map renderer.
 *
 * Uses offset (even-r) coordinates matching the backend world_gen.
 * Each hex is a flat-top hexagon drawn with a <polygon>.
 */

import React, { useCallback, useEffect, useRef, useState } from "react";
import type { Army, Nation, Sector } from "../types";

// Terrain colours (altitude + vegetation)
const ALTITUDE_COLOUR: Record<number, string> = {
  0: "#4a90d9",  // water
  1: "#a8c87a",  // lowland
  2: "#8db865",  // plains
  3: "#6e9e50",  // hills
  4: "#bfa878",  // highland
  5: "#a08a60",  // mountain foot
  6: "#ccc",     // mountain
  7: "#eee",     // peak
};

const DESIGNATION_COLOUR: Record<number, string> = {
  0: "",        // no overlay
  1: "#7db352", // farm — green
  2: "#8b6914", // mine — brown
  3: "#2d6a2d", // forest — dark green
  4: "#d4af37", // capital — gold
  5: "#b5651d", // town — sienna
  6: "#c0392b", // city — red
  7: "#7f8c8d", // fortress — grey
  8: "#9b59b6", // shrine — purple
  9: "#1a6fa3", // port — blue
};

const HEX_SIZE = 20; // pixels, flat-top hex

// Nation color palette — deterministic hash
function nationColor(nationId: string): string {
  const palette = [
    "#58a6ff", "#3fb950", "#f78166", "#d2a8ff",
    "#ffa657", "#79c0ff", "#56d364", "#ff7b72",
  ];
  let hash = 0;
  for (let i = 0; i < nationId.length; i++) {
    hash = (hash * 31 + nationId.charCodeAt(i)) & 0xffffffff;
  }
  return palette[Math.abs(hash) % palette.length];
}

function armyColor(army: Army, myNation: Nation | null, nations: Nation[]): string {
  if (myNation && army.nation_id === myNation.id) return "#ffd700"; // player = gold
  const nation = nations.find((n) => n.id === army.nation_id);
  if (nation?.is_npc) return "#8b949e"; // NPC = gray
  return "#f85149"; // enemy = red
}

function hexCorners(cx: number, cy: number, size: number): string {
  const pts: string[] = [];
  for (let i = 0; i < 6; i++) {
    const angle = (Math.PI / 180) * (60 * i); // flat-top
    pts.push(`${cx + size * Math.cos(angle)},${cy + size * Math.sin(angle)}`);
  }
  return pts.join(" ");
}

// Offset (even-r) → pixel centre
function hexToPixel(col: number, row: number, size: number): [number, number] {
  const w = size * Math.sqrt(3);
  const h = size * 2;
  const x = w * col + (row % 2 === 0 ? 0 : w / 2);
  const y = h * 0.75 * row;
  return [x + size, y + size];
}

interface HexMapProps {
  sectors: Sector[];
  armies: Army[];
  nations: Nation[];
  myNation: Nation | null;
  selectedHex: { x: number; y: number } | null;
  movementRange: { x: number; y: number }[] | null;
  centerHex: { x: number; y: number } | null;
  onSelectHex: (x: number, y: number, sector: Sector | null) => void;
}

export function HexMap({
  sectors, armies, nations, myNation, selectedHex,
  movementRange, centerHex, onSelectHex,
}: HexMapProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [viewBox, setViewBox] = useState({ x: 0, y: 0, w: 1400, h: 900 });
  const [dragging, setDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  const nationMap = new Map(nations.map((n) => [n.id, n]));

  // Army positions: group armies by (x,y)
  const armyByHex = new Map<string, Army[]>();
  for (const a of armies) {
    const key = `${a.x},${a.y}`;
    if (!armyByHex.has(key)) armyByHex.set(key, []);
    armyByHex.get(key)!.push(a);
  }

  // Movement range set for quick lookup
  const rangeSet = new Set<string>(
    (movementRange ?? []).map((h) => `${h.x},${h.y}`)
  );

  // Center map when centerHex changes
  useEffect(() => {
    if (!centerHex) return;
    const [px, py] = hexToPixel(centerHex.x, centerHex.y, HEX_SIZE);
    setViewBox((v) => ({
      ...v,
      x: px - v.w / 2,
      y: py - v.h / 2,
    }));
  }, [centerHex]);

  const onMouseDown = useCallback((e: React.MouseEvent) => {
    setDragging(true);
    setDragStart({ x: e.clientX, y: e.clientY });
  }, []);

  const onMouseMove = useCallback((e: React.MouseEvent) => {
    if (!dragging) return;
    const dx = e.clientX - dragStart.x;
    const dy = e.clientY - dragStart.y;
    setDragStart({ x: e.clientX, y: e.clientY });
    setViewBox((v) => ({ ...v, x: v.x - dx, y: v.y - dy }));
  }, [dragging, dragStart]);

  const onMouseUp = useCallback(() => setDragging(false), []);

  const onWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    const factor = e.deltaY > 0 ? 1.1 : 0.9;
    setViewBox((v) => ({
      x: v.x + (v.w * (1 - factor)) / 2,
      y: v.y + (v.h * (1 - factor)) / 2,
      w: v.w * factor,
      h: v.h * factor,
    }));
  }, []);

  return (
    <svg
      ref={svgRef}
      style={{ width: "100%", height: "100%", cursor: dragging ? "grabbing" : "grab", background: "#1a1a2e" }}
      viewBox={`${viewBox.x} ${viewBox.y} ${viewBox.w} ${viewBox.h}`}
      onMouseDown={onMouseDown}
      onMouseMove={onMouseMove}
      onMouseUp={onMouseUp}
      onMouseLeave={onMouseUp}
      onWheel={onWheel}
    >
      {/* Terrain + ownership layer */}
      {sectors.map((s) => {
        const [cx, cy] = hexToPixel(s.x, s.y, HEX_SIZE);
        const base = ALTITUDE_COLOUR[s.altitude] ?? "#888";
        const overlay = DESIGNATION_COLOUR[s.designation] ?? "";
        const isSelected = selectedHex?.x === s.x && selectedHex?.y === s.y;
        const owner = s.owner_nation_id ? nationMap.get(s.owner_nation_id) : null;
        const borderColor = isSelected
          ? "#fff"
          : owner
          ? nationColor(owner.id)
          : "#333";

        return (
          <g key={`${s.x},${s.y}`} onClick={() => onSelectHex(s.x, s.y, s)}>
            <polygon
              points={hexCorners(cx, cy, HEX_SIZE - 1)}
              fill={overlay || base}
              stroke={borderColor}
              strokeWidth={isSelected ? 2 : owner ? 1.5 : 0.5}
              opacity={0.9}
            />
            {s.designation === 4 && (
              <text x={cx} y={cy + 5} textAnchor="middle" fontSize={12} fill="#ffd700">★</text>
            )}
          </g>
        );
      })}

      {/* Movement range overlay */}
      {movementRange && movementRange.map((h) => {
        const [cx, cy] = hexToPixel(h.x, h.y, HEX_SIZE);
        return (
          <polygon
            key={`range-${h.x},${h.y}`}
            points={hexCorners(cx, cy, HEX_SIZE - 1)}
            fill="rgba(63,185,80,0.25)"
            stroke="#3fb950"
            strokeWidth={1}
            style={{ pointerEvents: "none" }}
          />
        );
      })}

      {/* Army layer */}
      {Array.from(armyByHex.entries()).map(([key, armyGroup]) => {
        const first = armyGroup[0];
        const [cx, cy] = hexToPixel(first.x, first.y, HEX_SIZE);
        const color = armyColor(first, myNation, nations);
        const ownerNation = nationMap.get(first.nation_id);
        const totalStr = armyGroup.reduce((s, a) => s + a.strength, 0);
        const label = ownerNation ? `${ownerNation.name} · Str:${totalStr}` : `Str:${totalStr}`;

        return (
          <g key={`army-${key}`}>
            <circle cx={cx} cy={cy} r={5} fill={color} stroke="#fff" strokeWidth={1} />
            {armyGroup.length > 1 && (
              <text x={cx + 6} y={cy - 4} fontSize={8} fill="#fff">{armyGroup.length}</text>
            )}
            <title>{label}</title>
          </g>
        );
      })}
    </svg>
  );
}
