"""
Vector Store module for Evermemos.
Handles all interactions with Qdrant for vector storage and retrieval.
"""

from typing import Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

from .config import Config
from .models import MemCell, MemScene


class VectorStore:
    """Qdrant-based vector store for MemCells and MemScenes."""
    
    def __init__(self):
        self.client = QdrantClient(
            url=Config.QDRANT_URL,
            api_key=Config.QDRANT_API_KEY,
            prefer_grpc=False
        )
        self._ensure_collections()
    
    def _ensure_collections(self):
        """Ensure required collections exist."""
        collections = [name.name for name in self.client.get_collections().collections]
        
        # Create MemCells collection
        if Config.QDRANT_COLLECTION_MEMCELLS not in collections:
            self.client.create_collection(
                collection_name=Config.QDRANT_COLLECTION_MEMCELLS,
                vectors_config=VectorParams(
                    size=Config.EMBEDDING_DIMENSION,
                    distance=Distance.COSINE
                )
            )
            print(f"Created collection: {Config.QDRANT_COLLECTION_MEMCELLS}")
        
        # Create MemScenes collection
        if Config.QDRANT_COLLECTION_MEMSCENES not in collections:
            self.client.create_collection(
                collection_name=Config.QDRANT_COLLECTION_MEMSCENES,
                vectors_config=VectorParams(
                    size=Config.EMBEDDING_DIMENSION,
                    distance=Distance.COSINE
                )
            )
            print(f"Created collection: {Config.QDRANT_COLLECTION_MEMSCENES}")
    
    # ==================== MemCell Operations ====================
    
    def upsert_memcell(self, memcell: MemCell):
        """Insert or update a MemCell."""
        if not memcell.embedding:
            raise ValueError("MemCell must have an embedding before storing")
        
        point = PointStruct(
            id=memcell.id,
            vector=memcell.embedding,
            payload=memcell.to_dict()
        )
        
        self.client.upsert(
            collection_name=Config.QDRANT_COLLECTION_MEMCELLS,
            points=[point]
        )
    
    def upsert_memcells_batch(self, memcells: list):
        """Insert or update multiple MemCells."""
        points = []
        for memcell in memcells:
            if not memcell.embedding:
                raise ValueError(f"MemCell {memcell.id} must have an embedding")
            points.append(PointStruct(
                id=memcell.id,
                vector=memcell.embedding,
                payload=memcell.to_dict()
            ))
        
        self.client.upsert(
            collection_name=Config.QDRANT_COLLECTION_MEMCELLS,
            points=points
        )
    
    def get_memcell(self, memcell_id: str) -> Optional[MemCell]:
        """Retrieve a MemCell by ID."""
        results = self.client.retrieve(
            collection_name=Config.QDRANT_COLLECTION_MEMCELLS,
            ids=[memcell_id],
            with_payload=True,
            with_vectors=True
        )
        
        if results:
            return MemCell.from_dict(results[0].payload)
        return None
    
    def get_memcells_by_ids(self, memcell_ids: list) -> list:
        """Retrieve multiple MemCells by IDs."""
        if not memcell_ids:
            return []
        
        results = self.client.retrieve(
            collection_name=Config.QDRANT_COLLECTION_MEMCELLS,
            ids=memcell_ids,
            with_payload=True,
            with_vectors=True
        )
        
        return [MemCell.from_dict(r.payload) for r in results]
    
    def search_memcells(self, query_vector: list, limit: int = 10, 
                        memscene_id: str = None) -> list:
        """
        Search MemCells by vector similarity.
        Returns list of (MemCell, score) tuples.
        """
        search_filter = None
        if memscene_id:
            search_filter = Filter(
                must=[FieldCondition(
                    key="memscene_id",
                    match=MatchValue(value=memscene_id)
                )]
            )
        
        results = self.client.search(
            collection_name=Config.QDRANT_COLLECTION_MEMCELLS,
            query_vector=query_vector,
            limit=limit,
            query_filter=search_filter,
            with_payload=True,
            with_vectors=True
        )
        
        return [(MemCell.from_dict(r.payload), r.score) for r in results]
    
    def get_all_memcells(self, limit: int = 1000) -> list:
        """Get all MemCells (for BM25 indexing)."""
        results = self.client.scroll(
            collection_name=Config.QDRANT_COLLECTION_MEMCELLS,
            limit=limit,
            with_payload=True,
            with_vectors=True
        )[0]
        
        return [MemCell.from_dict(r.payload) for r in results]
    
    def delete_memcell(self, memcell_id: str):
        """Delete a MemCell by ID."""
        self.client.delete(
            collection_name=Config.QDRANT_COLLECTION_MEMCELLS,
            points_selector=models.PointIdsList(points=[memcell_id])
        )
    
    # ==================== MemScene Operations ====================
    
    def upsert_memscene(self, memscene: MemScene):
        """Insert or update a MemScene."""
        if not memscene.centroid:
            raise ValueError("MemScene must have a centroid before storing")
        
        point = PointStruct(
            id=memscene.id,
            vector=memscene.centroid,
            payload=memscene.to_dict()
        )
        
        self.client.upsert(
            collection_name=Config.QDRANT_COLLECTION_MEMSCENES,
            points=[point]
        )
    
    def get_memscene(self, memscene_id: str) -> Optional[MemScene]:
        """Retrieve a MemScene by ID."""
        results = self.client.retrieve(
            collection_name=Config.QDRANT_COLLECTION_MEMSCENES,
            ids=[memscene_id],
            with_payload=True,
            with_vectors=True
        )
        
        if results:
            return MemScene.from_dict(results[0].payload)
        return None
    
    def get_all_memscenes(self) -> list:
        """Get all MemScenes."""
        results = self.client.scroll(
            collection_name=Config.QDRANT_COLLECTION_MEMSCENES,
            limit=1000,
            with_payload=True,
            with_vectors=True
        )[0]
        
        return [MemScene.from_dict(r.payload) for r in results]
    
    def search_memscenes(self, query_vector: list, limit: int = 5) -> list:
        """
        Search MemScenes by vector similarity.
        Returns list of (MemScene, score) tuples.
        """
        results = self.client.search(
            collection_name=Config.QDRANT_COLLECTION_MEMSCENES,
            query_vector=query_vector,
            limit=limit,
            with_payload=True,
            with_vectors=True
        )
        
        return [(MemScene.from_dict(r.payload), r.score) for r in results]
    
    def delete_memscene(self, memscene_id: str):
        """Delete a MemScene by ID."""
        self.client.delete(
            collection_name=Config.QDRANT_COLLECTION_MEMSCENES,
            points_selector=models.PointIdsList(points=[memscene_id])
        )
    
    # ==================== Utility Operations ====================
    
    def get_collection_stats(self) -> dict:
        """Get statistics about the collections."""
        memcells_info = self.client.get_collection(Config.QDRANT_COLLECTION_MEMCELLS)
        memscenes_info = self.client.get_collection(Config.QDRANT_COLLECTION_MEMSCENES)
        
        return {
            "memcells": {
                "count": memcells_info.points_count,
                "vectors_count": memcells_info.vectors_count
            },
            "memscenes": {
                "count": memscenes_info.points_count,
                "vectors_count": memscenes_info.vectors_count
            }
        }
    
    def clear_all(self):
        """Clear all data (use with caution!)."""
        self.client.delete_collection(Config.QDRANT_COLLECTION_MEMCELLS)
        self.client.delete_collection(Config.QDRANT_COLLECTION_MEMSCENES)
        self._ensure_collections()


# Singleton instance
_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get or create the singleton vector store."""
    global _store
    if _store is None:
        _store = VectorStore()
    return _store
