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
    
    # API Keys (optional now - Ollama doesn't need keys)
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")
    
    # Qdrant Configuration
    QDRANT_URL: str = os.getenv("QDRANT_URL", "https://8dffce31-7c8a-4622-8161-63ced058f692.europe-west3-0.gcp.cloud.qdrant.io")
    QDRANT_COLLECTION_MEMCELLS: str = "evermemos_memcells"
    QDRANT_COLLECTION_MEMSCENES: str = "evermemos_memscenes"
    
    # Embedding Configuration (LOCAL - no API calls)
    EMBEDDING_MODEL: str = "Alibaba-NLP/gte-Qwen2-1.5B-instruct"  # Local Qwen model
    EMBEDDING_DIMENSION: int = 1536
    
    # LLM Configuration
    LLM_PROVIDER: str = "groq"  # "ollama" (local), "groq", or "gemini"
    
    # Ollama Configuration (LOCAL - no rate limits!)
    OLLAMA_MODEL: str = "qwen2.5:7b"  # Local model you downloaded
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    
    # Groq Configuration (fallback)
    GROQ_MODEL: str = "llama-3.3-70b-versatile"  # High quality model
    GEMINI_MODEL: str = "models/gemini-2.5-flash"
    
    # Optimization: Skip boundary detection for short conversations
    # Set to 0 to always use LLM (local Ollama has no rate limits)
    SKIP_BOUNDARY_DETECTION_THRESHOLD: int = 0  # Always use LLM for accuracy
    
    # Semantic Boundary Detection
    SLIDING_WINDOW_SIZE: int = 3  # Reduced from 5 for finer-grained boundary detection
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
    
    # ==================== BetterMemory Pipeline ====================
    
    # Confidence Router (Phase 3 - SwiftMem)
    # If top-1 retrieval score > threshold, skip sufficiency check (fast path)
    CONFIDENCE_ROUTER_THRESHOLD: float = 0.7
    
    # Cross-Encoder Reranker
    CROSS_ENCODER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    
    # Priority Filter (Phase 1 - SwiftMem)
    # Discard chitchat turns before LLM processing
    PRIORITY_FILTER_ENABLED: bool = True
    CHITCHAT_MAX_WORDS: int = 5  # Turns with <= this many words are candidates for filtering
    CHITCHAT_PATTERNS: list = [
        "ok", "okay", "sure", "thanks", "thank you", "bye", "goodbye",
        "hi", "hello", "hey", "yeah", "yes", "no", "nope", "yep",
        "haha", "lol", "hehe", "hmm", "hm", "ah", "oh", "wow",
        "cool", "nice", "great", "alright", "fine", "sounds good",
        "got it", "i see", "right", "exactly", "agreed",
    ]
    
    # Entity-Driven Pre-filtering (Phase 3 - Grounding)
    ENTITY_FILTER_ENABLED: bool = True
    ENTITY_FILTER_MIN_RESULTS: int = 3  # Fallback to unfiltered if < this many results
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that all required configuration is present."""
        # Only check Qdrant - Ollama doesn't need API keys
        if not cls.QDRANT_API_KEY:
            raise ValueError("QDRANT_API_KEY not found in environment")
        return True


# Validate on import
Config.validate()
