from pipecat.transports.livekit.transport import LiveKitTransport, LiveKitParams
from pipecat.runner.livekit import generate_token_with_agent
from src.core.config import settings


async def configure_transport(room_name: str) -> LiveKitTransport:
    # 1. Enable audio in/out
    transport_params = LiveKitParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
    )

    # 2. Generate the secure entry token using your keys
    token = generate_token_with_agent(
        room_name,
        "scheme-setu-bot",
        settings.LIVEKIT_API_KEY,
        settings.LIVEKIT_API_SECRET
    )

    # 3. Initialize the transport using the generated token
    transport = LiveKitTransport(
        url=settings.LIVEKIT_URL,
        token=token,
        room_name=room_name,
        params=transport_params
    )

    return transport


