from pipecat.services.cerebras.llm import CerebrasLLMService
from voice.core.config import settings

def configure_llm() -> CerebrasLLMService:
    cerebras_llm = CerebrasLLMService(
        api_key=settings.CEREBRAS_API_KEY,
        settings=CerebrasLLMService.Settings(
            model="qwen-3-32b",  # Multilingual and excellent at tool-calling on Cerebras
            max_completion_tokens=512,  # Bounds answer so a turn can't run long
            # Note: extra={"reasoning_effort": "low"} is omitted here as it is primarily supported by the gpt-oss-120b model on Cerebras.
        ),
    )

    return cerebras_llm