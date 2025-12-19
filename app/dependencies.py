from fastapi import Request

from app.config.qdrant_config import QdrantConfig
from app.service.qdrant_service import QdrantService
from app.service.rag_service import RAGService


def get_qdrant_service(request: Request) -> QdrantService:
    """
    Provide a singleton QdrantService instance attached to app state.
    """
    if not hasattr(request.app.state, "qdrant_service"):
        config = QdrantConfig()
        request.app.state.qdrant_service = QdrantService(config=config)
    return request.app.state.qdrant_service


def get_rag_service(request: Request) -> RAGService:
    """
    Provide a singleton RAGService instance that uses QdrantService.
    """
    if not hasattr(request.app.state, "rag_service"):
        qdrant = get_qdrant_service(request)
        request.app.state.rag_service = RAGService(qdrant_service=qdrant)
    return request.app.state.rag_service
