"""
ivr.py — DTMF language-lock gate.

Sits between STT and the context aggregator in the pipeline. Plays the
menu (each line in its own language/voice), waits for one DTMF digit,
then locks the call to that language for good:
  - bakes a one-time directive into the shared LLMContext (no more
    per-turn language re-detection)
  - retunes TTS (downstream of this gate) and STT (upstream of this gate)
    to that language
  - stops gating frames, gets out of the way for the rest of the call

Until locked, all speech transcriptions are swallowed so the caller can't
accidentally talk to the LLM before a language is chosen.
"""

import asyncio
from typing import Optional

from loguru import logger

from pipecat.frames.frames import (
    Frame,
    StartFrame,
    InputDTMFFrame,
    TTSSpeakFrame,
    TTSUpdateSettingsFrame,
    STTUpdateSettingsFrame,
    TranscriptionFrame,
    InterimTranscriptionFrame,
)
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection
from pipecat.services.sarvam.tts import SarvamTTSService
from pipecat.services.sarvam.stt import SarvamSTTService

from voice.core.languages import LANGUAGES, DEFAULT_DIGIT, IVR_TIMEOUT_SECONDS, IVR_MAX_RETRIES


class IVRGate(FrameProcessor):
    def __init__(self, context, **kwargs):
        super().__init__(**kwargs)
        self._context = context          # shared LLMContext object built in pipeline.py
        self._locked = False
        self._retries = 0
        self._timeout_task: Optional[asyncio.Task] = None

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, StartFrame):
            await self.push_frame(frame, direction)   # downstream processors need this too
            await self._play_menu()
            self._start_timeout()
            return

        if self._locked:
            await self.push_frame(frame, direction)
            return

        if isinstance(frame, InputDTMFFrame):
            await self._handle_digit(frame.button)
            return  # consumed, don't forward the raw keypress

        if isinstance(frame, (TranscriptionFrame, InterimTranscriptionFrame)):
            return  # swallow speech until a language is locked

        await self.push_frame(frame, direction)  # audio/control frames pass through untouched

    async def _play_menu(self):
        for digit, lang in LANGUAGES.items():
            await self.push_frame(
                TTSUpdateSettingsFrame(delta=SarvamTTSService.Settings(language=lang["tts_language"])),
                FrameDirection.DOWNSTREAM,
            )
            await self.push_frame(TTSSpeakFrame(lang["menu_line"]), FrameDirection.DOWNSTREAM)

    def _start_timeout(self):
        self._cancel_timeout()
        self._timeout_task = asyncio.create_task(self._timeout_watch())

    def _cancel_timeout(self):
        if self._timeout_task and not self._timeout_task.done():
            self._timeout_task.cancel()

    async def _timeout_watch(self):
        try:
            await asyncio.sleep(IVR_TIMEOUT_SECONDS)
        except asyncio.CancelledError:
            return
        if self._locked:
            return
        self._retries += 1
        if self._retries > IVR_MAX_RETRIES:
            logger.info(f"IVR: no valid input after {self._retries - 1} retries, defaulting")
            await self._lock(DEFAULT_DIGIT)
        else:
            logger.info(f"IVR: timeout, re-prompting (attempt {self._retries})")
            await self._play_menu()
            self._start_timeout()

    async def _handle_digit(self, digit):
        if digit not in LANGUAGES:
            logger.info(f"IVR: invalid digit {digit}, re-prompting")
            self._retries += 1
            if self._retries > IVR_MAX_RETRIES:
                await self._lock(DEFAULT_DIGIT)
            else:
                await self._play_menu()
                self._start_timeout()
            return
        await self._lock(digit)

    async def _lock(self, digit):
        self._cancel_timeout()
        lang = LANGUAGES[digit]
        logger.info(f"IVR: locking call to {lang['name']}")

        # 1) bake the directive into the shared context ONCE — no per-turn injection
        self._context.messages.append({"role": "system", "content": lang["directive"]})

        # 2) TTS sits downstream of this gate -> push downstream
        await self.push_frame(
            TTSUpdateSettingsFrame(delta=SarvamTTSService.Settings(language=lang["tts_language"])),
            FrameDirection.DOWNSTREAM,
        )
        # 3) STT sits upstream of this gate -> push upstream so it actually reaches it
        await self.push_frame(
            STTUpdateSettingsFrame(delta=SarvamSTTService.Settings(language=lang["stt_language"])),
            FrameDirection.UPSTREAM,
        )
        self._locked = True