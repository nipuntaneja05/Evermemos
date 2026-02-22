# Evermemos BetterMemory Scale Evaluation — 100 Conversations

**Generated:** 2026-02-22 17:08:53

## Summary Table

| Metric | Value |
|--------|-------|
| Total Conversations | 100 |
| Total Turns | 624 |
| MemCells Created | 100 |
| MemScenes Formed | 27 |
| Conflicts Detected | 79 |
| Deduplication Rate | 53.3% |
| Ingestion Time | 1741.1s |
| Avg Retrieval Latency | 1834ms |

---

## Core Metrics

### Memory Extraction

- **MemCells Created:** 100
- **MemScenes Formed:** 27 (semantic clusters)
- **Raw Facts Extracted:** 471
- **Unique Facts:** 220

### Conflict Detection ✅

- **Conflicts Detected:** 79
- **Status:** Working - system identifies contradictions between facts

### Deduplication ✅

- **Raw Facts:** 471
- **Unique Facts:** 220
- **Deduplication Rate:** 53.3%
- **Storage Saved:** ~53.3% reduction

### Foresight Tracking ✅

- **Foresights Created:** 133
- **Active Foresights:** 67
- **Expired Foresights:** 66

### Profile Evolution ✅

- **Profile Attributes:** 186
- **Implicit Traits Inferred:** 136

---

## BetterMemory Enhancements

### Confidence Router (SwiftMem) 🚀

- **Queries Confidence-Routed:** 5/5 (100%)
- **Impact:** Skipped sufficiency LLM call on high-confidence retrievals

### Entity Extraction & Pre-filtering 🎯

- **Total Entities Extracted:** 197
- **Avg Entities per MemCell:** 2.0

### Soft-Delete Conflict Resolution 🗂️

- **Active Profile Facts:** 186
- **Deprecated (Soft-Deleted) Facts:** 0
- **Resolution Strategy:** recency_soft_delete

---

## Sample Retrieval

**Q:** What is the user's diet?
- **Latency:** 2312ms ⚡ (confidence-routed)
- **Episodes Retrieved:** 8
- **Answer:** The user has been considering changing their diet and is thinking of adopting a vegetarian diet, believing it to be healthier. They plan to cut out chicken, beef, and pork but might keep fish, essenti...

**Q:** Where does the user work?
- **Latency:** 1922ms ⚡ (confidence-routed)
- **Episodes Retrieved:** 8
- **Answer:** A user is planning a trip to Japan in late March for 2 weeks to visit cities like Tokyo, Kyoto, Osaka, and possibly Hiroshima. The user is excited to experience Japan for the first time, especially to...

**Q:** What are the user's hobbies?
- **Latency:** 1640ms ⚡ (confidence-routed)
- **Episodes Retrieved:** 8
- **Answer:** The user's parents are visiting from Florida next month and will stay for about 2 weeks. The user plans to take them to see the city and possibly go on a day trip to the mountains. This visit is signi...

**Q:** Does the user have any health conditions?
- **Latency:** 1605ms ⚡ (confidence-routed)
- **Episodes Retrieved:** 8
- **Answer:** The user made a delicious vegan curry the previous night and discussed its ingredients with the assistant. The user has been following a fully vegan diet for about 2 months and has noticed an increase...

**Q:** Where is the user planning to travel?
- **Latency:** 1691ms ⚡ (confidence-routed)
- **Episodes Retrieved:** 8
- **Answer:** A user is planning a trip to Japan for the spring season, specifically to see the cherry blossoms. The trip is scheduled for late March and will last for 2 weeks. The user plans to visit several citie...

---

## Performance Summary

- **Total Ingestion Time:** 1741.1 seconds
- **Avg Time per Conversation:** 17.41 seconds
- **Avg Retrieval Latency:** 1834 ms

## Comparison with Original Pipeline

| Metric | Original (100) | BetterMemory (100) |
|--------|----------------|--------------------|
| MemCells | 100 | 100 |
| MemScenes | 37 | 27 |
| Conflicts | 77 | 79 |
| Dedup Rate | 54.6% | 53.3% |
| Ingestion Time | 1631.8s | 1741.1s |
| Avg Retrieval Latency | 6312ms | 1834ms |
| Entities Extracted | N/A | 197 |
| Confidence Routing | N/A | 5/5 |
| Soft-Deleted Facts | N/A | 0 |
