#!/usr/bin/env python3
"""
Demo script for Phase 3: Vector Database Integration & Embeddings

This script demonstrates:
1. Fetching a Wikipedia page
2. Processing into chunks
3. Generating embeddings
4. Storing in ChromaDB
5. Performing similarity search

Requirements:
- Docker running with ChromaDB: docker-compose up -d

Run: python demo_phase3.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.adapters.chroma_adapter import ChromaAdapter
from src.services.document_processor import DocumentProcessor
from src.services.embedding_service import EmbeddingService
from src.services.wikipedia_scraper import WikipediaScraper

console = Console()


def main():
    """Demo Phase 3 functionality."""
    console.print("\n[bold blue]RAG Wikipedia Chatbot - Phase 3 Demo[/bold blue]")
    console.print("[dim]Vector Database Integration & Embeddings[/dim]\n")

    # Test page
    page_title = "Python (programming language)"

    try:
        # ===== Phase 2: Fetch and Process (Review) =====
        console.print(Panel("[bold]Phase 2 Review: Fetch & Process[/bold]"))

        console.print("\n[yellow]→ Fetching Wikipedia page...[/yellow]")
        scraper = WikipediaScraper()
        page = scraper.fetch(page_title)
        console.print(f"  ✓ Fetched: {page.title} ({page.word_count:,} words)")

        console.print("\n[yellow]→ Processing into chunks...[/yellow]")
        processor = DocumentProcessor()
        chunks = processor.process_page(page)
        console.print(f"  ✓ Created {len(chunks)} chunks")

        # ===== Phase 3: Embedding Generation =====
        console.print()
        console.print(Panel("[bold]Phase 3.1: Embedding Generation[/bold]"))

        console.print("\n[yellow]→ Initializing embedding service...[/yellow]")
        embedding_service = EmbeddingService()
        embedding_service.load_model()
        console.print(
            f"  ✓ Model loaded: {embedding_service.config.model_name}"
        )
        console.print(
            f"  ✓ Embedding dimension: {embedding_service.get_embedding_dimension()}"
        )

        console.print("\n[yellow]→ Generating embeddings for chunks...[/yellow]")
        embeddings = embedding_service.embed_chunks(chunks, show_progress=True)
        console.print(f"  ✓ Generated {len(embeddings)} embeddings")

        # Sample embedding info
        console.print(f"\n[dim]Sample embedding (first 10 values):[/dim]")
        console.print(f"  {embeddings[0][:10]}")

        # ===== Phase 3: Vector Database Storage =====
        console.print()
        console.print(Panel("[bold]Phase 3.2: Vector Database Storage[/bold]"))

        console.print("\n[yellow]→ Connecting to ChromaDB...[/yellow]")
        chroma_adapter = ChromaAdapter()
        chroma_adapter.initialize()
        console.print("  ✓ Connected to ChromaDB")

        collection_name = chroma_adapter.get_default_collection_name(page.title)
        console.print(f"  ✓ Collection name: {collection_name}")

        # Clean up existing collection if it exists
        if chroma_adapter.collection_exists(collection_name):
            console.print(
                f"\n[dim]→ Collection exists, clearing old data...[/dim]"
            )
            chroma_adapter.delete_collection(collection_name)

        console.print("\n[yellow]→ Storing chunks in ChromaDB...[/yellow]")
        chroma_adapter.store_documents(collection_name, chunks, embeddings)
        console.print(f"  ✓ Stored {len(chunks)} chunks")

        # Get collection info
        info = chroma_adapter.get_collection_info(collection_name)
        console.print(f"  ✓ Collection count: {info['count']}")

        # ===== Phase 3: Similarity Search =====
        console.print()
        console.print(Panel("[bold]Phase 3.3: Similarity Search[/bold]"))

        # Sample queries
        test_queries = [
            "What is Python used for?",
            "How does Python handle memory?",
            "What are Python's design principles?",
        ]

        for query in test_queries:
            console.print(f"\n[bold cyan]Query:[/bold cyan] {query}")

            # Generate query embedding
            query_embedding = embedding_service.embed_text(query)

            # Search
            results = chroma_adapter.similarity_search(
                collection_name, query_embedding, k=5
            )

            console.print(f"[green]Found {len(results)} results:[/green]\n")

            # Display results
            for idx, (chunk, score) in enumerate(results, 1):
                console.print(f"[bold]{idx}. Similarity: {score:.3f}[/bold]")
                console.print(f"   Section: {chunk.section_title or 'Introduction'}")
                console.print(
                    f"   Content: {chunk.content[:150]}..."
                    if len(chunk.content) > 150
                    else chunk.content
                )
                console.print()

        # ===== Summary =====
        console.print(Panel("[bold green]Phase 3 Demo Complete![/bold green]"))

        # Summary table
        summary_table = Table(title="Phase 3 Summary", show_header=True)
        summary_table.add_column("Component", style="cyan")
        summary_table.add_column("Status", style="green")
        summary_table.add_column("Details", style="dim")

        summary_table.add_row(
            "Wikipedia Scraper",
            "✓ Working",
            f"{page.word_count:,} words, {len(page.sections)} sections",
        )
        summary_table.add_row(
            "Document Processor",
            "✓ Working",
            f"{len(chunks)} chunks created",
        )
        summary_table.add_row(
            "Embedding Service",
            "✓ Working",
            f"{embedding_service.get_embedding_dimension()}D embeddings",
        )
        summary_table.add_row(
            "ChromaDB Adapter",
            "✓ Working",
            f"{info['count']} documents stored",
        )
        summary_table.add_row(
            "Similarity Search",
            "✓ Working",
            "3 queries tested successfully",
        )

        console.print("\n")
        console.print(summary_table)
        console.print()

        console.print("[bold]Next Steps:[/bold]")
        console.print("  → Phase 4: LLM Integration")
        console.print("  → Phase 5: RAG Service Orchestration")
        console.print("  → Phase 6: CLI Interface")
        console.print()

    except KeyboardInterrupt:
        console.print("\n[yellow]Demo interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]")
        import traceback

        traceback.print_exc()
        console.print("\n[yellow]Make sure ChromaDB is running:[/yellow]")
        console.print("  docker-compose up -d")
        console.print("  docker-compose ps")


if __name__ == "__main__":
    main()
