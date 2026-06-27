from loguru import logger
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection
from pipecat.frames.frames import (
    Frame,
    TranscriptionFrame,
    TTSUpdateSettingsFrame,
    LLMMessagesAppendFrame,
)

LANG_NAMES = {
    "en-IN": "English", "hi-IN": "Hindi", "bn-IN": "Bengali", "te-IN": "Telugu",
    "ta-IN": "Tamil", "mr-IN": "Marathi", "gu-IN": "Gujarati", "kn-IN": "Kannada",
    "ml-IN": "Malayalam", "pa-IN": "Punjabi", "od-IN": "Odia", "as-IN": "Assamese",
}


class LanguageSwitcher(FrameProcessor):
    """After STT: (1) switch the TTS voice to the detected language, and
    (2) inject a per-turn order so the LLM replies in that language, overriding
    the language of its own previous replies. Always forwards every frame."""

    def __init__(self):
        super().__init__()
        self._current_language = None

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, TranscriptionFrame) and frame.language is not None:
            code = getattr(frame.language, "value", str(frame.language))
            name = LANG_NAMES.get(code, code)

            # 1) switch the TTS voice only when the language actually changes
            if frame.language != self._current_language:
                self._current_language = frame.language
                logger.debug(f"LanguageSwitcher: switching TTS to {code}")
                await self.push_frame(
                    TTSUpdateSettingsFrame(settings={"language": frame.language}),
                    FrameDirection.DOWNSTREAM,
                )

            # 2) force the reply language THIS turn (beats history momentum)
            directive = {
                "role": "system",
                "content": (
                    f"The user's latest message is in {name}. "
                    f"Reply ONLY in {name}, regardless of what language your earlier replies used."
                ),
            }
            await self.push_frame(
                LLMMessagesAppendFrame([directive]),
                FrameDirection.DOWNSTREAM,
            )

        await self.push_frame(frame, direction)