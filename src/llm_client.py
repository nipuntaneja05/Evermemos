"""
LLM Client for Evermemos.
Uses Ollama (local) for text generation and local Qwen for embeddings.
NO API RATE LIMITS with Ollama!
"""

import json
import re
import time
import requests
from typing import Optional
from sentence_transformers import SentenceTransformer
from .config import Config


class OllamaClient:
    """Client for Ollama (local LLM) and local Qwen embeddings."""
    
    def __init__(self):
        self.base_url = Config.OLLAMA_BASE_URL
        self.model_id = Config.OLLAMA_MODEL
        
        # Test Ollama connection
        self._check_ollama_connection()
        
        # Local Qwen for embeddings (no API calls!)
        print(f"Loading local embedding model: {Config.EMBEDDING_MODEL}...")
        self.embedding_model = SentenceTransformer(Config.EMBEDDING_MODEL)
        print("✓ Embedding model loaded")
    
    def _check_ollama_connection(self):
        """Check if Ollama is running."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                if any(self.model_id in name for name in model_names):
                    print(f"✓ Ollama connected with model: {self.model_id}")
                else:
                    print(f"⚠ Model {self.model_id} not found. Available: {model_names}")
                    print(f"  Run: ollama pull {self.model_id}")
            else:
                raise ConnectionError("Ollama not responding")
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Please ensure Ollama is running (ollama serve)"
            )
    
    def generate(self, prompt: str, system_instruction: str = None, 
                 temperature: float = 0.7, max_tokens: int = 4096) -> str:
        """Generate text using Ollama (local, no rate limits!)."""
        
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
        
        payload = {
            "model": self.model_id,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120  # Local models can be slow
            )
            response.raise_for_status()
            result = response.json()
            return result.get("message", {}).get("content", "")
        except requests.exceptions.Timeout:
            return "Error: Request timed out. Model may be slow on first run."
        except Exception as e:
            return f"Error: {str(e)}"
    
    def generate_json(self, prompt: str, system_instruction: str = None,
                      temperature: float = 0.3) -> dict:
        """Generate JSON output using Ollama."""
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


class GroqClient:
    """Client for Groq API (fallback if Ollama not available)."""
    
    MAX_RETRIES = 3
    BASE_DELAY = 2
    MAX_DELAY = 30
    CALL_DELAY = 0.5
    
    def __init__(self):
        from groq import Groq
        self.client = Groq(api_key=Config.GROQ_API_KEY)
        self.model_id = Config.GROQ_MODEL
        
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
        time.sleep(self.CALL_DELAY)
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
        """Generate embeddings using LOCAL Qwen model."""
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
_client = None


def get_llm_client():
    """Get or create the singleton LLM client based on config."""
    global _client
    if _client is None:
        if Config.LLM_PROVIDER == "ollama":
            print("Using Ollama (local) for LLM - NO RATE LIMITS! 🚀")
            _client = OllamaClient()
        elif Config.LLM_PROVIDER == "groq":
            print("Using Groq API for LLM")
            _client = GroqClient()
        else:
            print(f"Unknown provider {Config.LLM_PROVIDER}, defaulting to Ollama")
            _client = OllamaClient()
    return _client
