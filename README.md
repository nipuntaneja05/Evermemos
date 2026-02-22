# Evermemos 🧠

**Advanced Memory System with Episodic Trace Formation, Semantic Consolidation, and Reconstructive Recollection**
Please Refer README.md and DESIGN.md

Evermemos is a sophisticated memory system that transforms conversation transcripts into structured, searchable memory units. Inspired by biological memory consolidation, it organizes episodic memories into thematic clusters and provides intelligent retrieval with temporal awareness.

---

## 📊 Scale Evaluation Results (500 Conversations)

| Metric | Value |
|--------|-------|
| **MemCells Created** | 495 |
| **MemScenes Formed** | 43 (semantic clusters) |
| **Conflicts Detected** | 455 |
| **Deduplication Rate** | 84.8% |
| **Foresights Tracked** | 716 (temporal plans) |
| **Implicit Traits** | 276 (profile evolution) |
| **Ingestion Time** | 132 minutes (15.8s/conversation) |
| **Avg Retrieval Latency** | 4.1 seconds |

✅ **All core features verified**: Conflict detection, deduplication, temporal filtering, retrieval relevance, and scalability from 100→500 conversations.

---

## 🏗️ Architecture Overview

The system operates in three distinct phases:

### Phase I: Episodic Trace Formation

Transforms continuous interaction history into discrete, stable memory units called **MemCells**.

```
Transcript → Semantic Segmentation → Narrative Synthesis → MemCell Extraction
```

- **Contextual Segmentation**: Sliding window analysis with LLM-based topic shift detection
- **Narrative Synthesis**: Third-person narrative rewriting that resolves coreferences
- **Structural Derivation**: Extraction of Episodes, Atomic Facts, and Foresights with temporal bounds

### Phase II: Semantic Consolidation

Organizes MemCells into higher-order structures called **MemScenes**.

```
MemCell → Vector Embedding → Incremental Clustering → Profile Evolution
```

- **Incremental Clustering**: Online mechanism using cosine similarity with threshold τ (0.70)
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

---

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

---

## 🚀 Quick Start

### 1. Installation

```bash
cd Evermemos
pip install -r requirements.txt
```

### 2. Environment Setup

Create a `.env` file with the following API keys:

```bash
# For Scale Evaluations (Groq - Fast & High Quality)
GROQ_API_KEY=your_groq_api_key

# For Embeddings (Local Model - No API needed)
# Using Alibaba-NLP/gte-Qwen2-1.5B-instruct (downloaded automatically)

# Vector Database (Qdrant Cloud)
QDRANT_API_KEY=your_qdrant_api_key
QDRANT_URL=your_qdrant_cluster_url

# Optional: For local testing with Ollama
# (System automatically downloads qwen2.5:3b)
```

### 3. Run the Demo

```bash
python main.py
```

Or run a quick test:

```bash
python main.py --test
```

---

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
print(f"Implicit traits: {len(profile.implicit_traits)}")

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

---

## 🔧 Configuration

Edit `src/config.py` to customize:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `LLM_PROVIDER` | `"groq"` | LLM provider: `"groq"`, `"ollama"`, or `"gemini"` |
| `GROQ_MODEL` | `"llama-3.3-70b-versatile"` | Groq model for scale evaluations |
| `OLLAMA_MODEL` | `"qwen2.5:3b"` | Ollama model for local testing |
| `EMBEDDING_PROVIDER` | `"local"` | Embedding provider: `"local"` or `"gemini"` |
| `LOCAL_EMBEDDING_MODEL` | `"Alibaba-NLP/gte-Qwen2-1.5B-instruct"` | Local embedding model |
| `SLIDING_WINDOW_SIZE` | 5 | Turns to analyze for boundary detection |
| `TOPIC_SHIFT_THRESHOLD` | 0.7 | Confidence threshold for topic shifts |
| `MEMSCENE_SIMILARITY_THRESHOLD` | 0.70 | τ for scene clustering |
| `TOP_K_RETRIEVAL` | 10 | Initial retrieval results |
| `TOP_K_EPISODES` | 8 | Episodes for final context |
| `RRF_K` | 60 | RRF fusion constant |
| `MAX_QUERY_REWRITES` | 3 | Maximum rewrite iterations |

---

## �️ Technologies

### LLM Strategy

We use different LLMs optimized for different tasks:

| Use Case | LLM Provider | Model | Rationale |
|----------|-------------|-------|-----------|
| **Scale Evaluations** | Groq | `llama-3.3-70b-versatile` | Fast API, high quality output, paid tier for rate limits |
| **Local Testing** | Ollama | `qwen2.5:3b` | Fully local, no API costs, good for quick tests |
| **Embeddings** | Local | `Alibaba-NLP/gte-Qwen2-1.5B-instruct` | No API costs, 1.5B params, excellent quality |

### Tech Stack

- **Vector Database**: Qdrant Cloud (with retry logic for transient errors)
- **Sparse Retrieval**: BM25 (rank-bm25)
- **Framework**: Python 3.10+
- **Dependencies**: sentence-transformers, transformers, groq, rich, python-dotenv

---

## �📁 Project Structure

```
Evermemos/
├── .env                           # API keys and configuration
├── requirements.txt               # Python dependencies
├── main.py                        # Entry point
├── data/
│   └── conversations/             # Evaluation datasets
│       ├── conversations_100.json
│       ├── conversations_300.json
│       └── conversations_500.json
├── results/
│   ├── scale_evaluation_results100.md
│   ├── scale_evaluation_results300.md
│   └── scale_evaluation_results500.md
├── tests/
│   ├── scale_evaluation.py        # Main evaluation script
│   ├── scale_evaluation_300.py    # 500-conversation evaluation
│   └── test_scenarios.py          # Feature test scenarios
└── src/
    ├── __init__.py
    ├── config.py                  # Configuration management
    ├── models.py                  # Data structures (MemCell, MemScene, etc.)
    ├── llm_client.py              # Multi-provider LLM client
    ├── vector_store.py            # Qdrant integration
    ├── phase1_episodic.py         # Episodic Trace Formation
    ├── phase2_consolidation.py    # Semantic Consolidation
    ├── phase3_recollection.py     # Reconstructive Recollection
    ├── evermemos.py               # Main orchestrator
    └── demo.py                    # Interactive demo
```

---

## 🔑 Key Features

### ✅ Temporal Awareness

Foresights (plans, temporary states) have validity windows:

```python
# Only returns foresights valid at query time
result = memory.query("Is user on a detox?", current_time=now)
# Foresight "User on 7-day detox" is only returned within those 7 days
```

**Scale Evaluation Result**: 716 foresights tracked across 500 conversations

### ✅ Conflict Detection

Automatic detection and resolution of conflicting information:

```python
# When weight changes from 180 to 175, system detects and resolves:
# ConflictRecord(attribute="weight", old="180", new="175", resolution="recency")
```

**Scale Evaluation Result**: 455 conflicts detected and resolved across 500 conversations

### ✅ Deduplication (Storage Optimization)

System automatically consolidates duplicate facts:

```python
# 2277 raw facts → 347 unique facts
# Deduplication rate: 84.8%
# Storage saved: ~85% reduction
```

**Impact**: Massive storage savings while preserving all unique information

### ✅ Hybrid Retrieval

Combines semantic understanding with keyword matching:

```python
# Dense: "dietary changes" matches "becoming vegan"
# Sparse: "180 pounds" matches exactly
# RRF: Fuses both for optimal results
```

**Scale Evaluation Result**: 8 relevant episodes retrieved per query with 4.1s avg latency

### ✅ Agentic Verification

Automatically expands queries when context is insufficient:

```python
# Query: "travel plans"
# If insufficient, rewrites to:
# - "Japan trip details"
# - "flight information from SFO"
# - "technology locations to visit"
```

**Result**: Iterative query expansion ensures comprehensive answers

### ✅ Profile Evolution

System builds a comprehensive user profile from conversations:

```python
profile = memory.get_profile()
# 276 implicit traits inferred from 500 conversations
# e.g., "health-conscious", "loves photography", "remote worker"
```

---

## 📊 Running Scale Evaluations

### Test Scenarios (Local)

Quick feature tests using Ollama (local LLM):

```bash
python tests/test_scenarios.py
```

Uses `qwen2.5:3b` for fast local testing without API costs.

### Scale Evaluation (Cloud)

Large-scale evaluation using Groq API:

```bash
# 100 conversations
python tests/scale_evaluation.py

# 500 conversations
python tests/scale_evaluation_300.py
```

Uses `llama-3.3-70b-versatile` via Groq for high-quality, fast processing.

**Results saved to**: `results/scale_evaluation_results{N}.md`

---

## 🎯 Performance Characteristics

### Ingestion Performance

| Scale | Time | Rate |
|-------|------|------|
| 100 conversations | ~26 min | 1 conversation every 15.6s |
| 300 conversations | ~77 min | 1 conversation every 15.4s |
| 500 conversations | ~132 min | 1 conversation every 15.8s |

**Observation**: Consistent ~15.5s per conversation regardless of scale (excellent scalability)

### Retrieval Performance

- **Average Latency**: 4.1 seconds
- **Breakdown**:
  - Embedding generation: ~50-100ms
  - Qdrant search: ~100-500ms
  - LLM sufficiency check: ~1-2s
  - Query rewrite (if needed): ~1-2s
  - Context building: ~100ms

**Main bottleneck**: LLM API calls for sufficiency verification (can be optimized by skipping or using faster models)

### Storage Efficiency

- **Deduplication**: 84.8% reduction in storage
- **Vector Database**: Qdrant Cloud (scalable)
- **Embeddings**: 1536 dimensions (gte-Qwen2-1.5B-instruct)

---

## 🧪 Testing

### Feature Tests

```bash
python tests/test_scenarios.py
```

Tests:
- Foresight expiry tracking
- Conflict detection and resolution
- Profile evolution
- Deduplication
- Retrieval relevance

### Scale Tests

```bash
# Small scale (quick test)
python tests/scale_evaluation.py

# Large scale (full evaluation)
python tests/scale_evaluation_300.py
```

Comprehensive metrics:
- MemCells created
- MemScenes formed
- Conflicts detected
- Deduplication rate
- Foresights tracked
- Profile evolution
- Retrieval latency
- Sample query relevance

---

## 🔮 Future Enhancements

- [ ] Improve foresight expiry date extraction (currently many show N/A)
- [ ] Add explicit profile attributes extraction
- [ ] Multi-user support with isolation
- [ ] REST API server
- [ ] Web interface
- [ ] Memory importance scoring
- [ ] Forgetting curve implementation
- [ ] Cross-session learning
- [ ] Query latency optimization (skip sufficiency check for simple queries)

---

## 📄 License

MIT License

---

**Built using Groq (Llama 3.3 70B), Ollama (Qwen 2.5 3B), and Qdrant**

*Scale evaluation: 500 conversations, 495 MemCells, 84.8% deduplication, 455 conflicts resolved ✅*

INGESTION (per conversation ~16s)
───────────────────────────────────────────────────────
Raw Transcript
    │
    ▼
[Phase 1 — Episodic Trace Formation]  phase1_episodic.py
    ├─ 🤖 LLM: Topic boundary detection     (sliding window of 5 turns → is this a new topic?)
    ├─ 🤖 LLM: Episode summarisation        (compress turns into a narrative episode)
    ├─ 🤖 LLM: Atomic fact extraction       (pull discrete facts from episode)
    └─ 🤖 LLM: Foresight extraction         (detect future plans/dates → Foresight objects)
          │
          └─→ Produces: MemCells  (1 per topic segment, stored in Qdrant)
    │
    ▼
[Phase 2 — Semantic Consolidation]  phase2_consolidation.py
    ├─ 🔢 Embedding: embed MemCell          (local Qwen2 1.5B, no API call)
    ├─ 🔢 Vector similarity: cluster into MemScene  (cosine sim > 0.70 threshold)
    ├─ 🤖 LLM: Conflict detection           (compare new facts vs existing profile)
    └─ 🤖 LLM: Profile update / trait inference
          │
          └─→ Produces: MemScenes (clusters), ConflictRecords, UserProfile updates
    │
    ▼
[BM25 Index Rebuild]  — local, fast, in-memory


RETRIEVAL (per query ~4–7s)
───────────────────────────────────────────────────────
User Query
    │
    ▼
[Phase 3 — Reconstructive Recollection]  phase3_recollection.py
    ├─ 🔢 Embedding: embed query            (local Qwen2 1.5B)
    ├─ 🌐 Qdrant: dense vector search       (remote cloud call)
    ├─ ⚡ BM25: sparse keyword search       (local, instant)
    ├─ ⚡ RRF fusion                         (merge dense + sparse rankings, local)
    ├─ ⚡ Temporal filter                    (drop expired Foresights, local)
    │
    ├─ 🤖 LLM: Sufficiency check            (is the retrieved context enough?)
    │     └─ IF NO (up to 3 retries):
    │         ├─ 🤖 LLM: Query rewriting    (generate 2-3 better sub-queries)
    │         └─ repeat search + sufficiency check
    │
    └─ 🤖 LLM: Final answer generation
          │
          └─→ Returns: Answer + episodes + facts + foresights