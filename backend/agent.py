"""
Study Buddy - an AI agent built FROM SCRATCH (no framework).

Agent = LLM + tools + a loop:
    1. THINK   - the LLM reads the goal and everything so far
    2. ACT     - it picks a tool and arguments (as JSON)
    3. OBSERVE - our code runs the tool and feeds the result back
    4. repeat until the LLM gives a final answer (or we hit MAX_STEPS)

Memory:
    short-term = this conversation's recent messages + the steps taken (scratchpad)
    long-term  = the student's notes in the database (reached through tools)
"""
import ast
import asyncio
import json
import operator

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

import llm
from models import Note
from rag import retrieve

MAX_STEPS = 6

# ---------------------------------------------------------------
# STEP 1: Describe the tools (this text is what the LLM "sees")
# ---------------------------------------------------------------
TOOL_DESCRIPTIONS = """
search_notes(query: str) -> the most relevant passages from the student's notes for a question
list_notes(subject: str | null) -> id, title and subject of the student's notes (optionally one subject)
summarize_note(note_id: int) -> a short bullet summary of one note
make_quiz(note_id: int, num_questions: int) -> multiple-choice questions from one note
calculator(expression: str) -> evaluates arithmetic like "(45 + 38) / 2"
""".strip()

SYSTEM_PROMPT = f"""You are Study Buddy, an AI study agent inside the StudyMate app.
You help a student using THEIR notes. You can use these tools:

{TOOL_DESCRIPTIONS}

Plan step by step. At every step reply with ONLY one JSON object, either:
  {{"thought": "why", "tool": "<tool name>", "args": {{...}}}}
or, when you have enough information:
  {{"thought": "why", "final_answer": "<answer for the student>"}}

Rules: use tools instead of guessing; never invent note ids (use list_notes or search_notes first);
if the notes don't cover something, say so; keep final answers clear and friendly."""


# ---------------------------------------------------------------
# STEP 2: A safe calculator (never use eval() on user input!)
# ---------------------------------------------------------------
_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
        ast.USub: operator.neg}


def safe_eval(expression: str) -> float:
    def walk(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](walk(node.left), walk(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](walk(node.operand))
        raise ValueError("Only numbers and + - * / ** % are allowed")
    return walk(ast.parse(expression, mode="eval").body)


# ---------------------------------------------------------------
# STEP 3: The agent with its tools and loop
# ---------------------------------------------------------------
class StudyBuddy:
    def __init__(self, session: AsyncSession, user_id: int):
        self.session = session
        self.user_id = user_id
        self.tools = {
            "search_notes": self.search_notes,
            "list_notes": self.list_notes,
            "summarize_note": self.summarize_note,
            "make_quiz": self.make_quiz,
            "calculator": self.calculator,
        }

    # ----- tools -----
    async def search_notes(self, query: str) -> str:
        results = await retrieve(self.session, self.user_id, query, k=3)
        if not results:
            return "No matching notes."
        return "\n".join(f"(note_id={c.note_id}) {c.text[:400]}" for c, _ in results)

    async def list_notes(self, subject: str | None = None) -> str:
        query = select(Note).where(Note.owner_id == self.user_id)
        if subject:
            query = query.where(Note.subject == subject)
        notes = (await self.session.exec(query)).all()
        if not notes:
            return "No notes found."
        return "\n".join(f"id={n.id} | {n.title} | {n.subject}" for n in notes)

    async def _own_note(self, note_id: int) -> Note:
        note = await self.session.get(Note, int(note_id))
        if not note or note.owner_id != self.user_id:
            raise ValueError(f"No note with id {note_id}")
        return note

    async def summarize_note(self, note_id: int) -> str:
        note = await self._own_note(note_id)
        prompt = f"Summarize this note in 3 short bullet points for revision.\n\n{note.title}\n{note.content}"
        return await asyncio.to_thread(llm.generate, prompt, None, 0.2)

    async def make_quiz(self, note_id: int, num_questions: int = 3) -> str:
        note = await self._own_note(note_id)
        prompt = (f"Create {int(num_questions)} multiple-choice questions from this note. Return JSON: "
                  '{"questions": [{"question": str, "options": [4 strings], "answer": str}]}'
                  f"\n\nNote:\n{note.title}\n{note.content}")
        quiz = await asyncio.to_thread(llm.generate_json, prompt)
        return json.dumps(quiz)

    async def calculator(self, expression: str) -> str:
        return str(safe_eval(expression))

    # ----- the loop -----
    async def run(self, message: str, history: list[dict]) -> dict:
        conversation = "\n".join(f"{m['role']}: {m['content']}" for m in history[-6:])
        scratchpad: list[str] = []
        steps: list[dict] = []

        for step in range(1, MAX_STEPS + 1):
            prompt = (f"Conversation so far:\n{conversation or '(none)'}\n\n"
                      f"Student's new message: {message}\n\n"
                      f"Steps taken so far:\n{chr(10).join(scratchpad) or '(none)'}\n\n"
                      "What is your next step? Reply with one JSON object.")
            try:
                decision = await asyncio.to_thread(llm.generate_json, prompt, SYSTEM_PROMPT)
            except (json.JSONDecodeError, ValueError):
                scratchpad.append(f"Step {step}: your last reply was not valid JSON. Reply with JSON only.")
                continue

            if "final_answer" in decision:
                return {"reply": decision["final_answer"], "steps": steps}

            tool_name = decision.get("tool", "")
            args = decision.get("args") or {}
            tool = self.tools.get(tool_name)
            try:
                if tool is None:
                    raise ValueError(f"Unknown tool '{tool_name}'")
                result = await tool(**args)
            except Exception as err:          # tell the agent what went wrong so it can recover
                result = f"ERROR: {err}"

            scratchpad.append(f"Step {step}: called {tool_name}({json.dumps(args)}) -> {result[:1500]}")
            steps.append({"tool": tool_name, "args": args, "result": result[:300]})

        return {"reply": "I couldn't finish that within my step limit. Try a more specific request.",
                "steps": steps}