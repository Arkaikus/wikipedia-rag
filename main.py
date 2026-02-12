#!/usr/bin/env python3
"""
RAG Wikipedia Chatbot MVP - Main CLI Application

Interactive command-line interface for the RAG Wikipedia Chatbot.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown

from src.services.rag_service import RAGService
from src.adapters.llm_adapter import LLMConnectionError, LLMModelNotFoundError
from src.services.wikipedia_scraper import PageNotFoundError, NetworkError
from src.utils.logger import get_logger

console = Console()
logger = get_logger(__name__)


class ChatbotCLI:
    """Command-line interface for the RAG Wikipedia Chatbot."""

    def __init__(self):
        """Initialize the chatbot CLI."""
        self.rag_service: RAGService = None
        self.running = True

    def start(self):
        """Start the chatbot CLI."""
        self._print_welcome()
        self._initialize_service()

        if self.rag_service:
            self._command_loop()

    def _print_welcome(self):
        """Print welcome message."""
        console.print()
        welcome_text = """
# RAG Wikipedia Chatbot

Ask questions about any Wikipedia page with AI-powered answers and source citations.

**Commands:**
- `load <page>` - Load a Wikipedia page
- `chat` - Enter chat mode
- `info` - Show current page info
- `clear` - Clear current page
- `help` - Show this help
- `exit` - Quit application
        """
        console.print(Panel(Markdown(welcome_text), title="Welcome", border_style="blue"))

    def _initialize_service(self):
        """Initialize the RAG service."""
        try:
            console.print("\n[yellow]Initializing services...[/yellow]")

            with console.status("[bold green]Loading..."):
                self.rag_service = RAGService()

            console.print("[green]✓ Services initialized[/green]")

            # Check component status
            status_table = Table(show_header=False, box=None, padding=(0, 2))
            status_table.add_column("Component", style="cyan")
            status_table.add_column("Status", style="green")

            status_table.add_row("Vector Database", "✓ Connected")
            status_table.add_row("Embedding Model", "✓ Loaded")

            if self.rag_service.llm.is_available():
                status_table.add_row("LLM (LMStudio)", "✓ Available")
            else:
                status_table.add_row("LLM (LMStudio)", "⚠️  Not Available")
                console.print("\n[yellow]⚠️  LMStudio not detected. Ensure it's running for Q&A.[/yellow]")

            console.print(status_table)
            console.print()

        except Exception as e:
            console.print(f"[bold red]Failed to initialize services: {e}[/bold red]")
            console.print("\n[yellow]Please check:[/yellow]")
            console.print("  • Docker is running: docker-compose up -d")
            console.print("  • LMStudio is running with a model loaded")
            logger.error(f"Initialization failed: {e}", exc_info=True)
            sys.exit(1)

    def _command_loop(self):
        """Main command loop."""
        while self.running:
            try:
                # Show prompt
                command = console.input("\n[bold cyan]>[/bold cyan] ").strip()

                if not command:
                    continue

                # Parse command
                parts = command.split(maxsplit=1)
                cmd = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""

                # Execute command
                if cmd == "load":
                    self._cmd_load(args)
                elif cmd == "chat":
                    self._cmd_chat()
                elif cmd == "info":
                    self._cmd_info()
                elif cmd == "clear":
                    self._cmd_clear()
                elif cmd == "help":
                    self._cmd_help()
                elif cmd in ["exit", "quit", "q"]:
                    self._cmd_exit()
                else:
                    console.print(f"[red]Unknown command: {cmd}[/red]")
                    console.print("Type [cyan]help[/cyan] for available commands.")

            except KeyboardInterrupt:
                console.print("\n[yellow]Use 'exit' to quit[/yellow]")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                logger.error(f"Command error: {e}", exc_info=True)

    def _cmd_load(self, page_identifier: str):
        """Load a Wikipedia page."""
        if not page_identifier:
            console.print("[red]Usage: load <page_title_or_url>[/red]")
            console.print("Example: load Python (programming language)")
            return

        try:
            console.print(f"\n[yellow]Loading Wikipedia page: {page_identifier}[/yellow]")

            with console.status("[bold green]Processing..."):
                page_info = self.rag_service.load_wikipedia_page(page_identifier)

            # Display success
            console.print("\n[bold green]✓ Page loaded and indexed![/bold green]\n")

            # Show page info
            info_table = Table(show_header=False, box=None, padding=(0, 2))
            info_table.add_column("Property", style="cyan")
            info_table.add_column("Value", style="white")

            info_table.add_row("Title", page_info["title"])
            info_table.add_row("Word Count", f"{page_info['word_count']:,}")
            info_table.add_row("Sections", str(page_info["sections"]))
            info_table.add_row("Chunks Created", str(page_info["chunks"]))
            info_table.add_row("Stored in DB", str(page_info["collection_info"]["count"]))

            console.print(info_table)
            console.print("\n[green]Ready to chat! Type[/green] [cyan]chat[/cyan] [green]to start.[/green]")

        except PageNotFoundError as e:
            console.print(f"[red]Page not found: {e}[/red]")
            console.print("Try searching on Wikipedia first to verify the page exists.")
        except NetworkError as e:
            console.print(f"[red]Network error: {e}[/red]")
            console.print("Check your internet connection.")
        except Exception as e:
            console.print(f"[red]Failed to load page: {e}[/red]")
            logger.error(f"Load command failed: {e}", exc_info=True)

    def _cmd_chat(self):
        """Enter chat mode."""
        if not self.rag_service.current_page_title:
            console.print("[red]No page loaded. Use 'load <page>' first.[/red]")
            return

        console.print(f"\n[bold green]Chat Mode[/bold green] - {self.rag_service.current_page_title}")
        console.print("[dim]Type your questions. Use 'exit' to leave chat mode.[/dim]\n")

        chat_active = True
        while chat_active:
            try:
                question = console.input("[bold cyan]You:[/bold cyan] ").strip()

                if not question:
                    continue

                if question.lower() in ["exit", "quit", "back"]:
                    console.print("[yellow]Exiting chat mode[/yellow]\n")
                    break

                # Query the RAG system
                with console.status("[bold green]Thinking..."):
                    result = self.rag_service.query(
                        question=question,
                        k=5,
                        min_similarity=0.3,
                        include_context=True,
                    )

                # Display response
                console.print("\n[bold green]Assistant:[/bold green]")
                console.print(Panel(result.context, border_style="green", padding=(1, 2)))

                # Show source chunks (optional, compact view)
                if result.retrieved_chunks:
                    console.print(
                        f"[dim]Retrieved {len(result.retrieved_chunks)} relevant sections "
                        f"(avg similarity: {sum(result.similarity_scores) / len(result.similarity_scores):.2f})[/dim]"
                    )

                console.print()

            except LLMConnectionError:
                console.print("[red]Cannot connect to LMStudio. Make sure it's running.[/red]")
                console.print("Start LMStudio and load a model, then try again.\n")
            except LLMModelNotFoundError:
                console.print("[red]Model not found in LMStudio.[/red]")
                console.print("Load a model in LMStudio and try again.\n")
            except KeyboardInterrupt:
                console.print("\n[yellow]Exiting chat mode[/yellow]\n")
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]\n")
                logger.error(f"Chat error: {e}", exc_info=True)

    def _cmd_info(self):
        """Show information about current page."""
        info = self.rag_service.get_current_page_info()

        if not info:
            console.print("[yellow]No page currently loaded.[/yellow]")
            console.print("Use [cyan]load <page>[/cyan] to load a Wikipedia page.")
            return

        console.print("\n[bold]Current Page Information[/bold]\n")

        info_table = Table(show_header=False, box=None, padding=(0, 2))
        info_table.add_column("Property", style="cyan")
        info_table.add_column("Value", style="white")

        info_table.add_row("Title", info["title"])
        info_table.add_row("Collection", info["collection"])
        info_table.add_row("Chunks Indexed", str(info["chunk_count"]))

        console.print(info_table)
        console.print()

    def _cmd_clear(self):
        """Clear the current page."""
        if not self.rag_service.current_page_title:
            console.print("[yellow]No page currently loaded.[/yellow]")
            return

        title = self.rag_service.current_page_title
        console.print(f"\n[yellow]Clearing page: {title}[/yellow]")

        try:
            self.rag_service.clear_current_page()
            console.print("[green]✓ Page cleared[/green]\n")
        except Exception as e:
            console.print(f"[red]Failed to clear page: {e}[/red]\n")
            logger.error(f"Clear command failed: {e}", exc_info=True)

    def _cmd_help(self):
        """Show help information."""
        help_text = """
# Available Commands

## Load a Wikipedia Page
```
load <page_title_or_url>
```
Load and index a Wikipedia page for Q&A.

**Examples:**
- `load Python (programming language)`
- `load https://en.wikipedia.org/wiki/Quantum_mechanics`

## Chat Mode
```
chat
```
Enter interactive chat mode to ask questions about the loaded page.
Type `exit` to leave chat mode.

## Information
```
info
```
Show information about the currently loaded page.

## Clear Page
```
clear
```
Remove the currently loaded page from the index.

## Help
```
help
```
Show this help message.

## Exit
```
exit
```
Quit the application.
        """
        console.print(Panel(Markdown(help_text), title="Help", border_style="blue"))

    def _cmd_exit(self):
        """Exit the application."""
        console.print("\n[yellow]Cleaning up...[/yellow]")

        try:
            # Clear current page if any
            if self.rag_service.current_page_title:
                self.rag_service.clear_current_page()
        except Exception as e:
            logger.error(f"Cleanup error: {e}", exc_info=True)

        console.print("[green]Thanks for using RAG Wikipedia Chatbot![/green]")
        console.print("[dim]Goodbye! 👋[/dim]\n")
        self.running = False


@click.command()
@click.option("--load", "-l", help="Load a Wikipedia page on startup")
@click.option("--debug", is_flag=True, help="Enable debug logging")
def main(load: str = None, debug: bool = False):
    """
    RAG Wikipedia Chatbot - Ask questions about Wikipedia pages with AI.

    \b
    Examples:
        python main.py
        python main.py --load "Albert Einstein"
        python main.py --debug
    """
    # Set debug level if requested
    if debug:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")

    # Create and start CLI
    cli = ChatbotCLI()

    # Auto-load page if specified
    if load:
        cli.start()
        if cli.rag_service:
            cli._cmd_load(load)
            cli._command_loop()
    else:
        cli.start()


if __name__ == "__main__":
    main()
