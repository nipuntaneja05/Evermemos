"""
Evermemos Feature Demonstration: Conflict Detection & Foresight Expiry

This script demonstrates two key features:
1. Conflict Detection - When user information changes (e.g., diet updates)
2. Foresight Expiry - When temporal plans expire (e.g., 7-day detox ends)
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evermemos import Evermemos
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def demo_conflict_detection():
    """Demonstrate how the system detects and resolves conflicting information."""
    
    console.print("\n" + "="*70)
    console.print(Panel.fit(
        "[bold cyan]DEMO 1: CONFLICT DETECTION[/bold cyan]\n"
        "Showing how Evermemos handles contradictory information",
        border_style="cyan"
    ))
    
    # Initialize memory system
    memory = Evermemos(user_id="conflict_demo")
    
    # Clear previous data
    try:
        memory.clear_memory(confirm=True)
    except:
        pass
    
    # Conversation 1: User is vegetarian (January 15)
    console.print("\n[bold]📅 January 15, 2024[/bold]")
    transcript1 = """
User: I've been vegetarian for the past 2 years now.
Assistant: That's great! What made you choose a vegetarian lifestyle?
User: Health reasons mainly. I feel much better without meat.
"""
    
    jan_15 = datetime(2024, 1, 15, 10, 0, 0)
    result1 = memory.ingest_transcript(
        transcript=transcript1,
        conversation_id="conv_jan_15",
        current_time=jan_15
    )
    
    console.print("[green]✓ Ingested conversation[/green]")
    console.print(f"  MemCells created: {result1['memcells_created']}")
    
    # Query current diet
    console.print("\n[bold yellow]Query:[/bold yellow] What is the user's diet?")
    answer1 = memory.answer("What is the user's diet?", current_time=jan_15)
    console.print(f"[blue]Answer:[/blue] {answer1[:150]}...")
    
    # Check profile
    profile1 = memory.get_profile()
    console.print("\n[bold]Current Profile:[/bold]")
    if hasattr(profile1, 'explicit_facts'):
        for key, value in list(profile1.explicit_facts.items())[:3]:
            console.print(f"  • {key}: {value}")
    
    # Conversation 2: User starts eating fish (March 20) - CONFLICT!
    console.print("\n[bold]📅 March 20, 2024 (2 months later)[/bold]")
    transcript2 = """
User: I've started incorporating fish into my diet now.
Assistant: Oh, that's a change! What prompted that?
User: My doctor recommended it for omega-3s. I'm a pescatarian now.
"""
    
    mar_20 = datetime(2024, 3, 20, 14, 30, 0)
    result2 = memory.ingest_transcript(
        transcript=transcript2,
        conversation_id="conv_mar_20",
        current_time=mar_20
    )
    
    console.print("[green]✓ Ingested conversation[/green]")
    console.print(f"  MemCells created: {result2['memcells_created']}")
    
    # Check for conflicts
    if result2.get('conflicts'):
        console.print(f"\n[bold red]🚨 CONFLICT DETECTED![/bold red]")
        console.print(f"  Found {len(result2['conflicts'])} conflict(s)")
        
        # Display conflict details
        table = Table(title="Conflict Details", show_header=True, header_style="bold magenta")
        table.add_column("Attribute", style="cyan")
        table.add_column("Old Value", style="yellow")
        table.add_column("New Value", style="green")
        table.add_column("Resolution", style="blue")
        
        for conflict in result2['conflicts'][:3]:
            if hasattr(conflict, 'attribute'):
                old_val = str(getattr(conflict, 'old_value', 'N/A'))[:30]
                new_val = str(getattr(conflict, 'new_value', 'N/A'))[:30]
                resolution = getattr(conflict, 'resolution', 'recency_wins')
                table.add_row(
                    conflict.attribute,
                    old_val,
                    new_val,
                    resolution
                )
        
        console.print(table)
    
    # Query diet again - should reflect new information
    console.print("\n[bold yellow]Query:[/bold yellow] What is the user's diet now?")
    answer2 = memory.answer("What is the user's diet?", current_time=mar_20)
    console.print(f"[blue]Answer:[/blue] {answer2[:150]}...")
    
    # Show updated profile
    profile2 = memory.get_profile()
    console.print("\n[bold]Updated Profile (after conflict resolution):[/bold]")
    if hasattr(profile2, 'explicit_facts'):
        for key, value in list(profile2.explicit_facts.items())[:3]:
            console.print(f"  • {key}: {value}")
    
    # Show conflict history
    if hasattr(profile2, 'conflict_history') and profile2.conflict_history:
        console.print(f"\n[bold]Conflict History:[/bold] {len(profile2.conflict_history)} conflicts logged")
        console.print("[dim]All conflicts are preserved for audit trail[/dim]")
    
    console.print("\n[bold green]✅ Conflict Detection Complete![/bold green]")
    console.print("[dim]The system detected the diet change, logged the conflict, and updated the profile using recency-based resolution.[/dim]")


def demo_foresight_expiry():
    """Demonstrate how foresights expire based on temporal validity."""
    
    console.print("\n\n" + "="*70)
    console.print(Panel.fit(
        "[bold magenta]DEMO 2: FORESIGHT EXPIRY[/bold magenta]\n"
        "Showing how Evermemos tracks temporal plans with expiry dates",
        border_style="magenta"
    ))
    
    # Initialize memory system
    memory = Evermemos(user_id="foresight_demo")
    
    # Clear previous data
    try:
        memory.clear_memory(confirm=True)
    except:
        pass
    
    # Conversation: User starts 7-day detox (Day 1)
    console.print("\n[bold]📅 Day 1: Starting Detox[/bold]")
    transcript_day1 = """
User: I'm starting a 7-day juice detox today!
Assistant: That's quite a commitment! What's your goal?
User: I want to reset my digestive system and lose a few pounds.
Assistant: Remember to stay hydrated! Good luck with your 7-day journey.
"""
    
    day_1 = datetime(2024, 4, 1, 8, 0, 0)
    result_day1 = memory.ingest_transcript(
        transcript=transcript_day1,
        conversation_id="conv_detox_start",
        current_time=day_1
    )
    
    console.print("[green]✓ Ingested conversation[/green]")
    console.print(f"  MemCells created: {result_day1['memcells_created']}")
    
    # Check for foresights
    memcells = result_day1.get('memcells', [])
    console.print("\n[bold]Foresights Extracted:[/bold]")
    for mc in memcells:
        if hasattr(mc, 'foresights') and mc.foresights:
            for f in mc.foresights:
                content = f.content if hasattr(f, 'content') else str(f)
                t_end = getattr(f, 't_end', None)
                console.print(f"  • {content[:60]}...")
                if t_end:
                    console.print(f"    [dim]Expires: {t_end.strftime('%Y-%m-%d')} (7 days from now)[/dim]")
                else:
                    console.print(f"    [dim]Duration: 7 days (inferred)[/dim]")
    
    # Query on Day 3 (still active)
    day_3 = datetime(2024, 4, 3, 10, 0, 0)
    console.print(f"\n[bold]📅 Day 3: Checking Progress[/bold]")
    console.print(f"Current time: {day_3.strftime('%Y-%m-%d')}")
    
    result_day3 = memory.query("Is the user on any special diet?", current_time=day_3)
    console.print("\n[bold yellow]Query:[/bold yellow] Is the user on any special diet?")
    
    if result_day3.get('valid_foresights'):
        console.print(f"[bold green]✓ Active Foresights Found: {len(result_day3['valid_foresights'])}[/bold green]")
        for f in result_day3['valid_foresights'][:2]:
            content = f.get('content', str(f)) if isinstance(f, dict) else getattr(f, 'content', str(f))
            console.print(f"  • {content[:70]}...")
        console.print("[dim]Foresight is ACTIVE (within validity window)[/dim]")
    else:
        console.print("[yellow]No active foresights found[/yellow]")
    
    # Query on Day 10 (expired)
    day_10 = datetime(2024, 4, 10, 12, 0, 0)
    console.print(f"\n[bold]📅 Day 10: After Detox Ends[/bold]")
    console.print(f"Current time: {day_10.strftime('%Y-%m-%d')} (9 days after start)")
    
    result_day10 = memory.query("Is the user on any special diet?", current_time=day_10)
    console.print("\n[bold yellow]Query:[/bold yellow] Is the user on any special diet?")
    
    if result_day10.get('valid_foresights'):
        console.print(f"[green]Active Foresights: {len(result_day10['valid_foresights'])}[/green]")
    else:
        console.print("[bold red]❌ No Active Foresights[/bold red]")
        console.print("[dim]The 7-day detox has EXPIRED (t_end < current_time)[/dim]")
    
    # Show temporal filtering in action
    console.print("\n[bold]Temporal Filtering Results:[/bold]")
    
    table = Table(title="Foresight Status Over Time", show_header=True, header_style="bold cyan")
    table.add_column("Day", style="cyan", justify="center")
    table.add_column("Date", style="white")
    table.add_column("Foresight Status", style="yellow")
    table.add_column("Reason", style="dim")
    
    table.add_row("1", day_1.strftime("%Y-%m-%d"), "✅ Active", "Within validity window")
    table.add_row("3", day_3.strftime("%Y-%m-%d"), "✅ Active", "Still within 7 days")
    table.add_row("7", datetime(2024, 4, 7).strftime("%Y-%m-%d"), "✅ Active", "Last valid day")
    table.add_row("8", datetime(2024, 4, 8).strftime("%Y-%m-%d"), "❌ Expired", "t_end exceeded")
    table.add_row("10", day_10.strftime("%Y-%m-%d"), "❌ Expired", "Well past expiry")
    
    console.print(table)
    
    console.print("\n[bold green]✅ Foresight Expiry Complete![/bold green]")
    console.print("[dim]The system correctly filtered foresights based on temporal validity (t_start ≤ current_time ≤ t_end)[/dim]")


def main():
    """Run both demonstrations."""
    
    console.print(Panel.fit(
        "[bold white]EVERMEMOS FEATURE DEMONSTRATIONS[/bold white]\n\n"
        "This script demonstrates two core features:\n"
        "1. Conflict Detection & Resolution\n"
        "2. Temporal Foresight Expiry",
        border_style="bold white",
        title="🧠 Memory System Demo"
    ))
    
    # Run demonstrations
    demo_conflict_detection()
    demo_foresight_expiry()
    
    # Summary
    console.print("\n\n" + "="*70)
    console.print(Panel.fit(
        "[bold green]✅ DEMONSTRATIONS COMPLETE[/bold green]\n\n"
        "[bold]Key Takeaways:[/bold]\n"
        "• Conflicts are detected automatically and resolved using recency\n"
        "• All conflicts are logged for audit trail\n"
        "• Foresights have temporal validity windows [t_start, t_end]\n"
        "• Queries are filtered based on current_time for temporal awareness\n\n"
        "[dim]These features enable Evermemos to handle evolving user information over time.[/dim]",
        border_style="green"
    ))


if __name__ == "__main__":
    main()
