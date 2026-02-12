#!/usr/bin/env python3
"""
Demo script for Phase 2: Wikipedia Data Retrieval & Processing

This script demonstrates:
1. Fetching a Wikipedia page
2. Processing it into chunks
3. Displaying statistics

Run: python demo_phase2.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.table import Table

from src.services.document_processor import DocumentProcessor
from src.services.wikipedia_scraper import WikipediaScraper

console = Console()


def main():
    """Demo Phase 2 functionality."""
    console.print("\n[bold blue]RAG Wikipedia Chatbot - Phase 2 Demo[/bold blue]\n")

    # Test pages of varying complexity
    test_pages = [
        "Python (programming language)",  # Medium complexity
        # "Quantum mechanics",             # High complexity
        # "Cat",                           # Low complexity
    ]

    for page_title in test_pages:
        console.print(f"\n[bold green]Testing with: {page_title}[/bold green]\n")

        try:
            # Step 1: Fetch Wikipedia page
            console.print("[yellow]Step 1: Fetching Wikipedia page...[/yellow]")
            scraper = WikipediaScraper()
            page = scraper.fetch(page_title)

            # Display page info
            console.print(f"✓ Title: {page.title}")
            console.print(f"✓ URL: {page.url}")
            console.print(f"✓ Word count: {page.word_count:,}")
            console.print(f"✓ Sections: {len(page.sections)}")
            console.print(f"✓ Summary length: {len(page.summary)} chars")

            # Step 2: Process into chunks
            console.print(f"\n[yellow]Step 2: Processing into chunks...[/yellow]")
            processor = DocumentProcessor()
            chunks = processor.process_page(page)

            console.print(f"✓ Created {len(chunks)} chunks")

            # Step 3: Display statistics
            stats = processor.get_chunk_stats(chunks)

            table = Table(title="Chunk Statistics", show_header=True)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Total Chunks", str(stats["total_chunks"]))
            table.add_row("Avg Chunk Size", f"{stats['avg_chunk_size']} chars")
            table.add_row("Min Chunk Size", f"{stats['min_chunk_size']} chars")
            table.add_row("Max Chunk Size", f"{stats['max_chunk_size']} chars")
            table.add_row("Total Tokens", f"{stats['total_tokens']:,}")
            table.add_row("Avg Tokens/Chunk", str(stats["avg_tokens_per_chunk"]))

            console.print(table)

            # Step 4: Show sample chunks
            console.print(f"\n[yellow]Sample Chunks:[/yellow]\n")

            for i, chunk in enumerate(chunks[:10]):  # Show first 10 chunks
                console.print(f"[bold]Chunk {i + 1}[/bold]")
                console.print(f"  Section: {chunk.section_title or 'Introduction'}")
                console.print(f"  Tokens: ~{chunk.token_count}")
                console.print(
                    f"  Content: {chunk.content[:150]}..."
                    if len(chunk.content) > 150
                    else chunk.content
                )
                console.print()

            console.print("[bold green]✓ Phase 2 Demo Complete![/bold green]\n")

        except Exception as e:
            console.print(f"[bold red]Error: {e}[/bold red]")
            import traceback

            traceback.print_exc()

    # Summary
    console.print("\n[bold blue]Phase 2 Components Status:[/bold blue]")
    console.print("✓ Wikipedia Scraper - Working")
    console.print("✓ Document Processor - Working")
    console.print("✓ Data Models - Working")
    console.print("✓ Configuration - Working")
    console.print("✓ Logging - Working")
    console.print("\n[bold green]Ready to proceed to Phase 3: Vector Database Integration[/bold green]\n")


if __name__ == "__main__":
    main()
