from openai import OpenAI
import io
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load .env into environment
load_dotenv()


class STTConfig(BaseSettings):
    """STT configuration"""

    model: str = "whisper-1"
    language: str = "en"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="STT_",
        extra="ignore",  # ignore unrelated env vars like OPENAI_API_KEY, QDRANT_URL, etc.
    )


class STTService:
    """
    Speech-to-Text service using OpenAI Whisper
    """

    def __init__(self, config: Optional[STTConfig] = None):
        self.config = config or STTConfig()

        # API key is automatically picked from OPENAI_API_KEY
        self.client = OpenAI()

        print(f"✓ STT Service initialized (model: {self.config.model})")

    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None
    ) -> str:
        try:
            audio_file = io.BytesIO(audio_data)
            audio_file.name = "audio.wav"

            transcript = self.client.audio.transcriptions.create(
                model=self.config.model,
                file=audio_file,
                language=language or self.config.language,
            )

            return transcript.text

        except Exception as e:
            print(f"❌ STT Error: {e}")
            return ""

    def transcribe_sync(
        self,
        audio_data: bytes,
        language: Optional[str] = None
    ) -> str:
        try:
            audio_file = io.BytesIO(audio_data)
            audio_file.name = "audio.wav"

            transcript = self.client.audio.transcriptions.create(
                model=self.config.model,
                file=audio_file,
                language=language or self.config.language,
            )

            return transcript.text

        except Exception as e:
            print(f"❌ STT Error: {e}")
            return ""

    def transcribe_file(
        self,
        file_path: str,
        language: Optional[str] = None
    ) -> str:
        try:
            with open(file_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model=self.config.model,
                    file=audio_file,
                    language=language or self.config.language,
                )

            return transcript.text

        except Exception as e:
            print(f"❌ STT Error: {e}")
            return ""
