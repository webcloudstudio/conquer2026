import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { login } from "../api/auth";
import { useAuthStore } from "../store/auth";

export function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { setToken, loadMe } = useAuthStore();
  const navigate = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const token = await login(username, password);
      setToken(token);
      await loadMe();
      navigate("/");
    } catch {
      setError("Invalid username or password");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <h1 style={styles.title}>Conquer v5</h1>
        <p style={styles.sub}>Sign in to your account</p>
        <form onSubmit={handleSubmit} style={styles.form}>
          <input
            style={styles.input}
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
          <input
            style={styles.input}
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          {error && <p style={styles.error}>{error}</p>}
          <button style={styles.btn} type="submit" disabled={loading}>
            {loading ? "Signing in…" : "Sign In"}
          </button>
        </form>
        <p style={styles.link}>
          No account? <Link to="/register" style={{ color: "#7fc" }}>Register</Link>
        </p>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center",
    background: "#0d1117",
  },
  card: {
    background: "#1c1c2e", border: "1px solid #333", borderRadius: 8,
    padding: "40px 32px", width: 360, textAlign: "center",
  },
  title: { color: "#ffd700", margin: "0 0 4px", fontSize: 28 },
  sub: { color: "#888", margin: "0 0 24px", fontSize: 14 },
  form: { display: "flex", flexDirection: "column", gap: 12 },
  input: {
    padding: "10px 12px", background: "#12121f", border: "1px solid #444",
    borderRadius: 4, color: "#fff", fontSize: 14,
  },
  error: { color: "#e74c3c", fontSize: 13, margin: 0 },
  btn: {
    padding: "10px", background: "#2980b9", border: "none",
    borderRadius: 4, color: "#fff", fontSize: 14, cursor: "pointer",
  },
  link: { color: "#666", marginTop: 16, fontSize: 13 },
};
