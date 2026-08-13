from pipecat.services.groq.llm import GroqLLMService
from voice.core.config import settings

def configure_llm() -> GroqLLMService:
    groqLLM = GroqLLMService(
        api_key=settings.GROQ_API_KEY,
        settings=GroqLLMService.Settings(
            model="openai/gpt-oss-20b",         # smaller + faster than 120b for real-time voice
            max_completion_tokens=512,          # bounds reasoning + answer so a turn can't run long
            extra={"reasoning_effort": "low"},  # minimal "thinking" -> seconds, not 80s
        ),
    )

    return groqLLM