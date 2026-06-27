from pipecat.services.sarvam.stt import SarvamSTTService
from src.core.config import settings


def configure_stt() -> SarvamSTTService:
    stt = SarvamSTTService(
        api_key=settings.SARVAM_API_KEY,
        settings=SarvamSTTService.Settings(
            model="saaras:v3",      # Sarvam's Indic ASR; auto-detects the spoken language
        ),
    )

    return stt