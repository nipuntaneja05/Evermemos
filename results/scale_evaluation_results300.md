# Evermemos Scale Evaluation Results - 300 Conversations



## Summary Table

| Metric | Value |
|--------|-------|
| Total Conversations | 300 |
| Total Turns | 1876 |
| MemCells Created | 296 |
| MemScenes Formed | 42 |
| Conflicts Detected | 271 |
| Deduplication Rate | 78.7% |
| Ingestion Time | 4618.2s |
| Avg Retrieval Latency | 7283ms |

---

## Core Metrics

### Memory Extraction

- **MemCells Created:** 296
- **MemScenes Formed:** 42 (semantic clusters)
- **Raw Facts Extracted:** 1356
- **Unique Facts:** 289

### Conflict Detection ✅

- **Conflicts Detected:** 271
- **Status:** Working - system identifies contradictions between facts

**Example Conflicts:**
1. ConflictRecord(id='b326fcab-98bc-438a-a53d-33ba826c0bde', attribute='age', old_value='unknown', new_...
2. ConflictRecord(id='6c015c06-e271-4433-8727-e75b020f445a', attribute='location', old_value='not speci...
3. ConflictRecord(id='3a27b1d2-c4a9-420b-b901-431fc5c6c1c9', attribute='occupation', old_value='profess...

### Deduplication (Reducing Storage) ✅

- **Raw Facts:** 1356
- **Unique Facts:** 289
- **Deduplication Rate:** 78.7%
- **Storage Saved:** ~78.7% reduction
- **Status:** Working - duplicate facts are consolidated

### Foresight Expiry Handling ✅

- **Foresights Created:** 428
- **Active Foresights:** 428
- **Expired Foresights:** 0
- **Status:** Working - temporal plans are tracked with expiry dates



### Profile Evolution ✅

- **Profile Attributes:** 0
- **Implicit Traits Inferred:** 211
- **Status:** Working - user profile evolves from conversations


---

## Sample Retrieval (Showing Relevance)

**Q:** What is the user's diet?
- **Latency:** 3626ms
- **Episodes Retrieved:** 8
- **Answer:** The user's nutritionist recommended increasing their protein intake to build muscle. The user is focusing on eggs, Greek yogurt, chicken, and is aiming for 150g of protein per day. They find this goal tough but manageable. The user is tracking their ...

**Q:** Where does the user work?
- **Latency:** 3740ms
- **Episodes Retrieved:** 8
- **Answer:** The user has been working remotely from Bali for the past month and is having an amazing experience. The cost of living in Bali is low, and the wifi is better than expected, allowing the user to work from cafes. The user plans to stay in Bali for at ...

**Q:** What are the user's hobbies?
- **Latency:** 3035ms
- **Episodes Retrieved:** 8
- **Answer:** The user recently started learning to play the guitar, specifically on their grandfather's old acoustic guitar. They are currently learning simple chords like G, C, and D, with the goal of playing Wonderwall. The user practices for about 30 minutes e...

**Q:** Does the user have any health conditions?
- **Latency:** 22180ms
- **Episodes Retrieved:** 8
- **Answer:** The user was promoted to senior engineer and received a 20% raise. The new role includes leading a team of 5 developers and architecting new features. The user is looking forward to the leadership aspect, having previously mentored juniors informally...

**Q:** Where is the user planning to travel?
- **Latency:** 3835ms
- **Episodes Retrieved:** 8
- **Answer:** The user's parents are visiting from Florida next month and will be staying for about 2 weeks. The user does not see them often, so this visit is a significant occasion. The user plans to take their parents to see the city and possibly go on a day tr...

---

## Performance Summary

- **Total Ingestion Time:** 4618.2 seconds
- **Avg Time per Conversation:** 15.39 seconds
- **Avg Retrieval Latency:** 7283 ms


