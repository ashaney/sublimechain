"""
Enhanced UI Components for ThinkChain CLI

This module provides rich, interactive CLI components that enhance the user experience
with beautiful formatting, progress indicators, and status displays.
"""

import time
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.columns import Columns
    from rich.layout import Layout
    from rich.live import Live
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich.status import Status
    from rich.text import Text
    from rich.tree import Tree
    from rich.rule import Rule
    from rich.syntax import Syntax
    from rich.markdown import Markdown
    from rich.prompt import Prompt, Confirm
    from rich.align import Align
    from rich.box import ROUNDED, MINIMAL
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

try:
    from prompt_toolkit import prompt
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.history import InMemoryHistory
    from prompt_toolkit.shortcuts import confirm
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.keys import Keys
    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False


class EnhancedConsole:
    """Enhanced console with rich formatting capabilities"""
    
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.history = InMemoryHistory() if PROMPT_TOOLKIT_AVAILABLE else None
        
        # Theme colors
        self.colors = {
            'primary': '#0066cc',
            'success': '#00cc66', 
            'warning': '#ff9900',
            'error': '#cc0066',
            'info': '#6600cc',
            'muted': '#666666',
            'claude': '#ff6b35',
            'thinking': '#4a90e2',
            'tool': '#ffa500',
            'mcp': '#9b59b6'
        }
        
        # Icons
        self.icons = {
            'claude': '🤖',
            'thinking': '💭',
            'tool': '🔧',
            'mcp': '🌐',
            'success': '✅',
            'error': '❌',
            'warning': '⚠️',
            'info': 'ℹ️',
            'loading': '⏳',
            'ready': '🔋',
            'config': '⚙️',
            'help': '❓',
            'refresh': '🔄',
            'list': '📋',
            'search': '🔍',
            'code': '💻',
            'data': '📊'
        }
    
    def print(self, *args, **kwargs):
        """Enhanced print with rich formatting"""
        if self.console:
            self.console.print(*args, **kwargs)
        else:
            print(*args, **kwargs)
    
    def print_panel(self, content: str, title: str = "", style: str = "primary", expand: bool = True):
        """Print content in a styled panel"""
        if not RICH_AVAILABLE:
            print(f"\n=== {title} ===")
            print(content)
            print("=" * (len(title) + 8))
            return
            
        panel = Panel(
            content,
            title=f"[bold]{title}[/bold]" if title else "",
            border_style=self.colors.get(style, style),
            box=ROUNDED,
            expand=expand
        )
        self.console.print(panel)
    
    def print_status_bar(self, local_tools: int, mcp_servers: int, thinking_enabled: bool, status: str):
        """Print a comprehensive status bar"""
        if not RICH_AVAILABLE:
            print(f"Local: {local_tools} tools | MCP: {mcp_servers} servers | Thinking: {'ON' if thinking_enabled else 'OFF'} | {status}")
            return
        
        # Create status components
        local_status = f"{self.icons['tool']} Local: [bold cyan]{local_tools}[/bold cyan] tools"
        mcp_status = f"{self.icons['mcp']} MCP: [bold magenta]{mcp_servers}[/bold magenta] servers"
        thinking_status = f"{self.icons['thinking']} Thinking: [bold {'green' if thinking_enabled else 'red'}]{'ON' if thinking_enabled else 'OFF'}[/bold {'green' if thinking_enabled else 'red'}]"
        system_status = f"{self.icons['ready']} [bold green]{status}[/bold green]"
        
        status_text = f"{local_status} │ {mcp_status} │ {thinking_status} │ {system_status}"
        
        panel = Panel(
            Align.center(status_text),
            title="[bold blue]Claude Tool Discovery Chat[/bold blue]",
            border_style="blue",
            box=MINIMAL
        )
        self.console.print(panel)
    
    def print_tool_table(self, tools_by_category: Dict[str, List[Dict[str, Any]]]):
        """Print tools in a beautiful table format"""
        if not RICH_AVAILABLE:
            for category, tools in tools_by_category.items():
                print(f"\n{category.upper()} TOOLS:")
                for tool in tools:
                    print(f"  - {tool['name']}: {tool['description'][:60]}...")
            return
        
        # Create tables for each category
        tables = []
        
        for category, tools in tools_by_category.items():
            if not tools:
                continue
                
            table = Table(
                title=f"{category.title()} Tools",
                box=ROUNDED,
                show_header=True,
                header_style="bold blue"
            )
            
            table.add_column("Tool Name", style="cyan", no_wrap=True)
            table.add_column("Description", style="white")
            table.add_column("Type", style="magenta", no_wrap=True)
            
            for tool in tools:
                tool_type = "MCP" if tool['name'].startswith('mcp_') else "Local"
                type_color = "magenta" if tool_type == "MCP" else "green"
                
                table.add_row(
                    f"[bold]{tool['name']}[/bold]",
                    tool['description'][:80] + ("..." if len(tool['description']) > 80 else ""),
                    f"[{type_color}]{tool_type}[/{type_color}]"
                )
            
            tables.append(table)
        
        # Display tables in columns if multiple categories
        if len(tables) > 1:
            self.console.print(Columns(tables, equal=True))
        elif tables:
            self.console.print(tables[0])
    
    def print_thinking(self, content: str):
        """Print thinking content with special formatting"""
        if not RICH_AVAILABLE:
            print(f"[Thinking] {content}")
            return
            
        self.console.print(f"{self.icons['thinking']} [italic blue]Thinking:[/italic blue] {content}")
    
    def print_tool_execution(self, tool_name: str, status: str, duration: Optional[float] = None):
        """Print tool execution status"""
        if not RICH_AVAILABLE:
            duration_str = f" ({duration:.1f}s)" if duration else ""
            print(f"[{tool_name}] {status}{duration_str}")
            return
        
        duration_str = f" [dim]({duration:.1f}s)[/dim]" if duration else ""
        icon = self.icons['tool'] if not tool_name.startswith('mcp_') else self.icons['mcp']
        
        if status == "executing":
            self.console.print(f"{icon} [bold yellow]{tool_name}[/bold yellow]: [yellow]Executing...[/yellow]{duration_str}")
        elif status == "completed":
            self.console.print(f"{icon} [bold green]{tool_name}[/bold green]: [green]Completed[/green]{duration_str}")
        elif status == "failed":
            self.console.print(f"{icon} [bold red]{tool_name}[/bold red]: [red]Failed[/red]{duration_str}")
        else:
            self.console.print(f"{icon} [bold]{tool_name}[/bold]: {status}{duration_str}")
    
    def print_claude_response(self, content: str):
        """Print Claude's response with special formatting"""
        if not RICH_AVAILABLE:
            print(f"\n[Claude] {content}")
            return
            
        self.console.print(f"\n{self.icons['claude']} [bold blue]Claude:[/bold blue] {content}")
    
    def print_error(self, message: str, details: Optional[str] = None):
        """Print error message with formatting"""
        if not RICH_AVAILABLE:
            print(f"ERROR: {message}")
            if details:
                print(f"Details: {details}")
            return
            
        error_text = f"{self.icons['error']} [bold red]Error:[/bold red] {message}"
        if details:
            error_text += f"\n[dim]{details}[/dim]"
        
        self.console.print(error_text)
    
    def print_success(self, message: str):
        """Print success message with formatting"""
        if not RICH_AVAILABLE:
            print(f"✓ {message}")
            return
            
        self.console.print(f"{self.icons['success']} [bold green]{message}[/bold green]")
    
    def print_warning(self, message: str):
        """Print warning message with formatting"""
        if not RICH_AVAILABLE:
            print(f"WARNING: {message}")
            return
            
        self.console.print(f"{self.icons['warning']} [bold yellow]Warning:[/bold yellow] {message}")
    
    def print_rule(self, title: Optional[str] = None, style: str = "blue"):
        """Print a horizontal rule separator"""
        if not RICH_AVAILABLE:
            print("-" * 80)
            return
            
        self.console.print(Rule(title, style=style))
    
    def print_code(self, code: str, language: str = "python", theme: str = "monokai"):
        """Print syntax-highlighted code"""
        if not RICH_AVAILABLE:
            print(f"\n{code}\n")
            return
            
        syntax = Syntax(code, language, theme=theme, line_numbers=True)
        self.console.print(syntax)
    
    def print_json(self, data: Any, title: str = "JSON Output"):
        """Print formatted JSON data"""
        import json
        json_str = json.dumps(data, indent=2)
        
        if not RICH_AVAILABLE:
            print(f"\n{title}:")
            print(json_str)
            return
            
        syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
        self.print_panel(syntax, title, "info")
    
    def print_markdown(self, markdown_text: str):
        """Print markdown-formatted text"""
        if not RICH_AVAILABLE:
            print(markdown_text)
            return
            
        md = Markdown(markdown_text)
        self.console.print(md)
    
    def print_session_stats(self, stats: Dict[str, Any]):
        """Print session statistics in a beautiful format"""
        if not RICH_AVAILABLE:
            print(f"Session Stats: {stats}")
            return
            
        # Calculate session duration
        duration = time.time() - stats.get("start_time", time.time())
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        duration_str = f"{hours:02d}:{minutes:02d}" if hours > 0 else f"{minutes:02d}m"
        
        # Create stats table
        table = Table(title="📊 Session Statistics", box=ROUNDED, show_header=False)
        table.add_column("Metric", style="bold cyan", width=20)
        table.add_column("Value", style="green", width=15)
        table.add_column("Icon", width=5)
        
        # Add rows
        table.add_row("Duration", duration_str, "⏱️")
        table.add_row("API Calls", str(stats.get("api_calls", 0)), "🔄")
        table.add_row("Tool Calls", str(stats.get("tool_calls", 0)), "🔧")
        table.add_row("Successful Tools", str(stats.get("successful_tools", 0)), "✅")
        table.add_row("Failed Tools", str(stats.get("failed_tools", 0)), "❌")
        table.add_row("Memories Created", str(stats.get("memories_created", 0)), "🧠")
        
        self.console.print(table)

    def get_input_with_stats(self, prompt_text: str, session_stats: Dict[str, Any]) -> str:
        """Enhanced input with session stats like Claude Code"""
        if not PROMPT_TOOLKIT_AVAILABLE:
            return input(f"{prompt_text}: ")
        
        # Calculate quick stats for status line
        duration = time.time() - session_stats.get("start_time", time.time())
        minutes = int(duration // 60)
        
        # Create status line like Claude Code
        stats_line = (
            f"🔧 Tools: {session_stats.get('successful_tools', 0)}"
            f" │ 🔄 API: {session_stats.get('api_calls', 0)}"
            f" │ 🧠 Memories: {session_stats.get('memories_created', 0)}"
            f" │ ⏱️ {minutes}m"
        )
        
        # Enhanced prompt with stats above input (visible immediately)
        try:
            # Show stats first, then clean prompt
            print(f"\n{stats_line}")
            result = prompt(
                "> ",
                history=self.history,
                complete_style="column", 
                wrap_lines=True
            )
            return result
        except (KeyboardInterrupt, EOFError):
            return ""

    def get_input(self, prompt_text: str = "Enter command", 
                  completer_words: Optional[List[str]] = None) -> str:
        """Get user input with intuitive key bindings"""
        if PROMPT_TOOLKIT_AVAILABLE:
            # Set up custom key bindings
            bindings = KeyBindings()
            
            @bindings.add(Keys.ControlM)  # Enter key
            def _(event):
                """Enter sends the command"""
                event.app.exit(result=event.app.current_buffer.text)
            
            @bindings.add(Keys.ControlJ)  # Ctrl+Enter 
            def _(event):
                """Ctrl+Enter adds a new line"""
                event.current_buffer.insert_text('\n')
            
            return prompt(
                f"{prompt_text}: ",
                history=self.history,
                multiline=True,
                mouse_support=False,  # Disable mouse capture to allow terminal scrolling
                complete_style=None,
                completer=None,
                auto_suggest=None,
                key_bindings=bindings,
            )
        elif RICH_AVAILABLE:
            return Prompt.ask(f"[bold blue]{prompt_text}[/bold blue]")
        else:
            return input(f"{prompt_text}: ").strip()
    
    def confirm(self, message: str, default: bool = False) -> bool:
        """Get confirmation from user"""
        if PROMPT_TOOLKIT_AVAILABLE:
            return confirm(message, default=default)
        elif RICH_AVAILABLE:
            return Confirm.ask(message, default=default)
        else:
            response = input(f"{message} (y/N): ").strip().lower()
            return response in ['y', 'yes', 'true', '1']
    
    @contextmanager
    def progress_context(self, description: str = "Processing..."):
        """Context manager for progress indication"""
        if RICH_AVAILABLE:
            with self.console.status(f"[bold blue]{description}[/bold blue]", spinner="dots"):
                yield
        else:
            print(f"{description}")
            yield
            print("Done.")
    
    @contextmanager
    def live_update_context(self):
        """Context manager for live updates"""
        if RICH_AVAILABLE:
            with Live(auto_refresh=True, console=self.console) as live:
                yield live
        else:
            yield None
    
    def clear_screen(self):
        """Clear the console screen"""
        if RICH_AVAILABLE:
            self.console.clear()
        else:
            import os
            os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_help(self, commands: Dict[str, str]):
        """Print help information in a formatted table"""
        if not RICH_AVAILABLE:
            print("\nAvailable Commands:")
            for cmd, desc in commands.items():
                print(f"  {cmd:<15} - {desc}")
            return
        
        table = Table(
            title="Available Commands",
            box=ROUNDED,
            show_header=True,
            header_style="bold blue"
        )
        
        table.add_column("Command", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")
        
        for cmd, desc in commands.items():
            table.add_row(f"[bold]{cmd}[/bold]", desc)
        
        self.console.print(table)


# Global console instance
ui = EnhancedConsole()


# Convenience functions for common operations
def print_banner(title: str = "ThinkChain", subtitle: str = "Claude Chat with Advanced Tool Integration & Thinking"):
    """Print customizable application banner"""
    
    # ASCII art for SublimeChain
    if "sublime" in title.lower():
        banner_text = f"""
·····························································································
 ███████╗██╗   ██╗██████╗ ██╗     ██╗███╗   ███╗███████╗ ██████╗██╗  ██╗ █████╗ ██╗███╗   ██╗ 
 ██╔════╝██║   ██║██╔══██╗██║     ██║████╗ ████║██╔════╝██╔════╝██║  ██║██╔══██╗██║████╗  ██║ 
 ███████╗██║   ██║██████╔╝██║     ██║██╔████╔██║█████╗  ██║     ███████║███████║██║██╔██╗ ██║ 
 ╚════██║██║   ██║██╔══██╗██║     ██║██║╚██╔╝██║██╔══╝  ██║     ██╔══██║██╔══██║██║██║╚██╗██║ 
 ███████║╚██████╔╝██████╔╝███████╗██║██║ ╚═╝ ██║███████╗╚██████╗██║  ██║██║  ██║██║██║ ╚████║ 
 ╚══════╝ ╚═════╝ ╚═════╝ ╚══════╝╚═╝╚═╝     ╚═╝╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝ 
                                                                                              
                            🧠 To err is human, to learn, sublime 💭                            
                            (a fork of ThinkChain by Martin Bowling)                                             
·····························································································
        """
    else:
        # Original ThinkChain banner
        banner_text = f"""
╔═══════════════════════════════════════════════════════════════════╗
║  ████████╗██╗  ██╗██╗███╗   ██╗██╗  ██╗ ██████╗██╗  ██╗ █████╗ ██╗███╗   ██╗  ║
║  ╚══██╔══╝██║  ██║██║████╗  ██║██║ ██╔╝██╔════╝██║  ██║██╔══██╗██║████╗  ██║  ║
║     ██║   ███████║██║██╔██╗ ██║█████╔╝ ██║     ███████║███████║██║██╔██╗ ██║  ║
║     ██║   ██╔══██║██║██║╚██╗██║██╔═██╗ ██║     ██╔══██║██╔══██║██║██║╚██╗██║  ║
║     ██║   ██║  ██║██║██║ ╚████║██║  ██╗╚██████╗██║  ██║██║  ██║██║██║ ╚████║  ║
║     ╚═╝   ╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝  ║
║                                                                               ║
║                          🧠 {subtitle} 💭                          ║
║                      Interleaved Thinking • Tool Streaming                    ║
╚═══════════════════════════════════════════════════════════════════════════════╝
        """
    
    if RICH_AVAILABLE:
        # Use lime green color
        ui.console.print(banner_text, style="bold bright_green")
    else:
        print(banner_text)


def print_initialization_progress(steps: List[str]):
    """Show initialization progress"""
    if not RICH_AVAILABLE:
        for i, step in enumerate(steps, 1):
            print(f"[{i}/{len(steps)}] {step}")
        return
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=ui.console
    ) as progress:
        
        task = progress.add_task("Initializing...", total=len(steps))
        
        for step in steps:
            progress.update(task, description=step)
            time.sleep(0.5)  # Simulate work
            progress.advance(task)


def format_command_suggestions(current_input: str) -> List[str]:
    """Generate command suggestions based on current input"""
    all_commands = [
        '/help', '/tools', '/memory', '/remember', '/recall', '/search-memory', 
        '/what-did-i', '/forget-memory', '/refresh', '/reload', '/config', 
        '/status', '/clear', '/exit', '/quit', 'help', 'tools', 'memory',
        'remember', 'recall', 'search-memory', 'what-did-i', 'forget-memory',
        'refresh', 'reload', 'config', 'status', 'clear', 'exit', 'quit'
    ]
    
    if not current_input:
        return all_commands
    
    # Filter commands that start with the current input
    suggestions = [cmd for cmd in all_commands if cmd.startswith(current_input.lower())]
    return suggestions[:10]  # Limit to 10 suggestions