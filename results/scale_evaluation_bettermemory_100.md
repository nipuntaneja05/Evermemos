# Evermemos BetterMemory Scale Evaluation — 100 Conversations

**Generated:** 2026-02-23 08:51:53

## Summary Table

| Metric | Value |
|--------|-------|
| Total Conversations | 100 |
| Total Turns | 624 |
| MemCells Created | 100 |
| MemScenes Formed | 25 |
| Conflicts Detected | 56 |
| Deduplication Rate | 56.4% |
| Ingestion Time | 1217.7s |
| Avg Retrieval Latency | 1123ms |

---

## Core Metrics

### Memory Extraction

- **MemCells Created:** 100
- **MemScenes Formed:** 25 (semantic clusters)
- **Raw Facts Extracted:** 475
- **Unique Facts:** 207w

### Conflict Detection ✅

- **Conflicts Detected:** 56
- **Status:** Working - system identifies contradictions between facts

### Deduplication ✅

- **Raw Facts:** 475
- **Unique Facts:** 207
- **Deduplication Rate:** 56.4%
- **Storage Saved:** ~56.4% reduction

### Foresight Tracking ✅

- **Foresights Created:** 132
- **Active Foresights:** 60
- **Expired Foresights:** 72

### Profile Evolution ✅

- **Profile Attributes:** 210
- **Implicit Traits Inferred:** 122

---

## BetterMemory Enhancements

### Confidence Router (SwiftMem) 🚀

- **Queries Confidence-Routed:** 5/5 (100%)
- **Impact:** Skipped sufficiency LLM call on high-confidence retrievals

### Entity Extraction & Pre-filtering 🎯

- **Total Entities Extracted:** 188
- **Avg Entities per MemCell:** 1.9

### Soft-Delete Conflict Resolution 🗂️

- **Active Profile Facts:** 210
- **Deprecated (Soft-Deleted) Facts:** 0
- **Resolution Strategy:** recency_soft_delete

---

## Sample Retrieval

**Q:** What is the user's diet?
- **Latency:** 1041ms ⚡ (confidence-routed)
- **Episodes Retrieved:** 8
- **Query Entities:** diet
- **Answer:** The user has been considering changing their diet and is thinking of adopting a vegetarian diet, which they believe is healthier. They plan to cut out chicken, beef, and pork but might keep fish, esse...

**Q:** Where does the user work?
- **Latency:** 1038ms ⚡ (confidence-routed)
- **Episodes Retrieved:** 8
- **Query Entities:** work
- **Answer:** A user is considering switching to a new company due to their current startup not doing well and seeking stability. The user has started interviewing and has an upcoming interview at Google for a posi...


**Q:** Does the user have any health conditions?
- **Latency:** 1192ms ⚡ (confidence-routed)
- **Episodes Retrieved:** 8
- **Query Entities:** conditions, health
- **Answer:** The user made a delicious vegan curry the previous night and discussed its ingredients with the assistant. The user has been following a fully vegan diet for about 2 months and is taking B12 supplemen...

**Q:** Where is the user planning to travel?
- **Latency:** 1154ms ⚡ (confidence-routed)
- **Episodes Retrieved:** 8
- **Query Entities:** planning, travel
- **Answer:** The user's parents are visiting them next month and will be staying for about 2 weeks. They live in Florida, so the user does not get to see them often. The user plans to take their parents to see the...

---

## Performance Summary

- **Total Ingestion Time:** 1217.7 seconds
- **Avg Time per Conversation:** 12.18 seconds
- **Avg Retrieval Latency:** 1123 ms

## Comparison with Original Pipeline

| Metric | Original (100) | BetterMemory (100) |
|--------|----------------|--------------------|
| MemCells | 100 | 100 |
| MemScenes | 37 | 25 |
| Conflicts | 77 | 56 |
| Dedup Rate | 54.6% | 56.4% |
| Ingestion Time | 1631.8s | 1217.7s |
| Avg Retrieval Latency | 6312ms | 1123ms |
| Entities Extracted | N/A | 188 |
| Confidence Routing | N/A | 5/5 |
| Soft-Deleted Facts | N/A | 0 |
