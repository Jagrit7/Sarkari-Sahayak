
from pipecat.services.sarvam.tts import SarvamTTSService
from pipecat.transcriptions.language import Language
from voice.core.config import settings

def configure_tts() -> SarvamTTSService:
    tts = SarvamTTSService(
        api_key=settings.SARVAM_API_KEY,
        settings=SarvamTTSService.Settings(
            model="bulbul:v3-beta",  # Their latest ultra-fast model
            voice="aditya",  # Standard male voice (or use "shubh")
            language=Language.HI,  # Set default to Hindi
            pace=1.1  # Slightly speed it up for better conversational flow
        )
    )

    return tts


