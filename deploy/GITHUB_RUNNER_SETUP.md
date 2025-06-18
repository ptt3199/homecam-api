# 🏃‍♂️ GitHub Self-Hosted Runner Setup Guide

## 📋 Tổng quan

Hướng dẫn này sẽ giúp bạn thiết lập GitHub self-hosted runner trên server Ubuntu để tự động deploy backend khi tạo Git tag mới.

### Luồng hoạt động:
```
Git Tag (v1.0.0) → GitHub Action → Self-hosted Runner → Build Docker → Deploy → Push to DockerHub
```

### Ưu điểm:
- ✅ Build trực tiếp trên server (tiết kiệm bandwidth)
- ✅ Tận dụng hardware server hiện có
- ✅ Kiểm soát hoàn toàn environment
- ✅ Deploy nhanh chóng (local build)

---

## 🔧 Bước 1: Thiết lập GitHub Workflow

### 1.1 Tạo workflow file

Tạo file `.github/workflows/self-hosted-deploy.yml` trong repo:

```yaml
name: 🚀 Self-Hosted Deploy

on:
  push:
    tags:
      - 'v*.*.*'    # Semantic versioning: v1.0.0, v1.2.3
      - 'release-*' # Release tags: release-20241215
  workflow_dispatch:
    inputs:
      tag:
        description: 'Tag to deploy (leave empty to use latest commit)'
        required: false
        type: string

env:
  DOCKER_IMAGE: ptt3199/homecam-api
  CONTAINER_NAME: homecam-api

jobs:
  deploy:
    name: 🏗️ Build and Deploy
    runs-on: self-hosted  # Chạy trên server của bạn
    
    steps:
    - name: 🏷️ Get deployment tag
      id: tag
      run: |
        if [[ "${{ github.event_name }}" == "workflow_dispatch" && -n "${{ github.event.inputs.tag }}" ]]; then
          TAG="${{ github.event.inputs.tag }}"
        elif [[ "${{ github.ref }}" =~ refs/tags/.* ]]; then
          TAG=${GITHUB_REF#refs/tags/}
        else
          TAG="latest"
        fi
        
        echo "tag=${TAG}" >> $GITHUB_OUTPUT
        echo "🏷️ Deploying tag: ${TAG}"

    - name: 📥 Checkout code
      uses: actions/checkout@v4
      with:
        fetch-depth: 0  # Full history for proper tag checkout

    - name: 🔑 Login to Docker Hub
      run: |
        echo "${{ secrets.DOCKER_PASSWORD }}" | docker login -u "${{ secrets.DOCKER_USERNAME }}" --password-stdin

    - name: 🛑 Stop existing container
      run: |
        echo "🛑 Stopping existing container..."
        docker stop ${{ env.CONTAINER_NAME }} || true
        docker rm ${{ env.CONTAINER_NAME }} || true
        echo "✅ Container stopped and removed"

    - name: 🏗️ Build Docker image
      run: |
        echo "🏗️ Building Docker image with tag: ${{ steps.tag.outputs.tag }}"
        
        docker build \
          --tag ${{ env.DOCKER_IMAGE }}:${{ steps.tag.outputs.tag }} \
          --tag ${{ env.DOCKER_IMAGE }}:latest \
          --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
          --build-arg VERSION=${{ steps.tag.outputs.tag }} \
          --build-arg VCS_REF=${{ github.sha }} \
          .
        
        echo "✅ Docker image built successfully"

    - name: 🚀 Deploy new container
      run: |
        echo "🚀 Starting new container..."
        
        docker run -d \
          --name ${{ env.CONTAINER_NAME }} \
          --restart unless-stopped \
          -p 8020:8020 \
          --device=/dev/video0:/dev/video0 \
          --device=/dev/video1:/dev/video1 \
          --device=/dev/video2:/dev/video2 \
          -e CAMERA_DEVICE_ID=0 \
          -e CAMERA_WIDTH=1280 \
          -e CAMERA_HEIGHT=720 \
          -e CAMERA_FPS=10 \
          -e ENV=production \
          -e VERSION=${{ steps.tag.outputs.tag }} \
          --privileged \
          ${{ env.DOCKER_IMAGE }}:${{ steps.tag.outputs.tag }}
        
        echo "✅ Container deployed successfully"

    - name: 🧪 Health check
      run: |
        echo "🧪 Running health check..."
        
        # Wait for container to start
        sleep 15
        
        # Test basic endpoints
        curl -f http://localhost:8020/ || (echo "❌ Health check failed" && exit 1)
        curl -f http://localhost:8020/camera/status || (echo "❌ Camera check failed" && exit 1)
        
        echo "✅ Health check passed"

    - name: 📤 Push to Docker Hub
      run: |
        echo "📤 Pushing images to Docker Hub..."
        
        docker push ${{ env.DOCKER_IMAGE }}:${{ steps.tag.outputs.tag }}
        docker push ${{ env.DOCKER_IMAGE }}:latest
        
        echo "✅ Images pushed to Docker Hub"

    - name: 🧹 Cleanup old images
      run: |
        echo "🧹 Cleaning up old Docker images..."
        
        # Keep last 3 versions, remove older ones
        docker images ${{ env.DOCKER_IMAGE }} --format "table {{.Repository}}:{{.Tag}}\t{{.CreatedAt}}" | \
        grep -v "latest" | \
        tail -n +4 | \
        awk '{print $1}' | \
        xargs -r docker rmi || true
        
        echo "✅ Cleanup completed"

    - name: 📊 Deployment summary
      run: |
        echo "🎉 Deployment completed successfully!"
        echo "================================================"
        echo "🏷️ Version: ${{ steps.tag.outputs.tag }}"
        echo "🐳 Container: ${{ env.CONTAINER_NAME }}"
        echo "🔗 Local URL: http://localhost:8020"
        echo "🔗 Public URL: http://$(curl -s ifconfig.me):8020"
        echo "📦 Docker Hub: https://hub.docker.com/r/${{ env.DOCKER_IMAGE }}"
        echo "================================================"
        
        # Show container status
        docker ps --filter "name=${{ env.CONTAINER_NAME }}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### 1.2 Cấu hình GitHub Secrets

Vào GitHub repo → Settings → Secrets and variables → Actions → New repository secret:

```bash
# Docker Hub credentials
DOCKER_USERNAME=ptt3199
DOCKER_PASSWORD=<your-docker-hub-access-token>
```

#### Tạo Docker Hub Access Token:
1. Đăng nhập Docker Hub → Account Settings → Security
2. New Access Token → Tên: `github-actions-ptt-home`
3. Copy token và paste vào GitHub Secrets

---

## 🖥️ Bước 2: Chuẩn bị Server

### 2.1 Cài đặt dependencies trên Ubuntu server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker (nếu chưa có)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Git (nếu chưa có)
sudo apt install git -y

# Install curl và các tools cần thiết
sudo apt install curl jq -y

# Logout và login lại để apply docker group
exit
# SSH lại vào server
```

### 2.2 Verify Docker hoạt động

```bash
# Test Docker
docker --version
docker run hello-world

# Test Docker Hub login
docker login
# Nhập Docker Hub username/password của bạn
```

### 2.3 Tạo workspace cho runner

```bash
# Tạo thư mục cho GitHub Actions
mkdir -p ~/actions-runner
cd ~/actions-runner

# Tạo thư mục cho project
mkdir -p ~/ptt-home-workspace
```

---

## 🏃‍♂️ Bước 3: Cài đặt GitHub Self-Hosted Runner

### 3.1 Download GitHub Actions Runner

```bash
cd ~/actions-runner

# Download latest runner (check GitHub for latest version)
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz

# Extract
tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz
```

### 3.2 Configure Runner với GitHub repo

#### Lấy Registration Token từ GitHub:
1. Vào GitHub repo → Settings → Actions → Runners
2. Click "New self-hosted runner"
3. Chọn Linux → Copy registration token

#### Configure runner:
```bash
cd ~/actions-runner

# Run config với token từ GitHub
./config.sh --url https://github.com/YOUR_USERNAME/ptt-home --token YOUR_REGISTRATION_TOKEN

# Khi được hỏi:
# Enter the name of the runner group: [Enter] (default)
# Enter the name of runner: ubuntu-server-ptt-home
# Enter any additional labels: self-hosted,ubuntu,docker
# Enter name of work folder: [Enter] (default: _work)
```

### 3.3 Test runner manually

```bash
# Test chạy runner
./run.sh

# Bạn sẽ thấy:
# ✓ Connected to GitHub
# ✓ Listening for Jobs...
```

**Để test:** Tạo một git tag và xem runner có nhận job không.

---

## 🔄 Bước 4: Thiết lập Runner Service

### 4.1 Cài đặt runner như system service

```bash
cd ~/actions-runner

# Install service
sudo ./svc.sh install

# Start service
sudo ./svc.sh start

# Check status
sudo ./svc.sh status

# Enable auto-start on boot
sudo systemctl enable actions.runner.YOUR_USERNAME-ptt-home.ubuntu-server-ptt-home.service
```

### 4.2 Verify service hoạt động

```bash
# Check service status
sudo systemctl status actions.runner.*.service

# Check logs
sudo journalctl -u actions.runner.*.service -f
```

---

## 🔐 Bước 5: Cấu hình Security & Permissions

### 5.1 Docker permissions

```bash
# Verify docker không cần sudo
docker ps
docker images

# Nếu vẫn bị permission denied:
sudo usermod -aG docker $(whoami)
newgrp docker
```

### 5.2 GitHub repository permissions

#### Repository Settings:
1. Vào GitHub repo → Settings → Actions → General
2. **Workflow permissions**: 
   - ✅ Read and write permissions
   - ✅ Allow GitHub Actions to create and approve pull requests

#### Branch Protection (optional):
1. Settings → Branches → Add rule for `main`
2. Require pull request reviews before merging
3. Allow administrators to bypass

### 5.3 Runner security

```bash
# Tạo dedicated user cho runner (recommended for production)
sudo adduser github-runner
sudo usermod -aG docker github-runner

# Hoặc continue với user hiện tại (cho testing)
```

---

## 🧪 Bước 6: Testing End-to-End

### 6.1 Test deployment flow

```bash
# 1. Trên local machine, tạo tag mới
cd /path/to/ptt-home
git add .
git commit -m "feat: test self-hosted deployment"
git push origin main

# 2. Tạo tag
git tag v1.0.0
git push origin v1.0.0

# 3. Kiểm tra GitHub Actions
# Vào GitHub repo → Actions → Xem workflow chạy
```

### 6.2 Monitor deployment

```bash
# Trên server, monitor logs
sudo journalctl -u actions.runner.*.service -f

# Check container status
docker ps
docker logs homecam-api

# Test API
curl http://localhost:8020/
curl http://localhost:8020/camera/status
```

### 6.3 Verify Docker Hub push

1. Vào https://hub.docker.com/r/ptt3199/homecam-api
2. Kiểm tra tag mới đã được push lên chưa

---

## 🛠️ Bước 7: Advanced Configuration

### 7.1 Environment variables cho runner

```bash
# Tạo file env cho runner
sudo nano /etc/systemd/system/actions.runner.*.service

# Thêm environment variables:
[Service]
Environment="DOCKER_IMAGE=ptt3199/homecam-api"
Environment="CONTAINER_NAME=homecam-api"
Environment="ENV=production"

# Reload service
sudo systemctl daemon-reload
sudo systemctl restart actions.runner.*.service
```

### 7.2 Monitoring và logging

```bash
# Setup log rotation
sudo nano /etc/logrotate.d/github-runner

# Nội dung:
/home/ubuntu/actions-runner/_diag/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 ubuntu ubuntu
}
```

### 7.3 Backup và disaster recovery

```bash
# Script backup Docker images
cat > ~/backup-images.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/ubuntu/docker-backups"
mkdir -p $BACKUP_DIR

# Backup current production image
CURRENT_IMAGE=$(docker inspect homecam-api --format='{{.Config.Image}}' 2>/dev/null)
if [[ -n "$CURRENT_IMAGE" ]]; then
    BACKUP_NAME="backup-$(date +%Y%m%d-%H%M%S).tar"
    docker save $CURRENT_IMAGE > $BACKUP_DIR/$BACKUP_NAME
    echo "Backup created: $BACKUP_DIR/$BACKUP_NAME"
    
    # Keep only last 5 backups
    ls -t $BACKUP_DIR/backup-*.tar | tail -n +6 | xargs -r rm
fi
EOF

chmod +x ~/backup-images.sh

# Thêm vào crontab để auto backup
crontab -e
# Thêm dòng: 0 2 * * * /home/ubuntu/backup-images.sh
```

---

## 📊 Bước 8: Usage & Operations

### 8.1 Deployment commands

```bash
# Deploy version mới
git tag v1.1.0
git push origin v1.1.0

# Manual trigger (nếu cần)
# Vào GitHub → Actions → Self-Hosted Deploy → Run workflow

# Check deployment status
docker ps
docker logs homecam-api
curl http://localhost:8020/camera/status
```

### 8.2 Troubleshooting

#### Runner không connect GitHub:
```bash
# Check network
ping github.com

# Check runner status
sudo systemctl status actions.runner.*.service

# Restart runner
sudo systemctl restart actions.runner.*.service

# Re-register runner (nếu cần)
cd ~/actions-runner
./config.sh remove --token YOUR_REMOVAL_TOKEN
./config.sh --url https://github.com/YOUR_USERNAME/ptt-home --token NEW_REGISTRATION_TOKEN
```

#### Docker build failed:
```bash
# Check disk space
df -h

# Check Docker daemon
sudo systemctl status docker

# Clean up Docker
docker system prune -f
docker image prune -a -f
```

#### Container failed to start:
```bash
# Check camera devices
ls -la /dev/video*

# Check container logs
docker logs homecam-api

# Manual test
docker run --rm -it --privileged --device=/dev/video0:/dev/video0 ptt3199/homecam-api:latest bash
```

### 8.3 Maintenance

```bash
# Update runner
cd ~/actions-runner
sudo ./svc.sh stop
# Download new version và extract
sudo ./svc.sh start

# Clean up old Docker images (tự động trong workflow)
docker image prune -f

# Monitor disk usage
du -sh ~/actions-runner/
df -h
```

---

## 🔐 Security Best Practices

### 1. Runner Security
- ✅ Sử dụng dedicated user cho runner
- ✅ Limit runner permissions
- ✅ Regular security updates
- ✅ Monitor runner logs

### 2. Docker Security
- ✅ Regular base image updates
- ✅ Scan images for vulnerabilities
- ✅ Use non-root user trong container
- ✅ Limit container privileges

### 3. Network Security
- ✅ Firewall rules cho port 8020
- ✅ HTTPS với reverse proxy (Nginx)
- ✅ VPN access cho admin
- ✅ Regular security audits

---

## 🎯 Expected Results

Sau khi setup xong, bạn sẽ có:

- ✅ GitHub self-hosted runner chạy như system service
- ✅ Automatic deployment khi tạo Git tags
- ✅ Local Docker build và deploy trên server
- ✅ Automatic push lên Docker Hub
- ✅ Health checks và error handling
- ✅ Log monitoring và cleanup

### Success Criteria:
```bash
# 1. Runner đang active
curl -H "Accept: application/vnd.github.v3+json" \
     -H "Authorization: token YOUR_GITHUB_TOKEN" \
     https://api.github.com/repos/YOUR_USERNAME/ptt-home/actions/runners

# 2. Service đang chạy
sudo systemctl is-active actions.runner.*.service

# 3. Deployment thành công
docker ps | grep homecam-api
curl http://localhost:8020/camera/status
```

---

## 📞 Support

Nếu gặp vấn đề:

1. **Check runner logs**: `sudo journalctl -u actions.runner.*.service -f`
2. **Check workflow logs**: GitHub → Actions → Latest workflow run
3. **Check container logs**: `docker logs homecam-api`
4. **GitHub runner docs**: https://docs.github.com/en/actions/hosting-your-own-runners

**🎉 Happy Self-Hosting!** 🚀 