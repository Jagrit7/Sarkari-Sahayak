"""
tool.py — voice-pipeline tool wiring for scheme search.

Calls into voice/retrieval/retriever.py (the new LangChain-based search),
not data/query.py.
"""

import asyncio

from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.frames.frames import FunctionCallResultProperties
from pipecat.services.llm_service import FunctionCallParams

from voice.retrieval.retriever import search_schemes

TOOL_NAME = "search_schemes"
MAX_RESULTS = 2  # how many schemes to hand back to the LLM per call — kept low, this is spoken aloud

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
                "another language). Include their state or whether they want a Central or State "
                "scheme directly in this text if they mentioned it, e.g. 'farmer income support "
                "scheme Uttar Pradesh', 'central government scholarship for disabled students'."
            ),
        },
    },
    required=["query"],
)

SCHEME_TOOLS = ToolsSchema(standard_tools=[search_schemes_schema])


def _format(docs):
    """Trim each scheme's metadata to what's tolerable to speak aloud."""
    out = []
    for doc in docs:
        md = doc.metadata or {}
        out.append({
            "name": md.get("scheme_name"),
            "level": md.get("government_level"),
            "state": md.get("target_state"),
            "benefits": (md.get("benefits") or "")[:300],
            "eligibility": (md.get("eligibility") or "")[:300],
            "documents": (md.get("required_documents") or "")[:200],
            "how_to_apply": (md.get("application_process") or "")[:200],
            "source": md.get("source_url"),
        })
    return out


async def _handle_search(params: FunctionCallParams):
    args = params.arguments or {}
    query = (args.get("query") or "").strip()
    run = FunctionCallResultProperties(run_llm=True)

    if not query:
        await params.result_callback({"error": "No query provided."}, properties=run)
        return

    try:
        docs = await asyncio.to_thread(search_schemes, query, MAX_RESULTS)
        schemes = _format(docs)
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
    """Register the search_schemes handler on the pipecat LLM service."""
    llm.register_function(TOOL_NAME, _handle_search)