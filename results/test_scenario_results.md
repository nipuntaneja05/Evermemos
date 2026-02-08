PS C:\Users\nipun\Desktop\Evermemos> python tests/test_scenarios.py
╔═══════════════════════════════════════
════╗
║     EVERMEMOS TEST SCENARIOS          
║
═══ TEST SCENARIO 1: Conflict Detection                                       
(Dietary Changes) ═══

Using Ollama (local) for LLM - NO RATE LIMITS! 🚀
✓ Ollama connected with model: qwen2.5:7b
Loading local embedding model: Alibaba-NLP/gte-Qwen2-1.5B-instruct...
Loading checkpoint shards: 100%|█| 2/2 
✓ Embedding model loaded
Processing: diet_week1 (from 30 days ago)
Processing: diet_week2 (from 21 days ago)
Processing: diet_week3 (from 14 days ago)
Processing: diet_week4 (from 3 days ago)

Conflict Summary:
          Detected Dietary Preference Conflicts          
┏━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Conversation ┃ Attribute ┃ Previous Value ┃ New Value ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
└──────────────┴───────────┴────────────────┴───────────┘

Query: What is the user's current diet?
╭────────────────────────────────── Answer ──────────────────────────────────╮
│ The user's current dietary preference, as of February 7, 2026, is a fully  │      
│ vegan lifestyle, having transitioned from being a pescatarian. They plan   │      
│ to incorporate plant-based proteins such as legumes, tofu, and tempeh into │      
│ their diet and will use B12 supplements due to their recent decision to    │      
│ adopt this dietary choice.                                                 │      
╰────────────────────────────────────────────────────────────────────────────╯      

═══ TEST SCENARIO 2: Foresight Expiry (Health Conditions) ═══

Processing: health_01 (from 20 days ago)
  MemCells: 1
Processing: health_02 (from 14 days ago)
  MemCells: 1
Processing: health_03 (from 7 days ago)
  MemCells: 1
Processing: health_04 (from 1 days ago)
  MemCells: 1

Testing Temporal Filtering:

Query NOW: Can the user drink alcohol?
  Valid foresights: 13
╭───────────────────────────────── Answer (Today) ─────────────────────────────────╮
│ No, the user cannot drink alcohol during the antibiotic treatment, as they have  │
│ been advised to avoid it to ensure the effectiveness of the antibiotics.         │
╰──────────────────────────────────────────────────────────────────────────────────╯

Query NOW: Can the user play basketball?
╭───────────────────────────────── Answer (Today) ─────────────────────────────────╮
│ The context does not provide specific information about whether the user can     │
│ exercise or play basketball after wisdom teeth removal surgery. Therefore, I     │
│ cannot provide a definitive answer. Typically, patients are advised to avoid     │
│ strenuous activities including playing basketball for at least 24 hours          │
│ post-surgery to prevent complications such as dry socket. However, this advice   │
│ should be confirmed with the dentist based on the user's specific recovery       │
│ status.                                                                          │
╰──────────────────────────────────────────────────────────────────────────────────╯

Query NOW: Can the user eat solid food?
╭───────────────────────────────── Answer (Today) ─────────────────────────────────╮
│ Based on the context, specifically from Episode 1 and Episode 3, the user will   │
│ not be eating solid food during their 3-day juice cleanse, which is scheduled to │
│ begin on February 8, 2026, and end on Friday, February 10, 2026.                 │
╰──────────────────────────────────────────────────────────────────────────────────╯

═══ TEST SCENARIO 3: Profile Evolution (Career Changes) ═══

Processing: career_01 (from 60 days ago)
Processing: career_02 (from 30 days ago)
  Profile Update: occupation: junior software deve... → mid-level developer...
  Profile Update: annual_income: $75,000... → $95,000...
Processing: career_03 (from 14 days ago)
  Profile Update: location: Austin, Texas... → San Francisco...
Processing: career_04 (from 1 days ago)
  Profile Update: occupation: mid-level developer... → backend developer at...

Final User Profile:
╭──────────────────────────────── Evolved Profile ─────────────────────────────────╮
│ User Profile (ID: profile_test_user)                                             │
│ ========================================                                         │
│                                                                                  │
│ EXPLICIT FACTS:                                                                  │
│   - occupation: backend developer at Meta                                        │
│   - location: San Francisco                                                      │
│   - annual_income: $95,000                                                       │
│   - current_technology_stack: React (frontend)                                   │
│   - current_skillset: learning Python and PostgreSQL                             │
│   - company: Meta                                                                │
│   - job start date: in three weeks                                               │
│   - relocation date: next week                                                   │
│   - rent: $3,200 per month                                                       │
│                                                                                  │
│ IMPLICIT TRAITS:                                                                 │
│   -  Considering a career transition to backend development (strength: 1.00)     │
│   -  Open to new challenges and willing to learn new technologies (strength:     │
│ 0.80)                                                                            │
│   -  willing to learn new skills for career advancement (strength: 0.90)         │
│   -  engaged in continuous learning and professional development (strength:      │
│ 0.80)                                                                            │
│   -  prefers to work at Meta (strength: 0.80)                                    │
│   -  plans and prepares for job transitions (strength: 1.00)                     │
│   -  prefers to live in the Mission District (strength: 0.80)                    │
│   -  adaptable and resilient due to handling an intense work environment         │
│ (strength: 0.70)                                                                 │
│                                                                                  │
│ CONFLICT HISTORY:                                                                │
│   - occupation: junior software developer -> mid-level developer (recency)       │
│   - annual_income: $75,000 -> $95,000 (recency)                                  │
│   - location: Austin, Texas -> San Francisco (recency)                           │
│   - occupation: mid-level developer -> backend developer at Meta (recency)       │
╰──────────────────────────────────────────────────────────────────────────────────╯

Query: Where does the user work?
╭────────────────────────────────── Current Job ───────────────────────────────────╮
│ The user works at Meta on the Instagram backend team.                            │
╰──────────────────────────────────────────────────────────────────────────────────╯

Query: Where does the user live?
╭──────────────────────────────── Current Location ────────────────────────────────╮
│ The provided context does not contain enough information to determine where the  │
│ user lives.                                                                      │
╰──────────────────────────────────────────────────────────────────────────────────╯

Query: What is the user's salary?
╭───────────────────────────────── Current Salary ─────────────────────────────────╮
│ The user's new salary is $95,000 per year.                                       │
╰──────────────────────────────────────────────────────────────────────────────────╯

═══ TEST SCENARIO 4: Timestamp-Based Retrieval ═══

Ingesting dietary conversations only...

Testing query at different timestamps:

Query today:
  Episodes retrieved: 8
╭───────────────────────────────── Answer (Today) ─────────────────────────────────╮
│ The user has adopted a pescatarian diet, consuming more salmon, tuna, shrimp,    │
│ and scallops since February 7, 2026.                                             │
╰──────────────────────────────────────────────────────────────────────────────────╯

All test scenarios completed!