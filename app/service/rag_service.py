import pandas as pd
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
from app.service.qdrant_service import QdrantService

class RAGService:
    """
    RAG service for CSV ingestion and vector search
    Uses dependency injection for QdrantService
    """
    
    def __init__(self, qdrant_service: QdrantService, 
                 embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize RAG service
        
        Args:
            qdrant_service: QdrantService instance (dependency injection)
            embedding_model: Name of sentence transformer model
        """
        self.qdrant_service = qdrant_service
        self.embedding_model = SentenceTransformer(embedding_model)
    
    def ingest_csv(self, csv_path: str, text_column: str, 
                   metadata_columns: Optional[List[str]] = None) -> int:
        """
        Ingest CSV file into vector database
        
        Args:
            csv_path: Path to CSV file
            text_column: Column name containing text to embed
            metadata_columns: Optional list of columns to include as metadata
        
        Returns:
            Number of documents ingested
        """
        # Read CSV
        df = pd.read_csv(csv_path)
        
        # Validate text column exists
        if text_column not in df.columns:
            raise ValueError(f"Column '{text_column}' not found in CSV")
        
        # Extract texts and convert to embeddings
        texts = df[text_column].fillna("").astype(str).tolist()
        embeddings = self.embedding_model.encode(texts)
        
        # Prepare payloads (metadata)
        payloads = []
        for idx, row in df.iterrows():
            payload = {
                "text": row[text_column],
                "row_index": int(idx)
            }
            
            # Add specified metadata columns
            if metadata_columns:
                for col in metadata_columns:
                    if col in df.columns:
                        payload[col] = row[col]
            
            payloads.append(payload)
        
        # Store in Qdrant
        self.qdrant_service.add(
            vectors=embeddings.tolist(),
            payloads=payloads
        )
        
        return len(texts)