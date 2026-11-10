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

export interface AskResponse {
  answer: string;
  sources: { note_id: number; title: string }[];
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface AgentStep {
  tool: string;
  args: Record<string, unknown>;
  result: string;
}

export interface BuddyResponse {
  reply: string;
  steps: AgentStep[];
}