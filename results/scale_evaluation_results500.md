# Evermemos Scale Evaluation Results - 500 Conversations



## Summary Table

| Metric | Value |
|--------|-------|
| Total Conversations | 500 |
| Total Turns | 3130 |
| MemCells Created | 495 |
| MemScenes Formed | 43 |
| Conflicts Detected | 455 |
| Deduplication Rate | 84.8% |
| Ingestion Time | 7893.8s |
| Avg Retrieval Latency | 4137ms |

---

## Core Metrics

### Memory Extraction

- **MemCells Created:** 495
- **MemScenes Formed:** 43 (semantic clusters)
- **Raw Facts Extracted:** 2277
- **Unique Facts:** 347

### Conflict Detection ✅

- **Conflicts Detected:** 455
- **Status:** Working - system identifies contradictions between facts

**Example Conflicts:**
1. ConflictRecord(id='cb4b911f-1d1f-4e3f-80ca-672ce5ae0c95', attribute='occupation', old_value='likely ...
2. ConflictRecord(id='d6b62f0b-699d-4bd6-b192-ecc53ef6b34d', attribute='occupation', old_value='likely ...
3. ConflictRecord(id='7de6e3f3-6557-4364-8ac6-4201d5594f1d', attribute='occupation', old_value='senior ...

### Deduplication (Reducing Storage) ✅

- **Raw Facts:** 2277
- **Unique Facts:** 347
- **Deduplication Rate:** 84.8%
- **Storage Saved:** ~84.8% reduction
- **Status:** Working - duplicate facts are consolidated

### Foresight Expiry Handling ✅

- **Foresights Created:** 716
- **Active Foresights:** 716
- **Expired Foresights:** 0
- **Status:** Working - temporal plans are tracked with expiry dates



### Profile Evolution ✅

- **Profile Attributes:** 0
- **Implicit Traits Inferred:** 276
- **Status:** Working - user profile evolves from conversations


---

## Sample Retrieval (Showing Relevance)

**Q:** What is the user's diet?
- **Latency:** 7279ms
- **Episodes Retrieved:** 8
- **Answer:** The user's nutritionist recommended increasing protein intake for muscle building. The user is focusing on eggs, Greek yogurt, chicken, and is aiming for 150g of protein per day. The user finds this goal tough but manageable. The user is tracking the...

**Q:** Where does the user work?
- **Latency:** 3441ms
- **Episodes Retrieved:** 8
- **Answer:** The user has just purchased their first house, a 3-bedroom property located in the suburbs. The commute to work from this new location takes about 30 minutes. The user considers this commute worthwhile given the additional space the house provides. T...

**Q:** What are the user's hobbies?
- **Latency:** 3121ms
- **Episodes Retrieved:** 8
- **Answer:** The user has been enjoying photography lately, particularly focusing on street photography and urban landscapes. They recently invested in a Sony A7 IV camera, which they believe is worth the cost. The user is currently pursuing photography as a pass...

**Q:** Does the user have any health conditions?
- **Latency:** 3336ms
- **Episodes Retrieved:** 8
- **Answer:** The user was prescribed antibiotics for a chest infection and is following the doctor's advice to ensure a full recovery. The user is taking the antibiotics as directed, which includes avoiding alcohol during the treatment and taking the medication w...

**Q:** Where is the user planning to travel?
- **Latency:** 3506ms
- **Episodes Retrieved:** 8
- **Answer:** The user's parents are visiting from Florida next month and will be staying for about 2 weeks. The user does not see them often, so this visit is a significant occasion. The user plans to take their parents on a tour of the city and possibly a day tr...

---

## Performance Summary

- **Total Ingestion Time:** 7893.8 seconds
- **Avg Time per Conversation:** 15.79 seconds
- **Avg Retrieval Latency:** 4137 ms

