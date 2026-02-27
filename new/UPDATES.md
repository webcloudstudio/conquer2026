# Conquer 2026 — Update Log
Newest entries first.

## 2026-02
- Fixed new player join: POST /nations now calls initialize_player_nation(), giving starting resources (5k talons, 2k food, 500 metals/wood, 100 jewels), a 2000-strength army at capital, and 4 surrounding farm sectors
- Fixed new player join: initialize_player_nation() now claims ring of adjacent sectors as farms (mirrors NPC + original C place() behavior)
- Game UI: ArmyPanel shows collapsible "🏰 First Steps" guide (7 steps: locate capital, designate sectors, build farms/mines/cities, army food, capturing territory, turn timing)
- Fixed player nation detection: added GET /worlds/{id}/nations/mine backend endpoint
- NationOut schema now returns user_id, attr_morale, power_*, and *_produced fields
- Game UI: NationDashboard now renders (was always null-blocked); shows production rates (+N) per resource
- Game UI: Magic power bars labeled "🔥 Military", "💧 Civilian", "🌍 Wizardry"
- Game UI: Player armies shown in gold, enemies red, NPCs gray on hex map
- Game UI: Hex borders colored per owning nation (deterministic color palette)
- Game UI: HexMap highlights reachable hexes (green) for selected army via BFS
- Game UI: "📍 Find" button in ArmyPanel centers map on army
- Game UI: ArmyPanel shows unit type name, strength bar, supply, efficiency per army card
- Game UI: ArmyPanel shows collapsible how-to-play guide (persisted in localStorage)
- Game UI: SectorPanel shows owner nation name and ownership badge (Your sector / Enemy territory / Unclaimed)
- Game UI: SectorPanel accepts nations prop for ownership lookup
- Game UI: JoinWorldPanel shown in sidebar when player has not yet joined the world
- Game UI: UnitTypeName lookup table added to types (40 unit types)
- Converted 15 original 1987 Adam Bryant nroff docs to HTML (docs/original/)
- Added "Original Docs (1987)" sidebar section to all 12 documentation pages
- docs/style.css: added nav-sep, nav-group, pre.screen, pre.table, p.see-also, p.indent, dt/dd styles
