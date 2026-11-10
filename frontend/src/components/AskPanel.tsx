import { useState } from "react";
import { ask } from "../api";
import type { AskResponse } from "../types";

export default function AskPanel() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<AskResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleAsk(e: React.FormEvent) {
    e.preventDefault();
    if (question.trim().length < 3) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      setResult(await ask(question));
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="card note-form">
      <h2>Ask StudyMate</h2>
      <p className="info">Ask a question – the answer comes only from your own notes.</p>
      <form className="note-form" onSubmit={handleAsk}>
        <textarea
          rows={3}
          placeholder="e.g. What are the conditions for a deadlock?"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <button type="submit" disabled={loading}>{loading ? "Thinking..." : "Ask"}</button>
      </form>
      {error && <p className="error">{error}</p>}
      {result && (
        <>
          <div className="answer">{result.answer}</div>
          {result.sources.length > 0 && (
            <p className="sources">
              From your notes: {result.sources.map((s) => s.title).join("  ·  ")}
            </p>
          )}
        </>
      )}
    </section>
  );
}