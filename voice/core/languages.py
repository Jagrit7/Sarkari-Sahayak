"""
languages.py — single source of truth for the IVR language menu.

Add or remove a supported language ONLY here. The DTMF digit map, the
spoken IVR menu, the STT/TTS locking, and the system-prompt directive
all read from this one dict — nothing else needs touching to add a language.
"""

from pipecat.audio.dtmf.types import KeypadEntry
from pipecat.transcriptions.language import Language

LANGUAGES = {
    KeypadEntry.ONE: {
        "name": "Hindi",
        "tts_language": Language.HI,
        "stt_language": "hi-IN",
        "menu_line": "हिंदी के लिए एक दबाएं।",
        "directive": "Reply only in Hindi, in Devanagari script.",
    },
    KeypadEntry.TWO: {
        "name": "English",
        "tts_language": Language.EN,
        "stt_language": "en-IN",
        "menu_line": "For English, press two.",
        "directive": "Reply only in English.",
    },
    KeypadEntry.THREE: {
        "name": "Tamil",
        "tts_language": Language.TA,
        "stt_language": "ta-IN",
        "menu_line": "தமிழுக்கு மூன்று அழுத்தவும்.",
        "directive": "Reply only in Tamil, in Tamil script.",
    },
    # add more digits (FOUR..NINE, ZERO) the same way
}

DEFAULT_DIGIT = KeypadEntry.ONE   # locked language if the caller never presses a valid key
IVR_TIMEOUT_SECONDS = 6.0         # how long to wait for a keypress before re-prompting
IVR_MAX_RETRIES = 2               # re-prompts allowed before falling back to DEFAULT_DIGIT