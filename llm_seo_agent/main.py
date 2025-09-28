#!/usr/bin/env python3
"""
LLM SEO Agent - Your AI Search Optimization Consultant

Main entry point for the conversational SEO agent.
"""

import asyncio
import sys
import os
from pathlib import Path
import click
import yaml
from rich.console import Console
from rich.panel import Panel

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.interfaces.cli_chat import CLIChatInterface, InteractiveCLI, main as cli_main
from src.agent.conversation_manager import ConversationManager


console = Console()


def load_config():
    """Load configuration from settings.yaml."""
    config_path = Path(__file__).parent / "config" / "settings.yaml"

    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Expand environment variables
        def expand_env_vars(obj):
            if isinstance(obj, dict):
                return {k: expand_env_vars(v) for k, v in obj.items()}
            elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
                env_var = obj[2:-1]
                return os.getenv(env_var, obj)
            else:
                return obj

        return expand_env_vars(config)

    return {}


@click.group(invoke_without_command=True)
@click.option('--version', is_flag=True, help='Show version information')
@click.pass_context
def main(ctx, version):
    """🤖 LLM SEO Agent - Your AI Search Optimization Consultant"""

    if version:
        console.print("[bold blue]LLM SEO Agent[/bold blue] v1.0.0")
        console.print("AI-powered SEO consultant for optimizing websites for AI search engines")
        return

    if ctx.invoked_subcommand is None:
        # Default to chat mode
        ctx.invoke(chat)


@main.command()
@click.option('--url', help='Website URL for quick analysis')
@click.option('--setup', is_flag=True, help='Run interactive setup')
@click.option('--api-key', help='Claude API key (or set CLAUDE_API_KEY env var)')
def chat(url, setup, api_key):
    """Start interactive chat with the SEO agent."""

    try:
        if url:
            # Quick analysis mode
            cli = InteractiveCLI(claude_api_key=api_key)
            asyncio.run(cli.run_quick_analysis(url))
        elif setup:
            # Interactive setup mode
            cli = InteractiveCLI(claude_api_key=api_key)
            asyncio.run(cli.run_interactive_setup())
        else:
            # Direct chat mode
            chat_interface = CLIChatInterface(claude_api_key=api_key)
            asyncio.run(chat_interface.start())

    except KeyboardInterrupt:
        console.print("\n[yellow]Goodbye![/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if "api_key" in str(e).lower():
            console.print("\n[yellow]💡 Tip: Set your Claude API key with:[/yellow]")
            console.print("   export CLAUDE_API_KEY='your-api-key-here'")
            console.print("   Or use: --api-key your-api-key-here")


@main.command()
@click.option('--port', default=8501, help='Port to run the web interface on')
@click.option('--host', default='localhost', help='Host to bind the web interface to')
def web():
    """Start the Streamlit web interface."""

    try:
        import streamlit.web.cli as stcli
        import sys

        # Get the web interface file path
        web_file = Path(__file__).parent / "src" / "interfaces" / "web_chat.py"

        # Run streamlit
        sys.argv = [
            "streamlit",
            "run",
            str(web_file),
            "--server.port", str(port),
            "--server.address", host
        ]

        console.print(f"[green]Starting web interface at http://{host}:{port}[/green]")
        stcli.main()

    except ImportError:
        console.print("[red]Error: Streamlit not installed.[/red]")
        console.print("Install with: pip install streamlit")
    except Exception as e:
        console.print(f"[red]Error starting web interface: {e}[/red]")


@main.command()
@click.argument('url')
@click.option('--format', 'output_format', default='markdown',
              type=click.Choice(['markdown', 'json']),
              help='Output format for analysis results')
@click.option('--api-key', help='Claude API key')
def analyze(url, output_format, api_key):
    """Analyze a website for SEO optimization opportunities."""

    async def run_analysis():
        try:
            # Create conversation manager
            manager = ConversationManager(claude_api_key=api_key)

            # Start session
            await manager.start_session()

            # Run analysis
            console.print(f"[blue]Analyzing {url}...[/blue]")

            with console.status("[bold blue]Running SEO analysis...", spinner="dots"):
                response = await manager.process_message(f"Analyze this website for SEO: {url}")

            if output_format == 'json':
                # In a real implementation, you'd return structured data
                console.print({"analysis": response, "url": url})
            else:
                # Markdown format
                panel = Panel(
                    response,
                    title=f"[bold green]SEO Analysis: {url}[/bold green]",
                    border_style="green"
                )
                console.print(panel)

        except Exception as e:
            console.print(f"[red]Analysis failed: {e}[/red]")

    asyncio.run(run_analysis())


@main.command()
@click.argument('your_site')
@click.argument('competitors', nargs=-1)
@click.option('--api-key', help='Claude API key')
def compare(your_site, competitors, api_key):
    """Compare your website against competitors."""

    if not competitors:
        console.print("[red]Error: Please provide at least one competitor URL[/red]")
        return

    async def run_comparison():
        try:
            manager = ConversationManager(claude_api_key=api_key)
            await manager.start_session()

            competitor_list = ", ".join(competitors)
            console.print(f"[blue]Comparing {your_site} against {competitor_list}...[/blue]")

            with console.status("[bold blue]Running competitive analysis...", spinner="dots"):
                response = await manager.process_message(
                    f"Compare {your_site} against these competitors: {competitor_list}"
                )

            panel = Panel(
                response,
                title="[bold green]Competitive Analysis[/bold green]",
                border_style="green"
            )
            console.print(panel)

        except Exception as e:
            console.print(f"[red]Comparison failed: {e}[/red]")

    asyncio.run(run_comparison())


@main.command()
def config():
    """Show current configuration."""

    config_data = load_config()

    if not config_data:
        console.print("[yellow]No configuration file found.[/yellow]")
        console.print("Create config/settings.yaml to customize settings.")
        return

    # Display key configuration items
    console.print("[bold blue]LLM SEO Agent Configuration[/bold blue]\n")

    # Claude settings
    claude_config = config_data.get('claude', {})
    console.print(f"Claude Model: {claude_config.get('model', 'Not set')}")
    console.print(f"API Key: {'Set' if claude_config.get('api_key') else 'Not set'}")

    # Interface settings
    interfaces = config_data.get('interfaces', {})
    console.print(f"\nEnabled Interfaces:")
    for interface, settings in interfaces.items():
        if isinstance(settings, dict):
            enabled = settings.get('enabled', False)
            console.print(f"  - {interface.title()}: {'✅' if enabled else '❌'}")

    # Storage settings
    storage = config_data.get('storage', {})
    console.print(f"\nStorage Paths:")
    for key, path in storage.items():
        console.print(f"  - {key}: {path}")


@main.command()
def setup():
    """Setup the LLM SEO Agent environment."""

    console.print(Panel.fit(
        "[bold blue]LLM SEO Agent Setup[/bold blue]",
        subtitle="Setting up your AI SEO consultant"
    ))

    # Check for required directories
    required_dirs = ['data/conversations', 'data/performance', 'data/cache', 'logs']

    for dir_path in required_dirs:
        full_path = Path(dir_path)
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            console.print(f"✅ Created directory: {dir_path}")
        else:
            console.print(f"📁 Directory exists: {dir_path}")

    # Check for Claude API key
    api_key = os.getenv('CLAUDE_API_KEY')
    if api_key:
        console.print("✅ Claude API key found in environment")
    else:
        console.print("[yellow]⚠️  Claude API key not found[/yellow]")
        console.print("Set it with: export CLAUDE_API_KEY='your-api-key'")

    # Check for optional dependencies
    optional_deps = [
        ('spacy', 'Advanced content analysis'),
        ('streamlit', 'Web interface'),
        ('plotly', 'Analytics dashboard')
    ]

    console.print("\n[bold]Optional Dependencies:[/bold]")
    for dep, description in optional_deps:
        try:
            __import__(dep)
            console.print(f"✅ {dep} - {description}")
        except ImportError:
            console.print(f"❌ {dep} - {description} (install with: pip install {dep})")

    console.print("\n[green]Setup complete! You can now run:[/green]")
    console.print("  python main.py chat          # Start CLI chat")
    console.print("  python main.py web           # Start web interface")
    console.print("  python main.py analyze <url> # Quick analysis")


@main.command()
def version():
    """Show version information."""
    console.print("[bold blue]LLM SEO Agent[/bold blue] v1.0.0")
    console.print("AI-powered SEO consultant for optimizing websites for AI search engines")
    console.print("\nFeatures:")
    console.print("  • Website SEO analysis")
    console.print("  • AI search optimization")
    console.print("  • Competitor analysis")
    console.print("  • Performance monitoring")
    console.print("  • Interactive chat interface")


if __name__ == "__main__":
    main()