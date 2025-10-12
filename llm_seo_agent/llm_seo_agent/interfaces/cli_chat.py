import asyncio
import sys
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns
from rich.status import Status
from rich.table import Table
from rich.markdown import Markdown
from rich.syntax import Syntax
from typing import Optional
import signal

from llm_seo_agent.agent.conversation_manager import ConversationManager


class CLIChatInterface:
    def __init__(self, claude_api_key: Optional[str] = None):
        self.console = Console()
        self.conversation_manager = ConversationManager(claude_api_key=claude_api_key)
        self.running = False

        # Add message handler for CLI-specific formatting
        self.conversation_manager.add_message_handler(self._handle_message_event)

    async def start(self, user_id: str = None, website_url: str = None):
        """Start the CLI chat interface."""
        self.running = True

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self._show_header()
        self._show_welcome()

        # Start conversation session
        with Status("[bold blue]Starting conversation...", console=self.console, spinner="dots"):
            welcome_message = await self.conversation_manager.start_session(user_id, website_url)

        # Show session ID
        session_id = self.conversation_manager.consultant.memory.current_session.session_id
        self.console.print(f"[dim]📁 Session ID: {session_id}[/dim]")
        self.console.print(
            f"[dim]💾 Conversation saved to: data/conversations/{session_id}.json[/dim]"
        )
        self.console.print()

        self._print_agent_message(welcome_message)

        # Main chat loop
        await self._chat_loop()

    async def _chat_loop(self):
        """Main chat interaction loop."""
        while self.running:
            try:
                # Get user input
                user_input = await self._get_user_input()

                if not user_input or user_input.lower() in ['exit', 'quit', 'bye']:
                    break

                # Handle special commands
                if user_input.startswith('/'):
                    await self._handle_command(user_input)
                    continue

                # Show typing indicator
                with Status("[bold blue]Thinking...", console=self.console, spinner="dots"):
                    response = await self.conversation_manager.process_message(user_input)

                self._print_agent_message(response)

            except KeyboardInterrupt:
                break
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")

        # End session
        goodbye = await self.conversation_manager.end_session()
        self._print_agent_message(goodbye)
        self._show_footer()

    def _show_header(self):
        """Display the application header."""
        header_text = Text.assemble(
            ("🤖 ", "bright_blue"),
            ("LLM SEO Agent", "bold bright_blue"),
            (" - Your AI Search Optimization Consultant", "blue"),
        )

        panel = Panel.fit(header_text, border_style="bright_blue", padding=(1, 2))

        self.console.print()
        self.console.print(panel)
        self.console.print()

    def _show_welcome(self):
        """Display welcome information."""
        welcome_text = """
💡 **Tips for better conversations:**
• Share your website URL for personalized advice
• Ask specific questions like "How do I optimize for AI search?"
• Request analysis: "Analyze my website" or "Compare me to competitor.com"
• Use `/help` to see all commands
• Use `/export` to save your recommendations as markdown

🚀 **Example questions:**
• "My website isn't showing up in ChatGPT responses"
• "How do I structure content for AI citations?"
• "Analyze example.com for SEO opportunities"
"""

        self.console.print(
            Panel(
                Markdown(welcome_text),
                title="[bold green]Getting Started[/bold green]",
                border_style="green",
            )
        )
        self.console.print()

    def _show_footer(self):
        """Display goodbye footer."""
        footer = Panel.fit(
            "Thanks for using LLM SEO Agent! Your conversation has been saved.",
            border_style="dim",
            title="[dim]Session Ended[/dim]",
        )
        self.console.print()
        self.console.print(footer)

    async def _get_user_input(self) -> str:
        """Get user input with proper formatting."""
        try:
            # Create a future for the input
            loop = asyncio.get_event_loop()
            user_input = await loop.run_in_executor(
                None, lambda: Prompt.ask("\n[bold green]You[/bold green]", console=self.console)
            )
            return user_input.strip()
        except EOFError:
            return "exit"

    def _print_agent_message(self, message: str):
        """Print agent response with formatting."""
        # Format the message
        formatted_message = self._format_agent_response(message)

        # Create panel with agent response
        panel = Panel(
            formatted_message,
            title="[bold blue]🤖 SEO Agent[/bold blue]",
            border_style="blue",
            padding=(1, 2),
        )

        self.console.print(panel)

    def _format_agent_response(self, message: str):
        """Format agent response with rich formatting."""
        # If message contains markdown-like formatting, render as markdown
        if any(marker in message for marker in ['**', '*', '`', '#', '-', '•']):
            return Markdown(message)

        # Otherwise, return as plain text
        return Text(message)

    async def _handle_message_event(self, event_type: str, data: dict):
        """Handle message events for CLI-specific formatting."""
        if event_type == "session_start":
            self.console.print(
                f"[dim]Session started for user: {data.get('user_id', 'default')}[/dim]"
            )

        elif event_type == "message_exchange":
            # Could add message logging or other CLI-specific handling here
            pass

        elif event_type == "session_end":
            # Could add session summary here
            pass

    def _signal_handler(self, signum, frame):
        """Handle interrupt signals gracefully."""
        self.console.print("\n[yellow]Shutting down gracefully...[/yellow]")
        self.running = False

    async def _handle_command(self, command: str):
        """Handle special slash commands."""
        cmd_parts = command.split()
        cmd = cmd_parts[0].lower()

        if cmd == '/help':
            self._show_help_panel()

        elif cmd == '/export':
            await self._handle_export_command(cmd_parts)

        elif cmd == '/status':
            await self._show_status()

        elif cmd == '/recommendations':
            await self._show_recommendations()

        elif cmd in ['/exit', '/quit', '/bye']:
            self.running = False
            self.console.print("[yellow]Ending session...[/yellow]")

        else:
            self.console.print(f"[yellow]Unknown command: {cmd}[/yellow]")
            self.console.print("Type [bold]/help[/bold] to see available commands")

    async def _handle_export_command(self, cmd_parts: list):
        """Handle the /export command."""
        from datetime import datetime
        from pathlib import Path

        # Parse options
        include_conversation = '--with-conversation' in cmd_parts or '-c' in cmd_parts

        # Get output filename
        output_file = None
        for i, part in enumerate(cmd_parts):
            if part in ['-o', '--output'] and i + 1 < len(cmd_parts):
                output_file = cmd_parts[i + 1]
                break

        # Default filename if not specified
        if not output_file:
            output_file = f"seo_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        try:
            # Export the current session
            markdown_content = self.conversation_manager.consultant.memory.export_to_markdown(
                output_path=output_file, include_conversation=include_conversation
            )

            # Show success message
            file_path = Path(output_file).absolute()

            success_panel = Panel(
                f"[green]✅ Report exported successfully![/green]\n\n"
                f"[bold]File:[/bold] {file_path}\n"
                f"[bold]Size:[/bold] {len(markdown_content)} bytes\n"
                f"[bold]Includes conversation:[/bold] {'Yes' if include_conversation else 'No'}\n\n"
                f"[dim]You can now share this report with colleagues or clients![/dim]",
                title="[bold green]Export Complete[/bold green]",
                border_style="green",
            )

            self.console.print()
            self.console.print(success_panel)

        except Exception as e:
            self.console.print(f"[red]❌ Export failed: {e}[/red]")

    async def _show_status(self):
        """Show user progress and status."""
        progress = await self.conversation_manager.consultant.get_user_progress()

        if not progress:
            self.console.print("[yellow]No progress data available yet.[/yellow]")
            return

        # Get session ID
        session = self.conversation_manager.consultant.memory.current_session
        session_id = session.session_id if session else "Unknown"

        status_text = f"""
**Session Info:**
• Session ID: `{session_id}`
• File: `data/conversations/{session_id}.json`

**Your SEO Journey:**
• Total Conversations: {progress.get('total_conversations', 0)}
• Recommendations: {progress['recommendations']['total']}
• Completed: {progress['recommendations']['completed']}
• In Progress: {progress['recommendations']['in_progress']}
• Completion Rate: {progress['recommendations']['completion_rate']:.1f}%
• Website Analyses: {progress.get('website_analyses', 0)}
"""

        panel = Panel(
            Markdown(status_text), title="[bold cyan]Your Progress[/bold cyan]", border_style="cyan"
        )

        self.console.print()
        self.console.print(panel)

    async def _show_recommendations(self):
        """Show current recommendations."""
        session = self.conversation_manager.consultant.memory.current_session

        if not session or not session.recommendations:
            self.console.print(
                "[yellow]No recommendations yet. Ask for a website analysis to get started![/yellow]"
            )
            return

        # Create table
        table = Table(title="Your SEO Recommendations")
        table.add_column("ID", style="dim", width=8)
        table.add_column("Title", style="bold")
        table.add_column("Priority", justify="center")
        table.add_column("Status", justify="center")

        for rec in session.recommendations:
            # Color code priority
            priority_color = {"high": "red", "medium": "yellow", "low": "green"}.get(
                rec.priority, "white"
            )

            # Status emoji
            status_emoji = {
                "pending": "⏳",
                "in_progress": "🔄",
                "completed": "✅",
                "dismissed": "❌",
            }.get(rec.implementation_status, "•")

            table.add_row(
                rec.id[:8],
                rec.title,
                f"[{priority_color}]{rec.priority.upper()}[/{priority_color}]",
                f"{status_emoji} {rec.implementation_status}",
            )

        self.console.print()
        self.console.print(table)

    def _show_help_panel(self):
        """Show help information in a formatted panel."""
        help_content = """**Chat Commands:**
- Type naturally: "Analyze my website: example.com"
- `/help` - Show this help
- `/status` - View your progress
- `/recommendations` - See your SEO recommendations
- `/export` - Export report as markdown
- `/exit` (or `/quit`, `/bye`) - End session
- `exit` or `quit` (without slash) - Also works

**Export Options:**
- `/export` - Export with default filename
- `/export -o myreport.md` - Export to specific file
- `/export --with-conversation` - Include full chat history
- `/export -o report.md -c` - Combine options

**Analysis Requests:**
- "Analyze [website-url]"
- "Compare me to [competitor-url]"
- "Check my AI search performance"
- "How do I optimize for AI search?"

**Recommendation Management:**
- `/complete [rec-id]` - Mark recommendation as done
- `/progress [rec-id]` - Mark as in progress
"""

        panel = Panel(
            Markdown(help_content),
            title="[bold yellow]Help & Commands[/bold yellow]",
            border_style="yellow",
        )

        self.console.print(panel)


class InteractiveCLI:
    """Enhanced CLI with interactive features."""

    def __init__(self, claude_api_key: Optional[str] = None):
        self.console = Console()
        self.chat_interface = CLIChatInterface(claude_api_key=claude_api_key)

    async def run_interactive_setup(self):
        """Run interactive setup to gather user information."""
        self.console.print(Panel.fit("🚀 Welcome to LLM SEO Agent Setup", style="bold blue"))

        # Get user information
        self.console.print("\n[bold]Let's get you set up for SEO success![/bold]")

        user_id = Prompt.ask("[green]What's your name or company?[/green]", default="Anonymous")

        website_url = Prompt.ask("[green]What's your website URL?[/green] (optional)", default="")

        industry = Prompt.ask(
            "[green]What industry are you in?[/green]",
            choices=["tech", "ecommerce", "b2b", "healthcare", "finance", "other"],
            default="other",
        )

        # Show setup summary
        setup_table = Table(title="Setup Summary")
        setup_table.add_column("Setting", style="cyan")
        setup_table.add_column("Value", style="green")

        setup_table.add_row("Name/Company", user_id)
        setup_table.add_row("Website", website_url or "Not provided")
        setup_table.add_row("Industry", industry)

        self.console.print()
        self.console.print(setup_table)

        # Confirm and start
        if (
            Prompt.ask(
                "\n[yellow]Start your SEO consultation?[/yellow]", choices=["y", "n"], default="y"
            )
            == "y"
        ):
            await self.chat_interface.start(user_id=user_id, website_url=website_url or None)
        else:
            self.console.print("[red]Setup cancelled.[/red]")

    async def run_quick_analysis(self, url: str):
        """Run a quick website analysis without full chat interface."""
        self.console.print(Panel.fit(f"🔍 Quick Analysis: {url}", style="bold blue"))

        # Start a temporary session
        manager = ConversationManager()
        await manager.start_session()

        with Status("[bold blue]Analyzing website...", console=self.console, spinner="dots"):
            response = await manager.process_message(f"Analyze this website: {url}")

        # Display results
        panel = Panel(
            Markdown(response),
            title="[bold green]Analysis Results[/bold green]",
            border_style="green",
        )

        self.console.print()
        self.console.print(panel)

        # Ask if they want to continue with full consultation
        if (
            Prompt.ask(
                "\n[yellow]Start full SEO consultation?[/yellow]", choices=["y", "n"], default="n"
            )
            == "y"
        ):
            await self.chat_interface.start(website_url=url)


async def main():
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="LLM SEO Agent CLI")
    parser.add_argument("--url", help="Quick analyze a website URL")
    parser.add_argument("--setup", action="store_true", help="Run interactive setup")
    parser.add_argument("--api-key", help="Claude API key (or set CLAUDE_API_KEY env var)")

    args = parser.parse_args()

    try:
        if args.url:
            # Quick analysis mode
            cli = InteractiveCLI(claude_api_key=args.api_key)
            await cli.run_quick_analysis(args.url)

        elif args.setup:
            # Interactive setup mode
            cli = InteractiveCLI(claude_api_key=args.api_key)
            await cli.run_interactive_setup()

        else:
            # Direct chat mode
            chat = CLIChatInterface(claude_api_key=args.api_key)
            await chat.start()

    except KeyboardInterrupt:
        Console().print("\n[yellow]Goodbye![/yellow]")
    except Exception as e:
        Console().print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
