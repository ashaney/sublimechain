# 🚀 SublimeChain VPS Deployment Guide

## 📱 **Best iOS Terminal Apps for 2024-2025**

**Top Recommendation: NeoServer** ($4.99)
- Best overall iOS SSH client for 2025
- iCloud sync across devices
- Docker/container management
- Beautiful UI with offline capabilities

**Alternatives:**
- **Termius** (Free + Premium) - Cross-platform sync, Mosh support
- **Blink Shell** ($19.99) - Professional terminal, external keyboard support
- **ShellFish** ($8.99) - Files app integration, drag-and-drop uploads
- **WebSSH** (Free) - Privacy-focused, local mode

## 🏗️ **Step 1: Vultr VPS Setup**

### Server Specs Recommendation:
- **Size:** Regular Cloud Compute - $6/month (1 vCPU, 1GB RAM, 25GB SSD)
- **OS:** Ubuntu 22.04 LTS (familiar, stable, great package support)
- **Location:** Choose closest to you for best latency

### Provisioning Steps:
1. Log into Vultr dashboard
2. Click **"Deploy New Server"**
3. Choose **"Cloud Compute - Regular Performance"**
4. Select **"Ubuntu 22.04 x64"**
5. Choose **$6/month plan** (sufficient for SublimeChain)
6. **Add SSH Key** (generate if needed - see SSH section)
7. Optional: Enable auto-backups (+20% cost)
8. Deploy server

## 🔐 **Step 2: Ultra-Secure SSH Configuration**

### On Your Local Machine:

```bash
# Generate ED25519 key (fastest modern crypto)
ssh-keygen -t ed25519 -C "sublimechain-server" -f ~/.ssh/sublime_ed25519

# Use strong passphrase when prompted!
# ED25519 is faster than RSA-4096 but equally secure
```

### Add Public Key to Vultr:
1. Copy public key: `cat ~/.ssh/sublime_ed25519.pub`
2. Add to Vultr account under SSH Keys
3. Select this key when deploying server

## ⚙️ **Step 3: Initial Server Hardening**

```bash
# Initial login (replace YOUR_SERVER_IP)
ssh -i ~/.ssh/sublime_ed25519 root@YOUR_SERVER_IP

# Update system
apt update && apt upgrade -y

# Create non-root user
adduser sublime
usermod -aG sudo sublime

# Create SSH directory for sublime user
mkdir -p /home/sublime/.ssh
cp ~/.ssh/authorized_keys /home/sublime/.ssh/
chown -R sublime:sublime /home/sublime/.ssh
chmod 700 /home/sublime/.ssh
chmod 600 /home/sublime/.ssh/authorized_keys
```

### Configure Secure SSH:

```bash
# Edit SSH config
nano /etc/ssh/sshd_config

# Key changes:
Port XXXX                    # Custom port (e.g. 3909)
PermitRootLogin no          # Disable root login
PasswordAuthentication no   # Key-only authentication
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
X11Forwarding no
AllowUsers sublime          # Only allow sublime user
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2

# Restart SSH
systemctl restart sshd
```

## 🛡️ **Step 4: Vultr Firewall Configuration**

### In Vultr Dashboard:
1. Go to **"Firewall"** → **"Manage"**
2. Create new firewall group: **"sublime-secure"**
3. **Add Rules:**
   - **SSH:** TCP Port 3909, Sources: Your IP(s)
   - **HTTP:** TCP Port 80, Sources: Anywhere (if needed)
   - **HTTPS:** TCP Port 443, Sources: Anywhere (if needed)
4. **Apply to your server**

### Test New SSH Connection:
```bash
# From your local machine (new terminal)
ssh -i ~/.ssh/sublime_ed25519 -p 2847 sublime@YOUR_SERVER_IP
```

## 🐍 **Step 5: SublimeChain Deployment**

### Install Dependencies:
```bash
# Python & system packages
sudo apt install -y python3 python3-pip python3-venv git curl nodejs npm byobu htop

# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# Install Node.js packages for MCP servers
sudo npm install -g @modelcontextprotocol/server-github
sudo npm install -g @notionhq/notion-mcp-server
sudo npm install -g pushover-mcp
```

### Deploy SublimeChain:
```bash
# Clone your repository
cd ~
git clone https://github.com/YOUR_USERNAME/thinkchain.git  # Replace with your repo
cd thinkchain

# Or upload via SCP if not in git:
# scp -i ~/.ssh/sublime_ed25519 -P 2847 -r /path/to/thinkchain sublime@YOUR_SERVER_IP:~/

# Set up environment
cp .env.example .env
nano .env  # Add your API keys
```

### Environment Variables (.env):
```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...
MEM0_API_KEY=your-mem0-key

# Optional MCP integrations
GITHUB_PERSONAL_ACCESS_TOKEN=github_pat_...
TAVILY_API_KEY=tvly-dev-...
NOTION_API_TOKEN=ntn_...
PUSHOVER_API_TOKEN=your-token
PUSHOVER_USER_KEY=your-key
```

## 🖥️ **Step 6: Byobu Session Management**

### Configure Byobu:
```bash
# Install and configure byobu
byobu-enable  # Enable byobu by default

# Create persistent session for SublimeChain
byobu new-session -d -s sublime
```

### Byobu Essential Commands:
- **F2** - New window
- **F3/F4** - Navigate windows
- **F6** - Detach session
- **Ctrl+A, D** - Alternative detach
- **byobu attach-session -t sublime** - Reattach

## 🧪 **Step 7: Test Complete Workflow**

### Test SublimeChain:
```bash
# Attach to byobu session
byobu attach-session -t sublime

# Run SublimeChain
cd ~/thinkchain
uv run sublimechain.py

# Test basic functionality
/status
/tools
Hello, can you tell me about yourself?
```

### Test Mobile Workflow:
1. **Connect via iOS app** (NeoServer/Termius):
   - Host: YOUR_SERVER_IP
   - Port: 2847  
   - Username: sublime
   - Private Key: Import your ED25519 key

2. **Start long-running task:**
   ```bash
   byobu attach-session -t sublime
   # Give SublimeChain a complex task that takes time
   ```

3. **Detach and disconnect:**
   - Press **F6** to detach from byobu
   - Close iOS app

4. **Get notification when complete** (via Pushover)

## 🔧 **Maintenance & Monitoring**

### Server Monitoring:
```bash
# Check system resources
htop

# Check logs
journalctl -f

# Update system regularly
sudo apt update && sudo apt upgrade -y
```

### Backup Strategy:
1. **Vultr Snapshots** - Enable automatic snapshots
2. **Environment Backup** - Keep .env file secure locally
3. **Code Backup** - Use git for code changes

## 🚨 **Security Checklist**

- ✅ Custom SSH port (2847)
- ✅ ED25519 key authentication
- ✅ Disabled root/password login
- ✅ Vultr firewall configured
- ✅ Non-root user (sublime)
- ✅ Strong passphrase on SSH key
- ✅ Limited user permissions
- ✅ Regular system updates

## 📋 **Quick Reference**

### SSH Connection:
```bash
ssh -i ~/.ssh/sublime_ed25519 -p 2847 sublime@YOUR_SERVER_IP
```

### Start SublimeChain Session:
```bash
byobu attach-session -t sublime
cd ~/thinkchain
uv run sublimechain.py
```

Your SublimeChain is now ready for secure remote access! You can connect from anywhere, start tasks, detach, and receive notifications when complete. 🎉

## 💡 **Pro Tips**

- Use **NeoServer** for best iOS experience
- Keep SSH key passphrase in your password manager
- Enable Vultr automatic backups for peace of mind
- Test the complete workflow before relying on it
- Monitor server resources with `htop`
- Update system packages regularly for security
