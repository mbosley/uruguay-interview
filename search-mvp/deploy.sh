#!/bin/bash

# Uruguay Interview Research Agent - Deployment Script

echo "🚀 Deploying Uruguay Interview Research Agent"
echo "==========================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create .env with your API keys:"
    echo "  MOONSHOT_API_KEY=your_key_here"
    echo "  GROQ_API_KEY=your_key_here"
    exit 1
fi

# Load environment variables
source .env

# Check for required API keys
if [ -z "$MOONSHOT_API_KEY" ] && [ -z "$GROQ_API_KEY" ]; then
    echo "❌ Error: At least one API key (MOONSHOT_API_KEY or GROQ_API_KEY) must be set"
    exit 1
fi

# Detect docker compose command
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    echo "❌ Error: Docker Compose not found!"
    echo "Please install Docker Desktop or Docker Compose"
    exit 1
fi

echo "✅ Using: $DOCKER_COMPOSE"

# Build and start containers
echo "🔨 Building Docker containers..."
$DOCKER_COMPOSE build

echo "🚀 Starting services..."
$DOCKER_COMPOSE up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
if curl -f http://localhost:8000/ > /dev/null 2>&1; then
    echo "✅ API server is running at http://localhost:8000"
else
    echo "❌ API server failed to start"
    $DOCKER_COMPOSE logs api
fi

if curl -f http://localhost:8501/ > /dev/null 2>&1; then
    echo "✅ Web interface is running at http://localhost:8501"
else
    echo "❌ Web interface failed to start"
    $DOCKER_COMPOSE logs streamlit
fi

echo ""
echo "🎉 Deployment complete!"
echo "Access the demo at: http://localhost:8501"
echo ""
echo "To view logs: $DOCKER_COMPOSE logs -f"
echo "To stop: $DOCKER_COMPOSE down"