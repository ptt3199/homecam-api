# 🚀 CI/CD với Self-Hosted Runner

## ⚡ Quick Start

### 1. Setup Runner trên Server
```bash
# Trên Ubuntu server
cd /path/to/ptt-home/homecam-api
chmod +x setup-runner.sh
./setup-runner.sh
```

### 2. Cấu hình GitHub Secrets
```
DOCKER_USERNAME=ptt3199ffffffffff
DOCKER_PASSWORD=<docker-hub-token>
```

### 3. Deploy với Git Tags
```bash
# Tạo và push tag
git tag v1.0.0
git push origin v1.0.0

# GitHub Action sẽ tự động:
# ✅ Build Docker image trên server
# ✅ Deploy container mới
# ✅ Push image lên Docker Hub
# ✅ Health check
# ✅ Cleanup old images
```

## 📋 Luồng hoạt động

```
Git Tag → GitHub Action → Self-hosted Runner → Docker Build → Deploy → DockerHub Push
```

## 🔧 Files được tạo

- `.github/workflows/self-hosted-deploy.yml` - GitHub Action workflow
- `GITHUB_RUNNER_SETUP.md` - Hướng dẫn chi tiết setup
- `setup-runner.sh` - Script setup tự động
- `README_CICD.md` - Tóm tắt này

## 📊 Monitoring

```bash
# Check runner status
sudo systemctl status actions.runner.*.service

# View logs
sudo journalctl -u actions.runner.*.service -f

# Check container
docker ps
docker logs homecam-api
```

## 🎯 Ưu điểm của approach này

- ✅ **Build local**: Tiết kiệm bandwidth, build nhanh
- ✅ **Hardware control**: Sử dụng server hiện có
- ✅ **Tag-based deploy**: Professional release process  
- ✅ **Zero-downtime**: Container replacement strategy
- ✅ **Auto cleanup**: Giữ storage sạch sẽ
- ✅ **Health checks**: Đảm bảo deploy success

Xem `GITHUB_RUNNER_SETUP.md` cho hướng dẫn chi tiết! 🚀 