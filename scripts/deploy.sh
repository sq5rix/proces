#!/bin/bash

# Kafka IoT Simulator - Deployment Script
# This script deploys edge devices using devcontainer CLI

set -e

echo "🚀 Deploying Kafka IoT Simulator with DevContainers..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if devcontainer CLI is available
if ! command -v devcontainer > /dev/null 2>&1; then
    print_error "DevContainer CLI is not installed."
    print_status "Install it with: npm install -g @devcontainers/cli"
    exit 1
fi

# Navigate to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

print_status "Project root: $PROJECT_ROOT"

# Function to deploy individual edge device
deploy_edge_device() {
    local device_name=$1
    local device_path=$2
    
    print_status "Deploying $device_name..."
    
    # Create temporary devcontainer.json for the edge device
    cat > "$device_path/.devcontainer.json" << EOF
{
  "name": "$device_name",
  "build": {
    "dockerfile": "Dockerfile"
  },
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python"
      ]
    }
  },
  "forwardPorts": [],
  "postCreateCommand": "pip install -r requirements.txt",
  "remoteUser": "sensor"
}
EOF

    # Build and run the devcontainer
    cd "$device_path"
    devcontainer build --workspace-folder .
    
    print_success "$device_name deployed successfully"
    cd "$PROJECT_ROOT"
}

# Start Kafka infrastructure first
print_status "Starting Kafka infrastructure..."
docker-compose up -d zookeeper kafka kafka-ui

print_status "Waiting for Kafka to be ready..."
sleep 15

# Deploy edge devices using devcontainer CLI
print_status "Deploying edge devices with DevContainer CLI..."

# Deploy each edge device
deploy_edge_device "Temperature Sensor" "edge-devices/temperature-sensor"
deploy_edge_device "Humidity Sensor" "edge-devices/humidity-sensor"
deploy_edge_device "Motion Detector" "edge-devices/motion-detector"

print_success "All edge devices deployed successfully!"

echo ""
echo "🎉 Kafka IoT Simulator deployment completed!"
echo ""
echo "📊 Access points:"
echo "   • Kafka UI: http://localhost:8080"
echo "   • Kafka Broker: localhost:9092"
echo ""
echo "🔧 Management:"
echo "   • Start sensors: ./scripts/start-simulation.sh"
echo "   • Stop everything: ./scripts/stop-simulation.sh"
echo ""
echo "💡 Note: Edge devices are built as DevContainers but not automatically started."
echo "   Use docker-compose or the start-simulation.sh script to run them."

