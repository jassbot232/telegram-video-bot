#!/bin/bash

# Deployment script for Telegram Video Bot
set -e

echo "🚀 Starting deployment process..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Function to log messages
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if required files exist
required_files=("Dockerfile" "requirements.txt" "bot.py" "video_processor.py" "config.py")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        error "Required file $file not found!"
        exit 1
    fi
done

# Build Docker image
log "Building Docker image..."
docker build -t telegram-video-bot .

# Test the image
log "Testing the Docker image..."
docker run --rm -e BOT_TOKEN="test" telegram-video-bot python -c "print('Docker image test successful')"

log "Docker image built successfully!"

# Push to Docker Hub (optional)
if [ "$1" == "--push" ]; then
    if [ -z "$DOCKER_USERNAME" ] || [ -z "$DOCKER_PASSWORD" ]; then
        warn "Docker credentials not set. Skipping push to Docker Hub."
    else
        log "Pushing to Docker Hub..."
        docker tag telegram-video-bot $DOCKER_USERNAME/telegram-video-bot:latest
        echo $DOCKER_PASSWORD | docker login -u $DOCKER_USERNAME --password-stdin
        docker push $DOCKER_USERNAME/telegram-video-bot:latest
        log "Image pushed to Docker Hub successfully!"
    fi
fi

log "Deployment preparation completed!"
echo ""
echo "Next steps:"
echo "1. Set BOT_TOKEN environment variable"
echo "2. Deploy to Koyeb using:"
echo "   - GitHub repository connection"
echo "   - Or using: docker-compose up -d"
echo ""
echo "To run locally:"
echo "docker run -d -e BOT_TOKEN='your_token_here' --name telegram-bot telegram-video-bot"
