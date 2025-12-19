
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class QdrantConfig(BaseSettings):
    """Qdrant configuration"""

    url: str = "http://localhost:6333"  # Local Qdrant
    api_key: Optional[str] = None  # For cloud
    collection_name: str = "ecommerce_knowledge"
    vector_size: int = 384  # all-MiniLM-L6-v2 dimension

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="QDRANT_",
        extra="ignore",  # ignore unrelated env vars like OPENAI_API_KEY
    )
