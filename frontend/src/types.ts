// Same shapes as the backend's NoteRead / NoteCreate models (Day 5)
export interface Note {
  id: number;
  title: string;
  content: string;
  subject: string;
  word_count: number;
  created_at: string;
}

export type NoteInput = Pick<Note, "title" | "content" | "subject">;