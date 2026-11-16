"""
language_router.py — follows the caller's language, turn by turn.

Sits between STT and the context aggregator in the pipeline. Saaras runs in
auto-detect mode and labels every transcript with the language it heard.
When the caller switches to another supported language, this:
  - retunes TTS (downstream of this router) to that language and its voice
  - adds that language's reply directive to the shared LLMContext, just
    before the caller's message reaches it

Short replies never switch: detection on a word or two is unreliable. STT is
never touched, so auto-detect stays on for the whole call. All language
settings live in languages.py.
"""

from loguru import logger

from pipecat.frames.frames import (
    Frame,
    StartFrame,
    TTSSpeakFrame,
    TTSUpdateSettingsFrame,
    TranscriptionFrame,
)
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection
from pipecat.services.sarvam.tts import SarvamTTSService

from voice.core.languages import (
    LANGUAGES,
    DEFAULT_LANGUAGE,
    MIN_WORDS_TO_SWITCH,
    GREETING,
    UNSUPPORTED_DIRECTIVE,
)


def _tts_settings(lang):
    # voice switches with language: each bulbul:v4-flash voice speaks only one language
    return SarvamTTSService.Settings(language=lang["tts_language"], voice=lang["tts_voice"])


class LanguageRouter(FrameProcessor):
    def __init__(self, context, **kwargs):
        super().__init__(**kwargs)
        self._context = context          # shared LLMContext object built in pipeline.py
        self._current = DEFAULT_LANGUAGE
        self._unsupported_noted = False

    @property
    def current_language(self):
        return self._current

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, StartFrame):
            await self.push_frame(frame, direction)   # downstream processors need this too
            await self._greet()
            return

        if isinstance(frame, TranscriptionFrame):
            await self._follow_language(frame)

        await self.push_frame(frame, direction)

    async def _greet(self):
        for code, line in GREETING:
            await self._set_tts(code)
            await self.push_frame(TTSSpeakFrame(line), FrameDirection.DOWNSTREAM)
        await self._set_tts(self._current)
        self._context.messages.append({"role": "system", "content": LANGUAGES[self._current]["directive"]})

    async def _set_tts(self, code):
        # TTS sits downstream of this router -> push downstream
        await self.push_frame(
            TTSUpdateSettingsFrame(delta=_tts_settings(LANGUAGES[code])),
            FrameDirection.DOWNSTREAM,
        )

    async def _follow_language(self, frame: TranscriptionFrame):
        if frame.language is None or len(frame.text.split()) < MIN_WORDS_TO_SWITCH:
            return

        code = str(frame.language.value).split("-")[0]   # "ta-IN" -> "ta"
        if code == self._current:
            return

        if code not in LANGUAGES:
            if not self._unsupported_noted:
                logger.info(f"Language router: heard unsupported language {frame.language.value}")
                self._context.messages.append({"role": "system", "content": UNSUPPORTED_DIRECTIVE})
                self._unsupported_noted = True
            return

        logger.info(f"Language router: switching {self._current} -> {code}")
        self._current = code
        await self._set_tts(code)
        self._context.messages.append({"role": "system", "content": LANGUAGES[code]["directive"]})
