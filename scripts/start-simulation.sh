#!/bin/bash

# Kafka IoT Simulator - Start Script
# This script starts the complete IoT simulation environment

set -e

echo "🚀 Starting Kafka IoT Simulator..."

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

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose > /dev/null 2>&1; then
    print_error "docker-compose is not installed. Please install docker-compose and try again."
    exit 1
fi

# Navigate to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

print_status "Project root: $PROJECT_ROOT"

# Create Kafka topics (optional - Kafka will auto-create them)
create_topics() {
    print_status "Creating Kafka topics..."
    
    # Wait for Kafka to be ready
    sleep 10
    
    docker exec kafka kafka-topics --bootstrap-server localhost:9092 --create --if-not-exists --topic iot-sensors --partitions 3 --replication-factor 1
    docker exec kafka kafka-topics --bootstrap-server localhost:9092 --create --if-not-exists --topic iot-alerts --partitions 1 --replication-factor 1
    
    print_success "Kafka topics created successfully"
}

# Start infrastructure (Kafka, Zookeeper, Kafka UI)
print_status "Starting Kafka infrastructure..."
docker-compose up -d zookeeper kafka kafka-ui

print_status "Waiting for Kafka to be ready..."
sleep 15

# Check if Kafka is ready
KAFKA_READY=false
for i in {1..30}; do
    if docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list > /dev/null 2>&1; then
        KAFKA_READY=true
        break
    fi
    print_status "Waiting for Kafka... (attempt $i/30)"
    sleep 2
done

if [ "$KAFKA_READY" = false ]; then
    print_error "Kafka failed to start within expected time"
    exit 1
fi

print_success "Kafka infrastructure is ready"

# Create topics
create_topics

# Build edge device images
print_status "Building edge device Docker images..."
docker-compose build temperature-sensor humidity-sensor motion-detector

# Start edge devices
print_status "Starting edge device simulators..."
docker-compose up -d temperature-sensor humidity-sensor motion-detector

print_success "All services started successfully!"

echo ""
echo "🎉 Kafka IoT Simulator is now running!"
echo ""
echo "📊 Access points:"
echo "   • Kafka UI: http://localhost:8080"
echo "   • Kafka Broker: localhost:9092"
echo "   • Zookeeper: localhost:2181"
echo ""
echo "🔧 Management commands:"
echo "   • View logs: docker-compose logs -f [service-name]"
echo "   • Stop simulation: ./scripts/stop-simulation.sh"
echo "   • View status: docker-compose ps"
echo ""
echo "📡 Edge devices running:"
echo "   • Temperature Sensor (temp-sensor-001)"
echo "   • Humidity Sensor (humidity-sensor-001)"  
echo "   • Motion Detector (motion-detector-001)"
echo ""
echo "💡 Monitor messages in Kafka UI or use:"
echo "   docker exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic iot-sensors --from-beginning"

