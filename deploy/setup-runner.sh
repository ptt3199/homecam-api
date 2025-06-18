#!/bin/bash

# PTT Home - GitHub Self-Hosted Runner Setup Script
# Usage: ./setup-runner.sh [GITHUB_TOKEN] [REPO_URL]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
RUNNER_VERSION="2.311.0"
RUNNER_DIR="$HOME/actions-runner"
RUNNER_NAME="ubuntu-server-ptt-home"
DOCKER_IMAGE="ptt3199/homecam-api"

echo -e "${BLUE}🏃‍♂️ PTT Home - GitHub Self-Hosted Runner Setup${NC}"
echo "=============================================="

# Function to print colored output
print_step() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Parse arguments
GITHUB_TOKEN="${1:-}"
REPO_URL="${2:-https://github.com/YOUR_USERNAME/ptt-home}"

if [[ -z "$GITHUB_TOKEN" ]]; then
    print_warning "GitHub token not provided as argument"
    echo "You'll need to manually configure the runner later"
    echo "Get token from: GitHub Repo → Settings → Actions → Runners → New self-hosted runner"
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo ""
echo "🔍 Checking prerequisites..."

# Check Docker
if command_exists docker; then
    print_step "Docker is installed"
    if groups $USER | grep &>/dev/null '\bdocker\b'; then
        print_step "User is in docker group"
    else
        print_warning "User not in docker group. Adding..."
        sudo usermod -aG docker $USER
        print_warning "Please logout and login again after this script finishes"
    fi
else
    print_error "Docker is not installed. Installing..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    print_step "Docker installed successfully"
fi

# Check Git
if command_exists git; then
    print_step "Git is installed"
else
    print_error "Git is not installed. Installing..."
    sudo apt update
    sudo apt install -y git
    print_step "Git installed successfully"
fi

# Check curl
if command_exists curl; then
    print_step "Curl is installed"
else
    sudo apt install -y curl
    print_step "Curl installed"
fi

# Install jq if not present
if ! command_exists jq; then
    sudo apt install -y jq
    print_step "jq installed"
fi

# Create runner directory
echo ""
echo "📁 Setting up runner directory..."
mkdir -p "$RUNNER_DIR"
cd "$RUNNER_DIR"

# Download runner if not exists
if [[ ! -f "actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz" ]]; then
    echo "📥 Downloading GitHub Actions Runner v${RUNNER_VERSION}..."
    curl -o "actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz" -L \
        "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz"
    print_step "Runner downloaded"
fi

# Extract runner if not already extracted
if [[ ! -f "run.sh" ]]; then
    echo "📦 Extracting runner..."
    tar xzf "./actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz"
    print_step "Runner extracted"
fi

# Configure runner if token provided
if [[ -n "$GITHUB_TOKEN" ]]; then
    echo ""
    echo "⚙️ Configuring runner..."
    
    # Check if already configured
    if [[ -f ".runner" ]]; then
        print_warning "Runner already configured. Removing existing configuration..."
        ./config.sh remove --token "$GITHUB_TOKEN" || true
    fi
    
    # Configure runner
    ./config.sh \
        --url "$REPO_URL" \
        --token "$GITHUB_TOKEN" \
        --name "$RUNNER_NAME" \
        --labels "self-hosted,ubuntu,docker,ptt-home" \
        --work "_work" \
        --unattended
    
    print_step "Runner configured successfully"
    
    # Install as service
    echo ""
    echo "🔧 Installing runner service..."
    sudo ./svc.sh install
    sudo ./svc.sh start
    
    # Enable auto-start
    SERVICE_NAME="actions.runner.$(echo $REPO_URL | sed 's/.*github.com\///').${RUNNER_NAME}.service"
    sudo systemctl enable "$SERVICE_NAME"
    
    print_step "Runner service installed and started"
    
    # Check service status
    echo ""
    echo "📊 Service status:"
    sudo systemctl status "$SERVICE_NAME" --no-pager -l
    
else
    echo ""
    print_warning "Manual configuration required:"
    echo "1. Get registration token from: ${REPO_URL}/settings/actions/runners"
    echo "2. Run: cd $RUNNER_DIR && ./config.sh --url $REPO_URL --token YOUR_TOKEN"
    echo "3. Run: sudo ./svc.sh install && sudo ./svc.sh start"
fi

# Test Docker access
echo ""
echo "🐳 Testing Docker access..."
if docker ps >/dev/null 2>&1; then
    print_step "Docker access works"
else
    print_warning "Docker access failed. You may need to logout/login or run 'newgrp docker'"
fi

# Create Docker Hub login script
echo ""
echo "🔑 Creating Docker Hub login helper..."
cat > "$HOME/docker-login.sh" << 'EOF'
#!/bin/bash
echo "Docker Hub Login Helper"
echo "======================="
echo "Login to Docker Hub with your credentials:"
docker login
if [[ $? -eq 0 ]]; then
    echo "✅ Docker Hub login successful"
else
    echo "❌ Docker Hub login failed"
fi
EOF
chmod +x "$HOME/docker-login.sh"
print_step "Docker login helper created at ~/docker-login.sh"

# Create backup script
echo ""
echo "💾 Creating backup script..."
cat > "$HOME/backup-docker-images.sh" << 'EOF'
#!/bin/bash
BACKUP_DIR="$HOME/docker-backups"
mkdir -p "$BACKUP_DIR"

# Backup current production image
CURRENT_IMAGE=$(docker inspect homecam-api --format='{{.Config.Image}}' 2>/dev/null)
if [[ -n "$CURRENT_IMAGE" ]]; then
    BACKUP_NAME="backup-$(date +%Y%m%d-%H%M%S).tar"
    echo "Creating backup: $BACKUP_DIR/$BACKUP_NAME"
    docker save "$CURRENT_IMAGE" > "$BACKUP_DIR/$BACKUP_NAME"
    echo "✅ Backup created successfully"
    
    # Keep only last 5 backups
    ls -t "$BACKUP_DIR"/backup-*.tar | tail -n +6 | xargs -r rm
    echo "🧹 Old backups cleaned up"
else
    echo "No running homecam-api container found"
fi
EOF
chmod +x "$HOME/backup-docker-images.sh"
print_step "Backup script created at ~/backup-docker-images.sh"

# Setup log rotation
echo ""
echo "📝 Setting up log rotation..."
sudo tee /etc/logrotate.d/github-runner > /dev/null << EOF
$RUNNER_DIR/_diag/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 $USER $USER
}
EOF
print_step "Log rotation configured"

# Final summary
echo ""
echo -e "${GREEN}🎉 Setup completed successfully!${NC}"
echo "=============================================="
echo ""
echo "📋 Next steps:"
echo "1. Add GitHub secrets:"
echo "   - DOCKER_USERNAME: ptt3199"
echo "   - DOCKER_PASSWORD: <your-docker-hub-token>"
echo ""
echo "2. Login to Docker Hub:"
echo "   ~/docker-login.sh"
echo ""
echo "3. Test deployment:"
echo "   git tag v1.0.0 && git push origin v1.0.0"
echo ""
echo "4. Monitor runner:"
echo "   sudo journalctl -u actions.runner.*.service -f"
echo ""
echo "📁 Important files:"
echo "   - Runner directory: $RUNNER_DIR"
echo "   - Backup script: ~/backup-docker-images.sh"
echo "   - Docker login: ~/docker-login.sh"
echo ""

if [[ -n "$GITHUB_TOKEN" ]]; then
    echo -e "${GREEN}✅ Runner is active and ready for jobs!${NC}"
else
    echo -e "${YELLOW}⚠️  Manual runner configuration required${NC}"
fi

echo ""
echo "🔗 Useful commands:"
echo "   Check runner status: sudo systemctl status actions.runner.*.service"
echo "   View runner logs: sudo journalctl -u actions.runner.*.service -f"
echo "   Restart runner: sudo systemctl restart actions.runner.*.service"
echo "   Test Docker: docker run hello-world"
echo ""
echo "Happy deploying! 🚀" 