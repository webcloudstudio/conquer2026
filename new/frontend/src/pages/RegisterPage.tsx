import React, { useState } from "react";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { register, login } from "../api/auth";
import { useAuthStore } from "../store/auth";

export function RegisterPage() {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { setToken, loadMe } = useAuthStore();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const next = searchParams.get("next") || "/worlds";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await register(username, email, password);
      const token = await login(username, password);
      setToken(token);
      await loadMe();
      navigate(next);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } }; message?: string };
      setError(e?.response?.data?.detail || e?.message || "Registration failed. Check the browser console for details.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <h1 style={styles.title}>Conquer v5</h1>
        <p style={styles.sub}>Create an account</p>
        <form onSubmit={handleSubmit} style={styles.form}>
          <input
            style={styles.input} placeholder="Username"
            value={username} onChange={(e) => setUsername(e.target.value)} required
          />
          <input
            style={styles.input} placeholder="Email" type="email"
            value={email} onChange={(e) => setEmail(e.target.value)} required
          />
          <input
            style={styles.input} placeholder="Password" type="password"
            value={password} onChange={(e) => setPassword(e.target.value)} required
          />
          {error && <p style={styles.error}>{error}</p>}
          <button style={styles.btn} type="submit" disabled={loading}>
            {loading ? "Creating…" : "Create Account"}
          </button>
        </form>
        <p style={styles.link}>
          Already have an account? <Link to={`/login?next=${encodeURIComponent(next)}`} style={{ color: "#7fc" }}>Sign in</Link>
        </p>
        <p style={styles.link}>
          <Link to="/" style={{ color: "#555" }}>← Back to home</Link>
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
    padding: "10px", background: "#27ae60", border: "none",
    borderRadius: 4, color: "#fff", fontSize: 14, cursor: "pointer",
  },
  link: { color: "#666", marginTop: 16, fontSize: 13 },
};
