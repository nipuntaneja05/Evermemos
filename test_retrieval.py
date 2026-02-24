import sys
import os
import time

# Add src to pythonpath
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.evermemos import create_evermemos

def main():
    print("Loading Evermemos for retrieval testing...")
    em = create_evermemos()
    
    queries = [
        "What am I training for next year?",
        "When is the marathon I'm training for?",
        "Am I looking for a job right now?",
        "Did I start a new job recently?",
        "Am I taking any medication or antibiotics?",
        "What are my plans for buying a house?",
        "Did I recently change my diet to something else like a juice cleanse?",
        "What is the capital of France?",
        "Did I buy a spaceship recently?"
    ]
    
    with open("test_results.txt", "w", encoding="utf-8") as f:
        f.write(f"\nTesting Retrieval Pipeline with {len(queries)} questions...\n\n")
        
        for idx, q in enumerate(queries, 1):
            f.write("=" * 60 + "\n")
            f.write(f"Test {idx}: {q}\n")
            f.write("-" * 60 + "\n")
            
            start = time.time()
            
            # Run the raw query to get deep stats
            res = em.query(q)
            
            # Generate the actual answer
            ans = em.answer(q)
            
            end = time.time()
            
            f.write(f"Extracted Entities: {res.get('query_entities', [])}\n")
            f.write(f"Pipeline: Confidence Routed (Fast)={res.get('confidence_routed', False)}, Reranked={res.get('reranked', False)}\n")
            f.write(f"Retrieve Stats: {len(res.get('episodes', []))} Episodes, Iterations={res.get('iterations', 1)}\n")
            f.write(f"Time Taken: {end - start:.2f}s\n")
            f.write(f"\nGenerated Answer: {ans}\n")
            f.write("=" * 60 + "\n\n")

if __name__ == "__main__":
    main()
