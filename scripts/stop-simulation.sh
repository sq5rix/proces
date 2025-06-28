#!/bin/bash

# Kafka IoT Simulator - Stop Script
# This script stops the complete IoT simulation environment

set -e

echo "🛑 Stopping Kafka IoT Simulator..."

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

# Navigate to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

print_status "Project root: $PROJECT_ROOT"

# Stop all services
print_status "Stopping all services..."
docker-compose down

# Optional: Remove volumes (uncomment if you want to clear all data)
# print_warning "Removing volumes and data..."
# docker-compose down -v

# Optional: Remove images (uncomment if you want to remove built images)
# print_warning "Removing built images..."
# docker-compose down --rmi local

print_success "All services stopped successfully!"

echo ""
echo "🏁 Kafka IoT Simulator has been stopped."
echo ""
echo "💡 To start again, run: ./scripts/start-simulation.sh"
echo "🗑️  To remove all data, run: docker-compose down -v"
echo "🧹 To remove images too, run: docker-compose down -v --rmi local"

