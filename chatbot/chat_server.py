"""
Lightweight, deploy-friendly chat API for Sarkari Sahayak.

This is a TEXT-ONLY entrypoint. It serves the frontend's /chat calls using the
same hybrid-RAG search + Groq LLM as the voice bot, but imports NONE of the voice
stack (no pipecat, no LiveKit, no PyTorch). That keeps it small enough to run on a
free host like Render.

Run locally:   uvicorn chat_server:app --reload --port 8000
Env required:  GROQ_API_KEY, QDRANT_URL, QDRANT_API_KEY,
               CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_API_TOKEN
"""

import os
import sys
import json
import asyncio
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# Reuse the RAG search from data/ (these modules don't import pipecat)
sys.path.insert(0, str(Path(__file__).parent / "data"))
from query import build_filter, hybrid_search  # noqa: E402

app = FastAPI(title="Sarkari Sahayak Chat API")

# Allow the deployed frontend to call us. In production you can replace "*" with
# your exact Vercel URL, e.g. allow_origins=["https://your-app.vercel.app"].
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
CHAT_MODEL = "openai/gpt-oss-120b"   # text can afford the bigger model

SYSTEM_PROMPT = """You are Sarkari Sahayak, a warm, plain-spoken assistant that helps people in India find and understand government welfare schemes — what they qualify for, the benefits, the documents needed, and how to apply.

How you work:
- For ANY question about schemes, ALWAYS call the search_schemes tool first, and answer ONLY from what it returns. Never name or describe a scheme that did not come from the tool. If nothing useful comes back, say so plainly and ask one clarifying question (their state, age, occupation, or what they need).
- Reply in the SAME language the user writes in (English, Hindi, or any Indian language), matching their script.
- Be genuinely helpful and concise. Lead with the single most relevant scheme and its key facts; don't dump everything at once. Offer to go deeper ("Want the full eligibility list, or how to apply?") instead of overwhelming them.
- Light formatting is fine — bold a scheme's name, a short bullet list for documents — but keep it clean, not a wall of text.
- Always remind users to confirm details on the official scheme page or myscheme.gov.in before applying, since rules change.

Many users are first-time applicants who find government processes intimidating — make it feel approachable."""

CHAT_TOOLS = [{
    "type": "function",
    "function": {
        "name": "search_schemes",
        "description": ("Search Indian government welfare schemes by what the user needs. Use for ANY "
                        "question about schemes — what exists, eligibility, benefits, documents, or how "
                        "to apply. Always call this before answering."),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string",
                          "description": "What the user needs, phrased in English (translate if needed)."},
                "state": {"type": ["string", "null"],
                          "description": "User's Indian state/UT if mentioned; null otherwise."},
                "government_level": {"type": ["string", "null"],
                                     "description": "'Central' or 'State'; null unless the user asks."},
            },
            "required": ["query"],
        },
    },
}]


def _format(points):
    """Trim each scheme to what the model needs to write a useful answer."""
    out = []
    for p in points:
        pl = p.payload or {}
        out.append({
            "name": pl.get("scheme_name"),
            "level": pl.get("government_level"),
            "state": pl.get("target_state"),
            "benefits": (pl.get("benefits") or "")[:600],
            "eligibility": (pl.get("eligibility") or "")[:600],
            "documents": (pl.get("required_documents") or "")[:400],
            "how_to_apply": (pl.get("application_process") or "")[:400],
            "source": pl.get("source_url"),
        })
    return out


def _run_search(args: dict) -> dict:
    query = (args.get("query") or "").strip()
    if not query:
        return {"schemes": [], "note": "No query provided."}
    flt = build_filter(government_level=args.get("government_level"), state=args.get("state"))
    schemes = _format(hybrid_search(query, 3, 40, flt))
    if schemes:
        return {"schemes": schemes}
    return {"schemes": [], "note": "No matching schemes; ask the user for more detail."}


def run_chat_turn(message: str, history: list) -> dict:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += [{"role": m["role"], "content": m["content"]} for m in history]
    messages.append({"role": "user", "content": message})

    first = groq_client.chat.completions.create(
        model=CHAT_MODEL, messages=messages, tools=CHAT_TOOLS, tool_choice="auto",
        max_completion_tokens=2048, reasoning_effort="low",
    )
    msg = first.choices[0].message
    if not msg.tool_calls:
        return {"content": msg.content or "", "citation": None}

    messages.append({
        "role": "assistant",
        "content": msg.content or "",
        "tool_calls": [{"id": tc.id, "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                       for tc in msg.tool_calls],
    })
    for tc in msg.tool_calls:
        try:
            args = json.loads(tc.function.arguments or "{}")
        except json.JSONDecodeError:
            args = {}
        messages.append({"role": "tool", "tool_call_id": tc.id,
                         "content": json.dumps(_run_search(args))})

    second = groq_client.chat.completions.create(
        model=CHAT_MODEL, messages=messages, max_completion_tokens=2048, reasoning_effort="low",
    )
    return {"content": second.choices[0].message.content or "",
            "citation": "Always confirm details on the official page or myscheme.gov.in"}


class ChatRequest(BaseModel):
    message: str
    history: list = []


@app.get("/health")
def health():
    """Lightweight endpoint for uptime pingers (keeps the free instance awake)."""
    return {"status": "ok"}


@app.post("/chat")
async def chat(req: ChatRequest):
    # Groq + Qdrant calls are blocking, so run the whole turn off the event loop.
    return await asyncio.to_thread(run_chat_turn, req.message, req.history)
