import { api } from "./client";
import type { Army, Message, Nation, Sector, World } from "../types";

// Worlds
export const listWorlds = () => api.get<World[]>("/worlds/").then((r) => r.data);
export const getWorld = (id: string) => api.get<World>(`/worlds/${id}`).then((r) => r.data);

// Nations
export const listNations = (worldId: string) =>
  api.get<Nation[]>(`/worlds/${worldId}/nations/`).then((r) => r.data);

export const getMyNation = (worldId: string) =>
  api.get<Nation>(`/worlds/${worldId}/nations/mine`).then((r) => r.data);

export const joinWorld = (worldId: string, body: {
  name: string;
  leader_title: string;
  race: string;
  player_class: string;
}) => api.post<Nation>(`/worlds/${worldId}/nations/`, body).then((r) => r.data);

// Sectors (full map)
export const listSectors = (worldId: string) =>
  api.get<Sector[]>(`/worlds/${worldId}/sectors/`).then((r) => r.data);

export const designateSector = (worldId: string, x: number, y: number, designation: number) =>
  api.post(`/worlds/${worldId}/sectors/${x}/${y}/designate`, { designation }).then((r) => r.data);

// Armies
export const listArmies = (worldId: string) =>
  api.get<Army[]>(`/worlds/${worldId}/armies/`).then((r) => r.data);

export const listMyArmies = (worldId: string) =>
  api.get<Army[]>(`/worlds/${worldId}/armies/mine`).then((r) => r.data);

export const orderMove = (worldId: string, armyId: string, x: number, y: number) =>
  api.post(`/worlds/${worldId}/armies/${armyId}/move`, { x, y }).then((r) => r.data);

export const orderAttack = (worldId: string, armyId: string, x: number, y: number) =>
  api.post(`/worlds/${worldId}/armies/${armyId}/attack`, { x, y }).then((r) => r.data);

export const orderDisband = (worldId: string, armyId: string) =>
  api.post(`/worlds/${worldId}/armies/${armyId}/disband`).then((r) => r.data);

// Messages
export const getInbox = (worldId: string) =>
  api.get<Message[]>(`/worlds/${worldId}/messages/`).then((r) => r.data);

export const sendMessage = (worldId: string, body: {
  recipient_nation_id: string;
  subject: string;
  body: string;
}) => api.post<Message>(`/worlds/${worldId}/messages/send`, body).then((r) => r.data);

export const markRead = (worldId: string, messageId: string) =>
  api.post(`/worlds/${worldId}/messages/${messageId}/read`).then((r) => r.data);

// My administered worlds
export const listMyWorlds = () => api.get<World[]>("/worlds/mine").then((r) => r.data);

// Worlds where current user is an active player
export const listPlayingWorlds = () => api.get<World[]>("/worlds/playing").then((r) => r.data);

// Add co-admin to a world
export const addWorldAdmin = (worldId: string, username: string) =>
  api.post(`/worlds/${worldId}/admins`, { username }).then((r) => r.data);

// Admin
export const processTurn = (worldId: string) =>
  api.post(`/admin/worlds/${worldId}/process-turn`).then((r) => r.data);

export const toggleMaintenance = (worldId: string) =>
  api.post(`/admin/worlds/${worldId}/maintenance`).then((r) => r.data);
