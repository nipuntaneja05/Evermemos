# Evermemos: Complete Technical Documentation

## Overview

**Evermemos** is an advanced memory system for AI companions that transforms unstructured conversations into structured, queryable memories. Unlike simple RAG systems that just store and retrieve text chunks, Evermemos extracts semantic meaning, tracks changes over time, and handles temporal information intelligently.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    EVERMEMOS ARCHITECTURE                        │
│                                                                  │
│  ┌────────── PHASE I ──────────┐                                │
│  │   Episodic Trace Formation   │  Conversation → MemCells       │
│  │  • Boundary Detection        │                                │
│  │  • Narrative Synthesis       │                                │
│  │  • Fact Extraction           │                                │
│  └──────────────────────────────┘                                │
│                 ↓                                                │
│  ┌────────── PHASE II ─────────┐                                │
│  │   Semantic Consolidation     │  MemCells → MemScenes          │
│  │  • Theme Clustering          │                                │
│  │  • Conflict Detection        │                                │
│  │  • Profile Evolution         │                                │
│  └──────────────────────────────┘                                │
│                 ↓                                                │
│  ┌────────── PHASE III ────────┐                                │
│  │   Reconstructive Recollection│  Query → Relevant Context      │
│  │  • Hybrid Retrieval          │                                │
│  │  • Temporal Filtering        │                                │
│  │  • Query Rewriting           │                                │
│  └──────────────────────────────┘                                │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Qdrant    │  │    Groq     │  │    Qwen     │              │
│  │ Vector DB   │  │ LLM (API)   │  │ Embeddings  │              │
│  │   (Cloud)   │  │  (Mixtral)  │  │   (Local)   │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Data Structures

### 1. MemCell (Atomic Memory Unit)

The fundamental unit of memory. Each MemCell represents one coherent piece of information.

```python
@dataclass
class MemCell:
    id: str                    # Unique identifier
    episode: str               # Third-person narrative summary
    atomic_facts: list[str]    # Discrete, verifiable statements
    foresights: list[Foresight]  # Time-bounded information
    metadata: Metadata         # Contextual grounding
    embedding: list[float]     # Vector for semantic search (1536 dims)
    memscene_id: str           # Parent MemScene reference
```

**Example MemCell:**
```json
{
  "episode": "The user discussed their decision to adopt a vegan diet after watching a documentary about ocean sustainability.",
  "atomic_facts": [
    "User is vegan",
    "User watched documentary about ocean sustainability",
    "User previously was pescatarian"
  ],
  "foresights": [
    {
      "content": "User researching B12 supplements",
      "t_start": "2026-02-07",
      "t_end": null
    }
  ]
}
```

### 2. Foresight (Temporal Information)

Captures time-bounded information with validity windows.

```python
@dataclass
class Foresight:
    id: str
    content: str               # What the user plans/is doing
    t_start: datetime          # When it becomes valid
    t_end: datetime | None     # When it expires (None = indefinite)
    confidence: float          # How certain we are
    
    def is_valid_at(self, timestamp: datetime) -> bool:
        """Check if foresight is valid at given time."""
        if timestamp < self.t_start:
            return False
        if self.t_end and timestamp > self.t_end:
            return False
        return True
```

**Example Foresights:**
| Statement | t_start | t_end | Type |
|-----------|---------|-------|------|
| "On antibiotics for 10 days" | now | now + 10d | Fixed |
| "Traveling to Japan next month" | now | now + 30d | Fixed |
| "User is vegan" | now | None | Indefinite |

### 3. MemScene (Thematic Cluster)

Groups related MemCells by theme for coherent retrieval.

```python
@dataclass
class MemScene:
    id: str
    theme: str                 # "Health and Wellness", "Career", etc.
    summary: str               # Aggregated summary
    memcell_ids: list[str]     # References to MemCells
    centroid: list[float]      # Average embedding vector
```

### 4. ProfileConflict (Change Tracking)

Explicitly logs when information changes.

```python
@dataclass
class ProfileConflict:
    attribute: str             # What changed ("diet")
    old_value: str             # Previous value ("pescatarian")
    new_value: str             # New value ("vegan")
    old_timestamp: datetime
    new_timestamp: datetime
    resolution: str            # "recency_wins"
```

---

## Phase I: Episodic Trace Formation

**Purpose:** Convert raw conversations into structured MemCells.

### Step 1: Boundary Detection

Identifies where conversations shift topics.

```
Input:  "I love my job" → "My ankle hurts" → "I need a doctor"
Output: Segment 1: turns 1-1 (career)
        Segment 2: turns 2-3 (health)
```

**Optimization:** For conversations ≤10 turns, skip LLM-based detection entirely.

### Step 2: Narrative Synthesis

Converts raw dialogue into third-person narrative.

```
Input:  User: "I'm going vegan!"
        Assistant: "That's great!"
        
Output: "The user announced their decision to adopt a vegan diet, 
         expressing enthusiasm about the lifestyle change."
```

### Step 3: Fact Extraction

Extracts structured data from the narrative.

```
Input:  "The user is 180 pounds and wants to reach 160 pounds."

Output: {
  "atomic_facts": [
    "User's current weight is 180 pounds",
    "User's target weight is 160 pounds"
  ],
  "foresights": [
    {"content": "Weight loss goal", "duration_type": "ongoing"}
  ]
}
```

**Optimization:** Steps 2 & 3 are combined into a single LLM call (50% fewer API calls).

---

## Phase II: Semantic Consolidation

**Purpose:** Organize MemCells into themes and track changes.

### Clustering Algorithm

Uses cosine similarity to group related MemCells:

```python
for new_memcell in memcells:
    best_scene = None
    best_similarity = 0
    
    for scene in existing_scenes:
        similarity = cosine_similarity(new_memcell.embedding, scene.centroid)
        if similarity > best_similarity:
            best_similarity = similarity
            best_scene = scene
    
    if best_similarity > 0.70:  # Threshold
        best_scene.memcell_ids.append(new_memcell.id)
        update_centroid(best_scene)
    else:
        create_new_scene(new_memcell)
```

### Conflict Detection

Compares new facts against existing profile:

```python
if old_profile["diet"] == "pescatarian" and new_info["diet"] == "vegan":
    conflict = ProfileConflict(
        attribute="diet",
        old_value="pescatarian",
        new_value="vegan",
        resolution="recency_wins"
    )
    log_conflict(conflict)
    profile["diet"] = "vegan"  # Apply resolution
```

---

## Phase III: Reconstructive Recollection

**Purpose:** Retrieve relevant context for queries.

### Hybrid Retrieval

Combines two search methods:

| Method | Strength | Weakness |
|--------|----------|----------|
| **BM25** | Exact keyword match | Misses synonyms |
| **Vector** | Semantic similarity | Misses keywords |

**Reciprocal Rank Fusion (RRF):**
```python
def rrf_score(doc, dense_rank, sparse_rank, k=60):
    return 1/(k + dense_rank) + 1/(k + sparse_rank)
```

### Temporal Filtering

Filters out expired foresights:

```python
def filter_by_time(memcells, query_time):
    valid = []
    for mc in memcells:
        valid_foresights = [f for f in mc.foresights if f.is_valid_at(query_time)]
        if mc.atomic_facts or valid_foresights:
            valid.append(mc)
    return valid
```

### Query Rewriting

If initial retrieval is insufficient:

```
Query 1: "What is the user's job?"
→ Retrieved: nothing relevant
→ Rewrite: "Where does the user work? What is their profession?"
→ Retrieved: relevant MemCells
```

---

## File Structure

```
Evermemos/
├── src/
│   ├── __init__.py
│   ├── config.py           # Environment variables and settings
│   ├── models.py           # Data structures (MemCell, MemScene, etc.)
│   ├── llm_client.py       # Groq API + local Qwen embeddings
│   ├── vector_store.py     # Qdrant operations
│   ├── phase1_episodic.py  # Conversation → MemCells
│   ├── phase2_consolidation.py  # Clustering + conflicts
│   ├── phase3_recollection.py   # Retrieval + filtering
│   ├── evermemos.py        # Main orchestrator
│   └── demo.py             # Interactive demo
├── tests/
│   ├── test_scenarios.py   # Test cases
│   └── scale_evaluation.py # Performance benchmarks
├── main.py                 # Entry point
├── requirements.txt        # Dependencies
├── .env                    # API keys (not in git)
├── .gitignore
├── README.md
├── DESIGN.md               # Design decisions
└── TECHNICAL.md            # This file
```

---

## Configuration

### Environment Variables (.env)

```env
GROQ_API_KEY=gsk_...        # Groq API (text generation)
QDRANT_API_KEY=eyJ...       # Qdrant cloud
QDRANT_URL=https://...      # Qdrant endpoint
```

### Key Settings (config.py)

```python
# Model Selection
GROQ_MODEL = "mixtral-8x7b-32768"  # Fast, high limits(had to select this as my gemini api free limit was too low and i didnt have any paid api keys,Overall the whole architecture can work better with models like gemini/chatgpt4/5)
EMBEDDING_MODEL = "Alibaba-NLP/gte-Qwen2-1.5B-instruct"  # Local
EMBEDDING_DIMENSION = 1536

# Optimizations
SKIP_BOUNDARY_DETECTION_THRESHOLD = 10  # Skip for short convos

# Retrieval
TOP_K_RETRIEVAL = 10
MEMSCENE_SIMILARITY_THRESHOLD = 0.70
MAX_QUERY_REWRITES = 3
```

---

## API Rate Limit Optimizations

### Problem

Free tier LLMs have strict limits:
- Groq: 30 req/min, 14,400 req/day

### Solutions Implemented

| Optimization | Effect | Implementation |
|--------------|--------|----------------|
| **Skip boundary detection** | -2-4 calls/conversation | If ≤10 turns, treat as 1 episode |
| **Combined prompts** | -50% calls | Narrative + extraction in 1 call |
| **Use Mixtral** | 5x higher limits | Faster model with more quota |
| **Local embeddings** | 0 embedding calls | Qwen runs locally |

### Before vs After

```
BEFORE (per 10-turn conversation):
- Boundary detection: 5 calls
- Narrative synthesis: 1 call
- Fact extraction: 1 call
- Query + answer: 2 calls
Total: 9 LLM calls

AFTER:
- Boundary detection: 0 calls (skipped)
- Combined prompt: 1 call
- Query + answer: 2 calls
Total: 3 LLM calls (67% reduction)
```

---

## Usage Examples

### Basic Usage

```python
from src.evermemos import Evermemos

# Initialize
memory = Evermemos(user_id="user_123")

# Ingest conversation
result = memory.ingest_transcript("""
User: I just got promoted to senior engineer!
Assistant: Congratulations! That's a big achievement.
User: Thanks! I'm now making $150,000 at Google.
""")

print(f"MemCells created: {result['memcells_created']}")
print(f"Conflicts: {result['conflicts']}")

# Query
answer = memory.answer("Where does the user work?")
print(answer)  # "The user works at Google as a senior engineer..."
```

### Command Line

```bash
# Quick test
python main.py --test

# Full demo (interactive)
python main.py

# Run test scenarios
python tests/test_scenarios.py
```

---

## Test Scenarios

### 1. Conflict Detection
- Input: User changes diet from meat → pescatarian → vegan
- Expected: System detects and logs each transition

### 2. Foresight Expiry
- Input: "On antibiotics for 10 days" (20 days ago)
- Expected: Query "Can user drink alcohol?" returns YES (expired)

### 3. Profile Evolution
- Input: User changes job 3 times over 60 days
- Expected: Latest job/salary/location returned

### 4. Temporal Retrieval
- Same query at different timestamps returns different results

---

## Dependencies

```
groq>=0.4.0              # LLM API client
qdrant-client>=1.7.0     # Vector database
sentence-transformers    # Local embeddings
torch                    # ML backend
python-dotenv            # Environment variables
numpy                    # Numerical operations
rank-bm25               # Keyword search
python-dateutil         # Date parsing
pydantic                # Data validation
rich                    # Pretty terminal output
```

---

## Performance Characteristics

| Operation | Time | LLM Calls |
|-----------|------|-----------|
| Ingest 10-turn conversation | ~3-5s | 1 |
| Ingest 50-turn conversation | ~15-20s | 5-10 |
| Query with answer | ~2-3s | 1-2 |
| Embedding (local) | ~0.1s | 0 |

---

## Limitations

1. **Rate limits** - Free tier still limits heavy testing
2. **Cold start** - First query loads 3GB embedding model
3. **No streaming** - Ingestion is batch, not real-time
4. **English only** - Prompts optimized for English

---

## Future Improvements

1. **Caching** - Cache common query patterns
2. **Streaming ingestion** - Process turns as they arrive
3. **Multi-language** - Support non-English conversations
4. **Fact verification** - Cross-reference contradictory facts
5. **Compression** - Merge old MemCells to reduce storage
