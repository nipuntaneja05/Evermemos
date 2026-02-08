# Evermemos: Design Document

## Overview

Evermemos is an advanced memory system for AI companions that transforms unstructured conversations into structured, queryable memories. This document explains the key design decisions, algorithms, and tradeoffs made during development.

---

## 1. Topic Boundary Detection

### Problem Statement

Conversations naturally flow between topics. A single 30-minute conversation might cover someone's diet, their job, and their weekend plans. We need to segment these into coherent "episodes" for meaningful memory storage.

### Approach: Sliding Window with LLM-Based Semantic Analysis

```
Conversation: [Turn 1] [Turn 2] [Turn 3] [Turn 4] [Turn 5] [Turn 6] [Turn 7]
                  │         │         │         │
              Window 1   Window 2   Window 3   Window 4
                  ↓         ↓         ↓         ↓
               LLM: Is there a topic shift in this window?
```

**Algorithm:**

```python
def detect_boundaries(turns, window_size=5):
    boundaries = []
    
    for i in range(len(turns) - window_size + 1):
        window = turns[i:i + window_size]
        
        # Ask LLM: "Is there a significant topic shift in this window?"
        shift_detected = llm.analyze_topic_shift(window)
        
        if shift_detected.confidence > 0.7:
            boundaries.append(i + shift_detected.position)
    
    return merge_adjacent_boundaries(boundaries)
```

**Why This Approach?**

| Alternative | Problem |
|-------------|---------|
| **Fixed-size chunks** | Breaks mid-topic, loses context |
| **Keyword matching** | Misses semantic shifts ("I'm happy" → "I'm sad" about same topic) |
| **Embedding similarity** | Computationally expensive for every turn pair |
| **LLM-based (our choice)** | Understands semantic meaning, handles nuance |

### Optimization: Skip for Short Conversations

For conversations with ≤3 turns, we skip boundary detection entirely:

```python
if len(turns) <= 3:
    return [(0, len(turns) - 1)]  # Treat as single episode
```

**Rationale:** Short conversations rarely have topic shifts. Skipping saves LLM calls without sacrificing quality.

---

## 2. Conflict Resolution Strategy

### Problem Statement

Users change over time. Someone might say "I'm vegetarian" in January and "I've started eating meat again" in March. The system must:
1. Detect when information conflicts
2. Decide which version is "correct"
3. Maintain history for context

### Strategy: Recency-Aware Resolution with Explicit Logging

```
┌─────────────────────────────────────────────────────────────┐
│                    CONFLICT RESOLUTION                       │
│                                                             │
│  OLD FACT: diet = "vegetarian" (Jan 15)                     │
│  NEW FACT: diet = "flexitarian" (Mar 20)                    │
│                                                             │
│  Resolution: RECENCY WINS                                   │
│  Current Value: "flexitarian"                               │
│  Conflict Logged: ✓ (for future reference)                  │
└─────────────────────────────────────────────────────────────┘
```

**Implementation:**

```python
def resolve_conflict(old_fact, new_fact):
    conflict = ConflictRecord(
        attribute=old_fact.attribute,
        old_value=old_fact.value,
        new_value=new_fact.value,
        old_timestamp=old_fact.timestamp,
        new_timestamp=new_fact.timestamp,
        resolution="recency_wins"
    )
    
    # Log the conflict for audit trail
    profile.conflict_history.append(conflict)
    
    # Apply recency resolution
    if new_fact.timestamp > old_fact.timestamp:
        profile.explicit_facts[old_fact.attribute] = new_fact
    
    return conflict
```

### Why "Recency Wins"?

| Strategy | Pros | Cons |
|----------|------|------|
| **Recency wins** | Simple, reflects current reality | Ignores confidence |
| **Confidence-based** | More accurate | Requires subjective scoring |
| **Ask user** | Guaranteed correct | Interrupts UX |
| **Keep both** | No data loss | Ambiguous queries |

**We chose recency because:**

1. **Most changes are intentional** - When someone says "I'm vegan now", they mean it
2. **Temporal grounding matters** - The most recent statement is usually the most relevant
3. **Conflict history provides context** - We don't lose the old information, just deprioritize it
4. **Queries can still access history** - "What did the user used to eat?" works because we log everything

### Edge Cases

| Scenario | Handling |
|----------|----------|
| Same-day conflicts | Later timestamp wins |
| Ambiguous statements | Lower confidence score, may not override |
| Explicit corrections | "Actually, I meant..." → high priority |

---

## 3. Foresight Validity Duration

### Problem Statement

When a user says "I'm on antibiotics for 10 days", we know exactly when it expires. But when they say "I'm traveling to Japan", how long is that valid?

### Approach: LLM-Guided Duration Inference with Defaults

**Types of Duration:**

| Type | Example | Duration |
|------|---------|----------|
| **Fixed** | "10 days of antibiotics" | Exactly 10 days |
| **Bounded** | "Traveling next month" | ~30 days |
| **Ongoing** | "Started a new diet" | Until explicitly changed |
| **Indefinite** | "I'm allergic to peanuts" | Forever (null end date) |

**Inference Algorithm:**

```python
def infer_duration(statement, context, current_time):
    # Extract explicit duration if present
    explicit = extract_temporal_expression(statement)
    if explicit:
        return ForesightDuration(
            t_start=current_time + explicit.start_offset,
            t_end=current_time + explicit.end_offset,
            type="fixed"
        )
    
    # LLM inference for implicit durations
    result = llm.infer_duration(f"""
        Statement: "{statement}"
        Context: {context}
        
        What is the likely duration of this?
        Options:
        - fixed: X days/weeks/months
        - ongoing: until changed
        - indefinite: permanent trait
    """)
    
    return parse_llm_duration(result, current_time)
```

**Default Durations When Unspecified:**

| Category | Default Duration | Rationale |
|----------|------------------|-----------|
| Travel plans | 14 days | Average trip length |
| Temporary health | 7 days | Common illness duration |
| Diet changes | Indefinite | Lifestyle, not temporary |
| Work projects | 30 days | Typical sprint/project |
| Appointments | 1 day | Single event |

### Why Not Always Ask?

| Approach | UX Impact |
|----------|-----------|
| **Infer from context** | Seamless, no interruption |
| **Ask for every foresight** | Annoying, breaks conversation flow |
| **Ignore duration** | Stale information persists |

**Our choice:** Infer intelligently, with conservative defaults. A foresight that expires too early is better than one that persists incorrectly.

---

## 4. Tradeoffs Made

### Tradeoff 1: LLM Quality vs. Rate Limits

**Problem:** High-quality LLMs (GPT-4, Claude) have strict rate limits on free tiers.

**Decision:** Use local LLM (Ollama + qwen2.5:7b) with cloud fallback.

| Aspect | Cloud LLM | Local LLM (Chosen) |
|--------|-----------|-------------------|
| Quality | Higher | Good enough |
| Speed | Fast | Medium (GPU) |
| Rate limits | Yes (100k/day) | None |
| Cost | Per-token | Free |
| Privacy | Data sent externally | Fully local |

**Result:** Unlimited processing with acceptable quality. Can scale to production with cloud LLMs later.

---

### Tradeoff 2: Storage Granularity

**Problem:** Store every word vs. summarize aggressively?

**Decision:** Hierarchical storage with MemCells and MemScenes.

```
┌─────────────────────────────────────┐
│            MemScenes                │  ← High-level themes
│  ┌─────────────────────────────┐    │
│  │        MemCells             │    │  ← Individual memories
│  │  ┌───────────────────────┐  │    │
│  │  │    Atomic Facts       │  │    │  ← Discrete statements
│  │  └───────────────────────┘  │    │
│  └─────────────────────────────┘    │
└─────────────────────────────────────┘
```

| Granularity | Pros | Cons |
|-------------|------|------|
| Raw transcripts | Complete | Expensive to search |
| MemCells only | Balanced | Some context loss |
| Heavy summarization | Compact | Loses nuance |

**Result:** Balance between detail and efficiency. MemCells preserve atomic facts while MemScenes enable thematic retrieval.

---

### Tradeoff 3: Embedding Model Choice

**Problem:** Cloud embeddings (OpenAI) vs. local models?

**Decision:** Local Qwen embeddings (1536 dimensions).

| Model | Quality | Speed | Cost |
|-------|---------|-------|------|
| OpenAI ada-002 | Excellent | Fast | $0.0001/1K tokens |
| Qwen2 1.5B (chosen) | Very good | Medium | Free |
| MiniLM | Good | Very fast | Free |

**Result:** High-quality embeddings with zero API costs. Runs on CPU, no GPU required.

---

### Tradeoff 4: Real-time vs. Batch Processing

**Problem:** Process each turn immediately vs. batch at end?

**Decision:** Batch processing after conversation ends.

| Approach | Latency | Accuracy | Complexity |
|----------|---------|----------|------------|
| Real-time | High (during chat) | Lower | Higher |
| Batch (chosen) | None (async) | Higher | Lower |

**Rationale:** 
- Conversations are ingested after they complete
- Allows full context for boundary detection
- No latency impact on user experience
- Simpler implementation

---

### Tradeoff 5: Conflict Detection Sensitivity

**Problem:** Too sensitive = false positives. Not sensitive enough = missed conflicts.

**Decision:** Attribute-based comparison with LLM-assisted detection.

```python
# Simple attribute matching
if old_fact.attribute == new_fact.attribute:
    if old_fact.value != new_fact.value:
        return CONFLICT

# LLM for semantic conflicts (e.g., "vegetarian" vs "eats fish")
if llm.are_semantically_conflicting(old_fact, new_fact):
    return CONFLICT
```

| Sensitivity | False Positives | Missed Conflicts |
|-------------|-----------------|------------------|
| High | Many | Few |
| Low | Few | Many |
| Balanced (chosen) | Some | Some |

**Result:** Catches most real conflicts while minimizing false alarms.

---

## 5. Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    EVERMEMOS DESIGN                              │
│                                                                  │
│  INPUT: Raw Conversation                                        │
│              ↓                                                  │
│  PHASE 1: Episodic Trace Formation                              │
│    • Boundary Detection (LLM + sliding window)                  │
│    • Narrative Synthesis (combined prompt)                      │
│    • Fact Extraction (atomic facts + foresights)                │
│              ↓                                                  │
│  PHASE 2: Semantic Consolidation                                │
│    • Theme Clustering (cosine similarity)                       │
│    • Profile Evolution (recency-based)                          │
│    • Conflict Detection (attribute matching)                    │
│              ↓                                                  │
│  PHASE 3: Reconstructive Recollection                           │
│    • Hybrid Retrieval (BM25 + vector)                           │
│    • Temporal Filtering (foresight validity)                    │
│    • Answer Generation (context-aware LLM)                      │
│              ↓                                                  │
│  OUTPUT: Coherent, temporally-aware answer                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Future Considerations

| Area | Current | Potential Improvement |
|------|---------|----------------------|
| Conflict resolution | Recency wins | Confidence-weighted voting |
| Duration inference | LLM + defaults | ML model trained on patterns |
| Boundary detection | Per-window LLM | Fine-tuned classifier |
| Storage | Qdrant cloud | Local vector store option |
| Privacy | Local LLM optional | End-to-end encryption |

---

## Conclusion

Evermemos balances accuracy, performance, and practicality through:

1. **Intelligent boundary detection** with optimization for short conversations
2. **Recency-based conflict resolution** with full history logging
3. **Context-aware duration inference** with sensible defaults
4. **Local-first architecture** to avoid rate limits and costs

These design decisions enable a production-ready memory system that can scale from personal use to enterprise deployment.
