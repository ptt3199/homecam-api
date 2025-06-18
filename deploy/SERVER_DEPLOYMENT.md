# Server Deployment Guide

## Super Quick One-Liner (No Files Needed)

If you don't want to copy any files, just run this directly on your Ubuntu server:

```bash
docker run -d \
  --name homecam-api \
  --restart unless-stopped \
  -p 8020:8020 \
  --device=/dev/video0:/dev/video0 \
  --device=/dev/video1:/dev/video1 \
  --device=/dev/video2:/dev/video2 \
  -e CAMERA_DEVICE_ID=0 \
  -e CAMERA_WIDTH=1280 \
  -e CAMERA_HEIGHT=720 \
  -e CAMERA_FPS=10 \
  --privileged \
  ptt3199/homecam-api:latest
```

## Quick Deployment (With Script - Recommended)

### Step 1: Copy Script to Server
```bash
# From your local machine, copy the deployment script to your Ubuntu server
scp homecam-api/deploy-server.sh user@your-server-ip:~/

# Or if you prefer, you can create the file directly on the server
```

### Step 2: SSH to Your Server
```bash
# Make sure Docker is installed
sudo apt update
sudo apt install docker.io docker-compose-plugin

# Add your user to docker group (to avoid sudo)
sudo usermod -aG docker $USER
# Log out and back in, or run: newgrp docker

# Make the script executable
chmod +x deploy-server.sh

# Run the deployment
./deploy-server.sh
```

### Step 3: That's It!
The script will automatically:
- Pull the latest image from Docker Hub (`ptt3199/homecam-api:latest`)
- Stop any existing container
- Start a new container with proper camera device access
- Show you the status and access URLs

## Usage Examples

### Basic deployment (uses defaults)
```bash
./deploy-server.sh
```

### Custom camera settings
```bash
./deploy-server.sh --camera-id 1 --width 1920 --height 1080 --fps 15
```

### Using environment variables
```bash
CAMERA_DEVICE_ID=2 CAMERA_FPS=20 ./deploy-server.sh
```

## What the Script Does

The `deploy-server.sh` script runs this Docker command equivalent:
```bash
docker run -d \
    --name homecam-api \
    --restart unless-stopped \
    -p 8020:8020 \
    --device=/dev/video0:/dev/video0 \
    --device=/dev/video1:/dev/video1 \
    --device=/dev/video2:/dev/video2 \
    -e CAMERA_DEVICE_ID=0 \
    -e CAMERA_WIDTH=1280 \
    -e CAMERA_HEIGHT=720 \
    -e CAMERA_FPS=10 \
    --privileged \
    ptt3199/homecam-api:latest
```

## Key Benefits vs Docker Compose

✅ **Simpler**: Just one script file  
✅ **Faster**: No need to copy docker-compose.yml  
✅ **Flexible**: Command-line arguments for easy configuration  
✅ **Self-contained**: Handles cleanup, pulling, and status checking  
✅ **Production-ready**: Includes restart policies and proper device mounting  

## Useful Commands After Deployment

```bash
# Check container status
docker ps

# View logs
docker logs homecam-api

# Follow logs in real-time
docker logs -f homecam-api

# Restart the container
docker restart homecam-api

# Stop the container
docker stop homecam-api

# Update to latest version
./deploy-server.sh  # Script handles cleanup and update
```

## Accessing Your Camera API

After deployment, access your camera at:
- **Local**: http://localhost:8020
- **Network**: http://YOUR_SERVER_IP:8020
- **Test endpoint**: http://YOUR_SERVER_IP:8020/camera/status

## Troubleshooting

### Camera not found
```bash
# Check available cameras
ls -la /dev/video*

# Check container logs
docker logs homecam-api
```

### Permission issues
```bash
# Make sure user is in docker group
groups $USER

# If not in docker group:
sudo usermod -aG docker $USER
newgrp docker
```

### Port already in use
```bash
# Check what's using port 8020
sudo netstat -tulpn | grep 8020

# Use different port
./deploy-server.sh --port 8021
``` 