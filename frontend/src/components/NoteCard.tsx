import { useState } from "react";
import type { Note, NoteInput } from "../types";

interface NoteCardProps {
  note: Note;
  onUpdate: (id: number, changes: Partial<NoteInput>) => Promise<void>;
  onDelete: (id: number) => Promise<void>;
}

export default function NoteCard({ note, onUpdate, onDelete }: NoteCardProps) {
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(note.title);
  const [content, setContent] = useState(note.content);

  async function save() {
    await onUpdate(note.id, { title, content });
    setEditing(false);
  }

  function cancel() {
    setTitle(note.title);
    setContent(note.content);
    setEditing(false);
  }

  if (editing) {
    return (
      <article className="card note-card note-form">
        <input value={title} onChange={(e) => setTitle(e.target.value)} />
        <textarea rows={4} value={content} onChange={(e) => setContent(e.target.value)} />
        <div className="note-actions">
          <button className="small" onClick={save}>Save</button>
          <button className="small secondary" onClick={cancel}>Cancel</button>
        </div>
      </article>
    );
  }

  return (
    <article className="card note-card">
      <div className="note-header">
        <h3>{note.title}</h3>
        <span className="badge">{note.subject}</span>
      </div>
      <p>{note.content}</p>
      <small>
        {note.word_count} words · {new Date(note.created_at).toLocaleString()}
      </small>
      <div className="note-actions">
        <button className="small secondary" onClick={() => setEditing(true)}>Edit</button>
        <button
          className="small danger"
          onClick={() => {
            if (confirm(`Delete "${note.title}"?`)) onDelete(note.id);
          }}
        >
          Delete
        </button>
      </div>
    </article>
  );
}