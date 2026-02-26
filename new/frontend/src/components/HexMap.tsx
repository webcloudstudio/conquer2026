/**
 * SVG hex map renderer.
 *
 * Uses offset (even-r) coordinates matching the backend world_gen.
 * Each hex is a flat-top hexagon drawn with a <polygon>.
 */

import React, { useCallback, useRef, useState } from "react";
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
  selectedHex: { x: number; y: number } | null;
  onSelectHex: (x: number, y: number, sector: Sector | null) => void;
}

export function HexMap({ sectors, armies, nations, selectedHex, onSelectHex }: HexMapProps) {
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
      {sectors.map((s) => {
        const [cx, cy] = hexToPixel(s.x, s.y, HEX_SIZE);
        const base = ALTITUDE_COLOUR[s.altitude] ?? "#888";
        const overlay = DESIGNATION_COLOUR[s.designation] ?? "";
        const isSelected = selectedHex?.x === s.x && selectedHex?.y === s.y;
        const hasArmy = armyByHex.has(`${s.x},${s.y}`);
        const owner = s.owner_nation_id ? nationMap.get(s.owner_nation_id) : null;

        return (
          <g key={`${s.x},${s.y}`} onClick={() => onSelectHex(s.x, s.y, s)}>
            {/* Base terrain hex */}
            <polygon
              points={hexCorners(cx, cy, HEX_SIZE - 1)}
              fill={overlay || base}
              stroke={isSelected ? "#fff" : owner ? "#ffd700" : "#333"}
              strokeWidth={isSelected ? 2 : owner ? 1 : 0.5}
              opacity={0.9}
            />
            {/* Army indicator */}
            {hasArmy && (
              <circle cx={cx} cy={cy} r={5} fill="#e74c3c" stroke="#fff" strokeWidth={1} />
            )}
            {/* Capital star */}
            {s.designation === 4 && (
              <text x={cx} y={cy + 5} textAnchor="middle" fontSize={12} fill="#ffd700">★</text>
            )}
          </g>
        );
      })}
    </svg>
  );
}
