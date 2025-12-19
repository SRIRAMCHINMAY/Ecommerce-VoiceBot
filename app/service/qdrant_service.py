from app.config.qdrant_config import QdrantConfig
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
)
from typing import List, Dict, Any, Optional
import uuid

class QdrantService:
    """
    Qdrant vector database service
    Single user - no datapoint management needed
    """
    
    def __init__(self, config: QdrantConfig):
        """
        Initialize Qdrant client
        
        Args:
            config: QdrantConfig instance
        """
        self.config = config
        self.client = QdrantClient(url=config.url)
        self.collection_name = config.collection_name
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Create collection if it doesn't exist"""
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if self.collection_name not in collection_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.config.vector_size,
                    distance=Distance.COSINE
                )
            )

    def clear_collection(self):
        """Delete and recreate the collection to clear all points"""
        self.client.delete_collection(collection_name=self.collection_name)
        self._ensure_collection()
    
    def add(self, vectors: List[List[float]], payloads: List[Dict[str, Any]]) -> List[str]:
        """
        Add vectors with metadata to collection
        
        Args:
            vectors: List of embedding vectors
            payloads: List of metadata dictionaries
        
        Returns:
            List of generated point IDs
        """
        # Generate IDs
        ids = [str(uuid.uuid4()) for _ in vectors]
        
        # Create points
        points = [
            PointStruct(id=point_id, vector=vector, payload=payload)
            for point_id, vector, payload in zip(ids, vectors, payloads)
        ]
        
        # Upsert to Qdrant
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
        return ids
    
    def update(self, point_id: str, vector: Optional[List[float]] = None, 
               payload: Optional[Dict[str, Any]] = None):
        """
        Update a point's vector or payload
        
        Args:
            point_id: ID of the point to update
            vector: New vector (optional)
            payload: New payload (optional)
        """
        if vector and payload:
            # Update both
            point = PointStruct(id=point_id, vector=vector, payload=payload)
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
        elif payload:
            # Update only payload
            self.client.set_payload(
                collection_name=self.collection_name,
                payload=payload,
                points=[point_id]
            )
    
    def delete(self, point_ids: List[str]):
        """
        Delete points by their IDs
        
        Args:
            point_ids: List of point IDs to delete
        """
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=point_ids
        )

    def count(self) -> int:
        """
        Return number of points in the collection.
        """
        res = self.client.count(
            collection_name=self.collection_name,
            exact=True,
        )
        return res.count

    def search(self, query_vector: List[float], limit: int = 5):
        """
        Search for nearest vectors using the newer Qdrant `query_points` API.
        """
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=limit,
            with_payload=True,
        )
        return response.points