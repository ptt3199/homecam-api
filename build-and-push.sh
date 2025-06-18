#!/bin/bash

# PTT Home Camera API - Multi-platform Docker Build and Push Script
# This script builds Docker images that work on both macOS (ARM64) and Ubuntu (AMD64)

set -e

# Configuration
IMAGE_NAME="ptt3199/homecam-api"
TAG="${1:-latest}"
FULL_IMAGE_NAME="${IMAGE_NAME}:${TAG}"

echo "🐳 PTT Home Camera API - Multi-platform Docker Build"
echo "=================================================="
echo "Building: ${FULL_IMAGE_NAME}"
echo "Platforms: linux/amd64, linux/arm64"
echo ""

# Function to check if buildx is available
check_buildx() {
    echo "🔍 Checking Docker buildx availability..."
    if ! docker buildx version >/dev/null 2>&1; then
        echo "❌ Docker buildx is not available"
        echo "   Please install Docker Desktop or enable buildx"
        exit 1
    fi
    echo "✅ Docker buildx is available"
}

# Function to create/use buildx builder
setup_builder() {
    echo "🛠️  Setting up multi-platform builder..."
    
    # Create a new builder instance if it doesn't exist
    if ! docker buildx ls | grep -q "multiplatform"; then
        echo "Creating new buildx builder..."
        docker buildx create --name multiplatform --driver docker-container --bootstrap
    fi
    
    # Use the multiplatform builder
    docker buildx use multiplatform
    echo "✅ Builder setup complete"
}

# Function to build and push multi-platform image
build_and_push() {
    echo "🚀 Building and pushing multi-platform image..."
    echo "This may take several minutes..."
    
    docker buildx build \
        --platform linux/amd64,linux/arm64 \
        --tag ${FULL_IMAGE_NAME} \
        --push \
        .
    
    echo "✅ Build and push completed successfully!"
}

# Function to verify the pushed image
verify_image() {
    echo "🔍 Verifying pushed image..."
    docker buildx imagetools inspect ${FULL_IMAGE_NAME}
    echo ""
    echo "✅ Image verification complete"
}

# Function to show usage instructions
show_usage() {
    echo "Usage: $0 [TAG]"
    echo ""
    echo "Examples:"
    echo "  $0                    # Build and push as 'latest'"
    echo "  $0 v1.0               # Build and push as 'v1.0'"
    echo "  $0 dev                # Build and push as 'dev'"
    echo ""
    echo "The script will build for both AMD64 (Ubuntu) and ARM64 (macOS) platforms."
}

# Function to show deployment instructions
show_deployment() {
    echo ""
    echo "🎉 Build completed successfully!"
    echo "================================="
    echo ""
    echo "Your image is now available at: ${FULL_IMAGE_NAME}"
    echo ""
    echo "To deploy on your Ubuntu server:"
    echo "1. SSH to your server:"
    echo "   ssh user@jarvis.thanhpt.xyz"
    echo ""
    echo "2. Run the deployment:"
    echo "   docker run -d \\"
    echo "     --name homecam-api \\"
    echo "     --restart unless-stopped \\"
    echo "     -p 8020:8020 \\"
    echo "     --device=/dev/video0:/dev/video0 \\"
    echo "     --device=/dev/video1:/dev/video1 \\"
    echo "     --device=/dev/video2:/dev/video2 \\"
    echo "     -e CAMERA_DEVICE_ID=0 \\"
    echo "     -e CAMERA_WIDTH=1280 \\"
    echo "     -e CAMERA_HEIGHT=720 \\"
    echo "     -e CAMERA_FPS=10 \\"
    echo "     --privileged \\"
    echo "     ${FULL_IMAGE_NAME}"
    echo ""
    echo "3. Or use the deployment script:"
    echo "   ./deploy-server.sh"
}

# Main execution
main() {
    check_buildx
    setup_builder
    build_and_push
    verify_image
    show_deployment
}

# Help function
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    show_usage
    exit 0
fi

# Run main function
main 