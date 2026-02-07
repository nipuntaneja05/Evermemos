"""
Configuration module for Evermemos.
Handles environment variables and system settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


class Config:
    """Central configuration for the Evermemos system."""
    
    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")
    
    # Qdrant Configuration
    QDRANT_URL: str = os.getenv("QDRANT_URL", "https://8dffce31-7c8a-4622-8161-63ced058f692.europe-west3-0.gcp.cloud.qdrant.io")
    QDRANT_COLLECTION_MEMCELLS: str = "evermemos_memcells"
    QDRANT_COLLECTION_MEMSCENES: str = "evermemos_memscenes"
    
    # Embedding Configuration (LOCAL - no API calls)
    EMBEDDING_MODEL: str = "Alibaba-NLP/gte-Qwen2-1.5B-instruct"  # Local Qwen model
    EMBEDDING_DIMENSION: int = 1536
    
    # LLM Configuration (API)
    GEMINI_MODEL: str = "models/gemini-2.5-flash"  # Latest Gemini model
    
    # Semantic Boundary Detection
    SLIDING_WINDOW_SIZE: int = 5  # Number of turns to analyze
    TOPIC_SHIFT_THRESHOLD: float = 0.7  # Confidence threshold for topic shift
    
    # MemScene Clustering
    MEMSCENE_SIMILARITY_THRESHOLD: float = 0.70  # τ threshold for clustering
    
    # Retrieval Configuration
    TOP_K_RETRIEVAL: int = 10  # Number of results for initial retrieval
    TOP_K_MEMSCENES: int = 5  # Number of MemScenes to select
    TOP_K_EPISODES: int = 8  # Compact set of episodes for reasoning
    RRF_K: int = 60  # RRF constant
    
    # Verification Loop
    MAX_QUERY_REWRITES: int = 3  # Maximum rewrite iterations
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that all required configuration is present."""
        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in environment")
        if not cls.QDRANT_API_KEY:
            raise ValueError("QDRANT_API_KEY not found in environment")
        return True


# Validate on import
Config.validate()
