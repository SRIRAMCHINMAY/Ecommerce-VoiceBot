from livekit import api
import os
from dotenv import load_dotenv

load_dotenv()

class LiveKitService:
    def __init__(self):
        self.api_key = os.getenv("LIVEKIT_API_KEY", "devkey")
        self.api_secret = os.getenv("LIVEKIT_API_SECRET", "devsecretdevsecretdevsecretdevsecret")
        self.url = os.getenv("LIVEKIT_URL", "ws://localhost:7880")

    def create_token(self, room_name: str, participant_name: str) -> str:
        """Create a LiveKit access token"""
        # Define grants
        grants = api.VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True
        )
        
        token = api.AccessToken(self.api_key, self.api_secret) \
            .with_identity(participant_name) \
            .with_name(participant_name) \
            .with_grants(grants)
        
        return token.to_jwt()

# Singleton instance
livekit_service = LiveKitService()

