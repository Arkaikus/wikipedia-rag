#!/usr/bin/env python3
"""
Demo script for Phase 5: Complete RAG Pipeline

This script demonstrates the full RAG pipeline:
1. Fetching a Wikipedia page
2. Processing into chunks
3. Generating embeddings
4. Storing in ChromaDB
5. Answering questions using LLM + retrieval

Requirements:
- Docker running with ChromaDB: docker-compose up -d
- LMStudio running with a model loaded on port 1234

Run: python demo_phase5.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.services.rag_service import RAGService

console = Console()


def main():
    """Demo Phase 5: Complete RAG pipeline."""
    console.print("\n[bold blue]RAG Wikipedia Chatbot - Phase 5 Demo[/bold blue]")
    console.print("[dim]Complete RAG Pipeline with LMStudio[/dim]\n")

    # Test page and questions
    page_title = "Artificial Intelligence"
    test_questions = [
        "What is artificial intelligence?",
        "Who are the pioneers of AI?",
        "What are the main approaches to AI?",
    ]

    try:
        # ===== Initialize RAG Service =====
        console.print(Panel("[bold]Initializing RAG Service[/bold]"))

        console.print("\n[yellow]→ Initializing components...[/yellow]")
        rag_service = RAGService()
        console.print("  ✓ RAG service initialized")

        # Check LLM availability
        if not rag_service.llm.is_available():
            console.print("\n[bold red]⚠️  LMStudio not available![/bold red]")
            console.print("\n[yellow]Please ensure:[/yellow]")
            console.print("  1. LMStudio is running")
            console.print("  2. A model is loaded")
            console.print("  3. Server is started on http://localhost:1234")
            console.print("\nContinuing demo with retrieval only...\n")
            llm_available = False
        else:
            console.print("  ✓ LMStudio connected")
            llm_available = True

        # ===== Load Wikipedia Page =====
        console.print()
        console.print(Panel("[bold]Phase 1: Load Wikipedia Page[/bold]"))

        console.print(f"\n[yellow]→ Loading page: {page_title}...[/yellow]")
        page_info = rag_service.load_wikipedia_page(page_title)

        # Display page info
        info_table = Table(title="Page Information", show_header=True)
        info_table.add_column("Metric", style="cyan")
        info_table.add_column("Value", style="green")

        info_table.add_row("Title", page_info["title"])
        info_table.add_row("Word Count", f"{page_info['word_count']:,}")
        info_table.add_row("Sections", str(page_info["sections"]))
        info_table.add_row("Chunks Created", str(page_info["chunks"]))
        info_table.add_row("Collection", page_info["collection"])
        info_table.add_row("Stored in DB", str(page_info["collection_info"]["count"]))

        console.print()
        console.print(info_table)
        console.print("\n✓ Page loaded and indexed successfully!")

        # ===== Query the RAG System =====
        console.print()
        console.print(Panel("[bold]Phase 2: RAG Query & Response[/bold]"))

        for idx, question in enumerate(test_questions, 1):
            console.print(f"\n[bold cyan]Question {idx}:[/bold cyan] {question}")
            console.print()

            # Query the RAG system
            console.print("[dim]→ Generating query embedding...[/dim]")
            console.print("[dim]→ Searching vector database...[/dim]")

            result = rag_service.query(question, k=3, min_similarity=0.3)

            console.print(f"[dim]→ Retrieved {len(result.retrieved_chunks)} relevant chunks[/dim]")

            if llm_available:
                console.print("[dim]→ Generating LLM response...[/dim]")

            # Display results
            console.print()
            console.print("[bold green]Answer:[/bold green]")
            console.print(Panel(result.context, border_style="green"))

            # Show retrieved chunks
            if result.retrieved_chunks:
                console.print("\n[bold dim]Retrieved Context:[/bold dim]")
                for i, (chunk, score) in enumerate(
                    zip(result.retrieved_chunks, result.similarity_scores), 1
                ):
                    console.print(
                        f"  [{i}] {chunk.section_title or 'Introduction'} "
                        f"(similarity: {score:.3f})"
                    )
                    console.print(
                        f"      {chunk.content[:100]}..."
                        if len(chunk.content) > 100
                        else chunk.content
                    )
                console.print()

        # ===== Summary =====
        console.print(Panel("[bold green]Phase 5 Demo Complete![/bold green]"))

        # Summary table
        summary_table = Table(title="RAG Pipeline Summary", show_header=True)
        summary_table.add_column("Component", style="cyan")
        summary_table.add_column("Status", style="green")

        summary_table.add_row("Wikipedia Scraper", "✓ Working")
        summary_table.add_row("Document Processor", "✓ Working")
        summary_table.add_row("Embedding Service", "✓ Working")
        summary_table.add_row("ChromaDB", "✓ Working")
        summary_table.add_row(
            "LMStudio", "✓ Working" if llm_available else "⚠️  Not Available"
        )
        summary_table.add_row("RAG Pipeline", "✓ Complete")

        console.print()
        console.print(summary_table)
        console.print()

        # Interactive mode offer
        console.print("[bold]Try it yourself![/bold]")
        console.print("The page is still loaded. Ask a question:")
        console.print()

        try:
            while True:
                question = console.input("[bold cyan]Your question[/bold cyan] (or 'quit'): ")

                if question.lower() in ["quit", "exit", "q"]:
                    break

                if not question.strip():
                    continue

                console.print()
                result = rag_service.query(question, k=3, min_similarity=0.3)
                console.print("[bold green]Answer:[/bold green]")
                console.print(Panel(result.context, border_style="green"))
                console.print()

        except (KeyboardInterrupt, EOFError):
            console.print("\n\n[yellow]Exiting interactive mode...[/yellow]")

        # Cleanup
        console.print("\n[dim]Cleaning up...[/dim]")
        rag_service.clear_current_page()
        console.print("[green]Done![/green]\n")

    except KeyboardInterrupt:
        console.print("\n[yellow]Demo interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]")
        import traceback

        traceback.print_exc()

        console.print("\n[yellow]Troubleshooting:[/yellow]")
        console.print("1. ChromaDB: docker-compose up -d")
        console.print("2. LMStudio: Start server on http://localhost:1234")
        console.print("3. Load a model in LMStudio (e.g., Mistral 7B)")


if __name__ == "__main__":
    main()
