# Evermemos BetterMemory Scale Evaluation — 300 Conversations

**Generated:** 2026-02-23 10:16:28

## Summary Table

| Metric | Value |
|--------|-------|
| Total Conversations | 300 |
| Total Turns | 1876 |
| MemCells Created | 300 |
| MemScenes Formed | 31 |
| Conflicts Detected | 718 |
| Deduplication Rate | 77.4% |
| Ingestion Time | 4081.7s |
| Avg Retrieval Latency | 1590ms |

---

## Core Metrics

### Memory Extraction

- **MemCells Created:** 300
- **MemScenes Formed:** 31 (semantic clusters)
- **Raw Facts Extracted:** 1402
- **Unique Facts:** 317

### Conflict Detection ✅

- **Conflicts Detected:** 718
- **Status:** Working - system identifies contradictions between facts

### Deduplication ✅

- **Raw Facts:** 1402
- **Unique Facts:** 317
- **Deduplication Rate:** 77.4%
- **Storage Saved:** ~77.4% reduction

### Foresight Tracking ✅

- **Foresights Created:** 392
- **Active Foresights:** 177
- **Expired Foresights:** 215

### Profile Evolution ✅

- **Profile Attributes:** 23
- **Implicit Traits Inferred:** 190

---

## BetterMemory Enhancements

### Confidence Router (SwiftMem) 🚀

- **Queries Confidence-Routed:** 5/5 (100%)
- **Impact:** Skipped sufficiency LLM call on high-confidence retrievals

### Entity Extraction & Pre-filtering 🎯

- **Total Entities Extracted:** 565
- **Avg Entities per MemCell:** 1.9

### Soft-Delete Conflict Resolution 🗂️

- **Active Profile Facts:** 23
- **Deprecated (Soft-Deleted) Facts:** 0
- **Resolution Strategy:** recency_soft_delete

---

## Sample Retrieval

**Q:** What is the user's diet or food preferences?
- **Latency:** 2530ms ⚡ (confidence-routed)
- **Episodes Retrieved:** 8
- **Query Entities:** food, diet, preferences
- **Answer:** The user has been considering changing their diet and is thinking of adopting a vegetarian diet, believing it to be healthier. They plan to cut out chicken, beef, and pork but might keep fish, essenti...

**Q:** Where does the user work and what is their job?
- **Latency:** 1956ms ⚡ (confidence-routed)
- **Episodes Retrieved:** 8
- **Query Entities:** work
- **Answer:** The user is moving in with their partner next month to a downtown apartment with two bedrooms, where they will both work from home sometimes. The apartment's rent is $2,400, which the user finds reaso...

**Q:** Tell me about the user's family.
- **Latency:** 1158ms ⚡ (confidence-routed)
- **Episodes Retrieved:** 8
- **Query Entities:** family
- **Answer:** The user's parents are visiting from Florida next month and will be staying for about 2 weeks. The user plans to take them to see the city and possibly go on a day trip to the mountains. This visit is...

**Q:** Does the user have any pets?
- **Latency:** 1155ms ⚡ (confidence-routed)
- **Episodes Retrieved:** 8
- **Query Entities:** pets
- **Answer:** The user made a delicious vegan curry the previous night, which included chickpeas, coconut milk, tomatoes, and lots of spices. The user has been fully vegan for about 2 months and has noticed an incr...

**Q:** What does the user do for exercise or fitness?
- **Latency:** 1151ms ⚡ (confidence-routed)
- **Episodes Retrieved:** 8
- **Query Entities:** fitness, exercise
- **Answer:** The user consulted a nutritionist who recommended increasing protein intake for muscle building. The user is focusing on eggs, Greek yogurt, chicken, and aims to consume 150g of protein per day. The u...

---

## Performance Summary

- **Total Ingestion Time:** 4081.7 seconds
- **Avg Time per Conversation:** 13.61 seconds
- **Avg Retrieval Latency:** 1590 ms

## Comparison with Original Pipeline

| Metric | Original (100) | BetterMemory (100) |
|--------|----------------|--------------------|
| MemCells | 100 | 300 |
| MemScenes | 37 | 31 |
| Conflicts | 77 | 718 |
| Dedup Rate | 54.6% | 77.4% |
| Ingestion Time | 1631.8s | 4081.7s |
| Avg Retrieval Latency | 6312ms | 1590ms |
| Entities Extracted | N/A | 565 |
| Confidence Routing | N/A | 5/5 |
| Soft-Deleted Facts | N/A | 0 |
