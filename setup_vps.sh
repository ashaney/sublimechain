#!/bin/bash

# 🚀 SublimeChain VPS Setup Script
# This script handles all package installation and environment setup
# Run this AFTER completing SSH security configuration
# Usage: bash setup_vps.sh

set -e  # Exit on any error

echo "🚀 Starting SublimeChain VPS Setup..."
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Don't run this script as root! Run as your regular user (sublime)."
    exit 1
fi

print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y
print_success "System packages updated"

print_status "Installing essential packages..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    htop \
    byobu \
    tmux \
    nano \
    vim \
    unzip \
    build-essential \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release
print_success "Essential packages installed"

# Install Node.js (latest LTS)
print_status "Installing Node.js..."
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
    sudo apt-get install -y nodejs
    print_success "Node.js installed: $(node --version)"
else
    print_success "Node.js already installed: $(node --version)"
fi

# Install uv (Python package manager)
print_status "Installing uv (Python package manager)..."
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Source bashrc to get uv in current session
    export PATH="$HOME/.local/bin:$PATH"
    print_success "uv installed successfully"
else
    print_success "uv already installed"
fi

# Install MCP servers (only the ones that are enabled and exist)
print_status "Installing MCP servers..."

# Install npm-based MCP servers (only enabled ones)
print_status "Installing npm-based MCP servers..."
sudo npm install -g @modelcontextprotocol/server-github
sudo npm install -g @notionhq/notion-mcp-server  
sudo npm install -g pushover-mcp-v2

# Install optional MCP servers (disabled by default but available)
print_status "Installing optional MCP servers..."
sudo npm install -g @modelcontextprotocol/server-puppeteer
sudo npm install -g @modelcontextprotocol/server-filesystem
# @modelcontextprotocol/server-fetch is Python-based (uvx), not npm

# Install Python-based MCP servers via uvx
print_status "Installing Python-based MCP servers..."
if command -v uvx &> /dev/null; then
    uvx --help > /dev/null 2>&1 && uvx install mcp-server-sqlite || print_warning "uvx install failed for mcp-server-sqlite"
    uvx --help > /dev/null 2>&1 && uvx install mcp-server-fetch || print_warning "uvx install failed for mcp-server-fetch"
else
    print_warning "uvx not available yet, Python MCP servers will be installed on first use"
fi

print_success "MCP servers installed"

# Clone SublimeChain repository (if not already present)
print_status "Setting up SublimeChain..."
if [ ! -d "$HOME/sublimechain" ]; then
    print_status "Repository not found. You'll need to either:"
    echo "  1. Clone from GitHub: git clone https://github.com/ashaney/sublimechain.git"
    echo "  2. Upload files via SCP from your local machine"
    echo ""
    echo "For SCP upload, run this from your LOCAL machine:"
    echo "  scp -i ~/.ssh/sublime_ed25519 -P XXXX -r /path/to/sublimechain sublime@YOUR_SERVER_IP:~/"
    echo ""
    read -p "Press Enter when you have the sublimechain directory in your home folder..."
fi

if [ -d "$HOME/sublimechain" ]; then
    cd $HOME/sublimechain
    print_success "Found thinkchain directory"
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        print_status "Creating .env file template..."
        cat > .env << 'EOF'
# Required API Keys
ANTHROPIC_API_KEY=your-anthropic-key-here
MEM0_API_KEY=your-mem0-key-here

# Optional MCP Integration Keys  
GITHUB_PERSONAL_ACCESS_TOKEN=your-github-token-here
TAVILY_API_KEY=your-tavily-key-here
NOTION_API_TOKEN=your-notion-token-here
PUSHOVER_API_TOKEN=your-pushover-token-here
PUSHOVER_USER_KEY=your-pushover-user-key-here

# System Settings
POSTHOG_DISABLED=1
DISABLE_TELEMETRY=1
DO_NOT_TRACK=1
ANALYTICS_DISABLED=1
EOF
        print_warning "Created .env template - YOU MUST EDIT IT WITH YOUR API KEYS!"
        print_warning "Edit with: nano ~/.env or nano ~/sublimechain/.env"
    else
        print_success ".env file already exists"
    fi
else
    print_error "sublimechain directory not found! Please clone/upload the repository first."
    exit 1
fi

# Configure byobu
print_status "Configuring byobu..."
byobu-enable
print_success "byobu enabled by default"

# Create persistent byobu session for SublimeChain
print_status "Creating persistent SublimeChain session..."
if ! byobu list-sessions 2>/dev/null | grep -q "sublime"; then
    byobu new-session -d -s sublime -c "$HOME/sublimechain"
    print_success "Created 'sublime' byobu session"
else
    print_success "SublimeChain byobu session already exists"
fi

# Add sublime alias to .bashrc
print_status "Adding 'sublime' command alias..."
if ! grep -q "alias sublime=" "$HOME/.bashrc"; then
    echo "" >> "$HOME/.bashrc"
    echo "# SublimeChain aliases" >> "$HOME/.bashrc"
    echo "alias sublime='cd ~/sublimechain && uv run sublimechain.py'" >> "$HOME/.bashrc"
    echo "alias sublime-attach='byobu attach-session -t sublime'" >> "$HOME/.bashrc"
    echo "alias sublime-session='cd ~/sublimechain && byobu attach-session -t sublime'" >> "$HOME/.bashrc"
    print_success "Added sublime aliases to .bashrc"
else
    print_success "sublime aliases already exist in .bashrc"
fi

# Add uv to PATH in .bashrc if not already there
if ! grep -q "/.local/bin" "$HOME/.bashrc"; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    print_success "Added uv to PATH in .bashrc"
fi

# Test SublimeChain dependencies
print_status "Testing SublimeChain setup..."
cd "$HOME/sublimechain"
if uv run python -c "import anthropic; print('✅ Anthropic SDK available')" 2>/dev/null; then
    print_success "SublimeChain dependencies look good!"
else
    print_warning "Some dependencies might be missing, but uv will handle them on first run"
fi

print_success "=================================================="
print_success "🎉 SublimeChain VPS setup complete!"
print_success "=================================================="
echo ""
echo "📋 Next steps:"
echo "  1. Edit your API keys: nano ~/sublimechain/.env"
echo "  2. Reload your shell: source ~/.bashrc"
echo "  3. Test SublimeChain: sublime"
echo "  4. Or attach to session: sublime-session"
echo ""
echo "🔧 Useful commands:"
echo "  sublime              - Run SublimeChain directly"
echo "  sublime-attach       - Attach to existing byobu session"  
echo "  sublime-session      - CD to sublimechain and attach to session"
echo "  byobu attach -t sublime - Alternative attach command"
echo ""
echo "📱 Mobile workflow:"
echo "  1. SSH from iOS: ssh -i key -p 2847 sublime@YOUR_SERVER_IP"
echo "  2. Run: sublime-session"
echo "  3. Start your task"
echo "  4. Press F6 to detach"
echo "  5. Close SSH app"
echo "  6. Get notification when done!"
echo ""
print_warning "⚠️  Don't forget to:"
print_warning "   - Add your API keys to .env file"
print_warning "   - Test the complete workflow"
print_warning "   - Set up Vultr snapshots for backups"
