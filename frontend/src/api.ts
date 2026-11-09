import type { Note, NoteInput } from "./types";

// Backend address: from .env (VITE_API_URL) or local default
const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const TOKEN_KEY = "studymate_token";
export const getToken = () => localStorage.getItem(TOKEN_KEY);
export const setToken = (token: string) => localStorage.setItem(TOKEN_KEY, token);
export const clearToken = () => localStorage.removeItem(TOKEN_KEY);

// One generic helper for every call: adds the token, parses JSON, throws readable errors
async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (options.body && !(options.body instanceof URLSearchParams)) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (response.status === 401) clearToken();
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = typeof body.detail === "string" ? body.detail : `Request failed (${response.status})`;
    throw new Error(detail);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

// ---------- Auth ----------
export async function login(email: string, password: string) {
  // FastAPI's OAuth2 form expects form fields "username" and "password"
  const form = new URLSearchParams({ username: email, password });
  const data = await request<{ access_token: string }>("/auth/login", { method: "POST", body: form });
  setToken(data.access_token);
}

export function signup(email: string, password: string) {
  return request<{ id: number; email: string }>("/auth/signup", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export const getMe = () => request<{ id: number; email: string }>("/auth/me");

// ---------- Notes ----------
export function getNotes(q = "") {
  const query = q ? `?q=${encodeURIComponent(q)}` : "";
  return request<Note[]>(`/notes${query}`);
}

export function createNote(note: NoteInput) {
  return request<Note>("/notes", { method: "POST", body: JSON.stringify(note) });
}

export function updateNote(id: number, changes: Partial<NoteInput>) {
  return request<Note>(`/notes/${id}`, { method: "PUT", body: JSON.stringify(changes) });
}

export function deleteNote(id: number) {
  return request<void>(`/notes/${id}`, { method: "DELETE" });
}