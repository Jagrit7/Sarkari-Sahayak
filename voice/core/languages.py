"""
languages.py — single source of truth for the languages the bot speaks.

Add or remove a supported language ONLY here. The language router, the TTS
voice switching, the greeting, and the reply-language directives all read
from this one dict — nothing else needs touching to add a language.

Keys are the base language codes Saaras reports ("ta" for "ta-IN"). Every
language needs a bulbul:v4-flash voice that speaks it: v4 voices are
per-language, so check Sarvam's voice list before adding one.
"""

from pipecat.transcriptions.language import Language

LANGUAGES = {
    "hi": {
        "name": "Hindi",
        "tts_language": Language.HI,
        "tts_voice": "aditya_hi_conversational",
        "directive": "The caller is speaking Hindi. Reply only in Hindi, in Devanagari script.",
    },
    "en": {
        "name": "English",
        "tts_language": Language.EN,
        "tts_voice": "dev_en_conversational",
        "directive": "The caller is speaking English. Reply only in English.",
    },
    "bn": {
        "name": "Bengali",
        "tts_language": Language.BN,
        "tts_voice": "arnab_bn_conversation",
        "directive": "The caller is speaking Bengali. Reply only in Bengali, in Bengali script.",
    },
    "gu": {
        "name": "Gujarati",
        "tts_language": Language.GU,
        "tts_voice": "bhavik_gu_conversation",
        "directive": "The caller is speaking Gujarati. Reply only in Gujarati, in Gujarati script.",
    },
    "kn": {
        "name": "Kannada",
        "tts_language": Language.KN,
        "tts_voice": "chetan_kn_conversation",
        "directive": "The caller is speaking Kannada. Reply only in Kannada, in Kannada script.",
    },
    "mr": {
        "name": "Marathi",
        "tts_language": Language.MR,
        "tts_voice": "nilesh_mr_conversation",
        "directive": "The caller is speaking Marathi. Reply only in Marathi, in Devanagari script.",
    },
    "pa": {
        "name": "Punjabi",
        "tts_language": Language.PA,
        "tts_voice": "anand_pa_conversation",
        "directive": "The caller is speaking Punjabi. Reply only in Punjabi, in Gurmukhi script.",
    },
    "ta": {
        "name": "Tamil",
        "tts_language": Language.TA,
        "tts_voice": "vijay_ta_narration",  # v4 has no conversational Tamil voice yet
        "directive": "The caller is speaking Tamil. Reply only in Tamil, in Tamil script.",
    },
    "te": {
        "name": "Telugu",
        "tts_language": Language.TE,
        "tts_voice": "pooja_te_conversation",
        "directive": "The caller is speaking Telugu. Reply only in Telugu, in Telugu script.",
    },
}

DEFAULT_LANGUAGE = "hi"      # used until the caller says something long enough to detect
MIN_WORDS_TO_SWITCH = 3      # "haan" or "ok" is too short to trust the detected language

# spoken once when the call starts, each line in its own language and voice
GREETING = [
    ("hi", "नमस्ते, मैं सरकारी सहायक हूँ। आप अपनी भाषा में बात कर सकते हैं।"),
    ("en", "Hello, I'm Sarkari Sahayak. You can talk to me in your own language."),
]

# added once to the LLM context if Saaras hears a language with no voice above
UNSUPPORTED_DIRECTIVE = (
    "The caller seems to be speaking a language this line can't speak yet. Apologise "
    "briefly in simple English, say you can help in "
    + ", ".join(lang["name"] for lang in LANGUAGES.values())
    + ", and continue in Hindi unless they ask for English."
)
