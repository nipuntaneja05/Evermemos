# Evermemos Scale Evaluation Results



## Summary Table

| Scale | Turns | MemCells | MemScenes | Conflicts | Dedup Rate | Ingestion Time | Retrieval Latency |
|-------|-------|----------|-----------|-----------|------------|----------------|-------------------|
| 100 | 624 | 100 | 37 | 77 | 54.6% | 1631.8s | 6312ms |

---

## Scale: 100 Conversations

### Metrics

- **Total Turns:** 624
- **MemCells Created:** 100
- **MemScenes Formed:** 37
- **Conflicts Detected:** 77
- **Raw Facts Extracted:** 467
- **Unique Facts:** 212
- **Deduplication Rate:** 54.6%
- **Profile Attributes:** 235
- **Implicit Traits:** 127
- **Ingestion Time:** 1631.83 seconds
- **Avg Retrieval Latency:** 6312 ms

### Sample Queries

**Q:** What is the user's diet?
- **Latency:** 11462ms
- **Episodes Retrieved:** 8
- **Answer:** The user had a great dining experience at a new restaurant called The Grill House downtown, where they enjoyed the best ribeye steak they've ever had. The user mentioned that they eat steak about once...

**Q:** Where does the user work?
- **Latency:** 3939ms
- **Episodes Retrieved:** 8
- **Answer:** The user was promoted to senior engineer and received a 20% raise. The promotion includes new responsibilities such as leading a team of developers and architecting new features. The user is looking f...

**Q:** What are the user's hobbies?
- **Latency:** 3538ms
- **Episodes Retrieved:** 8
- **Answer:** The user recently started learning to play the guitar, specifically on their grandfather's old acoustic guitar. They are currently learning simple chords like G, C, and D, with the goal of playing son...

**Q:** Does the user have any health conditions?
- **Latency:** 6371ms
- **Episodes Retrieved:** 8
- **Answer:** The user has been considering changing their diet and is planning to adopt a pescatarian approach, which involves cutting out meat like chicken, beef, and pork but possibly keeping fish. This decision...

**Q:** Where is the user planning to travel?
- **Latency:** 6248ms
- **Episodes Retrieved:** 8
- **Answer:** A user is planning a trip to Japan in late March for 2 weeks to experience the cherry blossoms. The user intends to visit Tokyo, Kyoto, Osaka, and possibly Hiroshima. This will be the user's first tim...
---

## Observations



