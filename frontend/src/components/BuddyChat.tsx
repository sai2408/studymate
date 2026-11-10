import { useState } from "react";
import { askBuddy } from "../api";
import type { AgentStep, ChatMessage } from "../types";

interface DisplayMessage extends ChatMessage {
  steps?: AgentStep[];
}

const EXAMPLES = ["Quiz me on my OS notes", "Summarize my DBMS notes", "What's my average if I scored 45, 38 and 59?"];

export default function BuddyChat() {
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function send(text: string) {
    if (!text.trim() || loading) return;
    const history: ChatMessage[] = messages.map(({ role, content }) => ({ role, content }));
    setMessages((m) => [...m, { role: "user", content: text }]);
    setInput("");
    setLoading(true);
    setError("");
    try {
      const res = await askBuddy(text, history);
      setMessages((m) => [...m, { role: "assistant", content: res.reply, steps: res.steps }]);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="card">
      <h2>Study Buddy 🤖</h2>
      <p className="info">An AI agent that uses tools on your notes: search, summarize, quiz, calculate.</p>

      <div className="chat">
        {messages.length === 0 && (
          <div className="row">
            {EXAMPLES.map((ex) => (
              <button key={ex} className="small secondary" onClick={() => send(ex)}>{ex}</button>
            ))}
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.role === "user" ? "user" : "bot"}`}>
            {m.content}
            {m.steps && m.steps.length > 0 && (
              <div className="steps">
                Tools used: {m.steps.map((s) => s.tool).join(" → ")}
              </div>
            )}
          </div>
        ))}
        {loading && <div className="msg bot">Thinking and using tools...</div>}
      </div>

      {error && <p className="error">{error}</p>}
      <form
        className="row"
        onSubmit={(e) => {
          e.preventDefault();
          send(input);
        }}
      >
        <input placeholder="Ask Study Buddy..." value={input} onChange={(e) => setInput(e.target.value)} />
        <button type="submit" disabled={loading}>Send</button>
      </form>
    </section>
  );
}