#!/bin/bash

# Land Analysis MSA Docker Build Script

set -e

echo "🐳 Building Land Analysis MSA Docker Image..."

# Check if we're in the docker directory
if [ ! -f "Dockerfile" ]; then
    echo "❌ Error: Please run this script from the docker directory"
    exit 1
fi

# Check if final directory exists
if [ ! -d "../final" ]; then
    echo "❌ Error: ../final directory not found"
    exit 1
fi

# Build the Docker image
echo "📦 Building Docker image..."
docker build -t land-analysis-msa:latest .

echo "✅ Docker image built successfully!"
echo ""
echo "🚀 To run the container:"
echo "   docker-compose up -d"
echo ""
echo "🌐 Or run directly:"
echo "   docker run -d --name land-analysis-msa -p 8000:8000 land-analysis-msa:latest"
echo ""
echo "📍 API will be available at: http://localhost:8000"
echo "📚 API docs at: http://localhost:8000/docs"