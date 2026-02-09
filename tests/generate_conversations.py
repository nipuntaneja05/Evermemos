"""
Generate synthetic conversations for scale evaluation.
Stores conversations in JSON files for human review.
"""

import json
import random
from pathlib import Path
from datetime import datetime, timedelta

# Categories of conversations to generate
CONVERSATION_TEMPLATES = {
    "diet": [
        {
            "turns": [
                {"speaker": "user", "content": "I've been thinking about changing my diet lately."},
                {"speaker": "assistant", "content": "That's great! What kind of changes are you considering?"},
                {"speaker": "user", "content": "I want to try going vegetarian. I've heard it's healthier."},
                {"speaker": "assistant", "content": "Vegetarian diets can be very nutritious! Are you planning to cut out all meat?"},
                {"speaker": "user", "content": "Yes, no more chicken, beef, or pork. Maybe I'll keep fish though."},
                {"speaker": "assistant", "content": "So more of a pescatarian approach! That's a great way to start."}
            ],
            "topic": "diet_change",
            "has_conflict_potential": True
        },
        {
            "turns": [
                {"speaker": "user", "content": "I made a delicious vegan curry last night."},
                {"speaker": "assistant", "content": "That sounds wonderful! What did you put in it?"},
                {"speaker": "user", "content": "Chickpeas, coconut milk, tomatoes, and lots of spices."},
                {"speaker": "assistant", "content": "Yum! Are you eating more plant-based meals these days?"},
                {"speaker": "user", "content": "Yes, I've been fully vegan for about 2 months now."},
                {"speaker": "assistant", "content": "That's fantastic progress! How are you feeling?"},
                {"speaker": "user", "content": "Much more energetic honestly. I'm taking B12 supplements too."}
            ],
            "topic": "vegan_lifestyle",
            "has_conflict_potential": True
        },
        {
            "turns": [
                {"speaker": "user", "content": "I had the most amazing steak last night at this new restaurant."},
                {"speaker": "assistant", "content": "Oh nice! Where did you go?"},
                {"speaker": "user", "content": "It's called The Grill House downtown. Best ribeye I've ever had."},
                {"speaker": "assistant", "content": "Sounds delicious! Do you eat steak often?"},
                {"speaker": "user", "content": "Maybe once a week. I love a good quality cut of beef."}
            ],
            "topic": "meat_eating",
            "has_conflict_potential": True
        },
        {
            "turns": [
                {"speaker": "user", "content": "My nutritionist suggested I eat more protein."},
                {"speaker": "assistant", "content": "That makes sense for building muscle. What protein sources are you focusing on?"},
                {"speaker": "user", "content": "Mostly eggs and Greek yogurt for breakfast. Chicken for lunch and dinner."},
                {"speaker": "assistant", "content": "Good choices! Are you tracking your protein intake?"},
                {"speaker": "user", "content": "Yes, aiming for 150g per day. It's tough but manageable."}
            ],
            "topic": "protein_focus",
            "has_conflict_potential": False
        }
    ],
    "health": [
        {
            "turns": [
                {"speaker": "user", "content": "I got prescribed antibiotics yesterday for a chest infection."},
                {"speaker": "assistant", "content": "I hope you feel better soon! How long is the course?"},
                {"speaker": "user", "content": "10 days. Doctor said to avoid alcohol during treatment."},
                {"speaker": "assistant", "content": "That's standard advice. Make sure to complete the full course!"},
                {"speaker": "user", "content": "Definitely. I'm also supposed to take them with food."}
            ],
            "topic": "antibiotics",
            "has_foresight": True,
            "foresight_days": 10
        },
        {
            "turns": [
                {"speaker": "user", "content": "I sprained my ankle playing soccer yesterday."},
                {"speaker": "assistant", "content": "Ouch! That's painful. Have you seen a doctor?"},
                {"speaker": "user", "content": "Yes, she said it's a grade 2 sprain. Need to rest for 2-3 weeks."},
                {"speaker": "assistant", "content": "That's frustrating but important for proper healing."},
                {"speaker": "user", "content": "I know. No running or jumping until it heals completely."}
            ],
            "topic": "ankle_sprain",
            "has_foresight": True,
            "foresight_days": 21
        },
        {
            "turns": [
                {"speaker": "user", "content": "I just found out I'm allergic to shellfish."},
                {"speaker": "assistant", "content": "Oh no! How did you discover that?"},
                {"speaker": "user", "content": "Had a reaction after eating shrimp. Had to go to urgent care."},
                {"speaker": "assistant", "content": "That must have been scary! Do you have an EpiPen now?"},
                {"speaker": "user", "content": "Yes, doctor prescribed one. I need to carry it everywhere."},
                {"speaker": "assistant", "content": "That's very important. Will you need to avoid all shellfish?"},
                {"speaker": "user", "content": "Yes, crab, lobster, shrimp - all of it. Forever, apparently."}
            ],
            "topic": "shellfish_allergy",
            "has_foresight": False
        },
        {
            "turns": [
                {"speaker": "user", "content": "Starting a 5-day juice cleanse tomorrow."},
                {"speaker": "assistant", "content": "That's a commitment! What made you decide to do it?"},
                {"speaker": "user", "content": "Want to reset after the holidays. No solid food for 5 days."},
                {"speaker": "assistant", "content": "Make sure you're getting enough calories from the juices!"},
                {"speaker": "user", "content": "I have a plan - green juices, fruit juices, and some vegetable broth."}
            ],
            "topic": "juice_cleanse",
            "has_foresight": True,
            "foresight_days": 5
        }
    ],
    "career": [
        {
            "turns": [
                {"speaker": "user", "content": "I got promoted to senior engineer today!"},
                {"speaker": "assistant", "content": "Congratulations! That's a huge accomplishment!"},
                {"speaker": "user", "content": "Thanks! It comes with a 20% raise too."},
                {"speaker": "assistant", "content": "Well deserved! What will your new responsibilities include?"},
                {"speaker": "user", "content": "Leading a team of 5 developers and architecting new features."},
                {"speaker": "assistant", "content": "That's exciting! Are you looking forward to the leadership aspect?"},
                {"speaker": "user", "content": "Definitely. I've been mentoring juniors informally anyway."}
            ],
            "topic": "promotion",
            "has_conflict_potential": True
        },
        {
            "turns": [
                {"speaker": "user", "content": "I'm thinking about switching to a new company."},
                {"speaker": "assistant", "content": "What's prompting the change?"},
                {"speaker": "user", "content": "The startup I'm at is not doing well. Might need to look for stability."},
                {"speaker": "assistant", "content": "That makes sense. Have you started interviewing?"},
                {"speaker": "user", "content": "Yes, I have an interview at Google next week."},
                {"speaker": "assistant", "content": "Google! That's amazing. What team?"},
                {"speaker": "user", "content": "YouTube backend engineering. Really excited about it."}
            ],
            "topic": "job_search",
            "has_conflict_potential": True
        },
        {
            "turns": [
                {"speaker": "user", "content": "I accepted the offer from Meta!"},
                {"speaker": "assistant", "content": "Congratulations! When do you start?"},
                {"speaker": "user", "content": "In 3 weeks. I'm relocating to Menlo Park."},
                {"speaker": "assistant", "content": "That's a big move! Are you excited?"},
                {"speaker": "user", "content": "Very! My salary will be $180,000 plus stock options."},
                {"speaker": "assistant", "content": "That's a great package! Will you be working on Instagram or Facebook?"},
                {"speaker": "user", "content": "Instagram Reels team. Really cutting-edge stuff."}
            ],
            "topic": "new_job",
            "has_conflict_potential": True
        },
        {
            "turns": [
                {"speaker": "user", "content": "I'm learning Python for my work."},
                {"speaker": "assistant", "content": "Great choice! Python is very versatile."},
                {"speaker": "user", "content": "My company is transitioning some projects to Python."},
                {"speaker": "assistant", "content": "What were you using before?"},
                {"speaker": "user", "content": "Mostly Java. But Python is better for our ML initiatives."}
            ],
            "topic": "learning_python",
            "has_conflict_potential": False
        }
    ],
    "hobbies": [
        {
            "turns": [
                {"speaker": "user", "content": "I just started learning guitar last month."},
                {"speaker": "assistant", "content": "That's awesome! Acoustic or electric?"},
                {"speaker": "user", "content": "Acoustic. I'm learning on my grandfather's old guitar."},
                {"speaker": "assistant", "content": "That's so special! What songs are you learning?"},
                {"speaker": "user", "content": "Starting with simple chords - G, C, D. Trying to play Wonderwall."},
                {"speaker": "assistant", "content": "Classic beginner song! How often do you practice?"},
                {"speaker": "user", "content": "About 30 minutes every day. Fingers are still sore though!"}
            ],
            "topic": "guitar",
            "has_conflict_potential": False
        },
        {
            "turns": [
                {"speaker": "user", "content": "I ran my first 5K this weekend."},
                {"speaker": "assistant", "content": "Congratulations! How did it go?"},
                {"speaker": "user", "content": "Finished in 28 minutes. I'm super proud!"},
                {"speaker": "assistant", "content": "That's a great time for a first 5K! Will you do more races?"},
                {"speaker": "user", "content": "Yes! Already signed up for a 10K in 3 months."}
            ],
            "topic": "running",
            "has_conflict_potential": False
        },
        {
            "turns": [
                {"speaker": "user", "content": "I've been really into photography lately."},
                {"speaker": "assistant", "content": "Nice! What do you like to photograph?"},
                {"speaker": "user", "content": "Mostly street photography and urban landscapes."},
                {"speaker": "assistant", "content": "Do you use a DSLR or phone camera?"},
                {"speaker": "user", "content": "Just got a Sony A7 IV. It's an investment but worth it."},
                {"speaker": "assistant", "content": "That's a serious camera! Are you thinking of doing it professionally?"},
                {"speaker": "user", "content": "Maybe someday. For now it's just a passion project."}
            ],
            "topic": "photography",
            "has_conflict_potential": False
        },
        {
            "turns": [
                {"speaker": "user", "content": "I'm training for a marathon next year."},
                {"speaker": "assistant", "content": "Wow! That's a big goal. Which marathon?"},
                {"speaker": "user", "content": "The Chicago Marathon in October."},
                {"speaker": "assistant", "content": "Great choice! What's your training plan?"},
                {"speaker": "user", "content": "Running 50 miles a week, gradually increasing to 70."},
                {"speaker": "assistant", "content": "That's serious mileage! What's your goal time?"},
                {"speaker": "user", "content": "Hoping to finish under 4 hours. We'll see!"}
            ],
            "topic": "marathon_training",
            "has_conflict_potential": False
        }
    ],
    "relationships": [
        {
            "turns": [
                {"speaker": "user", "content": "My sister is getting married in June!"},
                {"speaker": "assistant", "content": "How exciting! Are you in the wedding party?"},
                {"speaker": "user", "content": "Yes, I'm the maid of honor. Lots of planning to do."},
                {"speaker": "assistant", "content": "That's a big responsibility! Have you started planning the bachelorette?"},
                {"speaker": "user", "content": "We're thinking Nashville for a weekend trip."}
            ],
            "topic": "sister_wedding",
            "has_foresight": True,
            "foresight_days": 120
        },
        {
            "turns": [
                {"speaker": "user", "content": "I adopted a puppy yesterday!"},
                {"speaker": "assistant", "content": "Aww! What kind of dog?"},
                {"speaker": "user", "content": "A golden retriever mix. She's 3 months old."},
                {"speaker": "assistant", "content": "How adorable! What did you name her?"},
                {"speaker": "user", "content": "Luna. She's already stolen my heart."},
                {"speaker": "assistant", "content": "Great name! How's she adjusting to her new home?"},
                {"speaker": "user", "content": "Adjusting well! Though she chewed up my favorite shoe already."}
            ],
            "topic": "new_puppy",
            "has_conflict_potential": False
        },
        {
            "turns": [
                {"speaker": "user", "content": "My parents are visiting next month."},
                {"speaker": "assistant", "content": "That's nice! How long will they stay?"},
                {"speaker": "user", "content": "About 2 weeks. They live in Florida so I don't see them often."},
                {"speaker": "assistant", "content": "Two weeks is a good visit! Any plans?"},
                {"speaker": "user", "content": "Taking them to see the city, maybe a day trip to the mountains."}
            ],
            "topic": "parents_visiting",
            "has_foresight": True,
            "foresight_days": 30
        },
        {
            "turns": [
                {"speaker": "user", "content": "I'm moving in with my partner next month."},
                {"speaker": "assistant", "content": "That's a big step! Are you excited?"},
                {"speaker": "user", "content": "Very! We found a great apartment with two bedrooms."},
                {"speaker": "assistant", "content": "Two bedrooms - is one for an office?"},
                {"speaker": "user", "content": "Yes, we both work from home sometimes. Plus rent is $2,400."},
                {"speaker": "assistant", "content": "That's reasonable! What area?"},
                {"speaker": "user", "content": "Downtown, walking distance to everything."}
            ],
            "topic": "moving_in_together",
            "has_conflict_potential": True
        }
    ],
    "travel": [
        {
            "turns": [
                {"speaker": "user", "content": "I'm planning a trip to Japan next spring."},
                {"speaker": "assistant", "content": "Japan in spring! Cherry blossoms?"},
                {"speaker": "user", "content": "Exactly! Planning for late March, 2 weeks."},
                {"speaker": "assistant", "content": "Which cities will you visit?"},
                {"speaker": "user", "content": "Tokyo, Kyoto, Osaka, and maybe Hiroshima."},
                {"speaker": "assistant", "content": "Sounds amazing! Have you been to Japan before?"},
                {"speaker": "user", "content": "No, it's my first time. So excited to try authentic ramen!"}
            ],
            "topic": "japan_trip",
            "has_foresight": True,
            "foresight_days": 90
        },
        {
            "turns": [
                {"speaker": "user", "content": "Just booked flights to Barcelona for next month!"},
                {"speaker": "assistant", "content": "Fun! Is this a vacation or work?"},
                {"speaker": "user", "content": "Vacation! 5 days exploring the city."},
                {"speaker": "assistant", "content": "Have you been to Spain before?"},
                {"speaker": "user", "content": "Yes, Madrid last year. But Barcelona is supposed to be different."},
                {"speaker": "assistant", "content": "The architecture there is incredible! Visiting any Gaudi sites?"},
                {"speaker": "user", "content": "Definitely La Sagrada Familia and Park Güell!"}
            ],
            "topic": "barcelona_trip",
            "has_foresight": True,
            "foresight_days": 35
        },
        {
            "turns": [
                {"speaker": "user", "content": "I've been working remotely from Bali for the past month."},
                {"speaker": "assistant", "content": "That sounds incredible! How's the experience?"},
                {"speaker": "user", "content": "Amazing! Cost of living is so low here."},
                {"speaker": "assistant", "content": "How's the wifi for work?"},
                {"speaker": "user", "content": "Better than I expected! I work from cafes mostly."},
                {"speaker": "assistant", "content": "Are you planning to stay longer?"},
                {"speaker": "user", "content": "Yes, at least 2 more months. Maybe longer!"}
            ],
            "topic": "digital_nomad_bali",
            "has_conflict_potential": True
        }
    ],
    "finance": [
        {
            "turns": [
                {"speaker": "user", "content": "I just opened a Roth IRA."},
                {"speaker": "assistant", "content": "Smart move! What made you decide to start?"},
                {"speaker": "user", "content": "Realized I wasn't saving enough for retirement."},
                {"speaker": "assistant", "content": "What are you investing in?"},
                {"speaker": "user", "content": "Mostly index funds. S&P 500 and total market."},
                {"speaker": "assistant", "content": "Low cost and diversified! Are you maxing it out?"},
                {"speaker": "user", "content": "Trying to! That's $6,500 this year."}
            ],
            "topic": "roth_ira",
            "has_conflict_potential": False
        },
        {
            "turns": [
                {"speaker": "user", "content": "I'm trying to pay off my student loans faster."},
                {"speaker": "assistant", "content": "How much do you have left?"},
                {"speaker": "user", "content": "About $35,000. It's been hanging over me for years."},
                {"speaker": "assistant", "content": "What's your strategy?"},
                {"speaker": "user", "content": "Throwing an extra $500/month at it. Should be done in 3 years."},
                {"speaker": "assistant", "content": "That's great discipline! What's the interest rate?"},
                {"speaker": "user", "content": "About 5.5%. Not terrible but still annoying."}
            ],
            "topic": "student_loans",
            "has_conflict_potential": False
        },
        {
            "turns": [
                {"speaker": "user", "content": "Just bought my first house!"},
                {"speaker": "assistant", "content": "Congratulations! That's a huge milestone!"},
                {"speaker": "user", "content": "Thanks! A 3-bedroom in the suburbs."},
                {"speaker": "assistant", "content": "How's the commute to work?"},
                {"speaker": "user", "content": "About 30 minutes. Worth it for the space."},
                {"speaker": "assistant", "content": "What was the purchase price if you don't mind me asking?"},
                {"speaker": "user", "content": "We paid $450,000. Mortgage is about $2,800/month."}
            ],
            "topic": "house_purchase",
            "has_conflict_potential": True
        }
    ]
}

def generate_conversation(template: dict, base_time: datetime, conversation_id: int) -> dict:
    """Generate a single conversation from a template with some variation."""
    turns = []
    for i, turn in enumerate(template["turns"]):
        turns.append({
            "turn_id": i + 1,
            "speaker": turn["speaker"],
            "content": turn["content"],
            "timestamp": (base_time + timedelta(minutes=i * 2)).isoformat()
        })
    
    return {
        "conversation_id": f"conv_{conversation_id:04d}",
        "timestamp": base_time.isoformat(),
        "topic": template.get("topic", "general"),
        "has_conflict_potential": template.get("has_conflict_potential", False),
        "has_foresight": template.get("has_foresight", False),
        "foresight_days": template.get("foresight_days", None),
        "turns": turns,
        "metadata": {
            "category": None,  # Will be set below
            "generated_at": datetime.now().isoformat()
        }
    }

def generate_all_conversations(count: int, output_dir: Path) -> list:
    """Generate 'count' conversations and save to files."""
    conversations = []
    base_time = datetime.now() - timedelta(days=90)  # Start 90 days ago
    
    # Flatten all templates
    all_templates = []
    for category, templates in CONVERSATION_TEMPLATES.items():
        for template in templates:
            all_templates.append((category, template))
    
    for i in range(count):
        # Select a template (cycle through all)
        category, template = all_templates[i % len(all_templates)]
        
        # Generate with slightly varied timestamp
        time_offset = timedelta(days=random.randint(0, 90), hours=random.randint(0, 23))
        conv_time = base_time + time_offset
        
        conv = generate_conversation(template, conv_time, i + 1)
        conv["metadata"]["category"] = category
        conversations.append(conv)
    
    # Sort by timestamp
    conversations.sort(key=lambda x: x["timestamp"])
    
    # Save to file
    output_file = output_dir / f"conversations_{count}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(conversations, f, indent=2, ensure_ascii=False)
    
    print(f"Generated {count} conversations -> {output_file}")
    return conversations

def main():
    """Generate conversation files for different scales."""
    output_dir = Path(__file__).parent.parent / "data" / "conversations"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate for each scale
    for count in [100, 200, 300, 400, 500]:
        generate_all_conversations(count, output_dir)
    
    print("\n✓ All conversation files generated!")
    print(f"  Location: {output_dir}")

if __name__ == "__main__":
    main()
