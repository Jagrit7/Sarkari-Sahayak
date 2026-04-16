import json
import asyncio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from llm import get_rag_stream, GREETING

router = APIRouter()


@router.post("/vapi/webhook")
async def vapi_webhook(payload: dict):
    """Handles basic Vapi configuration requests."""
    msg = payload.get("message", {})
    if msg.get("type") == "assistant-request":
        return {
            "assistant": {
                "name": "Sahayak",
                "firstMessage": GREETING,
                "model": {
                    "provider": "custom-llm",
                    "url": "REPLACE_WITH_CLOUDFLARE_URL/vapi/chat/completions"  # Keep this configured in dashboard
                },
                "voice": {
                    "provider": "11labs",
                    "voiceId": "21m00Tcm4TlvDq8ikWAM",
                    "model": "eleven_multilingual_v2"
                }
            }
        }
    return {"status": "ok"}


@router.post("/vapi/chat/completions")
async def vapi_chat_completions(payload: dict):
    """The Custom LLM streaming endpoint Vapi connects to."""
    messages = payload.get("messages", [])

    # Extract the last user message
    user_message = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, list):
                content = " ".join(item.get("text", "") for item in content if isinstance(item, dict))
            user_message = content
            break

    # Helper function to safely encode Hindi characters for the UI
    def safe_json(data_dict):
        return json.dumps(data_dict, ensure_ascii=False)



    # Normal conversation turn
    async def stream_rag_response():
        # FIX: Added "index": 0
        primer = {"id": "chatcmpl-1", "object": "chat.completion.chunk",
                  "choices": [{"index": 0, "delta": {"role": "assistant", "content": ""}}]}
        yield f"data: {safe_json(primer)}\n\n"

        await asyncio.sleep(0.05)

        try:
            stream = await get_rag_stream(messages, user_message)

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    # FIX: Added "index": 0 and safe_json for Hindi text
                    data = {"id": "chatcmpl-1", "object": "chat.completion.chunk",
                            "choices": [{"index": 0, "delta": {"content": chunk.choices[0].delta.content}}]}
                    yield f"data: {safe_json(data)}\n\n"

            stop_chunk = {"id": "chatcmpl-1", "object": "chat.completion.chunk",
                          "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]}
            yield f"data: {safe_json(stop_chunk)}\n\n"
            yield "data: [DONE]\n\n"

        except Exception as e:
            print(f"Error: {e}")
            yield "data: [DONE]\n\n"

    return StreamingResponse(stream_rag_response(), media_type="text/event-stream")