import sys
import os
from datetime import datetime
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.phase3_recollection import ReconstructiveRecollection
from src.models import RetrievalResult, MemCell, Metadata
from src.config import Config

def test_reranker_triggering():
    """Test that reranker is triggered when dense score is low."""
    # Mock dependencies
    with patch('src.phase3_recollection.get_llm_client'), \
         patch('src.phase3_recollection.get_vector_store'), \
         patch('src.phase3_recollection.CrossEncoderReranker') as MockReranker:
        
        # Setup mock reranker
        mock_reranker_inst = MockReranker.return_value
        
        # Create ReconstructiveRecollection
        rr = ReconstructiveRecollection()
        
        # Create some mock retrieval results with low dense scores
        mc1 = MemCell(id="mc1", episode="Today I went to Paris.", atomic_facts=["User went to Paris"])
        mc2 = MemCell(id="mc2", episode="I love eating pizza in Rome.", atomic_facts=["User loves pizza", "User was in Rome"])
        
        # Dense score 0.1 < 0.7 threshold
        res1 = RetrievalResult(memcell=mc1, dense_score=0.1, rrf_score=0.5)
        res2 = RetrievalResult(memcell=mc2, dense_score=0.05, rrf_score=0.4)
        
        # Mock hybrid retriever and temporal filter
        rr.hybrid_retriever.retrieve = MagicMock(return_value=[res1, res2])
        rr.temporal_filter.filter_results = MagicMock(return_value=[res1, res2])
        
        # Mock rerank to return results in reverse order (to verify re-sorting)
        res1.rerank_score = 0.8
        res2.rerank_score = 0.9
        mock_reranker_inst.rerank.return_value = [res2, res1]
        
        # Mock other methods to avoid side effects
        rr._build_context = MagicMock(return_value="Mock context")
        rr._collect_foresights = MagicMock(return_value=[])
        rr._collect_facts = MagicMock(return_value=[])
        
        # Run recall
        query = "Where did I go?"
        result = rr.recall(query, require_sufficient=False)
        
        # Verify reranker was called
        MockReranker.assert_called_once()
        mock_reranker_inst.rerank.assert_called_once()
        
        # Verify results are re-sorted by rerank score
        assert result["results"][0].memcell.id == "mc2"
        assert result["results"][0].rerank_score == 0.9
        assert result["reranked"] is True
        print("Test passed: Reranker triggered and results re-sorted.")

def test_no_reranker_on_high_confidence():
    """Test that reranker is NOT triggered when dense score is high."""
    with patch('src.phase3_recollection.get_llm_client'), \
         patch('src.phase3_recollection.get_vector_store'), \
         patch('src.phase3_recollection.CrossEncoderReranker') as MockReranker:
        
        mock_reranker_inst = MockReranker.return_value
        rr = ReconstructiveRecollection()
        
        mc1 = MemCell(id="mc1", episode="Today I went to Paris.")
        # Dense score 0.8 > 0.7 threshold
        res1 = RetrievalResult(memcell=mc1, dense_score=0.8, rrf_score=0.9, sparse_score=1.0)
        
        rr.hybrid_retriever.retrieve = MagicMock(return_value=[res1])
        rr.temporal_filter.filter_results = MagicMock(return_value=[res1])
        rr._build_context = MagicMock(return_value="Mock context")
        rr._collect_foresights = MagicMock(return_value=[])
        rr._collect_facts = MagicMock(return_value=[])
        
        query = "Paris trip"
        result = rr.recall(query, require_sufficient=False)
        
        # Verify reranker was NOT called
        mock_reranker_inst.rerank.assert_not_called()
        assert result["reranked"] is False
        print("Test passed: Reranker skipped for high confidence.")

if __name__ == "__main__":
    try:
        test_reranker_triggering()
        test_no_reranker_on_high_confidence()
        print("\nAll tests passed successfully!")
    except Exception as e:
        print(f"\nTest failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
