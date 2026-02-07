"""
LLM Client for Evermemos.
Uses Groq API for text generation and local Qwen for embeddings.
"""

import json
import re
import time
from typing import Optional
from groq import Groq
from sentence_transformers import SentenceTransformer
from .config import Config


class GroqClient:
    """Client for Groq API (text gen) and local Qwen embeddings."""
    
    # Groq free tier: 30 req/min, 14,400 req/day
    MAX_RETRIES = 3
    BASE_DELAY = 2
    MAX_DELAY = 30
    CALL_DELAY = 0.5  # Much faster than Gemini!
    
    def __init__(self):
        # Groq for text generation
        self.client = Groq(api_key=Config.GROQ_API_KEY)
        self.model_id = Config.GROQ_MODEL
        
        # Local Qwen for embeddings (no API calls!)
        print(f"Loading local embedding model: {Config.EMBEDDING_MODEL}...")
        self.embedding_model = SentenceTransformer(Config.EMBEDDING_MODEL)
        print("✓ Embedding model loaded")
    
    def _retry_with_backoff(self, func, *args, **kwargs):
        """Execute a function with exponential backoff retry logic."""
        last_exception = None
        
        for attempt in range(self.MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_str = str(e).lower()
                if "rate" in error_str or "429" in error_str or "quota" in error_str:
                    last_exception = e
                    if attempt < self.MAX_RETRIES - 1:
                        delay = min(self.BASE_DELAY * (2 ** attempt), self.MAX_DELAY)
                        print(f"Rate limit hit, waiting {delay}s before retry {attempt + 2}/{self.MAX_RETRIES}...")
                        time.sleep(delay)
                else:
                    raise e
        
        raise last_exception
    
    def generate(self, prompt: str, system_instruction: str = None, 
                 temperature: float = 0.7, max_tokens: int = 4096) -> str:
        """Generate text using Groq."""
        
        def _do_generate():
            messages = []
            
            if system_instruction:
                messages.append({
                    "role": "system",
                    "content": system_instruction
                })
            
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
        
        result = self._retry_with_backoff(_do_generate)
        time.sleep(self.CALL_DELAY)  # Minimal delay for Groq
        return result
    
    def generate_json(self, prompt: str, system_instruction: str = None,
                      temperature: float = 0.3) -> dict:
        """Generate JSON output using Groq."""
        json_prompt = f"""{prompt}

IMPORTANT: Respond ONLY with valid JSON. No markdown, no code blocks, no explanations."""
        
        response = self.generate(
            json_prompt,
            system_instruction=system_instruction,
            temperature=temperature
        )
        
        # Clean the response
        cleaned = response.strip()
        
        if cleaned.startswith("```"):
            cleaned = re.sub(r'^```(?:json)?\s*\n?', '', cleaned)
            cleaned = re.sub(r'\n?```\s*$', '', cleaned)
        
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            json_match = re.search(r'\{[\s\S]*\}', cleaned)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            
            return {"error": str(e), "raw_response": response}
    
    def embed(self, text: str) -> list:
        """Generate embeddings using LOCAL Qwen model (no API call!)."""
        embedding = self.embedding_model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_query(self, query: str) -> list:
        """Generate embeddings for a query using LOCAL model."""
        embedding = self.embedding_model.encode(query, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_batch(self, texts: list) -> list:
        """Generate embeddings for multiple texts using LOCAL model."""
        embeddings = self.embedding_model.encode(texts, convert_to_numpy=True)
        return [emb.tolist() for emb in embeddings]


# Singleton instance
_client: Optional[GroqClient] = None


def get_llm_client() -> GroqClient:
    """Get or create the singleton LLM client."""
    global _client
    if _client is None:
        _client = GroqClient()
    return _client
