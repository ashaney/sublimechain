# SublimeChain

The Ultimate AI Assistant with persistent memory, advanced coding capabilities, and dynamic tool discovery. Built on Claude's streaming interface with memory-enhanced interactions that learn and evolve over time.

**Created by [Martin Bowling](https://martinbowling.com)** • [GitHub](https://github.com/martinbowling) • [Twitter/X](https://x.com/martinbowling)

## Overview

SublimeChain is the ultimate AI assistant that transcends traditional limitations through:

### 🧠 **Persistent Memory System**
- **Learns from every interaction** - Remembers your preferences, patterns, and successful solutions
- **Context-aware responses** - Leverages past conversations to provide better assistance
- **Pattern recognition** - Identifies successful tool usage patterns and suggests improvements
- **Cross-session continuity** - Pick up exactly where you left off, days or weeks later

### 💻 **Advanced Coding Capabilities**  
- **Claude Code SDK integration** - Professional-grade code analysis, generation, and refactoring
- **Memory-enhanced coding** - Learns your coding style and project patterns
- **Multi-file project understanding** - Works across entire codebases with intelligent context
- **Debugging assistance** - Contextual error resolution based on past solutions

### 🔧 **Dynamic Tool Ecosystem**
- **Interleaved and extended thinking** - Claude thinks through problems step-by-step in real-time
- **Fine-grained tool streaming** - Watch tools execute with live progress updates
- **Memory-enhanced tool execution** - Tools learn from successful usage patterns
- **MCP server integration** - GitHub, Tavily, and extensible server ecosystem
- **Hot-reloadable tools** - Develop and test tools without restarting

### ⚡ **Streaming Intelligence**
- **Real-time thinking visualization** - Watch Claude's reasoning process unfold
- **Memory context injection** - Relevant past context automatically enhances responses
- **Tool result integration** - Results are fed back into Claude's thinking process
- **Concurrent execution** - Multiple tools run simultaneously for complex workflows

The system combines local Python tools, MCP servers, persistent memory, and advanced coding capabilities to create an AI assistant that truly learns and evolves with you.

## 🚀 Quick Start

### Option 1: Zero-Setup with `uv run` (Recommended)

```bash
# Clone the repository
git clone https://github.com/martinbowling/SublimeChain.git
cd SublimeChain

# Set up your API keys
cat > .env << EOF
ANTHROPIC_API_KEY=your_anthropic_api_key_here
MEM0_API_KEY=your_mem0_api_key_here
GITHUB_PERSONAL_ACCESS_TOKEN=your_github_token_here
TAVILY_API_KEY=your_tavily_api_key_here
EOF

# Run immediately - uv handles all dependencies automatically!
uv run sublimechain.py   # 🚀 SublimeChain with full memory capabilities
uv run thinkchain.py     # Legacy enhanced UI mode
uv run thinkchain_cli.py # Minimal CLI version  
uv run run.py            # Smart launcher (auto-detects best UI)
```

### Option 2: Traditional Installation

```bash
# Clone and set up
git clone https://github.com/martinbowling/SublimeChain.git
cd SublimeChain

# Install dependencies
uv pip install -r requirements.txt
# or: pip install -r requirements.txt

# Install MCP servers (optional but recommended)
npm install -g @modelcontextprotocol/server-github
npm install -g @tavily/mcp-server

# Set up your API keys
cat > .env << EOF
ANTHROPIC_API_KEY=your_anthropic_api_key_here
MEM0_API_KEY=your_mem0_api_key_here
GITHUB_PERSONAL_ACCESS_TOKEN=your_github_token_here
TAVILY_API_KEY=your_tavily_api_key_here
EOF

# Run SublimeChain
python sublimechain.py   # 🚀 Full SublimeChain experience
python run.py            # Smart launcher
python thinkchain.py     # Legacy enhanced UI
python thinkchain_cli.py # CLI version
```

## ✨ Key Features

### 🧠 Persistent Memory System  
SublimeChain's revolutionary memory system creates truly intelligent, evolving interactions:

1. **Every interaction is remembered** - Conversations, successful solutions, preferences
2. **Context-aware responses** - Relevant memories are automatically surfaced
3. **Pattern learning** - Successful tool usage patterns are identified and suggested
4. **Cross-session continuity** - Continue conversations from days or weeks ago
5. **Personalized experience** - The AI learns your coding style, preferences, and workflow

### 💻 Advanced Coding Intelligence
Built-in Claude Code SDK integration provides professional-grade coding assistance:

1. **Memory-enhanced coding** - Learns from your past code patterns and style
2. **Multi-file project analysis** - Understands entire codebases, not just snippets  
3. **Intelligent refactoring** - Suggests improvements based on learned best practices
4. **Contextual debugging** - Leverages memory of similar past issues and solutions
5. **Architecture guidance** - Recommends patterns based on successful past implementations

### ⚡ Enhanced Thinking Integration
Building on the core innovation of tool result injection with memory enhancement:

1. **Memory context injection** - Relevant past context enhances Claude's thinking
2. **Tool execution learning** - Successful patterns are remembered and suggested
3. **Contextual tool selection** - Memory guides optimal tool choices
4. **Results fed back** - Tool outputs immediately enhance Claude's reasoning process
5. **Continuous improvement** - Each interaction makes the system smarter

### 🔧 Dynamic Tool Discovery
- **Local Tools**: Automatically discovers Python tools from the `/tools` directory
- **MCP Integration**: Connects to Model Context Protocol servers for extended functionality
- **Hot Reloading**: Use `refresh` command to reload tools during development
- **Unified Registry**: All tools (local + MCP) work identically in the streaming interface

### 🎨 Enhanced CLI Interface
- Rich formatting with colors, borders, and progress indicators
- Interactive tool browser with categorized displays
- Command autocomplete and history
- Real-time thinking visualization with syntax highlighting
- Graceful degradation to standard text interface

### ⚡ Streaming Architecture
- Server-sent events (SSE) for real-time communication
- Fine-grained streaming of tool execution progress
- Concurrent tool execution when possible
- Robust error handling and recovery

### 🔧 Developer Experience
- **Zero-setup execution** with `uv run` - no virtual environments or dependency installation needed
- **Automatic tool discovery** from `/tools` directory
- **Hot reloading** with `/refresh` command during development
- **Rich error messages** and graceful degradation when dependencies are missing

## 🛠 Technical Architecture

### Tool Injection System

The key technical innovation is the **tool result injection mechanism**:

```python
# Tool results are injected back into Claude's thinking process
async def stream_once(messages, tools):
    # Start streaming with thinking enabled
    async with client.messages.stream(
        model="claude-sonnet-4-20250514",
        messages=messages,
        tools=tools,
        betas=["interleaved-thinking-2025-05-14", "fine-grained-tool-streaming-2025-05-14"],
        thinking_budget=1024
    ) as stream:
        
        async for event in stream:
            if event.type == "tool_use":
                # Execute tool and inject result back into stream
                result = await execute_tool(event.name, event.input)
                
                # This result becomes part of Claude's thinking context
                # for the remainder of the response
                yield {"type": "tool_result", "content": result}
```

This creates a feedback loop where:
1. Claude's initial thinking leads to tool use
2. Tool results inform continued thinking
3. Final response incorporates both reasoning and tool outcomes

### Tool Discovery Pipeline

```
Local Tools (/tools/*.py) → Validation → Registry
                                         ↓
MCP Servers (config.json) → Connection → Registry → Unified Tool List → Claude API
```

Each tool must implement the `BaseTool` interface:
```python
class BaseTool:
    @property
    def name(self) -> str: ...
    
    @property  
    def description(self) -> str: ...
    
    @property
    def input_schema(self) -> Dict[str, Any]: ...
    
    def execute(self, **kwargs) -> str: ...
```

### Streaming Event Flow

```
User Input → Claude API → Thinking Stream → Tool Detection → Tool Execution
     ↑                                                            ↓
Response ← Thinking Integration ← Tool Result Injection ← Tool Output
```

## 📚 SublimeChain Tool Arsenal

### 🚀 Enhanced AI Tools

**💻 Claude Code Integration:**
- **claudecode**: Professional-grade coding assistant with memory-enhanced patterns
  - Advanced code generation, refactoring, and debugging
  - Multi-file project analysis and architecture guidance
  - Memory-aware suggestions based on past successful solutions
  - Context-sensitive code review and optimization

### 🛠️ Local Tools (`/tools` directory)

**🌐 Web & Data Tools:**
- **weathertool**: Real weather data from wttr.in API for any location worldwide
- **duckduckgotool**: Live DuckDuckGo search results for web queries and restaurant searches
- **webscrapertool**: Enhanced web scraper that extracts main content from any webpage

**📁 File & Development Tools:** 
- **filecreatortool**: Creates new files with specified content and directory structure
- **fileedittool**: Advanced file editing with full/partial content replacement and search/replace
- **filecontentreadertool**: Reads and returns content from multiple files simultaneously
- **createfolderstool**: Creates directories and nested folder structures
- **diffeditortool**: Precise text snippet replacement in files

**⚙️ Development & Package Management:**
- **uvpackagemanager**: Complete interface to uv package manager for Python projects
- **lintingtool**: Runs Ruff linter on Python files to detect and fix code issues
- **toolcreator**: Dynamically creates new tools based on natural language descriptions

### 🌐 Enhanced MCP Server Integration
Configure in `mcp_config.json`:
- **GitHub**: Repository management, issues, pull requests, and code analysis
- **Tavily**: Advanced web search and research capabilities  
- **SQLite**: Database operations and queries
- **Puppeteer**: Web browser automation
- **Filesystem**: Advanced file system operations  
- **Brave Search**: Alternative web search integration

## 🎮 SublimeChain Commands

While chatting with SublimeChain, you can use these enhanced slash commands:

**🧠 Memory Commands:**
- `/memory` - Show memory system status and statistics
- `/forget` - Clear memory for current session
- `/config memory <on|off>` - Toggle memory features

**🔧 Tool & System Commands:**
- `/tools` - Browse all available tools by category (local + MCP + enhanced)
- `/refresh` or `/reload` - Refresh tool discovery (picks up new tools)
- `/status` - Show comprehensive system status including memory stats
- `/clear` - Clear screen while preserving status bar

**⚙️ Configuration Commands:**
- `/config` - Show current configuration (model, thinking, memory)
- `/config model <model_name>` - Switch between Claude models (sonnet/opus)
- `/config thinking <1024-16000>` - Adjust thinking token budget
- `/config memory <on|off>` - Toggle memory learning and search

**ℹ️ Help & Navigation:**
- `/help` - Show comprehensive help with SublimeChain features
- `/exit` or `/quit` - End the conversation

**Legacy Support**: All commands work without the `/` prefix for backward compatibility.

## ⚙️ SublimeChain Configuration

### Environment Setup
Create `.env` file with all required API keys:
```bash
# Required for core functionality
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Required for memory system  
MEM0_API_KEY=your_mem0_api_key_here

# Optional for enhanced MCP servers
GITHUB_PERSONAL_ACCESS_TOKEN=your_github_token_here
TAVILY_API_KEY=your_tavily_api_key_here
BRAVE_API_KEY=your_brave_search_api_key_here

# Optional for Claude Code SDK (if using npm-installed version)
# OPENAI_API_KEY=your_openai_key_here
```

**Getting API Keys:**
- **Anthropic API**: [console.anthropic.com](https://console.anthropic.com)
- **Mem0 API**: [app.mem0.ai](https://app.mem0.ai) 
- **GitHub Token**: GitHub Settings → Developer settings → Personal access tokens
- **Tavily API**: [tavily.com](https://tavily.com)
- **Brave Search**: [api.search.brave.com](https://api.search.brave.com)

### Enhanced MCP Server Configuration
Edit `mcp_config.json` for SublimeChain's enhanced capabilities:
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": ""
      },
      "description": "GitHub repository and issue management",
      "enabled": true
    },
    "tavily": {
      "command": "npx", 
      "args": ["-y", "@tavily/mcp-server"],
      "env": {
        "TAVILY_API_KEY": ""
      },
      "description": "Advanced web search and research",
      "enabled": true
    },
    "sqlite": {
      "command": "uvx",
      "args": ["mcp-server-sqlite", "--db-path", "./database.db"],
      "description": "SQLite database operations",
      "enabled": true
    },
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
      "description": "Web browser automation",
      "enabled": false
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users"],
      "description": "File system operations", 
      "enabled": false
    }
  }
}
```

### Model Configuration
The system supports both Claude models with configurable settings:

**Available Models:**
- `claude-sonnet-4-20250514` (default) - Fast and efficient
- `claude-opus-4-20250514` - Most capable, slower

**Configurable Settings:**
- Thinking budget: 1024-16000 tokens (default: 1024)
- Max response tokens: 1024
- Beta features: `interleaved-thinking-2025-05-14`, `fine-grained-tool-streaming-2025-05-14`

**Runtime Configuration:**
```bash
# Change model during conversation
/config model claude-opus-4-20250514

# Increase thinking budget for complex problems  
/config thinking 8192
```

## 🔧 Development

### Creating New Local Tools

Creating a new tool is straightforward - just follow these steps:

#### 1. Create Tool File
Create a new Python file in the `/tools/` directory (e.g., `/tools/mytool.py`):

```python
from tools.base import BaseTool

class MyTool(BaseTool):
    name = "mytool"
    description = """
    A detailed description of what your tool does.
    
    Use this tool when users ask about:
    - Specific use case 1
    - Specific use case 2
    - "Keywords that should trigger this tool"
    """
    
    input_schema = {
        "type": "object",
        "properties": {
            "input_param": {
                "type": "string",
                "description": "Description of this parameter"
            },
            "optional_param": {
                "type": "integer", 
                "description": "Optional parameter with default",
                "default": 10
            }
        },
        "required": ["input_param"]
    }
    
    def execute(self, **kwargs) -> str:
        input_param = kwargs.get("input_param")
        optional_param = kwargs.get("optional_param", 10)
        
        # Your tool logic here
        result = f"Processed: {input_param} with {optional_param}"
        
        return result
```

#### 2. Key Requirements
- **Class name**: Must match filename (e.g., `MyTool` for `mytool.py`)
- **Inherit from BaseTool**: Import from `tools.base`
- **Four required attributes**: `name`, `description`, `input_schema`, `execute()` method
- **Return strings**: The `execute()` method must return a string result

#### 3. Tool Discovery
- Tools are automatically discovered on startup
- Use `/refresh` command to reload tools without restarting
- Check with `/tools` command to see your new tool listed

#### 4. Best Practices
- **Descriptive names**: Use clear, action-oriented names
- **Rich descriptions**: Include use cases and keywords that should trigger the tool
- **Input validation**: Use comprehensive JSON schemas
- **Error handling**: Wrap risky operations in try/catch blocks
- **Helpful output**: Return formatted, readable results

### Adding MCP (Model Context Protocol) Servers

MCP allows integration with external servers that provide additional tools:

#### 1. Install MCP Server
Most MCP servers can be installed via `uvx` or `npx`:

```bash
# Install SQLite MCP server
uvx install mcp-server-sqlite

# Install Puppeteer MCP server (requires Node.js)
npm install -g @modelcontextprotocol/server-puppeteer

# Install Brave Search MCP server  
npm install -g @modelcontextprotocol/server-brave-search
```

#### 2. Configure MCP Server
Edit `mcp_config.json` to add your server:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "uvx",
      "args": ["my-mcp-server", "--custom-arg", "value"],
      "description": "Description of what this server provides",
      "enabled": true,
      "env": {
        "API_KEY": "your_api_key_if_needed"
      }
    }
  }
}
```

#### 3. Available MCP Servers
Popular MCP servers you can integrate:

**Data & Storage:**
- `mcp-server-sqlite` - Database operations
- `mcp-server-postgres` - PostgreSQL integration
- `mcp-server-redis` - Redis cache operations

**Web & Automation:**
- `@modelcontextprotocol/server-puppeteer` - Browser automation
- `@modelcontextprotocol/server-brave-search` - Web search
- `@modelcontextprotocol/server-filesystem` - File operations

**APIs & Services:**
- `@modelcontextprotocol/server-github` - GitHub integration
- `@modelcontextprotocol/server-slack` - Slack integration
- `mcp-server-aws` - AWS operations

#### 4. Test MCP Integration
After adding a server, test it:

```bash
# Test MCP functionality
python test_mcp.py

# Start ThinkChain and check tools
python thinkchain.py
/tools  # Should show both local and MCP tools
```

### Development Workflow

#### 1. Tool Development Cycle
```bash
# Create tool
vim tools/newtool.py

# Test tool
python thinkchain.py
/refresh  # Reload tools
"Use my new tool for X"  # Test with Claude

# Iterate and improve
vim tools/newtool.py
/refresh  # Reload again
```

#### 2. Debugging Tools
- Use `print()` statements in your `execute()` method - they'll show in console
- Return error messages as strings for Claude to see
- Check the tool discovery logs on startup

### Running Different Interfaces
```bash
# Traditional Python execution
python run.py            # Smart launcher
python thinkchain.py     # Full-featured UI
python thinkchain_cli.py # Minimal dependencies

# Using uv run (handles dependencies automatically)
uv run run.py            # Smart launcher
uv run thinkchain.py     # Full-featured UI
uv run thinkchain_cli.py # Minimal dependencies
```

## 📋 Dependencies

### Core Requirements
- `anthropic>=0.25.0` - Claude API client
- `sseclient-py` - Server-sent events handling
- `pydantic` - Data validation and schemas
- `python-dotenv` - Environment variable management

### Enhanced UI (Optional)
- `rich` - Terminal formatting and colors
- `prompt_toolkit` - Interactive command line features

### MCP Integration (Optional)
- `mcp` - Model Context Protocol client
- MCP server packages (installed via `uvx` or `npx`)

### Tool Dependencies (Optional)
Some tools require additional packages that are installed automatically:

**Web Tools:** (weathertool, duckduckgotool, webscrapertool)
- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing

**Note**: Missing dependencies are handled gracefully - tools that can't import will be skipped during discovery with informative error messages.

### UV Run Support
All main scripts include inline dependency declarations that make them compatible with `uv run`:

```python
#!/usr/bin/env python3
# /// script
# dependencies = [
#     "anthropic>=0.25.0",
#     "sseclient-py",
#     "pydantic", 
#     "python-dotenv",
#     "rich>=13.0.0",
#     "requests",
#     "beautifulsoup4",
#     "mcp",
#     "httpx",
# ]
# ///
```

**Benefits of `uv run`:**
- ✅ **Zero setup** - No need to create virtual environments or install dependencies
- ✅ **Automatic dependency management** - uv handles everything
- ✅ **Isolated execution** - Each run gets a clean environment
- ✅ **Cross-platform** - Works identically on macOS, Linux, and Windows

```bash
# All these work immediately after cloning:
uv run thinkchain.py     # Enhanced UI with all features
uv run thinkchain_cli.py # Minimal CLI version  
uv run run.py            # Smart launcher
uv run test_mcp.py       # Test MCP integration
```

## 🤝 Contributing

This project is designed to be **forked and extended**! Here are some ideas:

- **Add new local tools** for your specific use cases
- **Integrate additional MCP servers** from the growing ecosystem
- **Enhance the UI** with new visualization features
- **Extend the streaming architecture** for custom event types
- **Build domain-specific tool collections** (data science, web dev, etc.)

### Getting Started with Your Fork

The process is straightforward with `uv run`:

```bash
# Fork and clone
git clone https://github.com/yourusername/your-thinkchain-fork.git
cd your-thinkchain-fork

# Set up API key
echo "ANTHROPIC_API_KEY=your_key" > .env

# Create your first tool
vim tools/yourtool.py

# Test immediately with uv run (no setup needed!)
uv run thinkchain.py
/refresh  # Loads your new tool
"Use my new tool for X"  # Test with Claude
```

### Fork Ideas
- **Data Science ThinkChain**: Add pandas, matplotlib, jupyter tools
- **Web Development ThinkChain**: Add React, npm, git, deployment tools
- **DevOps ThinkChain**: Add Docker, Kubernetes, AWS/GCP tools
- **Research ThinkChain**: Add academic paper search, citation tools

## 📄 License

MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by [Pietro Schirano's chain of tools concept](https://x.com/skirano/status/1933208161244086430) - we loved the idea and decided to crank out our own version!
- Built with [Anthropic's Claude API](https://www.anthropic.com/)
- MCP integration powered by the [Model Context Protocol](https://modelcontextprotocol.io/)
- Enhanced UI built with [Rich](https://github.com/Textualize/rich) and [Prompt Toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit)

---

**Ready to think differently about AI tool integration?** Fork ThinkChain and start building! 🚀
