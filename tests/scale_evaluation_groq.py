"""
Groq-optimized Scale Evaluation for Evermemos.
Uses Groq API with rate limiting for faster processing.
"""

import json
import time
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from dataclasses import dataclass, field

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

console = Console()

# Rate limiting for Groq free tier (30 requests/minute)
REQUESTS_PER_MINUTE = 25  # Leave buffer
REQUEST_INTERVAL = 60.0 / REQUESTS_PER_MINUTE  # ~2.4 seconds between requests


@dataclass
class ScaleMetrics:
    scale: int
    total_turns: int = 0
    memcells_created: int = 0
    memscenes_formed: int = 0
    conflicts_detected: int = 0
    raw_facts_extracted: int = 0
    unique_facts: int = 0
    deduplication_rate: float = 0.0
    ingestion_time_seconds: float = 0.0
    avg_retrieval_latency_ms: float = 0.0
    sample_queries: List[Dict] = field(default_factory=list)


def load_conversations(filepath: Path) -> List[Dict]:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def count_total_turns(conversations: List[Dict]) -> int:
    return sum(len(conv["turns"]) for conv in conversations)


class RateLimiter:
    """Simple rate limiter for Groq API."""
    def __init__(self, requests_per_minute: int = 25):
        self.interval = 60.0 / requests_per_minute
        self.last_request = 0
    
    def wait(self):
        """Wait if needed to respect rate limit."""
        elapsed = time.time() - self.last_request
        if elapsed < self.interval:
            time.sleep(self.interval - elapsed)
        self.last_request = time.time()


def run_groq_evaluation(conversations: List[Dict], scale: int) -> ScaleMetrics:
    """Run evaluation using Groq with rate limiting."""
    # Force Groq provider
    from src.config import Config
    original_provider = Config.LLM_PROVIDER
    Config.LLM_PROVIDER = "groq"
    
    # Reimport to get fresh Groq client
    import importlib
    import src.llm_client as llm_module
    importlib.reload(llm_module)
    
    from src.evermemos import Evermemos
    
    metrics = ScaleMetrics(scale=scale)
    metrics.total_turns = count_total_turns(conversations)
    
    console.print(f"\n[bold cyan]Initializing Evermemos with GROQ for {scale} conversations...[/bold cyan]")
    evo = Evermemos(user_id=f"groq_scale_test_{scale}")
    
    # Clear previous data
    try:
        evo.clear_memory(confirm=True)
    except:
        pass
    
    rate_limiter = RateLimiter(REQUESTS_PER_MINUTE)
    all_raw_facts = []
    start_time = time.time()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        console=console
    ) as progress:
        task = progress.add_task(f"[GROQ] Ingesting {scale} conversations", total=len(conversations))
        
        for i, conv in enumerate(conversations):
            # Rate limit before each conversation (each has ~2-3 LLM calls)
            rate_limiter.wait()
            
            transcript = "\n".join([
                f"{turn['speaker']}: {turn['content']}"
                for turn in conv["turns"]
            ])
            
            conv_time = datetime.fromisoformat(conv["timestamp"])
            
            try:
                result = evo.ingest_transcript(
                    transcript=transcript,
                    conversation_id=conv["conversation_id"],
                    current_time=conv_time
                )
                
                if result and result.get("success"):
                    metrics.memcells_created += result.get("memcells_created", 0)
                    for mc in result.get("memcells", []):
                        if hasattr(mc, 'atomic_facts'):
                            all_raw_facts.extend(mc.atomic_facts)
                
                if result and "conflicts" in result:
                    conflicts = result["conflicts"]
                    if isinstance(conflicts, list):
                        metrics.conflicts_detected += len(conflicts)
                    elif isinstance(conflicts, int):
                        metrics.conflicts_detected += conflicts
                        
            except Exception as e:
                if "rate" in str(e).lower():
                    console.print(f"[yellow]Rate limited, waiting 60s...[/yellow]")
                    time.sleep(60)
                    continue
                else:
                    console.print(f"[red]Error: {e}[/red]")
            
            progress.update(task, advance=1)
            
            # Extra rate limit every 10 conversations
            if (i + 1) % 10 == 0:
                rate_limiter.wait()
    
    metrics.ingestion_time_seconds = time.time() - start_time
    metrics.memscenes_formed = len(evo.get_all_memscenes())
    
    # Calculate deduplication
    metrics.raw_facts_extracted = len(all_raw_facts)
    metrics.unique_facts = len(set(all_raw_facts))
    if metrics.raw_facts_extracted > 0:
        metrics.deduplication_rate = 1 - (metrics.unique_facts / metrics.raw_facts_extracted)
    
    # Test queries
    sample_queries = [
        "What is the user's diet?",
        "Where does the user work?",
        "What are the user's hobbies?"
    ]
    
    latencies = []
    for query in sample_queries:
        rate_limiter.wait()
        start = time.time()
        result = evo.query(query)
        latency_ms = (time.time() - start) * 1000
        latencies.append(latency_ms)
        
        metrics.sample_queries.append({
            "query": query,
            "answer": result.get("answer", "")[:150] + "..." if result and result.get("answer") else "No answer",
            "latency_ms": latency_ms
        })
    
    metrics.avg_retrieval_latency_ms = sum(latencies) / len(latencies) if latencies else 0
    
    # Restore original provider
    Config.LLM_PROVIDER = original_provider
    
    return metrics


def save_report(metrics: ScaleMetrics, output_dir: Path):
    report_path = output_dir / "groq_scale_evaluation_results.md"
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Evermemos Scale Evaluation (GROQ)\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Results\n\n")
        f.write(f"- **Scale:** {metrics.scale} conversations\n")
        f.write(f"- **Total Turns:** {metrics.total_turns}\n")
        f.write(f"- **MemCells Created:** {metrics.memcells_created}\n")
        f.write(f"- **MemScenes Formed:** {metrics.memscenes_formed}\n")
        f.write(f"- **Conflicts Detected:** {metrics.conflicts_detected}\n")
        f.write(f"- **Deduplication Rate:** {metrics.deduplication_rate:.1%}\n")
        f.write(f"- **Ingestion Time:** {metrics.ingestion_time_seconds:.1f}s\n")
        f.write(f"- **Avg Retrieval Latency:** {metrics.avg_retrieval_latency_ms:.0f}ms\n\n")
        
        f.write("## Sample Queries\n\n")
        for sq in metrics.sample_queries:
            f.write(f"**Q:** {sq['query']}\n")
            f.write(f"- Latency: {sq['latency_ms']:.0f}ms\n")
            f.write(f"- Answer: {sq['answer']}\n\n")
    
    console.print(f"\n[bold green]✓ Report saved:[/bold green] {report_path}")
    return report_path


def main():
    console.print(Panel.fit(
        "[bold magenta]EVERMEMOS SCALE EVALUATION (GROQ)[/bold magenta]\n"
        "Testing 300 conversations with rate limiting",
        border_style="magenta"
    ))
    
    data_dir = Path(__file__).parent.parent / "data" / "conversations"
    results_dir = Path(__file__).parent.parent / "results"
    results_dir.mkdir(exist_ok=True)
    
    # Load 300 conversations
    conv_file = data_dir / "conversations_300.json"
    if not conv_file.exists():
        console.print("[red]Error: conversations_300.json not found![/red]")
        return
    
    conversations = load_conversations(conv_file)
    console.print(f"[bold]Loaded {len(conversations)} conversations ({count_total_turns(conversations)} turns)[/bold]")
    
    # Run evaluation
    metrics = run_groq_evaluation(conversations, 300)
    
    # Display results
    console.print(f"\n[green]✓ GROQ Scale 300 complete:[/green]")
    console.print(f"  MemCells: {metrics.memcells_created} | MemScenes: {metrics.memscenes_formed}")
    console.print(f"  Conflicts: {metrics.conflicts_detected} | Dedup: {metrics.deduplication_rate:.1%}")
    console.print(f"  Time: {metrics.ingestion_time_seconds:.1f}s | Latency: {metrics.avg_retrieval_latency_ms:.0f}ms")
    
    save_report(metrics, results_dir)
    console.print("\n[bold green]✓ GROQ evaluation complete![/bold green]")


if __name__ == "__main__":
    main()
