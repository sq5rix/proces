#!/bin/bash

# Kafka IoT Simulator - Monitoring Script
# This script provides monitoring capabilities for the IoT simulation

set -e

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

# Function to show help
show_help() {
    echo "🔍 Kafka IoT Simulator - Monitoring Tools"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  status          Show status of all services"
    echo "  logs [service]  Show logs for all services or specific service"
    echo "  topics          List Kafka topics"
    echo "  consume         Start consuming messages from iot-sensors topic"
    echo "  health          Check health of all services"
    echo "  stats           Show message statistics"
    echo "  help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 status"
    echo "  $0 logs temperature-sensor"
    echo "  $0 consume"
}

# Function to show service status
show_status() {
    print_status "Service Status:"
    docker-compose ps
    echo ""
    
    print_status "Docker Resource Usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
}

# Function to show logs
show_logs() {
    local service=$1
    if [ -z "$service" ]; then
        print_status "Showing logs for all services (last 50 lines):"
        docker-compose logs --tail=50 -f
    else
        print_status "Showing logs for $service:"
        docker-compose logs --tail=50 -f "$service"
    fi
}

# Function to list Kafka topics
list_topics() {
    print_status "Kafka Topics:"
    docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list
    echo ""
    
    print_status "Topic Details:"
    docker exec kafka kafka-topics --bootstrap-server localhost:9092 --describe
}

# Function to consume messages
consume_messages() {
    print_status "Consuming messages from iot-sensors topic (Press Ctrl+C to stop):"
    echo ""
    docker exec -it kafka kafka-console-consumer \
        --bootstrap-server localhost:9092 \
        --topic iot-sensors \
        --from-beginning \
        --property print.timestamp=true \
        --property print.key=true \
        --property print.value=true
}

# Function to check health
check_health() {
    print_status "Health Check Results:"
    echo ""
    
    # Check Kafka
    if docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list > /dev/null 2>&1; then
        print_success "✓ Kafka is healthy"
    else
        print_error "✗ Kafka is not responding"
    fi
    
    # Check Zookeeper
    if docker exec zookeeper zkServer.sh status > /dev/null 2>&1; then
        print_success "✓ Zookeeper is healthy"
    else
        print_error "✗ Zookeeper is not responding"
    fi
    
    # Check edge devices
    services=("temperature-sensor" "humidity-sensor" "motion-detector")
    for service in "${services[@]}"; do
        if docker-compose ps "$service" | grep -q "Up"; then
            print_success "✓ $service is running"
        else
            print_error "✗ $service is not running"
        fi
    done
    
    echo ""
    print_status "Container Health Status:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
}

# Function to show statistics
show_stats() {
    print_status "Message Statistics:"
    echo ""
    
    # Get topic statistics
    print_status "Topic Information:"
    docker exec kafka kafka-run-class kafka.tools.GetOffsetShell \
        --broker-list localhost:9092 \
        --topic iot-sensors
    
    echo ""
    print_status "Consumer Group Information:"
    docker exec kafka kafka-consumer-groups \
        --bootstrap-server localhost:9092 \
        --list
}

# Main script logic
case "${1:-help}" in
    "status")
        show_status
        ;;
    "logs")
        show_logs "$2"
        ;;
    "topics")
        list_topics
        ;;
    "consume")
        consume_messages
        ;;
    "health")
        check_health
        ;;
    "stats")
        show_stats
        ;;
    "help"|*)
        show_help
        ;;
esac

