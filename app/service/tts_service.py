from openai import OpenAI
from typing import Literal, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

VoiceType = Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

class TTSConfig(BaseSettings):
    """TTS configuration"""
    openai_api_key: str
    model: str = "tts-1"  # or "tts-1-hd" for higher quality
    voice: VoiceType = "alloy"
    speed: float = 1.0
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="TTS_",
        extra="ignore",  # ignore unrelated env vars
    )

class TTSService:
    """
    Text-to-Speech service using OpenAI TTS
    """
    
    def __init__(self, config: Optional[TTSConfig] = None):
        """
        Initialize TTS service
        
        Args:
            config: TTSConfig instance (uses env vars if not provided)
        """
        self.config = config or TTSConfig()
        self.client = OpenAI(api_key=self.config.openai_api_key)
        print(f"✓ TTS Service initialized (model: {self.config.model}, voice: {self.config.voice})")
    
    async def synthesize(self, text: str, 
                        voice: Optional[VoiceType] = None,
                        speed: Optional[float] = None) -> bytes:
        """
        Convert text to speech
        
        Args:
            text: Text to convert
            voice: Voice to use (overrides config)
            speed: Speech speed 0.25-4.0 (overrides config)
        
        Returns:
            Audio data as bytes (MP3 format)
        """
        try:
            response = self.client.audio.speech.create(
                model=self.config.model,
                voice=voice or self.config.voice,
                input=text,
                speed=speed or self.config.speed
            )
            
            return response.content
        
        except Exception as e:
            print(f"❌ TTS Error: {e}")
            return b""
    
    def synthesize_sync(self, text: str, 
                       voice: Optional[VoiceType] = None,
                       speed: Optional[float] = None) -> bytes:
        """Synchronous version of synthesize"""
        try:
            response = self.client.audio.speech.create(
                model=self.config.model,
                voice=voice or self.config.voice,
                input=text,
                speed=speed or self.config.speed
            )
            
            return response.content
        
        except Exception as e:
            print(f"❌ TTS Error: {e}")
            return b""
    
    def synthesize_to_file(self, text: str, output_path: str,
                          voice: Optional[VoiceType] = None,
                          speed: Optional[float] = None) -> bool:
        """
        Synthesize speech and save to file
        
        Args:
            text: Text to convert
            output_path: Path to save audio file
            voice: Voice to use
            speed: Speech speed
        
        Returns:
            True if successful
        """
        try:
            response = self.client.audio.speech.create(
                model=self.config.model,
                voice=voice or self.config.voice,
                input=text,
                speed=speed or self.config.speed
            )
            
            with open(output_path, "wb") as f:
                f.write(response.content)
            
            print(f"✓ Saved audio to: {output_path}")
            return True
        
        except Exception as e:
            print(f"❌ TTS Error: {e}")
            return False
