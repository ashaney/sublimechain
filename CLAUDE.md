# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with the SublimeChain repository.

SublimeChain is the ultimate AI assistant with persistent memory, advanced coding capabilities, and dynamic tool discovery.

## Commands

**Development Commands:**
- `uv run sublimechain.py` - 🚀 SublimeChain with full memory capabilities (RECOMMENDED)
- `uv run thinkchain.py` - Enhanced UI with rich formatting and interactive features
- `uv run thinkchain_cli.py` - Minimal CLI version with basic dependencies
- `uv run run.py` - Smart launcher (auto-detects best UI based on available dependencies)
- `uv run test_mcp.py` - Test MCP (Model Context Protocol) integration

**Dependency Management:**
- We use `bun` for general toolkit (per user preference)
- We use `uv` for Python package management and execution
- All main scripts support `uv run` with inline dependency declarations
- Traditional installation: `uv pip install -r requirements.txt`
- SublimeChain requires: `mem0ai`, `openai` (for Mem0), optional `qdrant-client`
- MCP servers via npm: `@modelcontextprotocol/server-github`, `@tavily/mcp-server`

**Tool Development:**
- `/refresh` or `/reload` - Hot reload tools during development
- `/tools` - Browse available tools by category (local + MCP + enhanced)
- `/memory` - Show memory system status and statistics
- `/forget` - Clear memory for current session
- `/config memory <on|off>` - Toggle memory features
- Create new tools in `/tools/` directory following `BaseTool` interface

## Architecture

**Core Components:**
- `sublimechain.py` - 🚀 Main SublimeChain interface with memory, enhanced streaming
- `memory_manager.py` - Persistent AI memory system using Mem0
- `tools/claudecode_tool.py` - Advanced coding assistant with Claude Code SDK integration
- `thinkchain.py` - Legacy enhanced UI with rich formatting, progress bars, streaming
- `thinkchain_cli.py` - Minimal CLI version with basic terminal output
- `tool_discovery.py` - Automatic tool discovery system for local and MCP tools
- `tools/base.py` - BaseTool abstract interface that all tools must implement
- `ui_components.py` - Rich UI components for enhanced terminal experience
- `mcp_integration.py` - Model Context Protocol server integration

**Tool System:**
- Local tools in `/tools/` directory auto-discovered at startup
- All tools inherit from `BaseTool` with required: `name`, `description`, `input_schema`, `execute()`
- Enhanced tools: `claudecode` (advanced coding with memory patterns)
- MCP (Model Context Protocol) servers configured in `mcp_config.json` (GitHub, Tavily enabled)
- Tool results are injected back into Claude's thinking stream for enhanced reasoning
- Memory integration: Successful tool patterns are learned and suggested

**Streaming Architecture:**
- Uses Claude's `interleaved-thinking-2025-05-14` and `fine-grained-tool-streaming-2025-05-14` beta features
- Memory context injection: Relevant past context automatically enhances responses
- Tool execution results fed back into Claude's thinking process mid-response
- Memory learning: Each successful interaction is stored for future reference
- Server-sent events (SSE) for real-time streaming with progress indicators
- Concurrent tool execution when possible

**Configuration:**
- Model: `claude-sonnet-4-20250514` (default) or `claude-opus-4-20250514`
- Thinking budget: 1024-16000 tokens (configurable via `/config thinking <tokens>`)
- Memory: Configurable via `/config memory <on|off>` commands
- Runtime config changes via `/config model <model>` commands
- Environment variables in `.env` file:
  - `ANTHROPIC_API_KEY` (required)
  - `MEM0_API_KEY` (required for memory)
  - `GITHUB_PERSONAL_ACCESS_TOKEN` (optional for GitHub MCP)
  - `TAVILY_API_KEY` (optional for Tavily MCP)

**Available Tools Categories:**
- Enhanced AI Tools: claudecode (advanced coding with memory patterns)
- Web & Data: weathertool, duckduckgotool, webscrapertool
- File & Development: filecreatortool, fileedittool, filecontentreadertool, createfolderstool, diffeditortool
- Development & Package Management: uvpackagemanager, lintingtool, toolcreator
- Enhanced MCP Servers: GitHub (enabled), Tavily (enabled), SQLite, Puppeteer, Filesystem, Brave Search

## Tool Development

**Creating New Tools:**
1. Create file in `/tools/` directory (e.g., `mytool.py`)
2. Inherit from `BaseTool` with required attributes
3. Use `/refresh` to hot reload without restart
4. Test with `/tools` command to verify discovery
5. Consider memory integration for enhanced patterns

**Tool Requirements:**
- Class name must match filename
- Must implement: `name`, `description`, `input_schema`, `execute(**kwargs) -> str`
- Use JSON Schema for `input_schema` validation
- Return string results from `execute()` method
- Handle errors gracefully with try/catch blocks
- Optional: Integrate with memory manager for pattern learning

**Memory-Enhanced Tools:**
- See `tools/claudecode_tool.py` for memory integration example
- Use `from memory_manager import get_memory_manager, remember_success`
- Store successful patterns with `remember_success(tool_name, task, result)`
- Search relevant memories with `memory.recall_context(query)`

**Enhanced MCP Integration:**
- Configure servers in `mcp_config.json` (GitHub and Tavily enabled by default)
- Support for uvx/npx installed MCP servers
- Unified tool registry combines local, enhanced, and MCP tools
- Test MCP with `python test_mcp.py`