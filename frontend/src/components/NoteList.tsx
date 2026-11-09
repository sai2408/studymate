import type { Note, NoteInput } from "../types";
import NoteCard from "./NoteCard";

interface NoteListProps {
  notes: Note[];
  onUpdate: (id: number, changes: Partial<NoteInput>) => Promise<void>;
  onDelete: (id: number) => Promise<void>;
}

export default function NoteList({ notes, onUpdate, onDelete }: NoteListProps) {
  if (notes.length === 0) {
    return <p className="empty">No notes yet. Add your first one!</p>;
  }
  return (
    <section className="note-list">
      {notes.map((note) => (
        <NoteCard key={note.id} note={note} onUpdate={onUpdate} onDelete={onDelete} />
      ))}
    </section>
  );
}