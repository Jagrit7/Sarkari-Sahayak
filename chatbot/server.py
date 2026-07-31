from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from src.core.transport import configure_transport
from src.core.pipeline import create_pipeline
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from livekit import api
import sys, json
from pathlib import Path
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
import uvicorn
import asyncio
import os

load_dotenv()
LIVEKIT_API_KEY = os.getenv('LIVEKIT_API_KEY')
LIVEKIT_API_SECRET = os.getenv('LIVEKIT_API_SECRET')

@asynccontextmanager
async def configure_lifespan(app):
    print('Server booting up....')
    yield
    print('Server shutting down....')

app = FastAPI(lifespan=configure_lifespan)



# make data/ importable so we reuse the SAME prompt + RAG as the voice bot
sys.path.insert(0, str(Path(__file__).parent / "data"))
from data.scheme_tool import SYSTEM_PROMPT, _format
from data.query import build_filter, hybrid_search

# let the Vite dev server call us (dev only; lock this down in prod)
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
CHAT_MODEL = "openai/gpt-oss-120b"   # text can afford the bigger model; voice uses 20b for latency

CHAT_TOOLS = [{
    "type": "function",
    "function": {
        "name": "search_schemes",
        "description": ("Search Indian government welfare schemes by what the user needs. Use for ANY "
                        "question about schemes. Always call this before answering; never name a scheme "
                        "that did not come from this tool."),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "What the user needs, in English (translate if needed)."},
                "state": {"type": ["string", "null"], "description": "User's Indian state/UT if known; null otherwise."},
                "government_level": {"type": ["string", "null"], "description": "'Central' or 'State'; null unless asked."},
            },
            "required": ["query"],
        },
    },
}]

def _run_search(args: dict) -> dict:
    q = (args.get("query") or "").strip()
    if not q:
        return {"schemes": [], "note": "No query."}
    flt = build_filter(government_level=args.get("government_level"), state=args.get("state"))
    schemes = _format(hybrid_search(q, 3, 40, flt))
    return {"schemes": schemes} if schemes else {"schemes": [], "note": "No matches; ask for more detail."}

def run_chat_turn(message: str, history: list) -> dict:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += [{"role": m["role"], "content": m["content"]} for m in history]
    messages.append({"role": "user", "content": message})

    first = groq_client.chat.completions.create(
        model=CHAT_MODEL, messages=messages, tools=CHAT_TOOLS, tool_choice="auto",
        max_completion_tokens=2048, reasoning_effort="low",  # needs recent groq pkg; drop if it errors
    )
    msg = first.choices[0].message
    if not msg.tool_calls:
        return {"content": msg.content or "", "citation": None}

    messages.append({"role": "assistant", "content": msg.content or "",
                     "tool_calls": [{"id": tc.id, "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                        for tc in msg.tool_calls]})
    for tc in msg.tool_calls:
        try:
            args = json.loads(tc.function.arguments or "{}")
        except json.JSONDecodeError:
            args = {}
        messages.append({"role": "tool", "tool_call_id": tc.id,
                         "content": json.dumps(_run_search(args))})

    second = groq_client.chat.completions.create(
        model=CHAT_MODEL, messages=messages, max_completion_tokens=2048, reasoning_effort="low")
    return {"content": second.choices[0].message.content or "",
            "citation": "Always confirm details on the official page or myscheme.gov.in"}

class ChatRequest(BaseModel):
    message: str
    history: list = []

@app.post("/chat")
async def chat(req: ChatRequest):
    # Groq call + Qdrant search are blocking, so run the whole turn off the event loop
    return await asyncio.to_thread(run_chat_turn, req.message, req.history)

@app.get('/token')
async def generate_token():
    token_obj = (
        api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity("user-123")
        .with_grants(api.VideoGrants(
            room_join=True,
            room='support-room'
        ))
    )
    access_token = token_obj.to_jwt()
    return {'accessToken': access_token}

async def run_bot():
    room_name = "support-room"
    transport = await configure_transport(room_name)
    # 2. Build the pipeline and unpack the runner and worker
    runner, worker = await create_pipeline(transport)
    # 3. Register your pipeline worker to the runner's shared message bus
    await runner.add_workers(worker)
    # 4. Start the execution loop and keep the process alive
    print(f" Bot is booting up and joining room: {room_name}...")
    await runner.run()

@app.websocket('/ws')
async def configure_websocket(websocket:WebSocket):
    await websocket.accept()
    bot_task = asyncio.create_task(run_bot())
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        print('User Disconnected')
    finally:
        bot_task.cancel()

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)