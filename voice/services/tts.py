
from pipecat.services.sarvam.tts import SarvamTTSService
from voice.core.config import settings
from voice.core.languages import LANGUAGES, DEFAULT_LANGUAGE

def configure_tts() -> SarvamTTSService:
    default_lang = LANGUAGES[DEFAULT_LANGUAGE]
    tts = SarvamTTSService(
        api_key=settings.SARVAM_API_KEY,
        settings=SarvamTTSService.Settings(
            model="bulbul:v4-flash",  # Sarvam's low-latency model; its voices are per-language
            voice=default_lang["tts_voice"],  # the language router switches voice with the language
            language=default_lang["tts_language"],  # Hindi until the caller's language is detected
            pace=1.4  # Slightly speed it up for better conversational flow
        )
    )

    return tts


