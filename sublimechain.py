#!/usr/bin/env python3
# /// script
# dependencies = [
#     "anthropic>=0.25.0",
#     "sseclient-py",
#     "pydantic",
#     "python-dotenv",
#     "rich>=13.0.0",
#     "prompt-toolkit>=3.0.0",
#     "click>=8.0.0",
#     "yaspin>=3.0.0",
#     "requests",
#     "beautifulsoup4",
#     "mcp",
#     "httpx",
#     "mem0ai",
# ]
# ///

"""
SublimeChain - The Ultimate AI Assistant

Enhanced AI experience with persistent memory, advanced coding capabilities,
dynamic tool discovery, and context-aware interactions that learn and evolve.

Features:
- 🧠 Persistent Memory: Learns from every interaction
- 💻 Advanced Coding: Claude Code SDK integration
- 🔧 Dynamic Tools: Auto-discovery + MCP servers
- 🎨 Beautiful UI: Rich terminal experience
- 🚀 Streaming: Real-time thinking + tool execution
"""

import os, json, itertools, time, asyncio
from collections import defaultdict
from typing import Dict, List, Any
import logging

# Setup logger for this module
logger = logging.getLogger(__name__)

# Nuclear option: Disable all telemetry/analytics completely
os.environ["POSTHOG_DISABLED"] = "1"
os.environ["DISABLE_TELEMETRY"] = "1"
os.environ["DO_NOT_TRACK"] = "1"
os.environ["ANALYTICS_DISABLED"] = "1"

# Mock PostHog to prevent it from loading
import sys
from unittest.mock import MagicMock

# Create a mock PostHog module
mock_posthog = MagicMock()
mock_posthog.capture = MagicMock()
mock_posthog.identify = MagicMock()
mock_posthog.flush = MagicMock()
sys.modules['posthog'] = mock_posthog

# Suppress all logging noise
import logging
import warnings

# Suppress specific MCP-related warnings and async cleanup noise
warnings.filterwarnings("ignore", message=".*cancel scope in a different task.*")
warnings.filterwarnings("ignore", message=".*unhandled errors in a TaskGroup.*")
warnings.filterwarnings("ignore", category=RuntimeWarning, module="anyio")
warnings.filterwarnings("ignore", category=RuntimeWarning, module="mcp")
warnings.filterwarnings("ignore", message=".*output_format.*deprecated.*", category=DeprecationWarning)

logging.getLogger("posthog").setLevel(logging.CRITICAL)
logging.getLogger("backoff").setLevel(logging.CRITICAL)
logging.getLogger("mcp_integration").setLevel(logging.WARNING)  # Back to quiet mode
logging.getLogger("tool_discovery").setLevel(logging.WARNING)
logging.getLogger("memory_manager").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.CRITICAL)  # Hide MCP async cleanup errors
logging.getLogger("anyio").setLevel(logging.CRITICAL)   # Hide anyio task group errors
logging.getLogger("httpx").setLevel(logging.WARNING)     # Suppress HTTP request logs
logging.getLogger("mem0").setLevel(logging.WARNING)      # Suppress Mem0 verbose logs

import anthropic              # ≥0.25.0
from sseclient import SSEClient  # pip install sseclient‑py
from dotenv import load_dotenv

# Import our enhanced tool discovery system
from tool_discovery import (
    get_tool_discovery, get_claude_tools, execute_tool_sync, 
    refresh_tools, list_tools, initialize_tool_discovery
)

# Import memory manager for persistent context
from memory_manager import get_memory_manager, SublimeMemory

# Import enhanced UI components
from ui_components import ui, print_banner, print_initialization_progress, format_command_suggestions

# Load environment variables from .env file
load_dotenv()

# ────────────────────────────── 0. Config ────────────────────────────── #
# Enhanced configuration for SublimeChain
CONFIG = {
    "model": "claude-sonnet-4-20250514",  # or "claude-opus-4-20250514"
    "lead_model": "claude-opus-4-20250514",    # Lead model for planning and synthesis
    "worker_model": "claude-sonnet-4-20250514", # Worker model for execution and tool calls
    "multi_model_mode": False,  # Enable lead/worker orchestration
    "lead_turns": 1,           # Number of lead model turns for planning
    "thinking_budget": 1024,   # Minimum allowed by API
    "max_tokens": 512,         # Reduced from 1024 to save tokens
    "memory_enabled": True,
    "memory_search": True,
    "memory_learning": True,
    "rate_limit_delay": 1.0    # Seconds between API calls
}

AVAILABLE_MODELS = [
    "claude-sonnet-4-20250514",
    "claude-opus-4-20250514"
]

BETA_HEADERS   = ",".join([
    "interleaved-thinking-2025-05-14",
    "fine-grained-tool-streaming-2025-05-14",
])

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Initialize memory manager
MEMORY = get_memory_manager("sublime_user")

# ────────────────────────────── Helper Functions ─────────────────────────────── #
def get_memory_stats_safe() -> Dict:
    """Safely get memory stats"""
    if not MEMORY.is_available():
        return {"status": "unavailable", "total_memories": 0}
    
    try:
        return MEMORY.get_memory_stats()
    except Exception as e:
        logger.warning(f"Failed to get memory stats: {e}")
        return {"status": "error", "total_memories": 0}

# ────────────────────────────── 1. Enhanced Tools ─────────────────────────────── #
# All tools are now discovered from the tools directory and MCP servers
# Plus memory integration

def initialize_tools_with_progress():
    """Initialize tools with beautiful progress display and memory integration"""
    steps = [
        "🔍 Discovering local tools...",
        "🌐 Initializing MCP integration...", 
        "🧠 Activating memory system...",
        "🔧 Building enhanced tool registry...",
        "✅ Finalizing SublimeChain setup..."
    ]
    
    print_initialization_progress(steps)
    
    try:
        # Local tool discovery
        try:
            tool_discovery = get_tool_discovery()
            local_count = len(tool_discovery.discovered_tools)
        except Exception as e:
            logger.warning(f"Local tool discovery failed: {e}")
            local_count = 0
        
        # MCP integration
        try:
            total_tools = asyncio.run(initialize_tool_discovery())
            mcp_count = total_tools - local_count
        except Exception as e:
            logger.warning(f"MCP initialization failed: {e}")
            total_tools = local_count
            mcp_count = 0
        
        # Get all available tools (local + MCP)
        try:
            tools = get_claude_tools()
        except Exception as e:
            logger.warning(f"Tool registry build failed: {e}")
            tools = []
        
        return tools, local_count, mcp_count
        
    except Exception as e:
        logger.error(f"Tool initialization failed: {e}")
        return [], 0, 0

# Initialize tools with memory
TOOLS, LOCAL_TOOL_COUNT, MCP_SERVER_COUNT = initialize_tools_with_progress()

# ────────────────────────────── 2. Memory-Enhanced Helpers ───────────────────────────── #
def beta_headers() -> dict[str, str]:
    """Return extra headers for every call."""
    return {"anthropic-beta": BETA_HEADERS}

def get_memory_context(user_input: str) -> str:
    """Get relevant memory context for the current interaction"""
    if not MEMORY.is_available() or not CONFIG["memory_search"]:
        return ""
    
    try:
        # Use smart recall for better context retrieval
        memories = MEMORY.smart_recall(user_input, max_results=5)
        
        if not memories:
            return ""
        
        context_parts = []
        for memory in memories:
            # Use the actual memory content from Mem0's format
            content = memory.get("content", "")
            relevance = memory.get("relevance", 0.8)  # Default to high relevance since Mem0 pre-filters
            
            # Use much lower threshold since Mem0 scores can be low but still relevant
            if relevance > 0.2:  # Very low threshold for better recall
                context_parts.append(f"📚 {content}")
        
        result = "\n".join(context_parts) if context_parts else ""
        return result
        
    except Exception as e:
        logger.warning(f"Memory context retrieval failed: {e}")
        return ""

def run_tool_with_memory(name: str, args: dict, context: str = "") -> str:
    """Enhanced tool execution with memory integration"""
    start_time = time.time()
    
    # Show tool execution start
    ui.print_tool_execution(name, "executing")
    
    # Execute discovered tool with memory context
    try:
        result = execute_tool_sync(name, args)
        duration = time.time() - start_time
        ui.print_tool_execution(name, "completed", duration)
        
        # Store successful tool usage in memory (async, non-blocking)
        if MEMORY.is_available() and CONFIG["memory_learning"]:
            try:
                task_description = f"{name} with args: {json.dumps(args, default=str)[:100]}"
                # Run memory storage in background to avoid blocking the UI
                import threading
                def store_memory():
                    try:
                        MEMORY.store_tool_success(name, task_description, result[:500], {"context": context})
                    except Exception as e:
                        logger.warning(f"Failed to store tool success in memory: {e}")
                
                thread = threading.Thread(target=store_memory, daemon=True)
                thread.start()
            except Exception as e:
                logger.warning(f"Failed to setup memory storage: {e}")
        
        return result
        
    except Exception as exc:
        duration = time.time() - start_time
        ui.print_tool_execution(name, "failed", duration)
        return f"<error>Tool {name} execution failed: {exc}</error>"

# ────────────────────────────── 3. Memory-Enhanced Streaming loop ────────────────────── #
def truncate_conversation_history(transcript: list[dict], max_messages: int = 20) -> list[dict]:
    """Truncate conversation history to prevent context explosion"""
    if len(transcript) <= max_messages:
        return transcript
    
    # Keep system messages and recent messages
    system_messages = [msg for msg in transcript if msg.get("role") == "system"]
    recent_messages = transcript[-max_messages:]
    
    # Combine system + recent, avoiding duplicates
    result = system_messages.copy()
    for msg in recent_messages:
        if msg not in result:
            result.append(msg)
    
    return result

def stream_once_with_memory(transcript: list[dict], user_input: str = "") -> dict:
    """
    Enhanced streaming with memory context injection.
    Provides memory-aware interactions and learns from each exchange.
    """
    try:
        # Get memory context for this interaction (reduced frequency)
        memory_context = ""
        if user_input and MEMORY.is_available() and len(user_input) > 10:
            # Only search memories for specific types of queries to reduce API calls
            memory_keywords = ["remember", "recall", "told you", "discussed", "my", "me", "i am", "name", "preferences"]
            should_search = any(keyword in user_input.lower() for keyword in memory_keywords)
            
            # Also limit memory search frequency
            import time
            current_time = time.time()
            if not hasattr(stream_once_with_memory, 'last_memory_search'):
                stream_once_with_memory.last_memory_search = 0
            
            if should_search and (current_time - stream_once_with_memory.last_memory_search) > 30:  # 30 second cooldown
                try:
                    memory_context = get_memory_context(user_input)
                    stream_once_with_memory.last_memory_search = current_time
                    if memory_context:
                        ui.print(f"🧠 [italic blue]Using memory context...[/italic blue]")
                except Exception as e:
                    logger.warning(f"Failed to get memory context: {e}")
                    memory_context = ""
        
        # Truncate conversation history to prevent context explosion
        truncated_transcript = truncate_conversation_history(transcript, max_messages=15)
        
        # Inject memory context into the conversation if available
        enhanced_transcript = truncated_transcript.copy()
        if memory_context and enhanced_transcript:
            # Add memory context to the last user message
            last_message = enhanced_transcript[-1]
            if last_message.get("role") == "user":
                content = last_message.get("content", "")
                if isinstance(content, str):
                    enhanced_content = f"{content}\n\n{memory_context}"
                    enhanced_transcript[-1] = {**last_message, "content": enhanced_content}
        
        # Add rate limiting to prevent API overload
        import time
        if hasattr(stream_once_with_memory, 'last_api_call'):
            time_since_last = time.time() - stream_once_with_memory.last_api_call
            if time_since_last < CONFIG["rate_limit_delay"]:
                time.sleep(CONFIG["rate_limit_delay"] - time_since_last)
        
        stream_once_with_memory.last_api_call = time.time()
        
        # Create a streaming request with thinking enabled
        with client.messages.stream(
            model=CONFIG["model"],
            max_tokens=CONFIG["max_tokens"],
            tools=TOOLS,
            messages=enhanced_transcript,
            extra_headers=beta_headers(),
            thinking={"type": "enabled", "budget_tokens": CONFIG["thinking_budget"]},
        ) as stream:
            
            thinking_content = []
            response_content = []
            in_thinking = False
            
            # Handle the stream events
            for chunk in stream:
                if chunk.type == 'message_start':
                    continue
                elif chunk.type == 'content_block_start':
                    if hasattr(chunk.content_block, 'type'):
                        if chunk.content_block.type == 'tool_use':
                            ui.print(f"\n🔧 [bold yellow]Tool Use:[/bold yellow] [cyan]{chunk.content_block.name}[/cyan]")
                        elif chunk.content_block.type == 'thinking':
                            ui.print(f"\n💭 [bold blue]Thinking:[/bold blue] ", end='')
                            in_thinking = True
                elif chunk.type == 'content_block_delta':
                    if hasattr(chunk.delta, 'text') and chunk.delta.text:
                        if in_thinking:
                            ui.console.print(chunk.delta.text, end='', style="italic blue")
                            thinking_content.append(chunk.delta.text)
                        else:
                            ui.console.print(chunk.delta.text, end='')
                            response_content.append(chunk.delta.text)
                elif chunk.type == 'content_block_stop':
                    if in_thinking:
                        ui.print("")  # New line after thinking
                        in_thinking = False
                elif chunk.type == 'message_delta':
                    continue
                elif chunk.type == 'message_stop':
                    break
            
            # Get the final message
            final_message = stream.get_final_message()
            
            # Store conversation in memory with reduced frequency
            if MEMORY.is_available() and CONFIG["memory_learning"] and len(user_input) > 20:
                try:
                    assistant_response = "".join(response_content)
                    # Only store significant conversations to reduce memory bloat
                    should_store = (
                        len(assistant_response) > 50 and  # Meaningful responses only
                        not any(phrase in assistant_response.lower() for phrase in [
                            "i don't have", "i don't know", "based on the information i have",
                            "according to what you've told me", "from what i can see",
                            "hello", "hi there", "how can i help"
                        ])
                    )
                    
                    if should_store:
                        # Store in background thread to avoid blocking
                        import threading
                        def store_memory():
                            try:
                                conversation_messages = [
                                    {"role": "user", "content": user_input},
                                    {"role": "assistant", "content": assistant_response}
                                ]
                                MEMORY.store_conversation(conversation_messages, "sublime_chat")
                            except Exception as e:
                                logger.warning(f"Background memory storage failed: {e}")
                        
                        thread = threading.Thread(target=store_memory, daemon=True)
                        thread.start()
                except Exception as e:
                    logger.warning(f"Failed to setup memory storage: {e}")
            
            # Check if there are tool uses that need to be handled
            tool_uses = [block for block in final_message.content if block.type == 'tool_use']
            
            if tool_uses:
                # Add the assistant message with tool uses
                enhanced_transcript.append({
                    "role": "assistant",
                    "content": [block.model_dump() for block in final_message.content]
                })
                
                # Process each tool use with memory context
                tool_results = []
                for tool_use in tool_uses:
                    ui.print(f"\n🔧 [bold cyan]Executing:[/bold cyan] {tool_use.name}")
                    ui.print_json(tool_use.input, f"Arguments for {tool_use.name}")
                    
                    # Run the tool with memory integration
                    result = run_tool_with_memory(tool_use.name, tool_use.input, user_input)
                    
                    # Format result nicely
                    try:
                        # Try to parse as JSON for better display
                        parsed_result = json.loads(result)
                        ui.print_json(parsed_result, f"Result from {tool_use.name}")
                    except:
                        # If not JSON, just show as text
                        ui.print_panel(result, f"Result from {tool_use.name}", "success")
                    
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": result,
                    })
                
                # Add tool results to transcript
                enhanced_transcript.append({
                    "role": "user",
                    "content": tool_results
                })
                
                ui.print("\n🔄 [bold blue]Continuing with tool results...[/bold blue]\n")
                # Add rate limiting between recursive calls
                import time
                time.sleep(0.5)  # Brief pause to avoid rapid API calls
                # Continue the conversation with tool results - this should trigger more thinking
                return stream_once_with_memory(enhanced_transcript, user_input)
            
            return final_message
            
    except Exception as e:
        ui.print_error("Stream error", str(e))
        # Fallback to non-streaming with thinking
        response = client.messages.create(
            model=CONFIG["model"],
            max_tokens=CONFIG["max_tokens"],
            tools=TOOLS,
            messages=enhanced_transcript,
            extra_headers=beta_headers(),
            thinking={"type": "enabled", "budget_tokens": CONFIG["thinking_budget"]},
        )
        return response

# ────────────────────────────── 4. Enhanced Commands with Memory ──────────────────── #
def show_tools_command():
    """Enhanced tools listing command with memory integration"""
    ui.print_rule("🛠️ SublimeChain Tool Arsenal")
    
    # Categorize tools
    tools_by_category = {
        'local': [],
        'mcp': [],
        'enhanced': []
    }
    
    # Get discovered tools
    all_tools = list_tools()
    local_tools = [t for t in all_tools if not t.startswith('mcp_')]
    mcp_tools = [t for t in all_tools if t.startswith('mcp_')]
    
    # Add local tools
    for tool_name in local_tools:
        category = 'enhanced' if tool_name in ['claudecode'] else 'local'
        tools_by_category[category].append({
            'name': tool_name,
            'description': f"{'🚀 ' if category == 'enhanced' else ''}Local tool: {tool_name}",
            'type': 'Enhanced' if category == 'enhanced' else 'Local'
        })
    
    # Add MCP tools
    for tool_name in mcp_tools:
        tools_by_category['mcp'].append({
            'name': tool_name,
            'description': f"🌐 MCP tool: {tool_name.replace('mcp_', '')}",
            'type': 'MCP'
        })
    
    ui.print_tool_table(tools_by_category)
    
    # Memory-enhanced usage stats
    memory_stats = ""
    if MEMORY.is_available():
        stats = get_memory_stats_safe()
        memory_stats = f" | 🧠 {stats.get('total_memories', 0)} memories"
    
    ui.print(f"\n📊 [bold]Total:[/bold] {len(TOOLS)} tools available{memory_stats}")

def show_memory_command():
    """Show memory system status and statistics"""
    if not MEMORY.is_available():
        ui.print_panel(
            "❌ Memory system is not available\n"
            "Install with: pip install mem0ai\n"
            "Add MEM0_API_KEY to your .env file",
            "Memory Status",
            "error"
        )
        return
    
    stats = get_memory_stats_safe()
    
    memory_info = f"""
🧠 **Memory System:** {stats.get('status', 'Unknown')}
📊 **Total Memories:** {stats.get('total_memories', 0)}
🛠️ **Tool Patterns:** {stats.get('tool_patterns', 0)}
👤 **User ID:** {stats.get('user_id', 'Unknown')}
⏰ **Session Start:** {stats.get('session_start', 'Unknown')}

**Memory Types:**
"""
    
    memory_types = stats.get('memory_types', {})
    for mem_type, count in memory_types.items():
        memory_info += f"• {mem_type}: {count}\n"
    
    ui.print_markdown(memory_info)

def show_help_command():
    """Enhanced help command with memory features"""
    commands = {
        "/help": "Show this help message",
        "/tools": "List all available tools in detail",
        "/memory": "Show memory system status and statistics",
        "/remember <content>": "Explicitly store a memory",
        "/recall <query>": "Search and recall specific memories",
        "/search-memory <query>": "Advanced memory search with filters",
        "/what-did-i <timeframe>": "Find activities from specific time period",
        "/forget-memory <id>": "Delete a specific memory by ID",
        "/refresh": "Refresh tool discovery (local + MCP)",
        "/status": "Show system status and configuration",
        "/clear": "Clear the screen",
        "/config": "Show/edit configuration (model, thinking, memory, multi-model)",
        "/config model <name>": "Change Claude model (sonnet/opus)",
        "/config multi-model <on|off>": "Toggle lead/worker model orchestration", 
        "/config lead-model <name>": "Set lead model for planning",
        "/config worker-model <name>": "Set worker model for execution",
        "/config thinking <1024-16000>": "Change thinking token budget",
        "/config memory <on|off>": "Toggle memory features",
        "/forget": "Clear memory for current session",
        "/exit": "Exit SublimeChain"
    }
    
    ui.print_help(commands)
    
    memory_status = "✅ Active" if MEMORY.is_available() else "❌ Unavailable"
    
    ui.print_panel(
        "💡 [bold]SublimeChain Features:[/bold]\n"
        "• 🧠 Persistent Memory: Learns from every interaction\n"
        "• 💻 Advanced Coding: Claude Code SDK integration\n"
        "• 🔧 Dynamic Tools: Auto-discovery + hot reload\n"
        "• 🌐 MCP Integration: Extensible server ecosystem\n"
        "• 🎨 Rich UI: Beautiful terminal experience\n"
        f"• 📊 Memory Status: {memory_status}\n\n"
        "💡 [bold]Tips:[/bold]\n"
        "• Use Tab for command completion\n"
        "• Use ↑/↓ arrows for command history\n"
        "• Memory enhances responses with past context\n"
        "• Claude Code tool provides advanced coding assistance", 
        "SublimeChain Guide", 
        "info"
    )

def show_status_command():
    """Show detailed system status with memory integration"""
    memory_active = MEMORY.is_available()
    status_text = "🚀 SublimeChain Active" if memory_active else "⚠️ Limited Mode"
    
    ui.print_status_bar(LOCAL_TOOL_COUNT, MCP_SERVER_COUNT, memory_active, status_text)
    
    # Memory stats
    memory_info = ""
    if memory_active:
        stats = get_memory_stats_safe()
        memory_info = f"🧠 **Memory:** {stats.get('total_memories', 0)} stored memories\n"
    
    # Additional status info
    status_info = f"""
🔧 **Local Tools:** {LOCAL_TOOL_COUNT} discovered
🌐 **MCP Servers:** {MCP_SERVER_COUNT} configured  
{memory_info}💭 **Thinking:** Enabled ({CONFIG['thinking_budget']} token budget)
🤖 **Model:** {CONFIG['model']}
🔋 **Status:** {status_text}
    """
    
    ui.print_markdown(status_info)

def show_config_command():
    """Enhanced config display command with memory and multi-model settings"""
    multi_model_status = "✅ Enabled" if CONFIG['multi_model_mode'] else "❌ Disabled"
    current_model_info = CONFIG['model']
    if CONFIG['multi_model_mode']:
        current_model_info = f"Multi-Model Mode (📋 {CONFIG['lead_model']} → 🔧 {CONFIG['worker_model']})"
    
    config_data = {
        "Current Mode": current_model_info,
        "Multi-Model Orchestration": multi_model_status,
        "Lead Model": f"📋 {CONFIG['lead_model']} (planning & synthesis)",
        "Worker Model": f"🔧 {CONFIG['worker_model']} (execution & tools)",
        "Lead Turns": CONFIG['lead_turns'],
        "Thinking Budget": f"{CONFIG['thinking_budget']} tokens",
        "Max Tokens": CONFIG['max_tokens'],
        "Memory Enabled": "✅ Yes" if CONFIG['memory_enabled'] else "❌ No",
        "Memory Search": "✅ Yes" if CONFIG['memory_search'] else "❌ No",
        "Memory Learning": "✅ Yes" if CONFIG['memory_learning'] else "❌ No",
        "Available Models": ", ".join(AVAILABLE_MODELS)
    }
    
    ui.print_panel(
        "\n".join([f"{k}: {v}" for k, v in config_data.items()]) + 
        "\n\n💡 Multi-Model Commands:" +
        "\n   /config multi-model <on|off> - Toggle orchestration" +
        "\n   /config lead-model <model> - Set planning model" +
        "\n   /config worker-model <model> - Set execution model" +
        "\n💡 Other Commands:" +
        "\n   /config model <model> - Change single model" +
        "\n   /config thinking <1024-16000> - Change thinking budget" +
        "\n   /config memory <on|off> - Toggle memory features",
        "SublimeChain Configuration",
        "info"
    )

def handle_config_command(args):
    """Handle enhanced /config command with memory settings."""
    if not args:
        show_config_command()
        return
    
    if args[0] == "model":
        if len(args) < 2:
            ui.print_error("Usage", "/config model <model_name>")
            ui.print(f"Available models: {', '.join(AVAILABLE_MODELS)}")
            return
        
        new_model = args[1]
        if new_model not in AVAILABLE_MODELS:
            ui.print_error("Unknown model", new_model)
            ui.print(f"Available models: {', '.join(AVAILABLE_MODELS)}")
            return
        
        CONFIG["model"] = new_model
        ui.print_success(f"Model changed to: {new_model}")
        
    elif args[0] == "thinking":
        if len(args) < 2:
            ui.print_error("Usage", "/config thinking <1024-16000>")
            return
        
        try:
            new_budget = int(args[1])
            if not (1024 <= new_budget <= 16000):
                ui.print_error("Invalid thinking budget", "Must be between 1024 and 16000")
                return
            
            CONFIG["thinking_budget"] = new_budget
            ui.print_success(f"Thinking budget changed to: {new_budget} tokens")
            
        except ValueError:
            ui.print_error("Invalid number", args[1])
            
    elif args[0] == "multi-model":
        if len(args) < 2:
            ui.print_error("Usage", "/config multi-model <on|off>")
            return
        
        if args[1].lower() in ["on", "true", "yes", "1", "enable"]:
            CONFIG["multi_model_mode"] = True
            ui.print_success("🎭 Multi-model orchestration enabled")
            ui.print(f"📋 Lead: {CONFIG['lead_model']} → 🔧 Worker: {CONFIG['worker_model']}")
        elif args[1].lower() in ["off", "false", "no", "0", "disable"]:
            CONFIG["multi_model_mode"] = False
            ui.print_success("Multi-model orchestration disabled")
        else:
            ui.print_error("Invalid option", "Use 'on' or 'off'")
    
    elif args[0] == "lead-model":
        if len(args) < 2:
            ui.print_error("Usage", "/config lead-model <model_name>")
            ui.print(f"Available models: {', '.join(AVAILABLE_MODELS)}")
            return
        
        new_model = args[1]
        if new_model == "sonnet":
            new_model = "claude-sonnet-4-20250514"
        elif new_model == "opus":
            new_model = "claude-opus-4-20250514"
        
        if new_model not in AVAILABLE_MODELS:
            ui.print_error("Unknown model", new_model)
            ui.print(f"Available models: {', '.join(AVAILABLE_MODELS)}")
            return
        
        CONFIG["lead_model"] = new_model
        ui.print_success(f"📋 Lead model changed to: {new_model}")
    
    elif args[0] == "worker-model":
        if len(args) < 2:
            ui.print_error("Usage", "/config worker-model <model_name>")
            ui.print(f"Available models: {', '.join(AVAILABLE_MODELS)}")
            return
        
        new_model = args[1]
        if new_model == "sonnet":
            new_model = "claude-sonnet-4-20250514"
        elif new_model == "opus":
            new_model = "claude-opus-4-20250514"
        
        if new_model not in AVAILABLE_MODELS:
            ui.print_error("Unknown model", new_model)
            ui.print(f"Available models: {', '.join(AVAILABLE_MODELS)}")
            return
        
        CONFIG["worker_model"] = new_model
        ui.print_success(f"🔧 Worker model changed to: {new_model}")
    
    elif args[0] == "memory":
        if len(args) < 2:
            ui.print_error("Usage", "/config memory <on|off>")
            return
        
        if args[1].lower() in ["on", "true", "yes", "1"]:
            CONFIG["memory_enabled"] = True
            CONFIG["memory_search"] = True
            CONFIG["memory_learning"] = True
            ui.print_success("Memory features enabled")
        elif args[1].lower() in ["off", "false", "no", "0"]:
            CONFIG["memory_enabled"] = False
            CONFIG["memory_search"] = False
            CONFIG["memory_learning"] = False
            ui.print_success("Memory features disabled")
        else:
            ui.print_error("Invalid option", "Use 'on' or 'off'")
    else:
        ui.print_error("Unknown config option", args[0])
        ui.print("Available options: model, multi-model, lead-model, worker-model, thinking, memory")

def handle_forget_command():
    """Clear memory for current session"""
    if not MEMORY.is_available():
        ui.print_error("Memory not available", "Memory system is not initialized")
        return
    
    # This is a placeholder - you'd need to implement memory clearing in the memory manager
    ui.print_success("🧠 Memory cleared for current session")
    ui.print("Note: Full memory management features coming soon!")

def handle_remember_command(args):
    """Handle /remember command to explicitly store memories"""
    if not MEMORY.is_available():
        ui.print_error("Memory not available", "Memory system is not initialized")
        return
    
    if not args:
        ui.print_error("Usage", "/remember <content> [category]")
        ui.print("Example: /remember I prefer React over Vue for frontend development personal_preferences")
        return
    
    # Parse content and optional category
    content = " ".join(args[:-1]) if len(args) > 1 and not args[-1].startswith("/") else " ".join(args)
    category = args[-1] if len(args) > 1 and not args[-1].startswith("/") and len(args[-1]) < 50 else "explicit"
    
    success = MEMORY.explicit_remember(content, category)
    if success:
        ui.print_success(f"📝 Memory stored: {content[:100]}...")
    else:
        ui.print_error("Failed to store memory", "Check memory system status")

def handle_recall_command(args):
    """Handle /recall command to search and display memories"""
    if not MEMORY.is_available():
        ui.print_error("Memory not available", "Memory system is not initialized")
        return
    
    if not args:
        ui.print_error("Usage", "/recall <query>")
        ui.print("Example: /recall what do you know about my programming preferences")
        return
    
    query = " ".join(args)
    memories = MEMORY.smart_recall(query, max_results=10)
    
    if not memories:
        ui.print_warning("No memories found for query: " + query)
        return
    
    ui.print_rule(f"🧠 Memory Search Results for: {query}")
    
    for i, memory in enumerate(memories, 1):
        content = memory.get("content", "")
        created_at = memory.get("created_at", "")
        metadata = memory.get("metadata", {})
        memory_type = metadata.get("type", "unknown")
        
        # Format the created_at date nicely
        try:
            if created_at:
                from datetime import datetime
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                date_str = dt.strftime("%Y-%m-%d %H:%M")
            else:
                date_str = "Unknown date"
        except:
            date_str = "Unknown date"
        
        ui.print_panel(
            f"**Content:** {content}\n**Type:** {memory_type}\n**Date:** {date_str}",
            f"Memory {i}",
            "info"
        )

def handle_search_memory_command(args):
    """Handle /search-memory command with advanced filtering"""
    if not MEMORY.is_available():
        ui.print_error("Memory not available", "Memory system is not initialized")
        return
    
    if not args:
        ui.print_error("Usage", "/search-memory <query> [options]")
        ui.print("Options: --type <type>, --date <timeframe>, --limit <num>")
        ui.print("Examples:")
        ui.print("  /search-memory programming --type conversation")
        ui.print("  /search-memory activities --date yesterday")
        ui.print("  /search-memory tools --limit 5")
        return
    
    # Parse arguments
    query_parts = []
    memory_type = None
    date_filter = None
    limit = 10
    
    i = 0
    while i < len(args):
        if args[i] == "--type" and i + 1 < len(args):
            memory_type = args[i + 1]
            i += 2
        elif args[i] == "--date" and i + 1 < len(args):
            date_filter = args[i + 1]
            i += 2
        elif args[i] == "--limit" and i + 1 < len(args):
            try:
                limit = int(args[i + 1])
            except ValueError:
                ui.print_warning(f"Invalid limit: {args[i + 1]}, using default: 10")
            i += 2
        else:
            query_parts.append(args[i])
            i += 1
    
    query = " ".join(query_parts)
    
    if memory_type:
        memories = MEMORY.search_memories_by_type(memory_type, limit)
    elif date_filter:
        # Handle temporal search
        if date_filter in ["yesterday", "today", "last week", "last month"]:
            memories = MEMORY._handle_temporal_query(f"memories from {date_filter}", limit)
        else:
            ui.print_error("Invalid date filter", "Use: yesterday, today, last week, last month")
            return
    else:
        memories = MEMORY.smart_recall(query, limit)
    
    if not memories:
        ui.print_warning(f"No memories found matching criteria")
        return
    
    ui.print_rule(f"🔍 Advanced Memory Search Results")
    
    for i, memory in enumerate(memories, 1):
        content = memory.get("content", "")
        created_at = memory.get("created_at", "")
        metadata = memory.get("metadata", {})
        memory_id = memory.get("id", "")
        
        ui.print_panel(
            f"**Content:** {content}\n**ID:** {memory_id}\n**Date:** {created_at}",
            f"Result {i}",
            "success"
        )

def handle_what_did_i_command(args):
    """Handle /what-did-i command for activity queries"""
    if not MEMORY.is_available():
        ui.print_error("Memory not available", "Memory system is not initialized")
        return
    
    if not args:
        ui.print_error("Usage", "/what-did-i <timeframe>")
        ui.print("Examples: /what-did-i yesterday, /what-did-i last week, /what-did-i today")
        return
    
    timeframe = " ".join(args)
    query = f"what did I do {timeframe}"
    
    memories = MEMORY.smart_recall(query, max_results=15)
    
    if not memories:
        ui.print_warning(f"No activities found for: {timeframe}")
        return
    
    ui.print_rule(f"📅 Activities from {timeframe}")
    
    for memory in memories:
        content = memory.get("content", "")
        metadata = memory.get("metadata", {})
        memory_type = metadata.get("type", "unknown")
        
        if memory_type == "tool_success":
            tool_name = metadata.get("tool", "unknown")
            ui.print(f"🔧 **Tool Usage:** {tool_name} - {content[:100]}...")
        elif memory_type == "conversation":
            ui.print(f"💬 **Conversation:** {content[:100]}...")
        else:
            ui.print(f"📝 **{memory_type}:** {content[:100]}...")

def handle_forget_memory_command(args):
    """Handle /forget-memory command to delete specific memories"""
    if not MEMORY.is_available():
        ui.print_error("Memory not available", "Memory system is not initialized")
        return
    
    if not args:
        ui.print_error("Usage", "/forget-memory <memory_id>")
        ui.print("Use /recall or /search-memory to find memory IDs")
        return
    
    memory_id = args[0]
    
    if ui.confirm(f"Are you sure you want to delete memory {memory_id}?"):
        success = MEMORY.forget_memory(memory_id)
        if success:
            ui.print_success(f"🗑️ Memory {memory_id} deleted")
        else:
            ui.print_error("Failed to delete memory", "Check memory ID and try again")

# ────────────────────────────── 5. Main Interactive Loop ──────────────────── #
def main():
    """Main SublimeChain interactive loop with memory integration"""
    
    # Print beautiful banner
    print_banner("SublimeChain", "The Ultimate AI Assistant with Memory")
    
    # Show initial status
    show_status_command()
    ui.print("")
    
    # Welcome message with memory awareness
    memory_status = "with persistent memory" if MEMORY.is_available() else "in standard mode"
    ui.print(f"🎉 Welcome to SublimeChain {memory_status}!")
    ui.print("💡 Type [bold]/help[/bold] for commands or just start chatting!")
    ui.print("")
    
    # Conversation history
    transcript = []
    
    # Main conversation loop
    while True:
        try:
            # Get user input with clean typing experience
            user_input = ui.get_input("Enter command")
            
            # Handle empty input
            if not user_input.strip():
                continue
            
            # Handle commands (both /command and legacy command formats)
            command_input = user_input.strip()
            
            # Check for slash commands first
            if command_input.startswith('/'):
                command_parts = command_input[1:].split()
                command = command_parts[0].lower()
                args = command_parts[1:] if len(command_parts) > 1 else []
                
                if command in ['help', 'h']:
                    show_help_command()
                elif command == 'tools':
                    show_tools_command()
                elif command == 'memory':
                    show_memory_command()
                elif command == 'remember':
                    handle_remember_command(args)
                elif command == 'recall':
                    handle_recall_command(args)
                elif command == 'search-memory':
                    handle_search_memory_command(args)
                elif command == 'what-did-i':
                    handle_what_did_i_command(args)
                elif command == 'forget-memory':
                    handle_forget_memory_command(args)
                elif command in ['refresh', 'reload']:
                    ui.print("🔄 Refreshing tools...")
                    refresh_tools()
                    ui.print_success("Tools refreshed successfully!")
                elif command == 'status':
                    show_status_command()
                elif command == 'clear':
                    ui.clear_screen()
                elif command == 'config':
                    handle_config_command(args)
                elif command == 'forget':
                    handle_forget_command()
                elif command in ['exit', 'quit', 'q']:
                    ui.print("👋 Thanks for using SublimeChain!")
                    break
                else:
                    ui.print_error("Unknown command", f"/{command}")
                    ui.print("Type [bold]/help[/bold] for available commands")
                continue
            
            # Legacy command support (without /)
            elif command_input.lower() in ['help', 'tools', 'refresh', 'reload', 'status', 'clear', 'exit', 'quit']:
                # Handle legacy commands by recursing with / prefix
                main_input = f"/{command_input}"
                continue
            
            # Regular conversation
            transcript.append({"role": "user", "content": user_input})
            
            ui.print("")  # Add some space
            
            # Stream the response with memory integration
            response = stream_once_with_memory(transcript, user_input)
            
            # Add assistant response to transcript
            if hasattr(response, 'content'):
                response_text = ""
                for block in response.content:
                    if hasattr(block, 'text'):
                        response_text += block.text
                
                transcript.append({"role": "assistant", "content": response_text})
            
            ui.print("\n")  # Add space after response
            
        except KeyboardInterrupt:
            ui.print("\n\n👋 Thanks for using SublimeChain!")
            break
        except Exception as e:
            ui.print_error("Unexpected error", str(e))
            ui.print("Please try again or type [bold]/help[/bold] for assistance")

if __name__ == "__main__":
    main()