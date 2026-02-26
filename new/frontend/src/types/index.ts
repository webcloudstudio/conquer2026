// Core game types mirroring the backend schemas

export interface WorldAdmin {
  user_id: string;
  username: string;
}

export interface World {
  id: string;
  name: string;
  turn: number;
  mapx: number;
  mapy: number;
  is_active: boolean;
  is_maintenance: boolean;
  created_at: string;
  admins: WorldAdmin[];
  max_players: number;
  player_count: number;
}

export interface Nation {
  id: string;
  name: string;
  leader_title: string;
  race: string;
  player_class: string;
  talons: number;
  jewels: number;
  metals: number;
  food: number;
  wood: number;
  power_fire: number;
  power_water: number;
  power_earth: number;
  attr_morale: number;
  victory_points: number;
  is_npc: boolean;
  capital_x: number | null;
  capital_y: number | null;
}

export interface Sector {
  x: number;
  y: number;
  altitude: number;
  vegetation: number;
  designation: number;
  efficiency: number;
  population: number;
  minerals: number;
  tradegood: number;
  owner_nation_id: string | null;
}

export interface Army {
  id: string;
  nation_id: string;
  unit_type: number;
  strength: number;
  supply: number;
  efficiency: number;
  movement: number;
  x: number;
  y: number;
  is_active: boolean;
}

export interface Message {
  id: string;
  sender_nation_id: string | null;
  recipient_nation_id: string | null;
  subject: string;
  body: string;
  is_read: boolean;
  turn_sent: number;
}

export interface User {
  id: string;
  username: string;
  email: string;
  is_admin: boolean;
}

// Designation enum values (mirrors backend)
export const Designation = {
  UNDESIGNATED: 0,
  FARM: 1,
  MINE: 2,
  FOREST: 3,
  CAPITAL: 4,
  TOWN: 5,
  CITY: 6,
  FORTRESS: 7,
  SHRINE: 8,
  PORT: 9,
  SHIPYARD: 10,
  GRANARY: 11,
  ARSENAL: 12,
  MARKET: 13,
  UNIVERSITY: 14,
  TEMPLE: 15,
} as const;

export const DesignationLabel: Record<number, string> = {
  0: "Undesignated",
  1: "Farm",
  2: "Mine",
  3: "Forest",
  4: "Capital",
  5: "Town",
  6: "City",
  7: "Fortress",
  8: "Shrine",
  9: "Port",
  10: "Shipyard",
  11: "Granary",
  12: "Arsenal",
  13: "Market",
  14: "University",
  15: "Temple",
};
