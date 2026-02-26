/**
 * In-game inbox — view messages and send mail to other nations.
 */

import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getInbox, markRead, sendMessage, listNations } from "../api/game";
import type { Message, Nation } from "../types";

export function InboxPage() {
  const { worldId } = useParams<{ worldId: string }>();
  const navigate = useNavigate();
  const [messages, setMessages] = useState<Message[]>([]);
  const [nations, setNations] = useState<Nation[]>([]);
  const [selected, setSelected] = useState<Message | null>(null);
  const [composing, setComposing] = useState(false);
  const [to, setTo] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [sendError, setSendError] = useState("");
  const [loading, setLoading] = useState(true);

  async function load() {
    if (!worldId) return;
    const [msgs, ns] = await Promise.all([getInbox(worldId), listNations(worldId)]);
    setMessages(msgs);
    setNations(ns);
    setLoading(false);
  }

  useEffect(() => { load(); }, [worldId]);

  async function handleOpen(msg: Message) {
    setSelected(msg);
    if (!msg.is_read && worldId) {
      await markRead(worldId, msg.id);
      setMessages((prev) => prev.map((m) => m.id === msg.id ? { ...m, is_read: true } : m));
    }
  }

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    if (!worldId) return;
    setSendError("");
    try {
      await sendMessage(worldId, { recipient_nation_id: to, subject, body });
      setComposing(false);
      setTo(""); setSubject(""); setBody("");
      load();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setSendError(e?.response?.data?.detail || "Send failed");
    }
  }

  return (
    <div style={styles.page}>
      <header style={styles.header}>
        <button style={styles.back} onClick={() => navigate(`/game/${worldId}`)}>← Map</button>
        <h2 style={styles.title}>Inbox</h2>
        <button style={styles.compose} onClick={() => setComposing(true)}>✉ Compose</button>
      </header>

      <div style={styles.body}>
        {/* Message list */}
        <div style={styles.list}>
          {loading && <p style={styles.empty}>Loading…</p>}
          {!loading && messages.length === 0 && <p style={styles.empty}>No messages</p>}
          {messages.map((m) => (
            <div
              key={m.id}
              style={{ ...styles.msgRow, background: selected?.id === m.id ? "#1e2d3d" : "transparent" }}
              onClick={() => handleOpen(m)}
            >
              <span style={{ color: m.is_read ? "#555" : "#fff", fontWeight: m.is_read ? "normal" : "bold", fontSize: 13 }}>
                {m.subject || "(no subject)"}
              </span>
              <span style={{ color: "#555", fontSize: 11 }}>Turn {m.turn_sent}</span>
            </div>
          ))}
        </div>

        {/* Message view */}
        <div style={styles.view}>
          {selected ? (
            <>
              <h3 style={{ color: "#fff", margin: "0 0 8px" }}>{selected.subject}</h3>
              <p style={{ color: "#666", fontSize: 12, margin: "0 0 16px" }}>
                Turn {selected.turn_sent} ·{" "}
                {selected.sender_nation_id ?? "World News"}
              </p>
              <pre style={styles.body_text}>{selected.body}</pre>
            </>
          ) : (
            <p style={{ color: "#444" }}>Select a message to read</p>
          )}
        </div>
      </div>

      {/* Compose overlay */}
      {composing && (
        <div style={styles.overlay}>
          <div style={styles.modal}>
            <h3 style={{ color: "#fff", margin: "0 0 16px" }}>New Message</h3>
            <form onSubmit={handleSend} style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              <select style={styles.input} value={to} onChange={(e) => setTo(e.target.value)} required>
                <option value="">Select recipient nation…</option>
                {nations.map((n) => (
                  <option key={n.id} value={n.id}>{n.name}</option>
                ))}
              </select>
              <input
                style={styles.input} placeholder="Subject"
                value={subject} onChange={(e) => setSubject(e.target.value)} required
              />
              <textarea
                style={{ ...styles.input, height: 120, resize: "vertical" }}
                placeholder="Message…"
                value={body} onChange={(e) => setBody(e.target.value)} required
              />
              {sendError && <p style={{ color: "#e74c3c", fontSize: 12 }}>{sendError}</p>}
              <div style={{ display: "flex", gap: 8 }}>
                <button type="submit" style={styles.sendBtn}>Send</button>
                <button type="button" style={styles.cancelBtn} onClick={() => setComposing(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: { display: "flex", flexDirection: "column", height: "100vh", background: "#0d1117" },
  header: {
    display: "flex", alignItems: "center", gap: 16,
    padding: "10px 20px", background: "#1c1c2e", borderBottom: "1px solid #333",
  },
  title: { color: "#fff", margin: 0, flex: 1, fontSize: 18 },
  back: {
    background: "none", border: "1px solid #444", borderRadius: 4,
    color: "#aaa", cursor: "pointer", fontSize: 12, padding: "4px 8px",
  },
  compose: {
    padding: "6px 14px", background: "#2980b9", border: "none",
    borderRadius: 4, color: "#fff", cursor: "pointer", fontSize: 13,
  },
  body: { display: "flex", flex: 1, overflow: "hidden" },
  list: { width: 280, borderRight: "1px solid #222", overflowY: "auto" },
  msgRow: {
    display: "flex", flexDirection: "column", padding: "10px 14px",
    borderBottom: "1px solid #1a1a2e", cursor: "pointer",
  },
  view: { flex: 1, padding: 24, overflowY: "auto" },
  empty: { color: "#555", padding: 16, fontSize: 13 },
  body_text: {
    color: "#ccc", fontSize: 13, lineHeight: 1.6,
    whiteSpace: "pre-wrap", fontFamily: "inherit", margin: 0,
  },
  overlay: {
    position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)",
    display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100,
  },
  modal: {
    background: "#1c1c2e", border: "1px solid #333", borderRadius: 8,
    padding: 24, width: 480,
  },
  input: {
    padding: "8px 10px", background: "#12121f", border: "1px solid #444",
    borderRadius: 4, color: "#fff", fontSize: 13, width: "100%",
  },
  sendBtn: {
    padding: "8px 20px", background: "#27ae60", border: "none",
    borderRadius: 4, color: "#fff", cursor: "pointer",
  },
  cancelBtn: {
    padding: "8px 16px", background: "none", border: "1px solid #555",
    borderRadius: 4, color: "#aaa", cursor: "pointer",
  },
};
