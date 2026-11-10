import { useEffect, useState } from "react";
import { clearToken, createNote, deleteNote, getMe, getNotes, getToken, updateNote } from "./api";
import AskPanel from "./components/AskPanel";
import BuddyChat from "./components/BuddyChat";
import Login from "./components/Login";
import NoteForm from "./components/NoteForm";
import NoteList from "./components/NoteList";
import SearchBar from "./components/SearchBar";
import type { Note, NoteInput } from "./types";

export default function App() {
  const [loggedIn, setLoggedIn] = useState(Boolean(getToken()));
  const [email, setEmail] = useState("");
  const [notes, setNotes] = useState<Note[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [tab, setTab] = useState<"notes" | "ask" | "buddy">("notes");

  // Load the user's notes from the API whenever we log in or the search changes
  useEffect(() => {
    if (!loggedIn) return;
    setLoading(true);
    setError("");
    getNotes(search)
      .then(setNotes)
      .catch((err: Error) => {
        setError(err.message);
        if (!getToken()) setLoggedIn(false);   // token expired -> back to login
      })
      .finally(() => setLoading(false));
  }, [loggedIn, search]);

  useEffect(() => {
    if (loggedIn) getMe().then((u) => setEmail(u.email)).catch(() => {});
  }, [loggedIn]);

  async function addNote(input: NoteInput) {
    try {
      const saved = await createNote(input);   // POST /notes
      setNotes([saved, ...notes]);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function editNote(id: number, changes: Partial<NoteInput>) {
    try {
      const updated = await updateNote(id, changes);   // PUT /notes/{id}
      setNotes(notes.map((n) => (n.id === id ? updated : n)));
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function removeNote(id: number) {
    try {
      await deleteNote(id);                            // DELETE /notes/{id}
      setNotes(notes.filter((n) => n.id !== id));
    } catch (err) {
      setError((err as Error).message);
    }
  }

  function logout() {
    clearToken();
    setLoggedIn(false);
    setNotes([]);
  }

  if (!loggedIn) return <Login onLoggedIn={() => setLoggedIn(true)} />;

  return (
    <main className="container">
      <header className="app-header">
        <h1>📚 StudyMate</h1>
        <div className="row">
          <span className="info">{email}</span>
          <button className="secondary small" onClick={logout}>Log out</button>
        </div>
      </header>
      <nav className="tabs">
        <button className={tab === "notes" ? "" : "secondary"} onClick={() => setTab("notes")}>My notes</button>
        <button className={tab === "ask" ? "" : "secondary"} onClick={() => setTab("ask")}>Ask StudyMate</button>
        <button className={tab === "buddy" ? "" : "secondary"} onClick={() => setTab("buddy")}>Study Buddy</button>
      </nav>
      {error && <p className="error">{error}</p>}
      {tab === "notes" && (
        <>
          <NoteForm onAdd={addNote} />
          <SearchBar value={search} onChange={setSearch} />
          {loading ? (
            <p className="info">Loading notes...</p>
          ) : (
            <NoteList notes={notes} onUpdate={editNote} onDelete={removeNote} />
          )}
        </>
      )}
      {tab === "ask" && <AskPanel />}
      {tab === "buddy" && <BuddyChat />}
    </main>
  );
}