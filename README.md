# Kafka IoT Simulator (proces)

A comprehensive Kafka-based IoT simulation environment using DevContainers and Docker. This project simulates multiple edge devices (temperature sensors, humidity sensors, and motion detectors) that send realistic IoT data to a Kafka message broker.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Temperature    │    │    Humidity     │    │     Motion      │
│    Sensor       │    │     Sensor      │    │   Detector      │
│   (Docker)      │    │   (Docker)      │    │   (Docker)      │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │       Kafka Broker        │
                    │      (with Zookeeper)     │
                    └─────────────┬─────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │       Kafka UI            │
                    │   (Web Dashboard)         │
                    └───────────────────────────┘
```

## Start

docker-compose up -d --build --scale temperature-sensor=4 --scale humidity-sensor=3 --scale motion-detector=2

## 🚀 Features

- **DevContainer Support**: Full development environment with VS Code integration
- **Multiple Edge Devices**: Temperature, humidity, and motion sensors with realistic data patterns
- **Kafka Infrastructure**: Complete Kafka setup with Zookeeper and web UI
- **Docker Containerization**: All edge devices run in separate Docker containers
- **Realistic IoT Data**: Time-based variations, noise, and realistic sensor patterns
- **Monitoring Tools**: Built-in scripts for monitoring and debugging
- **Easy Deployment**: One-command setup and teardown

## 📋 Prerequisites

- Docker and Docker Compose
- VS Code with DevContainers extension (optional)
- Git

## 🔧 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd proces
```

### 2. Start the Complete Simulation

```bash
./scripts/start-simulation.sh
```

This will:

- Start Kafka and Zookeeper
- Launch Kafka UI web interface
- Build and start all edge device simulators

### 3. Monitor the System

Access the Kafka UI at: http://localhost:8080

Or use the monitoring script:

```bash
./scripts/monitor.sh status    # Show service status
./scripts/monitor.sh logs      # Show all logs
./scripts/monitor.sh consume   # Consume messages in real-time
```

### 4. Stop the Simulation

```bash
./scripts/stop-simulation.sh
```

## 🛠️ Development with DevContainers

### Using VS Code

1. Open the project in VS Code
2. When prompted, click "Reopen in Container"
3. VS Code will build the devcontainer and provide a complete development environment

### Manual DevContainer Setup

```bash
# Install DevContainer CLI
npm install -g @devcontainers/cli

# Build and run devcontainer
devcontainer build --workspace-folder .
devcontainer up --workspace-folder .
```

## 📊 Edge Devices

### Temperature Sensor

- **Device ID**: `temp-sensor-001`
- **Interval**: 5 seconds
- **Data**: Temperature in Celsius and Fahrenheit
- **Features**: Daily temperature cycles, gradual drift, random noise

### Humidity Sensor

- **Device ID**: `humidity-sensor-001`
- **Interval**: 7 seconds
- **Data**: Humidity percentage with comfort levels
- **Features**: Inverse correlation with temperature, realistic bounds

### Motion Detector

- **Device ID**: `motion-detector-001`
- **Interval**: 3 seconds
- **Data**: Motion detection events with intensity levels
- **Features**: Time-based detection probability, motion state tracking

## 🗂️ Project Structure

```
proces/
├── .devcontainer/
│   └── devcontainer.json          # DevContainer configuration
├── edge-devices/
│   ├── temperature-sensor/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── sensor.py
│   ├── humidity-sensor/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── sensor.py
│   └── motion-detector/
│       ├── Dockerfile
│       ├── requirements.txt
│       └── sensor.py
├── scripts/
│   ├── start-simulation.sh        # Start everything
│   ├── stop-simulation.sh         # Stop everything
│   ├── deploy.sh                  # Deploy with DevContainer CLI
│   └── monitor.sh                 # Monitoring tools
├── config/
│   └── kafka-config.yml           # Configuration settings
├── docker-compose.yml             # Docker services definition
└── README.md
```

## 🔍 Monitoring and Debugging

### Kafka UI Dashboard

- URL: http://localhost:8080
- View topics, messages, consumer groups
- Real-time message monitoring

### Command Line Tools

```bash
# Show service status
./scripts/monitor.sh status

# View logs for specific service
./scripts/monitor.sh logs temperature-sensor

# Consume messages from command line
./scripts/monitor.sh consume

# Check health of all services
./scripts/monitor.sh health
```

### Direct Kafka Commands

```bash
# List topics
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# Consume messages
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic iot-sensors \
  --from-beginning
```

## ⚙️ Configuration

### Environment Variables

Each edge device supports the following environment variables:

- `KAFKA_BOOTSTRAP_SERVERS`: Kafka broker address (default: `localhost:9092`)
- `DEVICE_ID`: Unique device identifier
- `SENSOR_TYPE`: Type of sensor (temperature, humidity, motion)
- `KAFKA_TOPIC`: Target Kafka topic (default: `iot-sensors`)
- `SENSOR_INTERVAL`: Sending interval in seconds

### Kafka Configuration

Edit `config/kafka-config.yml` to modify:

- Kafka settings
- Device configurations
- Simulation parameters
- Monitoring settings

## 📡 Message Format

All sensors send messages in a standardized IoT format:

```json
{
  "device_id": "temp-sensor-001",
  "sensor_type": "temperature",
  "timestamp": "2024-01-15T10:30:00Z",
  "location": {
    "building": "Building-A",
    "floor": 2,
    "room": "Server-Room-01"
  },
  "data": {
    "temperature_celsius": 22.5,
    "temperature_fahrenheit": 72.5,
    "unit": "celsius",
    "status": "normal"
  },
  "metadata": {
    "firmware_version": "1.2.3",
    "battery_level": 85,
    "signal_strength": -45
  }
}
```

## 🚀 Deployment Options

### Option 1: Docker Compose (Recommended)

```bash
./scripts/start-simulation.sh
```

### Option 2: DevContainer CLI

```bash
./scripts/deploy.sh
```

### Option 3: Manual Docker

```bash
# Start infrastructure
docker-compose up -d zookeeper kafka kafka-ui

# Build and start edge devices
docker-compose build
docker-compose up -d temperature-sensor humidity-sensor motion-detector
```

## 🧪 Testing and Development

### Running Individual Sensors

```bash
# Run temperature sensor locally
cd edge-devices/temperature-sensor
pip install -r requirements.txt
python sensor.py

# Or with custom settings
DEVICE_ID=temp-test-001 SENSOR_INTERVAL=10 python sensor.py
```

### Adding New Sensors

1. Create a new directory under `edge-devices/`
2. Add `Dockerfile`, `requirements.txt`, and `sensor.py`
3. Update `docker-compose.yml` to include the new service
4. Follow the existing sensor patterns for message format

## 🔧 Troubleshooting

### Common Issues

1. **Kafka not starting**: Ensure Docker has enough memory allocated (4GB+)
2. **Port conflicts**: Check if ports 9092, 2181, or 8080 are already in use
3. **Permission errors**: Ensure scripts have execute permissions (`chmod +x scripts/*.sh`)

### Logs and Debugging

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f temperature-sensor

# Check container status
docker-compose ps
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues and questions:

- Create an issue in the repository
- Check the troubleshooting section
- Review container logs for error details
