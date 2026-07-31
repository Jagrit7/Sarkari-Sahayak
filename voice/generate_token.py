import os
from dotenv import load_dotenv
from livekit import api

# Load your .env variables
load_dotenv()


def generate_user_token(room_name: str, identity: str):
    # Ensure keys exist
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")

    if not api_key or not api_secret:
        raise ValueError("Missing LIVEKIT_API_KEY or LIVEKIT_API_SECRET in environment variables.")

    # Create the access token for a human participant
    token = (
        api.AccessToken(api_key, api_secret)
        .with_identity(identity)
        .with_name(f"{identity} Tester")
        .with_grants(api.VideoGrants(room_join=True, room=room_name))
        .to_jwt()
    )
    return token


if __name__ == "__main__":
    ROOM = "support-room"
    USER = "Human-User"

    try:
        jwt_token = generate_user_token(ROOM, USER)
        print("\n" + "=" * 50)
        print(f"🔑 TOKEN GENERATED FOR ROOM: {ROOM}")
        print("=" * 50)
        print(jwt_token)
        print("=" * 50 + "\n")
    except Exception as e:
        print(f"❌ Error generating token: {e}")