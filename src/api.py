from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from typing import Optional, List, Dict, Any

from .evermemos import create_evermemos

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Evermemos API", description="Backend server for the Evermemos memory system")

# Global system instance
# Initialize lazily when the first request comes in, or on startup
system = None

class ChatRequest(BaseModel):
    query: str
    user_id: str = "default"

class ChatResponse(BaseModel):
    answer: str
    context: str
    entities: List[str]
    confidence_routed: bool
    reranked: bool
    iterations: int
    episodes_count: int

@app.on_event("startup")
async def startup_event():
    global system
    logger.info("Initializing Evermemos system...")
    try:
        system = create_evermemos("default")
        logger.info("System initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize system: {e}")

@app.get("/health")
async def health_check():
    if system is None:
        raise HTTPException(status_code=503, detail="System not initialized")
    return {"status": "ok", "stats": system.get_stats()}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if system is None:
        raise HTTPException(status_code=503, detail="System not initialized")
        
    try:
        # We need both the direct answer and the deep stats
        # The frontend expects a simple string but taking stats is good for debugging
        logger.info(f"Processing query: {request.query}")
        
        # Get deep stats
        res = system.query(request.query)
        
        # Get actual string answer 
        # (could be optimized to not run LLM twice, but keeping current pattern)
        ans = system.answer(request.query)
        
        return ChatResponse(
            answer=ans,
            context=res.get("context", ""),
            entities=res.get("query_entities", []),
            confidence_routed=res.get("confidence_routed", False),
            reranked=res.get("reranked", False),
            iterations=res.get("iterations", 1),
            episodes_count=len(res.get("episodes", []))
        )
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))
