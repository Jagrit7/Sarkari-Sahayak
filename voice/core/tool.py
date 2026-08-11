"""
tool.py — voice-pipeline tool wiring for scheme search.

Calls into voice/retrieval/retriever.py (the new LangChain-based search),
not data/query.py.
"""

import asyncio
import re

from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.frames.frames import FunctionCallResultProperties
from pipecat.services.llm_service import FunctionCallParams

from voice.retrieval.retriever import search_schemes

TOOL_NAME = "search_schemes"
MAX_RESULTS = 2  # how many schemes to hand back to the LLM per call — kept low, this is spoken aloud

# document_text is built as labeled sections, e.g. "Benefits: ...\nEligibility: ...".
# This pulls each section out by its label so the LLM gets structured fields to speak from.
SECTION_LABELS = {
    "benefits": "Benefits",
    "eligibility": "Eligibility",
    "documents": "Documents Required",
    "how_to_apply": "How to Apply",
}

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


def _extract_section(text, label, next_labels):
    """Pull one labeled section out of document_text, stopping at the next label or end of text."""
    pattern = rf"{label}:\s*(.*?)(?=\n(?:{'|'.join(next_labels)}):|$)"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ""


def _format(docs):
    """Trim each scheme's content to what's tolerable to speak aloud."""
    all_labels = list(SECTION_LABELS.values())
    out = []
    for doc in docs:
        md = doc.metadata or {}
        text = doc.page_content or ""
        out.append({
            "name": md.get("scheme_name"),
            "level": md.get("government_level"),
            "benefits": _extract_section(text, SECTION_LABELS["benefits"], all_labels)[:300],
            "eligibility": _extract_section(text, SECTION_LABELS["eligibility"], all_labels)[:300],
            "documents": _extract_section(text, SECTION_LABELS["documents"], all_labels)[:200],
            "how_to_apply": _extract_section(text, SECTION_LABELS["how_to_apply"], all_labels)[:200],
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