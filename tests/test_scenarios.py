"""
Test Scenarios for Evermemos Memory System

Demonstrates:
1. Dietary preference changes (conflict handling)
2. Temporary health conditions (foresight expiry)
3. Job/location changes (profile evolution)
4. Timestamp-based retrieval differences
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.evermemos import Evermemos
from src.models import DialogueTurn

console = Console()


# =============================================================================
# TEST SCENARIO 1: Dietary Preference Changes (Conflict Handling)
# =============================================================================

DIETARY_CONVERSATIONS = [
    {
        "id": "diet_week1",
        "days_ago": 30,
        "transcript": """
User: I'm a dedicated meat eater. I have steak almost every night for dinner.
Assistant: That's a protein-rich diet! Do you have any favorite cuts or cooking methods?
User: I love ribeye, medium rare. I also eat a lot of chicken and fish.
Assistant: Variety in protein sources is good. Do you incorporate vegetables too?
User: Minimal vegetables honestly. Maybe some potatoes or corn occasionally.
"""
    },
    {
        "id": "diet_week2", 
        "days_ago": 21,
        "transcript": """
User: I've been reading about health and I'm thinking of reducing my meat intake.
Assistant: That's a thoughtful approach. Are you considering any specific dietary changes?
User: Maybe pescatarian? I'd still eat fish but cut out red meat and poultry.
Assistant: Pescatarian diets can be very healthy. Fish provides omega-3 fatty acids.
User: Yeah, I'm going to try it for a month starting next week.
"""
    },
    {
        "id": "diet_week3",
        "days_ago": 14,
        "transcript": """
User: I've officially gone pescatarian! It's been a week now.
Assistant: Congratulations on making the change! How are you feeling?
User: Really good actually. I'm eating more salmon and tuna now.
Assistant: That's great for heart health. Are you finding enough variety?
User: Yes, I've discovered I love shrimp and scallops too!
"""
    },
    {
        "id": "diet_week4",
        "days_ago": 3,
        "transcript": """
User: Big news - I've decided to go fully vegan!
Assistant: That's a significant change from pescatarian! What prompted this decision?
User: I watched a documentary about ocean sustainability. I can't support fishing anymore.
Assistant: That's a principled choice. Are you prepared for the nutritional changes?
User: Yes, I've been researching B12 supplements and plant proteins.
Assistant: Smart preparation. Legumes, tofu, and tempeh are excellent protein sources.
"""
    }
]


# =============================================================================
# TEST SCENARIO 2: Temporary Health Conditions (Foresight Expiry)
# =============================================================================

HEALTH_CONVERSATIONS = [
    {
        "id": "health_01",
        "days_ago": 20,
        "transcript": """
User: I just got diagnosed with a minor bacterial infection.
Assistant: I'm sorry to hear that. Did the doctor prescribe any treatment?
User: Yes, I'm on antibiotics for the next 10 days. Can't drink alcohol during that time.
Assistant: That's important to follow. Alcohol can interfere with antibiotic effectiveness.
User: I have a party next weekend but I'll just drink water.
"""
    },
    {
        "id": "health_02",
        "days_ago": 14,
        "transcript": """
User: I twisted my ankle playing basketball yesterday.
Assistant: Ouch! How severe is it?
User: The doctor said it's a mild sprain. I need to stay off it for 2 weeks.
Assistant: RICE protocol - rest, ice, compression, elevation. Are you using crutches?
User: Yes, and I have a follow-up appointment in 2 weeks.
"""
    },
    {
        "id": "health_03",
        "days_ago": 7,
        "transcript": """
User: I'm starting a 3-day juice cleanse tomorrow for detox.
Assistant: Juice cleanses can be intense. What's your plan?
User: Just fresh pressed juices, no solid food. It ends on Friday.
Assistant: Make sure to stay hydrated with water too. Listen to your body.
User: Will do! I've done this before and felt great after.
"""
    },
    {
        "id": "health_04",
        "days_ago": 1,
        "transcript": """
User: I'm getting my wisdom teeth removed tomorrow morning.
Assistant: That's a common procedure. Are you prepared for recovery?
User: Yes, stocked up on soft foods. The dentist said I'll need about 5 days to recover.
Assistant: Ice packs help with swelling. Avoid straws - the suction can cause dry socket.
User: Thanks for the tip! I'll be on pain medication for a few days too.
"""
    }
]


# =============================================================================
# TEST SCENARIO 3: Job/Location Changes (Profile Evolution)
# =============================================================================

CAREER_CONVERSATIONS = [
    {
        "id": "career_01",
        "days_ago": 60,
        "transcript": """
User: I'm a junior software developer at a small startup in Austin, Texas.
Assistant: Austin has a great tech scene! What kind of software do you work on?
User: Mostly frontend work with React. My salary is about $75,000.
Assistant: That's a solid starting salary for Austin. Do you enjoy the work?
User: It's okay, but I want to move into backend development eventually.
"""
    },
    {
        "id": "career_02",
        "days_ago": 30,
        "transcript": """
User: I got promoted to mid-level developer! And I'm moving to backend work.
Assistant: Congratulations! That's a great achievement. Any salary change?
User: Yes! I'm now making $95,000. I'm learning Python and PostgreSQL.
Assistant: Nice bump! Backend work opens up lots of interesting problems.
User: I'm excited. We're also thinking of moving to a bigger apartment.
"""
    },
    {
        "id": "career_03",
        "days_ago": 14,
        "transcript": """
User: I got a job offer from a FAANG company in San Francisco!
Assistant: That's amazing! Which company?
User: Meta! They're offering $180,000 base plus stock. I'm going to accept.
Assistant: Congratulations! When do you start?
User: In 3 weeks. I'm relocating to San Francisco next week.
"""
    },
    {
        "id": "career_04",
        "days_ago": 1,
        "transcript": """
User: I just finished my first week at Meta!
Assistant: Exciting! How's the new job treating you?
User: It's intense but amazing. I'm on the Instagram backend team.
Assistant: That's a high-impact team. How's San Francisco?
User: Love it! I found an apartment in the Mission District. $3,200/month though.
"""
    }
]


# =============================================================================
# TEST FUNCTIONS
# =============================================================================

def run_conflict_detection_test():
    """Test Scenario 1: Dietary preference changes with conflict detection."""
    console.print("\n[bold cyan]═══ TEST SCENARIO 1: Conflict Detection (Dietary Changes) ═══[/bold cyan]\n")
    
    memory = Evermemos(user_id="conflict_test_user")
    conflicts_found = []
    
    for conv in DIETARY_CONVERSATIONS:
        conv_time = datetime.now() - timedelta(days=conv["days_ago"])
        console.print(f"[yellow]Processing: {conv['id']} (from {conv['days_ago']} days ago)[/yellow]")
        
        result = memory.ingest_transcript(
            conv["transcript"],
            conversation_id=conv["id"],
            current_time=conv_time
        )
        
        if result["conflicts"]:
            for c in result["conflicts"]:
                conflicts_found.append({
                    "conversation": conv["id"],
                    "attribute": c.attribute,
                    "old_value": c.old_value,
                    "new_value": c.new_value
                })
                console.print(f"  [red]⚠ CONFLICT: {c.attribute}[/red]")
                console.print(f"    Old: {c.old_value}")
                console.print(f"    New: {c.new_value}")
    
    # Summary
    console.print("\n[bold]Conflict Summary:[/bold]")
    table = Table(title="Detected Dietary Preference Conflicts")
    table.add_column("Conversation")
    table.add_column("Attribute")
    table.add_column("Previous Value")
    table.add_column("New Value")
    
    for c in conflicts_found:
        table.add_row(c["conversation"], c["attribute"], c["old_value"][:30], c["new_value"][:30])
    
    console.print(table)
    
    # Query to verify current state
    console.print("\n[cyan]Query: What is the user's current diet?[/cyan]")
    answer = memory.answer("What is the user's current dietary preference?")
    console.print(Panel(answer, title="Answer", style="green"))
    
    return memory, conflicts_found


def run_foresight_expiry_test():
    """Test Scenario 2: Temporary health conditions with foresight expiry."""
    console.print("\n[bold cyan]═══ TEST SCENARIO 2: Foresight Expiry (Health Conditions) ═══[/bold cyan]\n")
    
    memory = Evermemos(user_id="foresight_test_user")
    
    for conv in HEALTH_CONVERSATIONS:
        conv_time = datetime.now() - timedelta(days=conv["days_ago"])
        console.print(f"[yellow]Processing: {conv['id']} (from {conv['days_ago']} days ago)[/yellow]")
        
        result = memory.ingest_transcript(
            conv["transcript"],
            conversation_id=conv["id"],
            current_time=conv_time
        )
        console.print(f"  MemCells: {result['memcells_created']}")
    
    # Query at different timestamps
    console.print("\n[bold]Testing Temporal Filtering:[/bold]")
    
    # Query 1: Ask about alcohol NOW (antibiotics should be expired)
    console.print("\n[cyan]Query NOW: Can the user drink alcohol?[/cyan]")
    result_now = memory.query("Can the user drink alcohol?", current_time=datetime.now())
    console.print(f"  Valid foresights: {len(result_now['valid_foresights'])}")
    answer_now = memory.answer("Can the user drink alcohol?")
    console.print(Panel(answer_now, title="Answer (Today)", style="green"))
    
    # Query 2: Ask about exercise NOW (ankle should be healed)
    console.print("\n[cyan]Query NOW: Can the user play basketball?[/cyan]")
    answer_exercise = memory.answer("Can the user exercise or play basketball?")
    console.print(Panel(answer_exercise, title="Answer (Today)", style="green"))
    
    # Query 3: Ask about eating (wisdom teeth - should still be recovering)
    console.print("\n[cyan]Query NOW: Can the user eat solid food?[/cyan]")
    answer_food = memory.answer("Can the user eat solid food?")
    console.print(Panel(answer_food, title="Answer (Today)", style="green"))
    
    return memory


def run_profile_evolution_test():
    """Test Scenario 3: Job/location changes with profile evolution."""
    console.print("\n[bold cyan]═══ TEST SCENARIO 3: Profile Evolution (Career Changes) ═══[/bold cyan]\n")
    
    memory = Evermemos(user_id="profile_test_user")
    
    for conv in CAREER_CONVERSATIONS:
        conv_time = datetime.now() - timedelta(days=conv["days_ago"])
        console.print(f"[yellow]Processing: {conv['id']} (from {conv['days_ago']} days ago)[/yellow]")
        
        result = memory.ingest_transcript(
            conv["transcript"],
            conversation_id=conv["id"],
            current_time=conv_time
        )
        
        if result["conflicts"]:
            for c in result["conflicts"]:
                console.print(f"  [magenta]Profile Update: {c.attribute}: {c.old_value[:20]}... → {c.new_value[:20]}...[/magenta]")
    
    # Show final profile
    console.print("\n[bold]Final User Profile:[/bold]")
    profile = memory.get_profile_summary()
    console.print(Panel(profile, title="Evolved Profile", style="magenta"))
    
    # Verify queries
    console.print("\n[cyan]Query: Where does the user work?[/cyan]")
    answer1 = memory.answer("Where does the user work and what is their role?")
    console.print(Panel(answer1, title="Current Job", style="green"))
    
    console.print("\n[cyan]Query: Where does the user live?[/cyan]")
    answer2 = memory.answer("Where does the user live?")
    console.print(Panel(answer2, title="Current Location", style="green"))
    
    console.print("\n[cyan]Query: What is the user's salary?[/cyan]")
    answer3 = memory.answer("What is the user's salary?")
    console.print(Panel(answer3, title="Current Salary", style="green"))
    
    return memory


def run_timestamp_retrieval_test():
    """Test Scenario 4: Retrieval differences based on query timestamp."""
    console.print("\n[bold cyan]═══ TEST SCENARIO 4: Timestamp-Based Retrieval ═══[/bold cyan]\n")
    
    memory = Evermemos(user_id="timestamp_test_user")
    
    # Ingest only dietary conversations (fewer API calls to avoid timeout)
    console.print("[yellow]Ingesting dietary conversations only...[/yellow]")
    for conv in DIETARY_CONVERSATIONS:
        conv_time = datetime.now() - timedelta(days=conv["days_ago"])
        memory.ingest_transcript(conv["transcript"], conversation_id=conv["id"], current_time=conv_time)
    
    console.print("\n[bold]Testing query at different timestamps:[/bold]")
    
    query = "What is the user's current diet?"
    
    # Query today (should return vegan)
    console.print(f"\n[cyan]Query today:[/cyan]")
    result_now = memory.query(query, current_time=datetime.now())
    console.print(f"  Episodes retrieved: {len(result_now['results'])}")
    answer_now = memory.answer(query)
    console.print(Panel(answer_now, title="Answer (Today)", style="green"))
    
    return memory


def run_all_tests():
    """Run all test scenarios."""
    console.print("[bold green]╔═══════════════════════════════════════════╗[/bold green]")
    console.print("[bold green]║     EVERMEMOS TEST SCENARIOS              ║[/bold green]")
    console.print("[bold green]╚═══════════════════════════════════════════╝[/bold green]")
    
    try:
        run_conflict_detection_test()
    except Exception as e:
        console.print(f"[red]Test 1 failed: {e}[/red]")
    
    try:
        run_foresight_expiry_test()
    except Exception as e:
        console.print(f"[red]Test 2 failed: {e}[/red]")
    
    try:
        run_profile_evolution_test()
    except Exception as e:
        console.print(f"[red]Test 3 failed: {e}[/red]")
    
    try:
        run_timestamp_retrieval_test()
    except Exception as e:
        console.print(f"[red]Test 4 failed: {e}[/red]")
    
    console.print("\n[bold green]All test scenarios completed![/bold green]")


if __name__ == "__main__":
    run_all_tests()
