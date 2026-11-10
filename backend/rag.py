"""
RAG = Retrieval-Augmented Generation
  INDEX : note -> chunks -> embeddings -> saved in the database
  ASK   : question -> embedding -> most similar chunks -> prompt with those chunks -> LLM answer
"""
import asyncio
import json

import numpy as np
from sqlmodel import delete, select
from sqlmodel.ext.asyncio.session import AsyncSession

import llm
from database import engine
from models import AskResponse, Note, NoteChunk, Source

CHUNK_WORDS = 120     # words per chunk
OVERLAP_WORDS = 20    # words shared between neighbouring chunks (keeps context at the edges)
TOP_K = 4             # how many chunks to send to the LLM


def ai_enabled() -> bool:
    return bool(llm.GEMINI_KEY)   # embeddings need Gemini


# ---------------- STEP 1: chunking ----------------
def chunk_text(text: str, size: int = CHUNK_WORDS, overlap: int = OVERLAP_WORDS) -> list[str]:
    words = text.split()
    if not words:
        return []
    chunks, start = [], 0
    while start < len(words):
        chunks.append(" ".join(words[start:start + size]))
        start += size - overlap
    return chunks


# ---------------- STEP 2: indexing (runs as a background task) ----------------
async def index_note(note_id: int):
    if not ai_enabled():
        return
    async with AsyncSession(engine) as session:
        note = await session.get(Note, note_id)
        if not note:
            return
        title, owner_id = note.title, note.owner_id
        chunks = chunk_text(f"{note.title}. {note.content}")
        # embed() is a normal (blocking) function -> run it in a thread so the server stays responsive
        vectors = await asyncio.to_thread(llm.embed, chunks)

        await session.exec(delete(NoteChunk).where(NoteChunk.note_id == note_id))  # remove old chunks
        for text, vector in zip(chunks, vectors):
            session.add(NoteChunk(note_id=note_id, owner_id=owner_id, text=text,
                                  embedding=json.dumps(vector)))
        await session.commit()
        print(f"[rag] indexed note {note_id} '{title}' -> {len(chunks)} chunk(s)")


async def delete_chunks(session: AsyncSession, note_id: int):
    await session.exec(delete(NoteChunk).where(NoteChunk.note_id == note_id))


# ---------------- STEP 3: retrieval ----------------
async def retrieve(session: AsyncSession, user_id: int, question: str, k: int = TOP_K):
    result = await session.exec(select(NoteChunk).where(NoteChunk.owner_id == user_id))
    chunks = result.all()
    if not chunks:
        return []
    [q_vec] = await asyncio.to_thread(llm.embed, [question])

    matrix = np.array([json.loads(c.embedding) for c in chunks])
    q = np.array(q_vec)
    scores = matrix @ q / (np.linalg.norm(matrix, axis=1) * np.linalg.norm(q))   # cosine similarity
    best = np.argsort(scores)[::-1][:k]
    return [(chunks[i], float(scores[i])) for i in best]


# ---------------- STEP 4: generation ----------------
SYSTEM_PROMPT = (
    "You are StudyMate, a study assistant. Answer ONLY using the student's notes provided. "
    "If the notes don't contain the answer, say: \"I couldn't find that in your notes.\" "
    "Be concise and cite sources like [1], [2]."
)


def build_prompt(question: str, retrieved) -> str:
    context = "\n\n".join(f"[{i}] {chunk.text}" for i, (chunk, _) in enumerate(retrieved, start=1))
    return f"Notes:\n{context}\n\nQuestion: {question}\nAnswer:"


async def answer_question(session: AsyncSession, user_id: int, question: str) -> AskResponse:
    retrieved = await retrieve(session, user_id, question)
    if not retrieved:
        return AskResponse(answer="You don't have any indexed notes yet. Add some notes first.",
                           sources=[])

    prompt = build_prompt(question, retrieved)
    answer = await asyncio.to_thread(llm.generate, prompt, SYSTEM_PROMPT, 0.2)

    # unique source notes, in the order they were retrieved
    sources, seen = [], set()
    for chunk, _ in retrieved:
        if chunk.note_id not in seen:
            seen.add(chunk.note_id)
            note = await session.get(Note, chunk.note_id)
            if note:
                sources.append(Source(note_id=note.id, title=note.title))
    return AskResponse(answer=answer, sources=sources)