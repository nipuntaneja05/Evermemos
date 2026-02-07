"""
Evermemos - Interactive Demo and CLI

This module provides a demonstration of the Evermemos memory system
with sample conversations and queries.
"""

from datetime import datetime, timedelta
import json
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.syntax import Syntax

from .evermemos import Evermemos
from .models import DialogueTurn


console = Console()


# Sample conversations for testing
SAMPLE_CONVERSATIONS = [
    {
        "id": "conv_001",
        "transcript": """
User: I've decided to go vegan starting today. I'm really excited about this lifestyle change!
Assistant: That's wonderful! Going vegan can have great health and environmental benefits. What inspired this decision?
User: I watched a documentary about factory farming and it really opened my eyes. Plus, I want to lose some weight.
Assistant: Both are valid reasons. Would you like some tips for transitioning to a vegan diet?
User: Yes please! I'm currently 180 pounds and want to get down to 160.
Assistant: Great goal! I recommend starting with plant-based proteins like legumes, tofu, and tempeh. Also, make sure you're getting enough B12 and iron.
User: Thanks! I'll also be doing a 7-day detox starting next Monday to kickstart this journey.
Assistant: A detox can be a good reset. Just make sure you're still getting adequate nutrition during that week.
"""
    },
    {
        "id": "conv_002",
        "transcript": """
User: I need help planning my trip to Japan next month
Assistant: Exciting! Japan is a wonderful destination. How long will you be there and what are your main interests?
User: I'll be there for 2 weeks. I love technology, history, and food.
Assistant: Perfect mix! I'd suggest: Tokyo for tech (Akihabara), Kyoto for history (temples and shrines), and both cities have amazing food scenes.
User: Great! I should mention I'm based in San Francisco, so I'll be flying from SFO.
Assistant: Good to know. Direct flights to Tokyo Narita or Haneda are available from SFO, about 11 hours flight time.
User: Also, I'm a software engineer specializing in machine learning, so I'd love to visit some tech companies there.
Assistant: You might enjoy visiting the Google Tokyo office or attending tech meetups. There's also TeamLab for interactive digital art.
"""
    },
    {
        "id": "conv_003", 
        "transcript": """
User: My weight is now 175 pounds, down from 180 last week!
Assistant: Congratulations! That's 5 pounds in a week - great progress on your vegan journey!
User: Thanks! The detox was tough but I feel so much better now. I'm sticking with the vegan diet.
Assistant: I'm glad to hear the detox went well. How are you finding the meal planning?
User: It's getting easier. I've been cooking a lot more at home. My favorite is Thai curry with tofu.
Assistant: Thai curry is delicious and packed with vegetables. It's a great vegan staple!
User: I've also started running in the mornings, 3 miles every day.
Assistant: That's excellent! Combining diet changes with exercise will definitely help you reach your goal of 160 pounds.
"""
    }
]

SAMPLE_QUERIES = [
    "What are the user's dietary preferences and health goals?",
    "Where is the user planning to travel?",
    "What is the user's current weight and target weight?",
    "What is the user's profession?",
    "Is the user currently on any special diet or detox program?"
]


def print_header():
    """Print the Evermemos header."""
    header = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ███████╗██╗   ██╗███████╗██████╗ ███╗   ███╗███████╗███╗   ███╗ ║
║   ██╔════╝██║   ██║██╔════╝██╔══██╗████╗ ████║██╔════╝████╗ ████║ ║
║   █████╗  ██║   ██║█████╗  ██████╔╝██╔████╔██║█████╗  ██╔████╔██║ ║
║   ██╔══╝  ╚██╗ ██╔╝██╔══╝  ██╔══██╗██║╚██╔╝██║██╔══╝  ██║╚██╔╝██║ ║
║   ███████╗ ╚████╔╝ ███████╗██║  ██║██║ ╚═╝ ██║███████╗██║ ╚═╝ ██║ ║
║   ╚══════╝  ╚═══╝  ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝╚═╝     ╚═╝ ║
║                                                               ║
║   Advanced Memory System with Episodic Trace Formation        ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"""
    console.print(header, style="bold cyan")


def run_demo():
    """Run the full demonstration of Evermemos."""
    print_header()
    
    console.print("\n[bold green]Initializing Evermemos Memory System...[/bold green]\n")
    
    # Initialize the system
    memory = Evermemos(user_id="demo_user")
    
    # Show initial stats
    stats = memory.get_stats()
    console.print(Panel(
        f"MemCells: {stats['memcells_count']}\nMemScenes: {stats['memscenes_count']}",
        title="Initial Memory State"
    ))
    
    # Phase I & II: Ingest sample conversations
    console.print("\n[bold yellow]═══ Phase I & II: Ingesting Conversations ═══[/bold yellow]\n")
    
    for i, conv in enumerate(SAMPLE_CONVERSATIONS, 1):
        console.print(f"\n[cyan]Processing Conversation {i}: {conv['id']}[/cyan]")
        
        # Simulate time progression
        conv_time = datetime.now() - timedelta(days=len(SAMPLE_CONVERSATIONS) - i)
        
        result = memory.ingest_transcript(
            conv["transcript"],
            conversation_id=conv["id"],
            current_time=conv_time
        )
        
        if result["success"]:
            console.print(f"  ✓ MemCells created: {result['memcells_created']}")
            console.print(f"  ✓ New scenes: {result['new_scenes']}")
            console.print(f"  ✓ Updated scenes: {result['updated_scenes']}")
            
            if result["conflicts"]:
                console.print(f"  ⚠ Conflicts detected: {len(result['conflicts'])}")
                for conflict in result["conflicts"]:
                    console.print(f"    - {conflict.attribute}: {conflict.old_value} → {conflict.new_value}")
        else:
            console.print(f"  ✗ Error: {result.get('error', 'Unknown error')}")
    
    # Show updated stats
    stats = memory.get_stats()
    console.print(Panel(
        f"MemCells: {stats['memcells_count']}\nMemScenes: {stats['memscenes_count']}",
        title="Memory State After Ingestion",
        style="green"
    ))
    
    # Display MemScenes
    console.print("\n[bold yellow]═══ MemScenes Overview ═══[/bold yellow]\n")
    
    scenes = memory.get_all_memscenes()
    for scene in scenes:
        console.print(Panel(
            f"Theme: {scene.theme}\n\nSummary: {scene.summary[:200]}...\n\nMemCells: {len(scene.memcell_ids)}",
            title=f"MemScene: {scene.id[:8]}...",
            style="blue"
        ))
    
    # Display User Profile
    console.print("\n[bold yellow]═══ User Profile ═══[/bold yellow]\n")
    profile_summary = memory.get_profile_summary()
    console.print(Panel(profile_summary, title="Evolved User Profile", style="magenta"))
    
    # Phase III: Queries
    console.print("\n[bold yellow]═══ Phase III: Reconstructive Recollection ═══[/bold yellow]\n")
    
    for query in SAMPLE_QUERIES:
        console.print(f"\n[bold cyan]Query:[/bold cyan] {query}")
        
        # Get full recollection
        result = memory.query(query)
        
        # Display results
        console.print(f"  [dim]Iterations: {result['iterations']} | Episodes retrieved: {len(result['results'])}[/dim]")
        
        # Get answer
        answer = memory.answer(query)
        console.print(Panel(answer, title="Answer", style="green"))
        
        # Show active foresights if any
        if result["valid_foresights"]:
            foresight_text = "\n".join(f"• {f.content}" for f in result["valid_foresights"][:3])
            console.print(Panel(foresight_text, title="Active Foresights", style="yellow"))
    
    # Interactive mode
    console.print("\n[bold yellow]═══ Interactive Mode ═══[/bold yellow]")
    console.print("\nYou can now query the memory system.")
    console.print("Type 'quit' to exit, 'stats' for stats, 'profile' for user profile.\n")
    
    while True:
        try:
            user_input = input("\n[Query] > ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == 'quit':
                console.print("[yellow]Goodbye![/yellow]")
                break
            
            if user_input.lower() == 'stats':
                stats = memory.get_stats()
                console.print(Panel(json.dumps(stats, indent=2), title="System Stats"))
                continue
            
            if user_input.lower() == 'profile':
                console.print(Panel(memory.get_profile_summary(), title="User Profile"))
                continue
            
            if user_input.lower() == 'export':
                memory.export_memory_json("memory_export.json")
                continue
            
            # Process query
            answer = memory.answer(user_input)
            console.print(Panel(answer, title="Answer", style="green"))
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted. Goodbye![/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


def run_quick_test():
    """Run a quick test of the system."""
    console.print("[bold]Running quick test...[/bold]\n")
    
    memory = Evermemos(user_id="test_user")
    
    # Ingest one conversation
    result = memory.ingest_transcript(SAMPLE_CONVERSATIONS[0]["transcript"])
    
    console.print(f"Ingestion: {'✓ Success' if result['success'] else '✗ Failed'}")
    console.print(f"MemCells: {result['memcells_created']}")
    
    # Query
    answer = memory.answer("What dietary changes is the user making?")
    console.print(f"\nAnswer: {answer}")
    
    return result["success"]


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        run_quick_test()
    else:
        run_demo()
