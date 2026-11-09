import { useState } from "react";
import type { NoteInput } from "../types";

interface NoteFormProps {
  onAdd: (note: NoteInput) => void;
}

const SUBJECTS = ["General", "DBMS", "OS", "CN", "DSA", "Python"];

export default function NoteForm({ onAdd }: NoteFormProps) {
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [subject, setSubject] = useState("General");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();               // stop the page from reloading
    if (!title.trim() || !content.trim()) return;
    onAdd({ title, content, subject });
    setTitle("");
    setContent("");
  }

  return (
    <form className="card note-form" onSubmit={handleSubmit}>
      <h2>Add a note</h2>
      <input placeholder="Title" value={title} onChange={(e) => setTitle(e.target.value)} />
      <textarea
        placeholder="Write your note..."
        rows={4}
        value={content}
        onChange={(e) => setContent(e.target.value)}
      />
      <select value={subject} onChange={(e) => setSubject(e.target.value)}>
        {SUBJECTS.map((s) => (
          <option key={s}>{s}</option>
        ))}
      </select>
      <button type="submit">Save note</button>
    </form>
  );
}