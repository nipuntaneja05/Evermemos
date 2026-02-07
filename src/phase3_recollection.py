"""
Phase III: Reconstructive Recollection

This module implements active reconstruction-based retrieval guided by
the principle of necessity and sufficiency.
Implements:
- Step 1: MemScene Selection (Hybrid Retrieval with RRF)
- Step 2: Episode and Foresight Filtering
- Step 3: Agentic Verification and Query Rewriting
"""

from datetime import datetime
from typing import Optional
import numpy as np
from rank_bm25 import BM25Okapi

from .models import MemCell, MemScene, Foresight, RetrievalResult
from .llm_client import get_llm_client
from .vector_store import get_vector_store
from .config import Config


class HybridRetriever:
    """
    Step 1: MemScene Selection (Hybrid Retrieval)
    
    Fuses dense and sparse retrieval via Reciprocal Rank Fusion (RRF).
    - Dense: Vector similarity using embeddings
    - Sparse: BM25 over Atomic Facts
    """
    
    def __init__(self):
        self.llm = get_llm_client()
        self.vector_store = get_vector_store()
        self.rrf_k = Config.RRF_K
        self.top_k = Config.TOP_K_RETRIEVAL
        self.top_k_scenes = Config.TOP_K_MEMSCENES
        self._bm25_index = None
        self._bm25_memcells = None
    
    def _build_bm25_index(self, memcells: list = None):
        """Build or rebuild the BM25 index."""
        if memcells is None:
            memcells = self.vector_store.get_all_memcells()
        
        if not memcells:
            self._bm25_index = None
            self._bm25_memcells = []
            return
        
        # Tokenize atomic facts for each memcell
        tokenized_corpus = []
        for mc in memcells:
            # Combine atomic facts into searchable text
            facts_text = " ".join(mc.atomic_facts).lower()
            tokens = facts_text.split()
            tokenized_corpus.append(tokens)
        
        self._bm25_memcells = memcells
        self._bm25_index = BM25Okapi(tokenized_corpus)
    
    def retrieve(self, query: str, top_k: int = None) -> list:
        """
        Perform hybrid retrieval combining dense and sparse methods.
        
        Args:
            query: The search query
            top_k: Number of results to return
            
        Returns:
            List of RetrievalResult objects sorted by RRF score
        """
        if top_k is None:
            top_k = self.top_k
        
        # Get query embedding for dense retrieval
        query_embedding = self.llm.embed_query(query)
        
        # Dense retrieval
        dense_results = self.vector_store.search_memcells(query_embedding, limit=top_k * 2)
        
        # Sparse retrieval (BM25)
        sparse_results = self._bm25_search(query, top_k * 2)
        
        # Reciprocal Rank Fusion
        fused_results = self._reciprocal_rank_fusion(dense_results, sparse_results)
        
        # Sort by RRF score and take top k
        fused_results.sort(key=lambda x: x.rrf_score, reverse=True)
        return fused_results[:top_k]
    
    def _bm25_search(self, query: str, top_k: int) -> list:
        """Perform BM25 sparse search."""
        # Ensure index is built
        if self._bm25_index is None:
            self._build_bm25_index()
        
        if not self._bm25_memcells:
            return []
        
        # Tokenize query
        query_tokens = query.lower().split()
        
        # Get scores
        scores = self._bm25_index.get_scores(query_tokens)
        
        # Get top k indices
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # Only include matches
                results.append((self._bm25_memcells[idx], float(scores[idx])))
        
        return results
    
    def _reciprocal_rank_fusion(self, dense_results: list, sparse_results: list) -> list:
        """
        Fuse results using Reciprocal Rank Fusion.
        
        RRF Score = Σ 1 / (k + rank_i)
        """
        # Build score maps
        rrf_scores = {}
        dense_scores = {}
        sparse_scores = {}
        memcells = {}
        
        # Process dense results
        for rank, (memcell, score) in enumerate(dense_results, start=1):
            memcell_id = memcell.id
            memcells[memcell_id] = memcell
            dense_scores[memcell_id] = score
            rrf_scores[memcell_id] = rrf_scores.get(memcell_id, 0) + (1.0 / (self.rrf_k + rank))
        
        # Process sparse results
        for rank, (memcell, score) in enumerate(sparse_results, start=1):
            memcell_id = memcell.id
            memcells[memcell_id] = memcell
            sparse_scores[memcell_id] = score
            rrf_scores[memcell_id] = rrf_scores.get(memcell_id, 0) + (1.0 / (self.rrf_k + rank))
        
        # Build result objects
        results = []
        for memcell_id, rrf_score in rrf_scores.items():
            result = RetrievalResult(
                memcell=memcells[memcell_id],
                dense_score=dense_scores.get(memcell_id, 0.0),
                sparse_score=sparse_scores.get(memcell_id, 0.0),
                rrf_score=rrf_score
            )
            results.append(result)
        
        return results
    
    def select_memscenes(self, retrieval_results: list, top_k: int = None) -> list:
        """
        Select top MemScenes based on constituent MemCells.
        
        Args:
            retrieval_results: List of RetrievalResult from hybrid retrieval
            top_k: Number of scenes to select
            
        Returns:
            List of (MemScene, aggregated_score) tuples
        """
        if top_k is None:
            top_k = self.top_k_scenes
        
        # Aggregate scores by MemScene
        scene_scores = {}
        scene_objects = {}
        
        for result in retrieval_results:
            scene_id = result.memcell.memscene_id
            if scene_id:
                current_score = scene_scores.get(scene_id, 0.0)
                scene_scores[scene_id] = max(current_score, result.rrf_score)
                
                # Fetch scene if not cached
                if scene_id not in scene_objects:
                    scene = self.vector_store.get_memscene(scene_id)
                    if scene:
                        scene_objects[scene_id] = scene
        
        # Sort and return top k
        sorted_scenes = sorted(scene_scores.items(), key=lambda x: x[1], reverse=True)
        
        results = []
        for scene_id, score in sorted_scenes[:top_k]:
            if scene_id in scene_objects:
                results.append((scene_objects[scene_id], score))
        
        return results
    
    def refresh_bm25_index(self):
        """Force refresh of the BM25 index."""
        self._build_bm25_index()


class TemporalFilter:
    """
    Step 2: Episode and Foresight Filtering
    
    Filters retrieval results based on temporal validity.
    Only retains "time-valid" Foresight where current time is within validity window.
    """
    
    def filter_foresights(self, memcell: MemCell, current_time: datetime) -> list:
        """
        Filter foresights to only include temporally valid ones.
        
        Args:
            memcell: The MemCell containing foresights
            current_time: The timestamp to check validity against
            
        Returns:
            List of valid Foresight objects
        """
        valid_foresights = []
        
        for foresight in memcell.foresights:
            if isinstance(foresight, Foresight):
                if foresight.is_valid_at(current_time):
                    valid_foresights.append(foresight)
            elif isinstance(foresight, dict):
                # Handle dict representation
                f = Foresight.from_dict(foresight)
                if f.is_valid_at(current_time):
                    valid_foresights.append(f)
        
        return valid_foresights
    
    def filter_results(self, results: list, current_time: datetime) -> list:
        """
        Filter a list of RetrievalResults to include only valid foresights.
        
        Args:
            results: List of RetrievalResult objects
            current_time: The timestamp to check validity against
            
        Returns:
            List of RetrievalResult with temporal_valid_foresights populated
        """
        filtered = []
        
        for result in results:
            valid_foresights = self.filter_foresights(result.memcell, current_time)
            result.temporal_valid_foresights = valid_foresights
            filtered.append(result)
        
        return filtered


class SufficiencyVerifier:
    """
    Step 3: Agentic Verification and Query Rewriting
    
    An LLM-based sufficiency check that:
    1. Evaluates if retrieved context is enough to answer the query
    2. If insufficient, triggers query rewriting for follow-up queries
    """
    
    VERIFIER_PROMPT = """You are a context sufficiency evaluator. Your job is to determine
if the provided context contains enough information to adequately answer the query.

Consider:
1. Is all necessary information present?
2. Are there gaps that would prevent a complete answer?
3. Is the information clear and unambiguous?"""

    REWRITER_PROMPT = """You are a query rewriting specialist. When initial retrieval is insufficient,
you generate targeted follow-up queries to fill information gaps.

Strategies:
1. Pivot Entity Association: Focus on related entities mentioned
2. Temporal Calculation: Query about time-related information
3. Aspect Decomposition: Break the query into sub-questions
4. Contextual Expansion: Broaden scope to capture missing context"""

    def __init__(self):
        self.llm = get_llm_client()
        self.max_rewrites = Config.MAX_QUERY_REWRITES
    
    def verify_sufficiency(self, query: str, context: str) -> dict:
        """
        Verify if the context is sufficient to answer the query.
        
        Args:
            query: The original query
            context: The retrieved context
            
        Returns:
            Dict with 'is_sufficient', 'confidence', 'reasoning', 'missing_info'
        """
        prompt = f"""Evaluate if this context is sufficient to answer the query.

QUERY: {query}

CONTEXT:
{context}

Respond with JSON:
{{
    "is_sufficient": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "explanation of your assessment",
    "missing_info": ["list", "of", "missing", "information"] or []
}}"""
        
        result = self.llm.generate_json(prompt, self.VERIFIER_PROMPT)
        
        if "error" in result:
            return {
                "is_sufficient": True,  # Default to sufficient on error
                "confidence": 0.5,
                "reasoning": "Verification error - defaulting to sufficient",
                "missing_info": []
            }
        
        return result
    
    def rewrite_query(self, original_query: str, missing_info: list, 
                      previous_queries: list = None) -> list:
        """
        Generate rewritten queries to supplement retrieval.
        
        Args:
            original_query: The original query
            missing_info: List of missing information items
            previous_queries: Queries already tried (to avoid repetition)
            
        Returns:
            List of 2-3 rewritten query strings
        """
        if previous_queries is None:
            previous_queries = []
        
        previous_str = "\n".join(f"- {q}" for q in previous_queries) if previous_queries else "None"
        missing_str = "\n".join(f"- {m}" for m in missing_info) if missing_info else "General information gaps"
        
        prompt = f"""Generate 2-3 targeted follow-up queries to fill the information gaps.

ORIGINAL QUERY: {original_query}

MISSING INFORMATION:
{missing_str}

PREVIOUS QUERIES (avoid similar):
{previous_str}

Use strategies like:
- Pivot Entity Association: Focus on related entities
- Temporal Calculation: Query about time-related info
- Aspect Decomposition: Break into sub-questions

Respond with JSON:
{{
    "queries": ["query 1", "query 2", "query 3"],
    "strategies_used": ["strategy for query 1", "strategy for query 2", "strategy for query 3"]
}}"""
        
        result = self.llm.generate_json(prompt, self.REWRITER_PROMPT)
        
        if "error" in result:
            # Fallback queries
            return [
                f"{original_query} more details",
                f"background information for {original_query}"
            ]
        
        return result.get("queries", [])[:3]


class ReconstructiveRecollection:
    """
    Main class for Phase III: Reconstructive Recollection.
    Orchestrates the full retrieval pipeline with agentic verification.
    """
    
    def __init__(self):
        self.hybrid_retriever = HybridRetriever()
        self.temporal_filter = TemporalFilter()
        self.sufficiency_verifier = SufficiencyVerifier()
        self.llm = get_llm_client()
    
    def recall(self, query: str, current_time: datetime = None,
               require_sufficient: bool = True,
               max_episodes: int = None) -> dict:
        """
        Perform full reconstructive recollection for a query.
        
        Args:
            query: The search/retrieval query
            current_time: Timestamp for temporal filtering
            require_sufficient: Whether to iterate until sufficient
            max_episodes: Maximum number of episodes to return
            
        Returns:
            Dict with retrieval results and metadata
        """
        if current_time is None:
            current_time = datetime.now()
        
        if max_episodes is None:
            max_episodes = Config.TOP_K_EPISODES
        
        # Track all queries and results
        all_queries = [query]
        all_results = []
        iteration = 0
        
        while iteration <= self.sufficiency_verifier.max_rewrites:
            # Step 1: Hybrid Retrieval
            current_query = all_queries[-1]
            retrieval_results = self.hybrid_retriever.retrieve(current_query)
            
            # Step 1b: Select MemScenes
            top_scenes = self.hybrid_retriever.select_memscenes(retrieval_results)
            
            # Step 2: Temporal Filtering
            filtered_results = self.temporal_filter.filter_results(
                retrieval_results, current_time
            )
            
            # Merge with existing results (deduplicate by memcell ID)
            seen_ids = {r.memcell.id for r in all_results}
            for result in filtered_results:
                if result.memcell.id not in seen_ids:
                    all_results.append(result)
                    seen_ids.add(result.memcell.id)
            
            # Re-rank all results
            all_results.sort(key=lambda x: x.rrf_score, reverse=True)
            
            # Build context from top results
            top_results = all_results[:max_episodes]
            context = self._build_context(top_results)
            
            if not require_sufficient:
                break
            
            # Step 3: Verify sufficiency
            verification = self.sufficiency_verifier.verify_sufficiency(query, context)
            
            if verification.get("is_sufficient", True):
                break
            
            # Need more info - rewrite query
            missing = verification.get("missing_info", [])
            new_queries = self.sufficiency_verifier.rewrite_query(
                query, missing, all_queries
            )
            
            if not new_queries:
                break
            
            all_queries.extend(new_queries)
            iteration += 1
        
        # Compile final results
        final_results = all_results[:max_episodes]
        
        return {
            "query": query,
            "current_time": current_time.isoformat(),
            "iterations": iteration + 1,
            "queries_used": all_queries,
            "results": final_results,
            "episodes": [r.memcell.episode for r in final_results],
            "valid_foresights": self._collect_foresights(final_results),
            "atomic_facts": self._collect_facts(final_results),
            "context": self._build_context(final_results),
            "memscenes": [s for s, _ in top_scenes] if 'top_scenes' in dir() else []
        }
    
    def recall_simple(self, query: str, top_k: int = 5) -> list:
        """
        Simple retrieval without verification loop.
        
        Args:
            query: The search query
            top_k: Number of results
            
        Returns:
            List of RetrievalResult objects
        """
        results = self.hybrid_retriever.retrieve(query, top_k)
        return self.temporal_filter.filter_results(results, datetime.now())
    
    def _build_context(self, results: list) -> str:
        """Build a context string from retrieval results."""
        sections = []
        
        for i, result in enumerate(results, start=1):
            mc = result.memcell
            
            section = f"[Episode {i}]\n{mc.episode}"
            
            if result.temporal_valid_foresights:
                foresight_text = "\n".join(
                    f"  - {f.content}" for f in result.temporal_valid_foresights
                )
                section += f"\n\nActive Foresights:\n{foresight_text}"
            
            if mc.atomic_facts:
                facts_text = "\n".join(f"  - {f}" for f in mc.atomic_facts[:5])
                section += f"\n\nKey Facts:\n{facts_text}"
            
            sections.append(section)
        
        return "\n\n---\n\n".join(sections)
    
    def _collect_foresights(self, results: list) -> list:
        """Collect all valid foresights from results."""
        foresights = []
        for result in results:
            foresights.extend(result.temporal_valid_foresights)
        return foresights
    
    def _collect_facts(self, results: list) -> list:
        """Collect all atomic facts from results."""
        facts = []
        for result in results:
            facts.extend(result.memcell.atomic_facts)
        return list(set(facts))  # Deduplicate
    
    def answer_query(self, query: str, current_time: datetime = None) -> str:
        """
        Full pipeline: retrieve context and generate an answer.
        
        Args:
            query: The user's question
            current_time: Current timestamp
            
        Returns:
            Generated answer string
        """
        # Retrieve relevant context
        recollection = self.recall(query, current_time)
        context = recollection["context"]
        
        if not context:
            return "I don't have enough information in memory to answer this question."
        
        # Generate answer
        prompt = f"""Based on the following memory context, please answer the user's question.

MEMORY CONTEXT:
{context}

QUESTION: {query}

Answer based only on the provided context. If the context doesn't contain enough information,
say so clearly. Be concise and accurate."""
        
        answer = self.llm.generate(prompt, temperature=0.5)
        return answer.strip()
    
    def refresh_index(self):
        """Refresh the BM25 index for sparse retrieval."""
        self.hybrid_retriever.refresh_bm25_index()
