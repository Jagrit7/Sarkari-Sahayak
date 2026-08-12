import asyncio
import re

from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.frames.frames import FunctionCallResultProperties
from pipecat.services.llm_service import FunctionCallParams

from voice.retrieval.retriever import (
    check_application_process,
    check_benefits,
    check_documents,
    check_eligibility,
    search_schemes,
    check_scheme_details
)

MAX_RESULTS = 3  # how many schemes to hand back to the LLM per call — kept low, this is spoken aloud

search_schemes_schema = FunctionSchema(
    name="search_schemes",
    description=(
        "Find Indian government welfare schemes that may be suitable for the caller's "
        "needs or situation. Use this tool when the caller is looking for schemes "
        "available to them, asks what schemes they can benefit from, or describes a "
        "need and wants to know which government schemes are available. "
        "Do NOT use this tool when the caller is asking about a specific scheme that "
        "has already been identified, such as its eligibility, benefits, required "
        "documents, or application process. In those cases, use the appropriate "
        "specialized tool. "
        "Never name or describe a scheme unless it was returned by this tool or is "
        "already explicitly identified by the caller."
    ),
    properties={
        "query": {
            "type": "string",
            "description": (
                "A concise English description of what the caller needs or is looking "
                "for. Include relevant information such as occupation, purpose, age "
                "group, student/farmer status, income-related details, disability "
                "status if explicitly provided, state, district, or whether they "
                "want a Central or State government scheme. Preserve important details "
                "from the caller's request. Do not invent missing information. "
                "Examples: 'farmer income support schemes in Uttar Pradesh', "
                "'scholarships available for college students in Delhi', "
                "'housing assistance schemes for a low-income family in Bihar'."
            ),
        },
    },
    required=["query"],
)
check_eligibility_schema = FunctionSchema(
    name="check_eligibility",
    description=(
        "Check the eligibility criteria for a specific Indian government scheme. "
        "Use this tool when the caller asks who is eligible, whether they qualify, "
        "who can apply, or what eligibility requirements apply to a specific scheme. "
        "The scheme must already be identified from the conversation or from a "
        "previous search_schemes result. Do not use this tool to discover schemes. "
        "Return information only from the retrieved scheme data."
    ),
    properties={
        "scheme_name": {
            "type": "string",
            "description": (
                "The exact or near-exact name of the specific government scheme the "
                "caller is asking about. Use the scheme name returned by "
                "search_schemes when available. Do not invent or guess a scheme name."
            ),
        },
        "scheme_id": {
            "type": "string",
            "description": (
                "The unique identifier or slug of the specific government scheme. "
                "Use the identifier returned by search_schemes whenever available. "
                "Do not invent an identifier."
            ),
        },
        "query": {
            "type": "string",
            "description": (
                "The caller's specific eligibility question, expressed in English. "
                "Preserve important details such as the caller's age, occupation, "
                "state, income category, or other eligibility-related information "
                "that the caller explicitly mentioned. Do not invent missing details. "
                "Example: 'Am I eligible for PM Kisan if I am a small farmer in Uttar Pradesh?'"
            ),
        },
    },
    required=["query", "scheme_name", "scheme_id"],
)

check_documents_schema = FunctionSchema(
    name="check_documents",
    description=(
        "Find the documents or paperwork required for a specific Indian government "
        "scheme. Use this tool when the caller asks what documents are required, "
        "what paperwork they need, which certificates are needed, or what they need "
        "to submit for a specific scheme. The scheme must already be identified from "
        "the conversation or from a previous search_schemes result. Do not use this "
        "tool to discover schemes. Return information only from the retrieved scheme data."
    ),
    properties={
        "scheme_name": {
            "type": "string",
            "description": (
                "The exact or near-exact name of the specific government scheme. "
                "Use the scheme name returned by search_schemes when available. "
                "Do not invent or guess a scheme name."
            ),
        },
        "scheme_id": {
            "type": "string",
            "description": (
                "The unique identifier or slug of the specific government scheme. "
                "Use the identifier returned by search_schemes whenever available. "
                "Do not invent an identifier."
            ),
        },
        "query": {
            "type": "string",
            "description": (
                "The caller's specific question about required documents, expressed "
                "in English. Preserve relevant details from the caller's request. "
                "Example: 'What documents do I need to apply for PM Kisan?'"
            ),
        },
    },
    required=["query", "scheme_name", "scheme_id"],
)

check_benefits_schema = FunctionSchema(
    name="check_benefits",
    description=(
        "Find the benefits, financial assistance, services, subsidies, or other "
        "advantages provided by a specific Indian government scheme. Use this tool "
        "when the caller asks what they will receive, what a scheme provides, how "
        "much financial assistance it gives, or what benefits are available under "
        "a specific scheme. The scheme must already be identified from the conversation "
        "or from a previous search_schemes result. Do not use this tool to discover "
        "schemes. Return information only from the retrieved scheme data."
    ),
    properties={
        "scheme_name": {
            "type": "string",
            "description": (
                "The exact or near-exact name of the specific government scheme. "
                "Use the scheme name returned by search_schemes when available. "
                "Do not invent or guess a scheme name."
            ),
        },
        "scheme_id": {
            "type": "string",
            "description": (
                "The unique identifier or slug of the specific government scheme. "
                "Use the identifier returned by search_schemes whenever available. "
                "Do not invent an identifier."
            ),
        },
        "query": {
            "type": "string",
            "description": (
                "The caller's specific question about the scheme's benefits, expressed "
                "in English. Preserve relevant details from the caller's request. "
                "Example: 'How much financial assistance does PM Kisan provide?'"
            ),
        },
    },
    required=["query", "scheme_name", "scheme_id"],
)

check_application_process_schema = FunctionSchema(
    name="check_application_process",
    description=(
        "Find the application process or steps on how to apply for a specific Indian "
        "government scheme. Use this tool when the caller asks how to apply, where "
        "to go, or what the procedure is. The scheme must already be identified from "
        "the conversation or a previous search_schemes result. Return information "
        "only from the retrieved scheme data."
    ),
    properties={
        "scheme_name": {
            "type": "string",
            "description": "The exact or near-exact name of the specific government scheme."
        },
        "scheme_id": {
            "type": "string",
            "description": "The unique identifier or slug of the specific government scheme."
        },
        "query": {
            "type": "string",
            "description": "The caller's specific question about the application process, in English."
        },
    },
    required=["query", "scheme_name", "scheme_id"],
)

check_scheme_details_schema = FunctionSchema(
    name="check_scheme_details",
    description=(
        "Retrieve the overview and general description of a specific Indian government "
        "scheme. Use this tool when the caller asks to know about, explain, describe, "
        "or give an overview of a particular scheme that has already been identified. "
        "Use this tool for general scheme information when the caller is not specifically "
        "asking about eligibility, benefits, required documents, or another specialized "
        "aspect. Do not use this tool to discover schemes based on the caller's needs. "
        "For eligibility questions use check_eligibility, for document questions use "
        "check_documents, and for benefit questions use check_benefits."
    ),
    properties={
        "scheme_name": {
            "type": "string",
            "description": (
                "The exact or near-exact name of the specific government scheme the "
                "caller is asking about. Use the scheme name identified by the caller "
                "or returned by search_schemes. Do not invent or guess a scheme name."
            ),
        },
        "scheme_id": {
            "type": "string",
            "description": (
                "The unique identifier or slug of the specific government scheme. "
                "Use the identifier returned by search_schemes whenever available. "
                "Do not invent an identifier."
            ),
        },
        "query": {
            "type": "string",
            "description": (
                "The caller's question about the scheme, expressed in English. "
                "Preserve the caller's intent and important details. Example: "
                "'Tell me about PM Awas Yojana' or 'What is PM Kisan Samman Nidhi?'"
            ),
        },
    },
    required=["query", "scheme_name", "scheme_id"],
)
SCHEME_TOOLS = ToolsSchema(standard_tools=[search_schemes_schema, check_eligibility_schema, check_documents_schema, check_benefits_schema, check_application_process_schema, check_scheme_details_schema])


# ---------------------------------------------------------------------------
# Formatting: turn retrieved chunks into text the LLM can speak from.
# Each chunk is already scoped to one scheme + one section, and already has the
# scheme name at the top of its content (see retrieval/loader.py), so there's no
# extraction step needed here — just present what came back.
# ---------------------------------------------------------------------------

def _format(docs):
    """search_schemes: join results, appending scheme_id (not in document_text) for follow-ups."""
    if not docs:
        return "No matching schemes were found for that request."
    return "\n\n".join(f"{d.page_content}\n(scheme_id: {d.metadata.get('scheme_id')})" for d in docs)


def _format_section(docs):
    """check_*: unwrap the single matched chunk, or say nothing matched."""
    return docs[0].page_content if docs else "No information was found for that scheme_name/scheme_id combination."


# ---------------------------------------------------------------------------
# Handlers: bridge pipecat's function-calling into the (sync, blocking) retriever.
# Run on a thread so embedding/rerank calls don't block the event loop.
# ---------------------------------------------------------------------------

async def search_schemes_handler(params: FunctionCallParams):
    query = params.arguments["query"]
    docs = await asyncio.to_thread(search_schemes, query, MAX_RESULTS)
    await params.result_callback(_format(docs))


async def check_eligibility_handler(params: FunctionCallParams):
    args = params.arguments
    docs = await asyncio.to_thread(
        check_eligibility, args["query"], args["scheme_name"], args["scheme_id"]
    )
    await params.result_callback(_format_section(docs))


async def check_documents_handler(params: FunctionCallParams):
    args = params.arguments
    docs = await asyncio.to_thread(
        check_documents, args["query"], args["scheme_name"], args["scheme_id"]
    )
    await params.result_callback(_format_section(docs))


async def check_benefits_handler(params: FunctionCallParams):
    args = params.arguments
    docs = await asyncio.to_thread(
        check_benefits, args["query"], args["scheme_name"], args["scheme_id"]
    )
    await params.result_callback(_format_section(docs))


async def check_application_process_handler(params: FunctionCallParams):
    args = params.arguments
    docs = await asyncio.to_thread(
        check_application_process, args["query"], args["scheme_name"], args["scheme_id"]
    )
    await params.result_callback(_format_section(docs))

async def check_scheme_details_handler(params: FunctionCallParams):
    args = params.arguments
    docs = await asyncio.to_thread(
        check_scheme_details, args["query"], args["scheme_name"], args["scheme_id"]
    )
    await params.result_callback(_format_section(docs))

def register_scheme_tool(llm):
    llm.register_function("search_schemes", search_schemes_handler)
    llm.register_function("check_eligibility", check_eligibility_handler)
    llm.register_function("check_documents", check_documents_handler)
    llm.register_function("check_benefits", check_benefits_handler)
    llm.register_function("check_application_process", check_application_process_handler)


