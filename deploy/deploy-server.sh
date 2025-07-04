#!/bin/bash

# PTT Home Camera API - Server Deployment Script
# This script runs the homecam-api Docker container directly without docker-compose

set -e

# Configuration
IMAGE_NAME="ptt3199/homecam-api:latest"
CONTAINER_NAME="homecam-api"
PORT="8020"
STREAMING_TOKEN_SECRET="${STREAMING_TOKEN_SECRET:-your-streaming-secret-key-change-in-production}"

# Environment variables for camera configuration
CAMERA_DEVICE_ID="${CAMERA_DEVICE_ID:-0}"
CAMERA_WIDTH="${CAMERA_WIDTH:-1280}"
CAMERA_HEIGHT="${CAMERA_HEIGHT:-720}"
CAMERA_FPS="${CAMERA_FPS:-10}"

echo "🏠 PTT Home Camera API - Server Deployment"
echo "=========================================="

# Function to stop and remove existing container
cleanup_container() {
    echo "🧹 Cleaning up existing container..."
    if docker ps -a --format "table {{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
        docker stop ${CONTAINER_NAME} || true
        docker rm ${CONTAINER_NAME} || true
        echo "✅ Existing container removed"
    else
        echo "ℹ️  No existing container found"
    fi
}

# Function to pull latest image
pull_image() {
    echo "📥 Pulling latest image from Docker Hub..."
    docker pull ${IMAGE_NAME}
    echo "✅ Image pulled successfully"
}

# Function to check camera devices
check_cameras() {
    echo "📷 Checking available camera devices..."
    if ls /dev/video* 2>/dev/null; then
        echo "✅ Camera devices found"
    else
        echo "⚠️  No camera devices found at /dev/video*"
        echo "   Make sure your USB camera is connected"
    fi
}

# Function to run the container
run_container() {
    echo "🚀 Starting homecam-api container..."
    
    docker run -d \
        --name ${CONTAINER_NAME} \
        --restart unless-stopped \
        -p ${PORT}:8020 \
        --device=/dev/video0:/dev/video0 \
        --device=/dev/video1:/dev/video1 \
        --device=/dev/video2:/dev/video2 \
        --dns=8.8.8.8 \
        --dns=8.8.4.4 \
        -e CAMERA_DEVICE_ID=${CAMERA_DEVICE_ID} \
        -e CAMERA_WIDTH=${CAMERA_WIDTH} \
        -e CAMERA_HEIGHT=${CAMERA_HEIGHT} \
        -e CAMERA_FPS=${CAMERA_FPS} \
        -e STREAMING_TOKEN_SECRET=${STREAMING_TOKEN_SECRET} \
        --privileged \
        ${IMAGE_NAME}
    
    echo "✅ Container started successfully"
}

# Function to connect to network
connect_network() {
    echo "🔗 Connecting to network..."
    docker network connect jarvis-proxy ${CONTAINER_NAME}
    echo "✅ Network connected"
}

# Function to test network connectivity
test_connectivity() {
    echo "🌐 Testing network connectivity..."
    
    # Test basic API health
    if curl -s http://localhost:${PORT}/health > /dev/null; then
        echo "✅ API health check passed"
    else
        echo "❌ API health check failed"
        return 1
    fi
    
    # Test network connectivity from inside container
    echo "🔍 Testing external connectivity from container..."
    if docker exec ${CONTAINER_NAME} curl -s --max-time 10 https://www.google.com > /dev/null; then
        echo "✅ External internet connectivity working"
    else
        echo "❌ External internet connectivity failed"
        echo "   This may cause Clerk authentication issues"
    fi
    
    # Test Clerk domain connectivity
    if docker exec ${CONTAINER_NAME} curl -s --max-time 10 https://clerk.com > /dev/null; then
        echo "✅ Clerk domain connectivity working"
    else
        echo "❌ Clerk domain connectivity failed"
        echo "   Check firewall/proxy settings"
    fi
}

# Function to show container status
show_status() {
    echo "📊 Container Status:"
    echo "==================="
    docker ps --filter "name=${CONTAINER_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    echo ""
    echo "🔗 Access the API at:"
    echo "   Local:    http://localhost:${PORT}"
    echo "   Network:  http://$(hostname -I | awk '{print $1}'):${PORT}"
    echo ""
    echo "🔍 Test endpoints:"
    echo "   Health:       curl http://localhost:${PORT}/health"
    echo "   Network test: curl http://localhost:${PORT}/health/network"
    echo ""
    echo "📋 Useful commands:"
    echo "   View logs:    docker logs ${CONTAINER_NAME}"
    echo "   Follow logs:  docker logs -f ${CONTAINER_NAME}"
    echo "   Stop:         docker stop ${CONTAINER_NAME}"
    echo "   Restart:      docker restart ${CONTAINER_NAME}"
    echo "   Debug net:    docker exec ${CONTAINER_NAME} python test_clerk_connectivity.py"
}

# Main execution
main() {
    cleanup_container
    pull_image
    check_cameras
    run_container
    connect_network
    
    # Wait a moment for container to start
    echo "⏳ Waiting for container to start..."
    sleep 5
    
    show_status
    
    # Test network connectivity for Clerk authentication
    echo ""
    test_connectivity
    
    echo ""
    echo "🎉 Deployment completed!"
    echo "   Check logs with: docker logs -f ${CONTAINER_NAME}"
    echo ""
    echo "🔐 For Clerk authentication to work:"
    echo "   1. Ensure the above connectivity tests pass"
    echo "   2. Set a secure STREAMING_TOKEN_SECRET environment variable"
    echo "   3. Test with: curl -H \"Authorization: Bearer <jwt>\" http://localhost:${PORT}/camera/status"
}

# Help function
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --camera-id N     Set camera device ID (default: 0)"
    echo "  --width N         Set camera width (default: 1280)"
    echo "  --height N        Set camera height (default: 720)"
    echo "  --fps N           Set camera FPS (default: 10)"
    echo "  --port N          Set external port (default: 8020)"
    echo "  --help            Show this help message"
    echo ""
    echo "Environment variables:"
    echo "  CAMERA_DEVICE_ID       Camera device index"
    echo "  CAMERA_WIDTH           Camera resolution width"
    echo "  CAMERA_HEIGHT          Camera resolution height"
    echo "  CAMERA_FPS             Camera frames per second"
    echo "  STREAMING_TOKEN_SECRET Secret key for streaming authentication (required)"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Use defaults"
    echo "  $0 --camera-id 1 --width 1920        # HD camera on device 1"
    echo "  CAMERA_FPS=15 $0                     # Use environment variable"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --camera-id)
            CAMERA_DEVICE_ID="$2"
            shift 2
            ;;
        --width)
            CAMERA_WIDTH="$2"
            shift 2
            ;;
        --height)
            CAMERA_HEIGHT="$2"
            shift 2
            ;;
        --fps)
            CAMERA_FPS="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Run main function
main 