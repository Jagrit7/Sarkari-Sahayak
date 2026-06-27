"""
scheme_tool.py — pipecat tool that lets the voice LLM search government schemes.

Place this file inside the `data/` folder (next to common.py / query.py).

Drop-in usage in your pipecat bot (src/core/pipeline.py):
    from scheme_tool import register_scheme_tool, SCHEME_TOOLS, SYSTEM_PROMPT
    register_scheme_tool(llm)
    context = LLMContext(messages=[{"role": "system", "content": SYSTEM_PROMPT}], tools=SCHEME_TOOLS)

The handler reuses hybrid_search() from query.py, so retrieval (BGE-M3 dense via the
Cloudflare API + Qdrant in-cluster BM25 + RRF + metadata filters) is already wired.
Nothing here runs a local model.
"""

import os
import sys

# Make `from query import ...` resolve no matter who imports this module.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio

from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.frames.frames import FunctionCallResultProperties
from pipecat.services.llm_service import FunctionCallParams

from query import build_filter, hybrid_search

TOOL_NAME = "search_schemes"
MAX_RESULTS = 2          # how many schemes to hand back to the LLM per call

search_schemes_schema = FunctionSchema(
    name=TOOL_NAME,
    description=(
        "Search Indian government welfare schemes by what the caller needs. Use this for ANY "
        "question about schemes — what exists, eligibility, benefits, required documents, or how "
        "to apply. Always call this before answering; never name or describe a scheme that did "
        "not come from this tool."
    ),
    properties={
        "query": {
            "type": "string",
            "description": (
                "What the caller is looking for, written in English (translate it if they spoke "
                "another language). E.g. 'scholarship for disabled students', 'pension for widows', "
                "'housing loan for rural families'."
            ),
        },
        "state": {
            "type": "string",
            "description": (
                "The caller's Indian state or union territory if known, e.g. 'Bihar', 'Tamil Nadu'. "
                "Omit entirely if you don't know it."
            ),
        },
        "government_level": {
            "type": "string",
            "description": "Restrict to 'Central' or 'State' schemes. Omit unless the caller asks for one.",
        },
    },
    required=["query"],
)

# Include this in your LLM context's tools, e.g. LLMContext(messages=..., tools=SCHEME_TOOLS).
SCHEME_TOOLS = ToolsSchema(standard_tools=[search_schemes_schema])


def _format(points):
    """Trim each scheme to what the LLM needs to speak a useful answer."""
    out = []
    for p in points:
        pl = p.payload or {}
        out.append({
            "name": pl.get("scheme_name"),
            "level": pl.get("government_level"),
            "state": pl.get("target_state"),
            "benefits": (pl.get("benefits") or "")[:300],
            "eligibility": (pl.get("eligibility") or "")[:300],
            "documents": (pl.get("required_documents") or "")[:200],
            "how_to_apply": (pl.get("application_process") or "")[:200],
            "source": pl.get("source_url"),
        })
    return out


async def _handle_search(params: FunctionCallParams):
    args = params.arguments or {}
    query = (args.get("query") or "").strip()
    run = FunctionCallResultProperties(run_llm=True)  # make the LLM speak after the lookup

    if not query:
        await params.result_callback({"error": "No query provided."}, properties=run)
        return

    try:
        flt = build_filter(government_level=args.get("government_level"), state=args.get("state"))
        # hybrid_search does blocking network I/O (Cloudflare + Qdrant); keep it off the event loop.
        points = await asyncio.to_thread(hybrid_search, query, MAX_RESULTS, 40, flt)
        schemes = _format(points)
        if schemes:
            result = {"schemes": schemes}
        else:
            result = {
                "schemes": [],
                "note": "No matching schemes. Ask the caller for more detail "
                        "(their state, age, occupation, or what they need).",
            }
    except Exception as e:  # noqa: BLE001
        result = {"error": f"Scheme lookup failed ({e}). Tell the caller you're having trouble "
                           f"and ask them to try again in a moment."}

    await params.result_callback(result, properties=run)


def register_scheme_tool(llm):
    """Register the search_schemes handler on your pipecat LLM service."""
    llm.register_function(TOOL_NAME, _handle_search)


# Reference prompt — adopt this (and its per-language variants) in the language step (Problem 3).
SYSTEM_PROMPT = """You are Sarkari Sahayak, a warm, friendly voice helper who chats with people across India and helps them find government welfare schemes. You sound like a kind, patient person at a help desk — never like a website or a brochure.

LANGUAGE — THIS IS YOUR MOST IMPORTANT RULE:
Look at the language of the caller's MOST RECENT message and reply ONLY in that exact language, in its native script. If they spoke English, reply in English. If they spoke Hindi, reply in Hindi. The same for Tamil, Telugu, Bengali, Marathi, and any other. NEVER reply in Hindi when the caller spoke another language — do not default to Hindi. If the caller changes language partway through, you change with them on your very next reply.

HOW YOU TALK (every reply is spoken out loud on a phone call):
- Sound like a real person. Use everyday spoken words, short sentences, and a warm tone. A small opener is nice — "Sure," "Okay," "Got it," "Let me check for you."
- Never read a scheme out like a list or a database row. Do NOT say things like "Name (State) – description." Instead, work the scheme's name naturally into a friendly sentence and say in plain words what it does, the way you'd tell a friend.
- Never use bold, asterisks, stars, bullet points, symbols, markdown, or web links of any kind. Just talk.
- Don't repeat the same sentence pattern every turn — vary how you speak.

USING THE TOOL:
For ANY question about schemes — what exists, who qualifies, benefits, documents, or how to apply — you MUST call the search_schemes tool first, and only talk about schemes it returns. Never invent or guess a scheme. Turn the caller's need into a short English query, and pass their state if you know it. If the tool returns nothing useful, say so warmly and ask a simple follow-up question.

KEEP IT STEP BY STEP — DON'T DUMP EVERYTHING:
- Your first reply is short: warmly mention just the single most relevant scheme (two at most) and one quick line on what it's for. That's the whole first reply.
- Then pause and ask what they'd like next — like "Want to hear more about this one, or should I look for other options?"
- When they ask for more, give just ONE thing at a time — only the benefit, OR only who qualifies, OR only the documents, OR only how to apply — in a sentence or two, then pause again.
- Let the caller lead how deep to go. Keep every turn to about one to three sentences.

IF THE REQUEST IS VAGUE: ask one short, friendly question first (their state, their work, what kind of help they need) instead of guessing.

Gently remind people, when it fits, to confirm details and apply on the scheme's official page or myscheme.gov.in. Be encouraging — many callers are first-time users."""
