/**
 * Landing page — public entry point to Conquer v5.
 * Top bar: Play (→ worlds) and Admin Setup (→ admin panel).
 * Left sidebar: links to the static documentation at /docs/.
 * Main area: "What is Conquer" overview.
 */

import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../store/auth";

const DOC_LINKS = [
  { label: "What is Conquer", href: "/docs/index.html" },
  { label: "Running the Game", href: "/docs/setup.html" },
  { label: "Game Administration", href: "/docs/game-admin.html" },
  { label: "Gameplay Guide", href: "/docs/gameplay.html" },
  { label: "Player Classes", href: "/docs/classes.html" },
  { label: "Economy & Resources", href: "/docs/economy.html" },
  { label: "Military & Combat", href: "/docs/military.html" },
  { label: "Magic System", href: "/docs/magic.html" },
  { label: "Diplomacy", href: "/docs/diplomacy.html" },
  { label: "World Events", href: "/docs/events.html" },
  { label: "Artifacts", href: "/docs/artifacts.html" },
  { label: "Admin API Reference", href: "/docs/admin.html" },
];

export function LandingPage() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  function handlePlay() {
    if (user) navigate("/worlds");
    else navigate("/login?next=/worlds");
  }

  function handleAdmin() {
    if (!user) navigate("/login?next=/admin");
    else if (user.is_admin) navigate("/admin");
    else alert("Admin access required. Ask a server administrator to promote your account.");
  }

  return (
    <div style={s.page}>
      {/* ── Top action bar ── */}
      <header style={s.topBar}>
        <span style={s.logo}>⚔️ Conquer v5</span>
        <nav style={s.actions}>
          <button style={s.btnPlay} onClick={handlePlay}>▶ Play Game</button>
          <button style={s.btnAdmin} onClick={handleAdmin}>⚙ Admin Setup</button>
        </nav>
        <div style={s.authArea}>
          {user ? (
            <>
              <span style={s.username}>{user.username}</span>
              <button style={s.btnGhost} onClick={logout}>Sign Out</button>
            </>
          ) : (
            <>
              <button style={s.btnGhost} onClick={() => navigate("/login")}>Sign In</button>
              <button style={s.btnRegister} onClick={() => navigate("/register")}>Register</button>
            </>
          )}
        </div>
      </header>

      {/* ── Body: sidebar + content ── */}
      <div style={s.body}>
        {/* Left sidebar — documentation nav */}
        <nav style={s.sidebar}>
          <p style={s.sidebarHeading}>Documentation</p>
          <ul style={s.navList}>
            {DOC_LINKS.map((link) => (
              <li key={link.href} style={s.navItem}>
                <a href={link.href} style={s.navLink}>{link.label}</a>
              </li>
            ))}
          </ul>
        </nav>

        {/* Main content */}
        <main style={s.main}>
          <h1 style={s.h1}>What is Conquer v5?</h1>
          <p style={s.lead}>
            Conquer v5 is an open-source, turn-based multiplayer strategy game — a
            modernised reboot of the classic 1987 USENET game. Nations compete for
            territory, resources, and dominance on a procedurally generated hex world.
          </p>

          {/* CTA cards */}
          <div style={s.ctaRow}>
            <div style={s.ctaCard}>
              <div style={s.ctaIcon}>▶</div>
              <h3 style={s.ctaTitle}>Play a Game</h3>
              <p style={s.ctaText}>
                Join an existing world, build your nation, recruit armies, cast spells,
                and compete for victory against human players and NPC nations.
              </p>
              <button style={s.btnPlay} onClick={handlePlay}>
                {user ? "Open World List" : "Sign In to Play"}
              </button>
            </div>
            <div style={s.ctaCard}>
              <div style={s.ctaIcon}>⚙</div>
              <h3 style={s.ctaTitle}>Run a Server</h3>
              <p style={s.ctaText}>
                Administrators create game worlds, manage players, configure the map,
                and control turn processing from the Admin Panel.
              </p>
              <button style={s.btnAdmin} onClick={handleAdmin}>
                {user?.is_admin ? "Open Admin Panel" : "Admin Sign In"}
              </button>
            </div>
          </div>

          {/* Feature highlights */}
          <h2 style={s.h2}>Key Features</h2>
          <div style={s.featureGrid}>
            <div style={s.feature}>
              <span style={s.featureIcon}>🗺️</span>
              <div>
                <strong style={s.featureTitle}>Procedural Hex Map</strong>
                <p style={s.featureText}>
                  Every game generates a unique world with oceans, mountains, forests,
                  and deserts. Configurable size and terrain ratios.
                </p>
              </div>
            </div>
            <div style={s.feature}>
              <span style={s.featureIcon}>⚔️</span>
              <div>
                <strong style={s.featureTitle}>8 Asymmetric Player Classes</strong>
                <p style={s.featureText}>
                  Warlord, Trader, Theocrat, Diplomat, and more — each with unique
                  units, bonuses, and a distinct victory condition.
                </p>
              </div>
            </div>
            <div style={s.feature}>
              <span style={s.featureIcon}>🏭</span>
              <div>
                <strong style={s.featureTitle}>Deep Economy</strong>
                <p style={s.featureText}>
                  Five resource types, sector designations, caravan trade routes,
                  and a national tax and morale system.
                </p>
              </div>
            </div>
            <div style={s.feature}>
              <span style={s.featureIcon}>🔮</span>
              <div>
                <strong style={s.featureTitle}>Magic System</strong>
                <p style={s.featureText}>
                  Three power types regenerated by shrines. Ten spells from Bless
                  Army to the devastating once-per-game Armageddon.
                </p>
              </div>
            </div>
            <div style={s.feature}>
              <span style={s.featureIcon}>🌍</span>
              <div>
                <strong style={s.featureTitle}>World Events</strong>
                <p style={s.featureText}>
                  Blizzards, plagues, wandering dragons, treasure strikes, and more —
                  15 event types with configurable frequency and chain reactions.
                </p>
              </div>
            </div>
            <div style={s.feature}>
              <span style={s.featureIcon}>🤝</span>
              <div>
                <strong style={s.featureTitle}>Diplomacy</strong>
                <p style={s.featureText}>
                  Declare war, form alliances, offer tribute. Bilateral diplomatic
                  status with in-game messaging between nations.
                </p>
              </div>
            </div>
          </div>

          <div style={s.origin}>
            <p>
              <strong style={{ color: "#ffd700" }}>Origin:</strong> Conquer v5 is a
              GPL-relicensed (2025) revival of a 65,000-line C game written in 1987 for
              USENET distribution. The Python rewrite keeps the spirit of the original
              while redesigning onboarding, AI, and diplomacy.
            </p>
          </div>
        </main>
      </div>
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  page: { display: "flex", flexDirection: "column", minHeight: "100vh", background: "#0d1117" },

  // Top bar
  topBar: {
    display: "flex", alignItems: "center", gap: 16,
    padding: "0 24px", height: 56,
    background: "#161b22", borderBottom: "1px solid #30363d",
    position: "sticky", top: 0, zIndex: 10,
  },
  logo: { color: "#ffd700", fontWeight: "bold", fontSize: 18, marginRight: 8 },
  actions: { display: "flex", gap: 8, flex: 1 },
  authArea: { display: "flex", alignItems: "center", gap: 8 },
  username: { color: "#8b949e", fontSize: 13 },

  btnPlay: {
    padding: "7px 18px", background: "#238636", border: "none",
    borderRadius: 6, color: "#fff", fontWeight: "bold", fontSize: 14, cursor: "pointer",
  },
  btnAdmin: {
    padding: "7px 18px", background: "#1f6feb", border: "none",
    borderRadius: 6, color: "#fff", fontSize: 14, cursor: "pointer",
  },
  btnGhost: {
    padding: "5px 12px", background: "none", border: "1px solid #30363d",
    borderRadius: 6, color: "#8b949e", fontSize: 13, cursor: "pointer",
  },
  btnRegister: {
    padding: "5px 12px", background: "#21262d", border: "1px solid #30363d",
    borderRadius: 6, color: "#c9d1d9", fontSize: 13, cursor: "pointer",
  },

  // Layout
  body: { display: "flex", flex: 1 },

  // Sidebar
  sidebar: {
    width: 220, minWidth: 220,
    background: "#0d1117", borderRight: "1px solid #21262d",
    padding: "24px 0",
  },
  sidebarHeading: {
    color: "#8b949e", fontSize: 11, fontWeight: 600, textTransform: "uppercase",
    letterSpacing: 1, padding: "0 16px", margin: "0 0 8px",
  },
  navList: { listStyle: "none", margin: 0, padding: 0 },
  navItem: { margin: 0 },
  navLink: {
    display: "block", padding: "6px 16px",
    color: "#8b949e", textDecoration: "none", fontSize: 14,
    borderLeft: "3px solid transparent",
    transition: "color 0.15s",
  },

  // Main content
  main: { flex: 1, padding: "40px 48px", overflowY: "auto", maxWidth: 860 },
  h1: { color: "#c9d1d9", margin: "0 0 12px", fontSize: 28, fontWeight: 700 },
  h2: { color: "#c9d1d9", margin: "32px 0 16px", fontSize: 20, fontWeight: 600 },
  lead: { color: "#8b949e", fontSize: 16, lineHeight: 1.6, margin: "0 0 32px" },

  // CTA cards
  ctaRow: { display: "flex", gap: 16, margin: "0 0 40px", flexWrap: "wrap" },
  ctaCard: {
    flex: 1, minWidth: 240,
    background: "#161b22", border: "1px solid #30363d",
    borderRadius: 8, padding: "20px 24px",
    display: "flex", flexDirection: "column", gap: 8,
  },
  ctaIcon: { fontSize: 28, marginBottom: 4 },
  ctaTitle: { color: "#c9d1d9", margin: 0, fontSize: 16, fontWeight: 600 },
  ctaText: { color: "#8b949e", fontSize: 13, lineHeight: 1.5, margin: "0 0 12px", flex: 1 },

  // Feature grid
  featureGrid: { display: "flex", flexDirection: "column", gap: 16, marginBottom: 32 },
  feature: {
    display: "flex", gap: 16, alignItems: "flex-start",
    background: "#161b22", border: "1px solid #21262d",
    borderRadius: 6, padding: "12px 16px",
  },
  featureIcon: { fontSize: 24, flexShrink: 0, marginTop: 2 },
  featureTitle: { color: "#c9d1d9", display: "block", marginBottom: 4 },
  featureText: { color: "#8b949e", fontSize: 13, lineHeight: 1.5, margin: 0 },

  // Origin note
  origin: {
    background: "#161b22", border: "1px solid #30363d",
    borderRadius: 6, padding: "14px 18px",
  },
};
