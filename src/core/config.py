from dotenv import load_dotenv
import os

load_dotenv()

#loading env vars/ api keys
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")

#guard check
if not LIVEKIT_URL or not LIVEKIT_API_SECRET or not LIVEKIT_API_KEY or not GROQ_API_KEY:
    raise ValueError("Invalid or missing environment variables")

#creating settings class
class Settings:
    def __init__(self):
        self.LIVEKIT_URL = LIVEKIT_URL
        self.LIVEKIT_API_SECRET = LIVEKIT_API_SECRET
        self.LIVEKIT_API_KEY = LIVEKIT_API_KEY
        self.GROQ_API_KEY = GROQ_API_KEY
        self.SARVAM_API_KEY = SARVAM_API_KEY

settings = Settings()
