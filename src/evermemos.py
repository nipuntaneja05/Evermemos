"""
Evermemos - Main Orchestrator

This module provides the unified interface for the complete memory system,
orchestrating all three phases of the pipeline.
"""

from datetime import datetime
from typing import Optional
import json

from .models import MemCell, MemScene, UserProfile, DialogueTurn
from .phase1_episodic import EpisodicTraceFormation
from .phase2_consolidation import SemanticConsolidation
from .phase3_recollection import ReconstructiveRecollection
from .vector_store import get_vector_store
from .llm_client import get_llm_client


class Evermemos:
    """
    Main orchestrator for the Evermemos memory system.
    
    Provides a unified interface for:
    - Ingesting conversations and extracting MemCells
    - Organizing memories into MemScenes
    - Retrieving relevant context for queries
    - Managing user profiles
    """
    
    def __init__(self, user_id: str = "default"):
        """
        Initialize the Evermemos memory system.
        
        Args:
            user_id: Identifier for the user/context
        """
        self.user_id = user_id
        
        # Initialize phases
        self.phase1 = EpisodicTraceFormation()
        self.phase2 = SemanticConsolidation()
        self.phase3 = ReconstructiveRecollection()
        
        # Components
        self.vector_store = get_vector_store()
        self.llm = get_llm_client()
    
    # ==================== Ingestion ====================
    
    def ingest_transcript(self, transcript: str, 
                         conversation_id: str = "",
                         current_time: datetime = None) -> dict:
        """
        Ingest a conversation transcript into the memory system.
        
        This runs the full pipeline:
        1. Phase I: Extract MemCells from transcript
        2. Phase II: Cluster into MemScenes and update profile
        
        Args:
            transcript: Raw conversation transcript
            conversation_id: Optional ID for the conversation
            current_time: Current timestamp
            
        Returns:
            Dict with ingestion results
        """
        if current_time is None:
            current_time = datetime.now()
        
        # Phase I: Extract MemCells
        memcells = self.phase1.process_transcript(
            transcript, conversation_id, current_time
        )
        
        if not memcells:
            return {
                "success": False,
                "error": "No MemCells extracted from transcript",
                "memcells": [],
                "scenes": [],
                "conflicts": []
            }
        
        # Phase II: Consolidate
        consolidation_results = self.phase2.process_memcells(
            memcells, self.user_id
        )
        
        # Refresh BM25 index
        self.phase3.refresh_index()
        
        return {
            "success": True,
            "memcells_created": len(memcells),
            "memcells": memcells,
            "new_scenes": consolidation_results["new_scenes_created"],
            "updated_scenes": consolidation_results["scenes_updated"],
            "scenes": consolidation_results["scenes"],
            "conflicts": consolidation_results["conflicts_detected"],
            "profile": consolidation_results["profile"]
        }
    
    def ingest_turns(self, turns: list,
                    conversation_id: str = "",
                    current_time: datetime = None) -> dict:
        """
        Ingest a list of DialogueTurn objects.
        
        Args:
            turns: List of DialogueTurn objects
            conversation_id: Optional conversation ID
            current_time: Current timestamp
            
        Returns:
            Dict with ingestion results
        """
        if current_time is None:
            current_time = datetime.now()
        
        # Phase I
        memcells = self.phase1.process_turns(
            turns, conversation_id, current_time
        )
        
        if not memcells:
            return {
                "success": False,
                "error": "No MemCells extracted",
                "memcells": [],
                "scenes": [],
                "conflicts": []
            }
        
        # Phase II
        consolidation_results = self.phase2.process_memcells(
            memcells, self.user_id
        )
        
        # Refresh BM25 index
        self.phase3.refresh_index()
        
        return {
            "success": True,
            "memcells_created": len(memcells),
            "memcells": memcells,
            "new_scenes": consolidation_results["new_scenes_created"],
            "updated_scenes": consolidation_results["scenes_updated"],
            "scenes": consolidation_results["scenes"],
            "conflicts": consolidation_results["conflicts_detected"],
            "profile": consolidation_results["profile"]
        }
    
    # ==================== Retrieval ====================
    
    def query(self, query_text: str, 
              current_time: datetime = None,
              require_sufficient: bool = True) -> dict:
        """
        Query the memory system with full reconstructive recollection.
        
        Args:
            query_text: The query/question
            current_time: Timestamp for temporal filtering
            require_sufficient: Whether to iterate until context is sufficient
            
        Returns:
            Dict with retrieval results
        """
        if current_time is None:
            current_time = datetime.now()
        
        return self.phase3.recall(
            query_text, current_time, require_sufficient
        )
    
    def answer(self, question: str, 
               current_time: datetime = None) -> str:
        """
        Get a direct answer to a question based on memory.
        
        Args:
            question: The user's question
            current_time: Current timestamp
            
        Returns:
            Generated answer string
        """
        if current_time is None:
            current_time = datetime.now()
        
        return self.phase3.answer_query(question, current_time)
    
    def search(self, query: str, top_k: int = 5) -> list:
        """
        Simple search without the full verification loop.
        
        Args:
            query: Search query
            top_k: Number of results
            
        Returns:
            List of RetrievalResult objects
        """
        return self.phase3.recall_simple(query, top_k)
    
    # ==================== Memory Management ====================
    
    def get_all_memcells(self) -> list:
        """Get all MemCells in the system."""
        return self.vector_store.get_all_memcells()
    
    def get_memcell(self, memcell_id: str) -> Optional[MemCell]:
        """Get a specific MemCell by ID."""
        return self.vector_store.get_memcell(memcell_id)
    
    def get_all_memscenes(self) -> list:
        """Get all MemScenes in the system."""
        return self.phase2.get_all_scenes()
    
    def get_memscene(self, scene_id: str) -> Optional[MemScene]:
        """Get a specific MemScene by ID."""
        return self.phase2.get_scene(scene_id)
    
    def get_scene_contents(self, scene_id: str) -> dict:
        """Get a MemScene with its constituent MemCells."""
        scene = self.phase2.get_scene(scene_id)
        if not scene:
            return {"error": "Scene not found"}
        
        memcells = self.phase2.get_scene_memcells(scene_id)
        return {
            "scene": scene,
            "memcells": memcells,
            "memcell_count": len(memcells)
        }
    
    # ==================== Profile Management ====================
    
    def get_profile(self) -> UserProfile:
        """Get the current user profile."""
        return self.phase2.get_profile(self.user_id)
    
    def get_profile_summary(self) -> str:
        """Get a human-readable profile summary."""
        return self.phase2.get_profile_summary(self.user_id)
    
    # ==================== Statistics ====================
    
    def get_stats(self) -> dict:
        """Get system statistics."""
        vector_stats = self.vector_store.get_collection_stats()
        
        return {
            "user_id": self.user_id,
            "memcells_count": vector_stats["memcells"]["count"],
            "memscenes_count": vector_stats["memscenes"]["count"],
            "vector_dimensions": vector_stats["memcells"].get("vectors_count", "N/A")
        }
    
    # ==================== Maintenance ====================
    
    def refresh_indices(self):
        """Refresh all indices (useful after bulk operations)."""
        self.phase3.refresh_index()
    
    def clear_memory(self, confirm: bool = False):
        """
        Clear all memory data. USE WITH CAUTION!
        
        Args:
            confirm: Must be True to proceed
        """
        if not confirm:
            raise ValueError("Must pass confirm=True to clear memory")
        
        self.vector_store.clear_all()
        print("All memory data has been cleared.")
    
    # ==================== Export/Import ====================
    
    def export_memory(self) -> dict:
        """Export all memory data as a dictionary."""
        memcells = self.get_all_memcells()
        memscenes = self.get_all_memscenes()
        profile = self.get_profile()
        
        return {
            "user_id": self.user_id,
            "export_time": datetime.now().isoformat(),
            "memcells": [mc.to_dict() for mc in memcells],
            "memscenes": [ms.to_dict() for ms in memscenes],
            "profile": profile.to_dict() if profile else None,
            "stats": self.get_stats()
        }
    
    def export_memory_json(self, filepath: str):
        """Export memory to a JSON file."""
        data = self.export_memory()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Memory exported to {filepath}")


def create_evermemos(user_id: str = "default") -> Evermemos:
    """Factory function to create an Evermemos instance."""
    return Evermemos(user_id)
