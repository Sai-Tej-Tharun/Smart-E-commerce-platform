import { useEffect, useRef, useState } from "react";
import { sendSupportMessage } from "../api/support";

const WELCOME_MESSAGE = {
  role: "assistant",
  text: "Hi! I can help with creating posts, subscriptions, billing, your profile, or your dashboard. What do you need?",
};

export default function SupportChatWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, open]);

  const handleSend = async (e) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || sending) return;

    setMessages((prev) => [...prev, { role: "user", text }]);
    setInput("");
    setSending(true);

    try {
      const { reply } = await sendSupportMessage(text);
      setMessages((prev) => [...prev, { role: "assistant", text: reply }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "Sorry, I couldn't reach support right now. Please try again in a moment." },
      ]);
    } finally {
      setSending(false);
    }
  };

  return (
    <div style={{ position: "fixed", bottom: "1.5rem", right: "1.5rem", zIndex: 1000 }}>
      {open && (
        <div
          style={{
            width: "320px",
            maxWidth: "calc(100vw - 2rem)",
            height: "440px",
            display: "flex",
            flexDirection: "column",
            background: "var(--card-bg, #fff)",
            borderRadius: "14px",
            boxShadow: "0 12px 32px rgba(0,0,0,0.18)",
            overflow: "hidden",
            marginBottom: "0.75rem",
            border: "1px solid rgba(0,0,0,0.08)",
          }}
        >
          <div
            style={{
              padding: "0.9rem 1rem",
              background: "#4f8ef7",
              color: "#fff",
              fontWeight: 600,
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <span>Support Assistant</span>
            <button
              type="button"
              onClick={() => setOpen(false)}
              aria-label="Close chat"
              style={{ background: "none", border: "none", color: "#fff", fontSize: "1.1rem", cursor: "pointer", lineHeight: 1 }}
            >
              ×
            </button>
          </div>

          <div ref={scrollRef} style={{ flex: 1, overflowY: "auto", padding: "1rem", display: "flex", flexDirection: "column", gap: "0.6rem" }}>
            {messages.map((m, i) => (
              <div
                key={i}
                style={{
                  alignSelf: m.role === "user" ? "flex-end" : "flex-start",
                  background: m.role === "user" ? "#4f8ef7" : "#f1f3f5",
                  color: m.role === "user" ? "#fff" : "#1a1a1a",
                  padding: "0.55rem 0.85rem",
                  borderRadius: "12px",
                  maxWidth: "85%",
                  fontSize: "0.9rem",
                  lineHeight: 1.4,
                  whiteSpace: "pre-wrap",
                }}
              >
                {m.text}
              </div>
            ))}
            {sending && (
              <div style={{ alignSelf: "flex-start", fontSize: "0.85rem", opacity: 0.6, fontStyle: "italic" }}>
                Typing...
              </div>
            )}
          </div>

          <form onSubmit={handleSend} style={{ display: "flex", borderTop: "1px solid rgba(0,0,0,0.08)" }}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question..."
              style={{ flex: 1, border: "none", padding: "0.75rem 1rem", outline: "none", fontSize: "0.9rem" }}
              disabled={sending}
            />
            <button
              type="submit"
              disabled={sending || !input.trim()}
              style={{ border: "none", background: "#4f8ef7", color: "#fff", padding: "0 1.1rem", cursor: "pointer", fontWeight: 600 }}
            >
              Send
            </button>
          </form>
        </div>
      )}

      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? "Close support chat" : "Open support chat"}
        style={{
          width: "56px",
          height: "56px",
          borderRadius: "50%",
          border: "none",
          background: "#4f8ef7",
          color: "#fff",
          fontSize: "1.5rem",
          cursor: "pointer",
          boxShadow: "0 6px 18px rgba(79,142,247,0.45)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {open ? "×" : "💬"}
      </button>
    </div>
  );
}