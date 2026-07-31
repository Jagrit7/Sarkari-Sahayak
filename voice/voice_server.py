from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from voice.core.transport import configure_transport
from voice.core.pipeline import create_pipeline
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from livekit import api
from fastapi.middleware.cors import CORSMiddleware
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

# let the Vite dev frontend call /token from the browser (dev only; lock this down in prod)
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])


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
async def configure_websocket(websocket: WebSocket):
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