# PTT Home - Ubuntu Server Deployment Guide

## 🖥️ **Development vs Production Setup**

### Development (macOS/Local)
- **Run natively**: Use `python3 run_native.py` for local development
- **Camera access**: Works directly through macOS camera APIs
- **Hot reload**: Automatic code reloading for development

### Production (Ubuntu Server)
- **Run in Docker**: Use `docker-compose up --build`
- **Camera access**: Through `/dev/video*` device mounting
- **Deployment**: Containerized production environment

---

## 🚀 **Ubuntu Server Deployment Steps**

### 1. **Server Prerequisites**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER
# Log out and back in for group changes
```

### 2. **Camera Setup on Ubuntu**
```bash
# Check available cameras
ls -la /dev/video*

# Install v4l-utils for camera debugging
sudo apt install v4l-utils

# List camera details
v4l2-ctl --list-devices

# Test camera access
v4l2-ctl --device=/dev/video0 --info

# Set camera permissions (if needed)
sudo chmod 666 /dev/video*
```

### 3. **Deploy Application**
```bash
# Clone/copy your project to server
git clone <your-repo> ptt-home
cd ptt-home/homecam-api

# Check camera before starting
python3 find_camera.py

# Update docker-compose.yml based on available cameras
# Edit the devices section to match your camera:
# devices:
#   - /dev/video0:/dev/video0  # Change number as needed

# Build and run
docker-compose up --build

# Run in background
docker-compose up -d --build
```

### 4. **Verify Deployment**
```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs -f

# Test endpoints
curl http://localhost:8020/camera/status
curl http://localhost:8020/camera/debug

# Test video feed
curl -I http://localhost:8020/video_feed
```

---

## 🔧 **Troubleshooting Ubuntu Camera Issues**

### **Camera Not Found**
```bash
# 1. Check if camera is detected
lsusb | grep -i camera
ls /dev/video*

# 2. Check camera permissions
ls -la /dev/video*
sudo chmod 666 /dev/video*

# 3. Check if camera is in use
sudo lsof /dev/video*
```

### **Docker Permission Issues**
```bash
# Add user to video group
sudo usermod -a -G video $USER

# Run with specific user permissions
docker-compose run --user $(id -u):$(id -g) homecam-api
```

### **Camera Index Issues**
```bash
# Test different camera indices in docker-compose.yml:
devices:
  - /dev/video0:/dev/video0  # Most common
  - /dev/video1:/dev/video1  # Alternative
  - /dev/video2:/dev/video2  # Sometimes needed
```

---

## 🌐 **Network Access Configuration**

### **Local Network Access**
- Application runs on: `http://server-ip:8020`
- Video feed: `http://server-ip:8020/video_feed`

### **External Access (Optional)**
If you want external access, consider:

1. **Reverse Proxy (Nginx)**
```bash
# Install nginx
sudo apt install nginx

# Configure reverse proxy
sudo nano /etc/nginx/sites-available/ptt-home
```

2. **Cloudflare Tunnel** (Recommended)
```bash
# Install cloudflared
wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Setup tunnel to http://localhost:8020
cloudflared tunnel --url http://localhost:8020
```

---

## 📊 **Monitoring & Maintenance**

### **Auto-restart on Boot**
```bash
# Create systemd service
sudo nano /etc/systemd/system/ptt-home.service

[Unit]
Description=PTT Home Camera Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/user/ptt-home/homecam-api
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target

# Enable service
sudo systemctl enable ptt-home.service
```

### **Log Management**
```bash
# View logs
docker-compose logs -f --tail=100

# Rotate logs (prevent disk full)
docker system prune -f
```

---

## ✅ **Expected Results**

When properly deployed on Ubuntu server:
- ✅ Camera detection successful
- ✅ Video stream accessible at `/video_feed`
- ✅ Real-time video streaming working
- ✅ Container auto-restarts on failure
- ✅ Accessible from network devices 