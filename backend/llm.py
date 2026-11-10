"""
Small helper around the LLM APIs (used on Days 12-14).
- Chat/text: Gemini (GEMINI_API_KEY) or Groq (GROQ_API_KEY)
- Embeddings: Gemini only (Groq has no embedding API)
Model names can be changed in .env without touching code.
"""
import json
import os
import time

from dotenv import load_dotenv

load_dotenv()

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
GROQ_KEY = os.getenv("GROQ_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
EMBED_MODEL = os.getenv("EMBED_MODEL", "gemini-embedding-001")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

_gemini = None
_groq = None


def _gemini_client():
    global _gemini
    if _gemini is None:
        from google import genai
        _gemini = genai.Client(api_key=GEMINI_KEY)
    return _gemini


def _groq_client():
    global _groq
    if _groq is None:
        from groq import Groq
        _groq = Groq(api_key=GROQ_KEY)
    return _groq


def _with_retry(call, attempts: int = 4):
    """Retry when the API is busy (503) or rate-limited (429): wait 2s, 4s, 8s between tries."""
    for attempt in range(1, attempts + 1):
        try:
            return call()
        except Exception as err:
            busy = any(code in str(err) for code in ("503", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED"))
            if not busy or attempt == attempts:
                raise
            wait = 2 ** attempt
            print(f"[llm] API busy, retrying in {wait}s (attempt {attempt}/{attempts - 1})...")
            time.sleep(wait)


def generate(prompt: str, system: str | None = None, temperature: float = 0.3,
             json_mode: bool = False) -> str:
    """Send a prompt, get text back. json_mode=True asks the model for valid JSON."""
    if GEMINI_KEY:
        from google.genai import types
        config = types.GenerateContentConfig(
            system_instruction=system,
            temperature=temperature,
            response_mime_type="application/json" if json_mode else None,
        )
        response = _with_retry(lambda: _gemini_client().models.generate_content(
            model=GEMINI_MODEL, contents=prompt, config=config))
        return response.text or ""
    if GROQ_KEY:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        response = _with_retry(lambda: _groq_client().chat.completions.create(
            model=GROQ_MODEL, messages=messages, temperature=temperature,
            response_format={"type": "json_object"} if json_mode else None,
        ))
        return response.choices[0].message.content or ""
    raise RuntimeError("No API key found. Add GEMINI_API_KEY (or GROQ_API_KEY) to your .env file.")


def generate_json(prompt: str, system: str | None = None) -> dict:
    """Like generate(), but returns a Python dict."""
    text = generate(prompt, system=system, temperature=0, json_mode=True)
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
    return json.loads(text)


def embed(texts: list[str]) -> list[list[float]]:
    """Turn each text into a vector of numbers (needs GEMINI_API_KEY)."""
    if not GEMINI_KEY:
        raise RuntimeError("Embeddings need GEMINI_API_KEY in your .env file.")
    response = _with_retry(lambda: _gemini_client().models.embed_content(model=EMBED_MODEL, contents=texts))
    return [e.values for e in response.embeddings]