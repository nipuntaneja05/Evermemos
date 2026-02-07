# Evermemos 🧠

**Advanced Memory System with Episodic Trace Formation, Semantic Consolidation, and Reconstructive Recollection**

Evermemos is a sophisticated memory system that transforms conversation transcripts into structured, searchable memory units. Inspired by biological memory consolidation, it organizes episodic memories into thematic clusters and provides intelligent retrieval with temporal awareness.

## 🏗️ Architecture Overview

The system operates in three distinct phases:

### Phase I: Episodic Trace Formation

Transforms continuous interaction history into discrete, stable memory units called **MemCells**.

```
Transcript → Semantic Segmentation → Narrative Synthesis → MemCell Extraction
```

- **Contextual Segmentation**: Sliding window analysis with LLM-based topic shift detection
- **Narrative Synthesis**: Third-person narrative rewriting that resolves coreferences
- **Structural Derivation**: Extraction of Episodes, Atomic Facts, and Foresights

### Phase II: Semantic Consolidation

Organizes MemCells into higher-order structures called **MemScenes**.

```
MemCell → Vector Embedding → Incremental Clustering → Profile Evolution
```

- **Incremental Clustering**: Online mechanism using cosine similarity with threshold τ
- **Scene-Driven Profile Evolution**: Updates user profile with conflict detection
- **Recency-Aware Resolution**: Latest evidence takes precedence

### Phase III: Reconstructive Recollection

Retrieval modeled as active reconstruction with sufficiency verification.

```
Query → Hybrid Retrieval (RRF) → Temporal Filtering → Sufficiency Check → Answer
```

- **Hybrid Search**: Dense (semantic) + Sparse (BM25) with Reciprocal Rank Fusion
- **Temporal Filtering**: Validates Foresight signals against current timestamp
- **Agentic Verification**: LLM-based sufficiency check with query rewriting loop

## 📦 Data Structures

### MemCell: `c = (E, F, P, M)`

| Component | Description |
|-----------|-------------|
| **E** (Episode) | Third-person narrative summary |
| **F** (Atomic Facts) | Discrete, verifiable statements |
| **P** (Foresight) | Forward-looking inferences with `[t_start, t_end]` validity |
| **M** (Metadata) | Timestamps, source pointers, tags |

### MemScene

Thematic cluster of related MemCells with:
- Theme title
- Aggregated summary
- Centroid vector for similarity matching
- List of constituent MemCell IDs

### User Profile

Compact representation with:
- **Explicit Facts**: Verifiable attributes (e.g., weight: 175 lbs)
- **Implicit Traits**: Preferences, habits, personality traits
- **Conflict History**: Record of detected and resolved conflicts

## 🚀 Quick Start

### 1. Installation

```bash
cd Evermemos
pip install -r requirements.txt
```

### 2. Configuration

The system requires:
- `GEMINI_API_KEY` - Google Gemini API key
- `QDRANT_API_KEY` - Qdrant Cloud API key
- `QDRANT_URL` - Qdrant cluster endpoint

These should be in your `.env` file.

### 3. Run the Demo

```bash
python main.py
```

Or run a quick test:

```bash
python main.py --test
```

## 💻 Usage

### Basic Usage

```python
from src.evermemos import Evermemos

# Initialize the memory system
memory = Evermemos(user_id="my_user")

# Ingest a conversation
transcript = """
User: I've decided to go vegan starting today!
Assistant: That's wonderful! What inspired this decision?
User: I want to improve my health and lose weight.
"""

result = memory.ingest_transcript(transcript, conversation_id="conv_001")
print(f"Created {result['memcells_created']} MemCells")

# Query the memory
answer = memory.answer("What are the user's dietary preferences?")
print(answer)
```

### Advanced Usage

```python
from datetime import datetime

# Query with specific timestamp (for temporal filtering)
result = memory.query(
    "Is the user currently on any special diet?",
    current_time=datetime.now(),
    require_sufficient=True
)

# Access detailed results
print(f"Episodes retrieved: {len(result['results'])}")
print(f"Active foresights: {len(result['valid_foresights'])}")
print(f"Context:\n{result['context']}")

# Get user profile
profile = memory.get_profile()
print(f"Explicit facts: {list(profile.explicit_facts.keys())}")

# Export memory
memory.export_memory_json("backup.json")
```

### Working with MemScenes

```python
# List all scenes
scenes = memory.get_all_memscenes()
for scene in scenes:
    print(f"Theme: {scene.theme}")
    print(f"  MemCells: {len(scene.memcell_ids)}")

# Get scene contents
contents = memory.get_scene_contents(scene_id)
for mc in contents["memcells"]:
    print(f"Episode: {mc.episode}")
    print(f"Facts: {mc.atomic_facts}")
```

## 🔧 Configuration

Edit `src/config.py` to customize:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `SLIDING_WINDOW_SIZE` | 5 | Turns to analyze for boundary detection |
| `TOPIC_SHIFT_THRESHOLD` | 0.7 | Confidence threshold for topic shifts |
| `MEMSCENE_SIMILARITY_THRESHOLD` | 0.70 | τ for scene clustering |
| `TOP_K_RETRIEVAL` | 10 | Initial retrieval results |
| `TOP_K_EPISODES` | 8 | Episodes for final context |
| `RRF_K` | 60 | RRF fusion constant |
| `MAX_QUERY_REWRITES` | 3 | Maximum rewrite iterations |

## 📁 Project Structure

```
Evermemos/
├── .env                       # API keys and configuration
├── requirements.txt           # Python dependencies
├── main.py                    # Entry point
└── src/
    ├── __init__.py
    ├── config.py              # Configuration management
    ├── models.py              # Data structures (MemCell, MemScene, etc.)
    ├── llm_client.py          # Gemini API client
    ├── vector_store.py        # Qdrant integration
    ├── phase1_episodic.py     # Episodic Trace Formation
    ├── phase2_consolidation.py # Semantic Consolidation
    ├── phase3_recollection.py  # Reconstructive Recollection
    ├── evermemos.py           # Main orchestrator
    └── demo.py                # Interactive demo
```

## 🔑 Key Features

### ✅ Temporal Awareness

Foresights (plans, temporary states) have validity windows:

```python
# Only returns foresights valid at query time
result = memory.query("Is user on a detox?", current_time=now)
# Foresight "User on 7-day detox" is only returned within those 7 days
```

### ✅ Conflict Detection

Automatic detection and resolution of conflicting information:

```python
# When weight changes from 180 to 175, system detects and resolves:
# ConflictRecord(attribute="weight", old="180", new="175", resolution="recency")
```

### ✅ Hybrid Retrieval

Combines semantic understanding with keyword matching:

```python
# Dense: "dietary changes" matches "becoming vegan"
# Sparse: "180 pounds" matches exactly
# RRF: Fuses both for optimal results
```

### ✅ Agentic Verification

Automatically expands queries when context is insufficient:

```python
# Query: "travel plans"
# If insufficient, rewrites to:
# - "Japan trip details"
# - "flight information from SFO"
# - "technology locations to visit"
```

## 🛠️ Technologies

- **LLM**: Google Gemini 2.0 Flash
- **Embeddings**: Gemini text-embedding-004
- **Vector Database**: Qdrant Cloud
- **Sparse Retrieval**: BM25 (rank-bm25)
- **Framework**: Python 3.10+

## 📊 System Stats

Check system status:

```python
stats = memory.get_stats()
# {
#   "user_id": "demo_user",
#   "memcells_count": 15,
#   "memscenes_count": 3,
#   "vector_dimensions": 768
# }
```

## 🔮 Future Enhancements

- [ ] Multi-user support with isolation
- [ ] REST API server
- [ ] Web interface
- [ ] Memory importance scoring
- [ ] Forgetting curve implementation
- [ ] Cross-session learning

## 📄 License

MIT License

---

**Built with ❤️ using Gemini AI and Qdrant**
