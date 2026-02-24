import sys
import os
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.evermemos import create_evermemos
from src.models import DialogueTurn

def main():
    print("Loading Evermemos...")
    em = create_evermemos("default")
    
    print("Clearing Qdrant memory...")
    em.clear_memory(confirm=True)
    
    json_path = os.path.join(os.path.dirname(__file__), "data", "conversations", "conversations_100.json")
    print(f"Reading {json_path}...")
    
    with open(json_path, "r", encoding="utf-8") as f:
        conversations = json.load(f)
        
    print(f"Found {len(conversations)} conversations. Ingesting...")
    
    for i, conv in enumerate(conversations):
        conv_id = conv.get("conversation_id", f"conv_{i}")
        time_str = conv.get("timestamp", "")
        # Parse timestamp safely
        try:
            current_time = datetime.fromisoformat(time_str)
        except:
            current_time = datetime.now()
            
        turns_data = conv.get("turns", [])
        turns = []
        for t in turns_data:
            turn_time_str = t.get("timestamp", datetime.now().isoformat())
            try:
                turn_time = datetime.fromisoformat(turn_time_str)
            except:
                turn_time = datetime.now()
                
            turn = DialogueTurn(
                turn_id=t.get("turn_id", 0),
                speaker=t.get("speaker", "user"),
                content=t.get("content", ""),
                timestamp=turn_time
            )
            turns.append(turn)
            
        import time
        print(f"[{i+1}/{len(conversations)}] Ingesting {conv_id} ({len(turns)} turns)...")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                res = em.ingest_turns(turns, conversation_id=conv_id, current_time=current_time)
                if res["success"]:
                    print(f"  -> Extracted {res['memcells_created']} MemCells, {res['new_scenes']} new scenes, {res['updated_scenes']} updated scenes.")
                else:
                    print(f"  -> Failed: {res.get('error', 'Unknown error')}")
                break
            except Exception as e:
                print(f"  -> Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    print(f"  -> Failed to ingest {conv_id} after {max_retries} attempts.")
            
    print("Ingestion complete!")
    stats = em.get_stats()
    print("System Stats:", stats)

if __name__ == "__main__":
    main()
