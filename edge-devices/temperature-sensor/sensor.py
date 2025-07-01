#!/usr/bin/env python3
"""
Temperature Sensor Simulator for Kafka IoT System
Simulates a temperature sensor that sends readings to Kafka
"""

import json
import random
import time
import logging
import os
import math
from datetime import datetime
import uuid
from kafka import KafkaProducer
from kafka.errors import KafkaError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TemperatureSensor:
    def __init__(self, device_id, kafka_servers, topic='iot-sensors'):
        self.device_id = device_id
        self.kafka_servers = kafka_servers
        self.topic = topic
        self.producer = None
        self.base_temperature = 20.0  # Base temperature in Celsius
        self.temperature_drift = 0.0  # Gradual temperature drift
        
    def connect_kafka(self):
        """Connect to Kafka broker"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.kafka_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                retries=5,
                retry_backoff_ms=1000
            )
            logger.info(f"Connected to Kafka at {self.kafka_servers}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            return False
    
    def generate_temperature_reading(self):
        """Generate realistic temperature reading with some randomness and drift"""
        # Simulate daily temperature variation (simplified sine wave)
        hour = datetime.now().hour
        daily_variation = 5 * math.sin((hour - 6) * math.pi / 12)
        
        # Add random noise
        noise = random.uniform(-1.0, 1.0)
        
        # Gradual drift simulation
        self.temperature_drift += random.uniform(-0.01, 0.01)
        self.temperature_drift = max(-5.0, min(5.0, self.temperature_drift))
        
        temperature = self.base_temperature + daily_variation + noise + self.temperature_drift
        return round(temperature, 2)
    
    def create_sensor_message(self):
        """Create sensor message in standard IoT format"""
        timestamp = datetime.utcnow().isoformat() + 'Z'
        temperature = self.generate_temperature_reading()
        
        message = {
            'device_id': self.device_id,
            'sensor_type': 'temperature',
            'timestamp': timestamp,
            'location': {
                'building': 'Building-A',
                'floor': 2,
                'room': 'Server-Room-01'
            },
            'data': {
                'temperature_celsius': temperature,
                'temperature_fahrenheit': round(temperature * 9/5 + 32, 2),
                'unit': 'celsius',
                'status': 'normal' if -10 <= temperature <= 50 else 'alert'
            },
            'metadata': {
                'firmware_version': '1.2.3',
                'battery_level': random.randint(80, 100),
                'signal_strength': random.randint(-70, -30)
            }
        }
        return message
    
    def send_message(self, message):
        """Send message to Kafka topic"""
        try:
            future = self.producer.send(
                self.topic,
                key=self.device_id,
                value=message
            )
            # Wait for message to be sent
            record_metadata = future.get(timeout=10)
            logger.info(f"Message sent to topic {record_metadata.topic} "
                       f"partition {record_metadata.partition} "
                       f"offset {record_metadata.offset}")
            return True
        except KafkaError as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    def run_simulation(self, interval=5):
        """Run the temperature sensor simulation"""
        logger.info(f"Starting temperature sensor simulation for device {self.device_id}")
        
        if not self.connect_kafka():
            logger.error("Cannot start simulation without Kafka connection")
            return
        
        try:
            while True:
                message = self.create_sensor_message()
                if self.send_message(message):
                    logger.info(f"Temperature reading: {message['data']['temperature_celsius']}°C")
                else:
                    logger.warning("Failed to send temperature reading")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("Simulation stopped by user")
        except Exception as e:
            logger.error(f"Simulation error: {e}")
        finally:
            if self.producer:
                self.producer.close()
            logger.info("Temperature sensor simulation ended")

def main():
    # Get configuration from environment variables
    device_id = str(uuid.uuid4()) # Generate a unique device ID
    kafka_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092').split(',')
    topic = os.getenv('KAFKA_TOPIC', 'iot-sensors')
    interval = int(os.getenv('SENSOR_INTERVAL', '5'))
    
    logger.info(f"Initializing temperature sensor: {device_id}")
    logger.info(f"Kafka servers: {kafka_servers}")
    logger.info(f"Topic: {topic}")
    logger.info(f"Interval: {interval} seconds")
    
    # Create and run sensor
    sensor = TemperatureSensor(device_id, kafka_servers, topic)
    sensor.run_simulation(interval)

if __name__ == "__main__":
    main()

