#!/usr/bin/env python3
"""
Humidity Sensor Simulator for Kafka IoT System
Simulates a humidity sensor that sends readings to Kafka
"""

import json
import random
import time
import logging
import os
import math
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import KafkaError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HumiditySensor:
    def __init__(self, device_id, kafka_servers, topic='iot-sensors'):
        self.device_id = device_id
        self.kafka_servers = kafka_servers
        self.topic = topic
        self.producer = None
        self.base_humidity = 45.0  # Base humidity percentage
        self.humidity_drift = 0.0  # Gradual humidity drift
        
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
    
    def generate_humidity_reading(self):
        """Generate realistic humidity reading with some randomness and drift"""
        # Simulate daily humidity variation (inverse relationship with temperature cycle)
        hour = datetime.now().hour
        daily_variation = -10 * math.sin((hour - 6) * math.pi / 12)
        
        # Add random noise
        noise = random.uniform(-3.0, 3.0)
        
        # Gradual drift simulation
        self.humidity_drift += random.uniform(-0.02, 0.02)
        self.humidity_drift = max(-10.0, min(10.0, self.humidity_drift))
        
        humidity = self.base_humidity + daily_variation + noise + self.humidity_drift
        # Ensure humidity stays within realistic bounds (0-100%)
        humidity = max(0.0, min(100.0, humidity))
        return round(humidity, 2)
    
    def get_humidity_status(self, humidity):
        """Determine humidity status based on reading"""
        if humidity < 30:
            return 'low'
        elif humidity > 70:
            return 'high'
        else:
            return 'normal'
    
    def create_sensor_message(self):
        """Create sensor message in standard IoT format"""
        timestamp = datetime.utcnow().isoformat() + 'Z'
        humidity = self.generate_humidity_reading()
        
        message = {
            'device_id': self.device_id,
            'sensor_type': 'humidity',
            'timestamp': timestamp,
            'location': {
                'building': 'Building-A',
                'floor': 2,
                'room': 'Server-Room-01'
            },
            'data': {
                'humidity_percentage': humidity,
                'unit': 'percent',
                'status': self.get_humidity_status(humidity),
                'comfort_level': 'comfortable' if 40 <= humidity <= 60 else 'uncomfortable'
            },
            'metadata': {
                'firmware_version': '1.1.8',
                'battery_level': random.randint(75, 100),
                'signal_strength': random.randint(-75, -25),
                'calibration_date': '2024-01-15'
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
    
    def run_simulation(self, interval=7):
        """Run the humidity sensor simulation"""
        logger.info(f"Starting humidity sensor simulation for device {self.device_id}")
        
        if not self.connect_kafka():
            logger.error("Cannot start simulation without Kafka connection")
            return
        
        try:
            while True:
                message = self.create_sensor_message()
                if self.send_message(message):
                    logger.info(f"Humidity reading: {message['data']['humidity_percentage']}% "
                               f"({message['data']['status']})")
                else:
                    logger.warning("Failed to send humidity reading")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("Simulation stopped by user")
        except Exception as e:
            logger.error(f"Simulation error: {e}")
        finally:
            if self.producer:
                self.producer.close()
            logger.info("Humidity sensor simulation ended")

def main():
    # Get configuration from environment variables
    device_id = os.getenv('DEVICE_ID', 'humidity-sensor-001')
    kafka_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092').split(',')
    topic = os.getenv('KAFKA_TOPIC', 'iot-sensors')
    interval = int(os.getenv('SENSOR_INTERVAL', '7'))
    
    logger.info(f"Initializing humidity sensor: {device_id}")
    logger.info(f"Kafka servers: {kafka_servers}")
    logger.info(f"Topic: {topic}")
    logger.info(f"Interval: {interval} seconds")
    
    # Create and run sensor
    sensor = HumiditySensor(device_id, kafka_servers, topic)
    sensor.run_simulation(interval)

if __name__ == "__main__":
    main()

