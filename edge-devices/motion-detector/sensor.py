#!/usr/bin/env python3
"""
Motion Detector Simulator for Kafka IoT System
Simulates a motion detector that sends event data to Kafka
"""

import json
import random
import time
import logging
import uuid
import os
from datetime import datetime, timedelta
from kafka import KafkaProducer
from kafka.errors import KafkaError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MotionDetector:
    def __init__(self, device_id, kafka_servers, topic='iot-sensors'):
        self.device_id = device_id
        self.kafka_servers = kafka_servers
        self.topic = topic
        self.producer = None
        self.last_motion_time = None
        self.motion_state = False
        self.motion_count_today = 0
        
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
    
    def should_detect_motion(self):
        """Simulate realistic motion detection patterns based on time of day"""
        hour = datetime.now().hour
        
        # Higher probability during business hours (9-17)
        if 9 <= hour <= 17:
            base_probability = 0.3
        # Lower probability during evening/night
        elif 18 <= hour <= 22:
            base_probability = 0.15
        # Very low probability during night/early morning
        else:
            base_probability = 0.05
        
        # Add some randomness
        return random.random() < base_probability
    
    def generate_motion_event(self):
        """Generate motion detection event"""
        now = datetime.utcnow()
        
        # Determine if motion is detected
        motion_detected = self.should_detect_motion()
        
        if motion_detected:
            self.last_motion_time = now
            self.motion_count_today += 1
            self.motion_state = True
        else:
            # Motion state becomes false after 30 seconds of no motion
            if self.last_motion_time and (now - self.last_motion_time).seconds > 30:
                self.motion_state = False
        
        return motion_detected
    
    def get_motion_intensity(self):
        """Simulate motion intensity based on detection patterns"""
        if not self.motion_state:
            return 0
        
        # Simulate different intensities
        intensities = ['low', 'medium', 'high']
        weights = [0.5, 0.3, 0.2]  # Most motion is low intensity
        return random.choices(intensities, weights=weights)[0]
    
    def create_sensor_message(self):
        """Create sensor message in standard IoT format"""
        timestamp = datetime.utcnow().isoformat() + 'Z'
        motion_detected = self.generate_motion_event()
        intensity = self.get_motion_intensity()
        
        message = {
            'device_id': self.device_id,
            'sensor_type': 'motion',
            'timestamp': timestamp,
            'location': {
                'building': 'Building-A',
                'floor': 2,
                'room': 'Server-Room-01',
                'zone': 'entrance'
            },
            'data': {
                'motion_detected': motion_detected,
                'motion_state': self.motion_state,
                'intensity': intensity,
                'motion_count_today': self.motion_count_today,
                'last_motion_time': self.last_motion_time.isoformat() + 'Z' if self.last_motion_time else None,
                'detection_range_meters': 5.0,
                'confidence': random.uniform(0.85, 0.99) if motion_detected else 1.0
            },
            'metadata': {
                'firmware_version': '2.0.1',
                'battery_level': random.randint(70, 100),
                'signal_strength': random.randint(-80, -20),
                'sensitivity_level': 'medium',
                'installation_date': '2024-01-10'
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
    
    def run_simulation(self, interval=3):
        """Run the motion detector simulation"""
        logger.info(f"Starting motion detector simulation for device {self.device_id}")
        
        if not self.connect_kafka():
            logger.error("Cannot start simulation without Kafka connection")
            return
        
        try:
            while True:
                message = self.create_sensor_message()
                if self.send_message(message):
                    motion_status = "MOTION DETECTED" if message['data']['motion_detected'] else "No motion"
                    intensity = message['data']['intensity'] if message['data']['motion_detected'] else "N/A"
                    logger.info(f"Motion status: {motion_status} (intensity: {intensity})")
                else:
                    logger.warning("Failed to send motion detection data")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("Simulation stopped by user")
        except Exception as e:
            logger.error(f"Simulation error: {e}")
        finally:
            if self.producer:
                self.producer.close()
            logger.info("Motion detector simulation ended")

def main():
    # Get configuration from environment variables
    device_id = str(uuid.uuid4()) # Generate a unique UUID for the device ID
    kafka_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092').split(',')
    topic = os.getenv('KAFKA_TOPIC', 'iot-sensors')
    interval = int(os.getenv('SENSOR_INTERVAL', '3'))
    
    logger.info(f"Initializing motion detector: {device_id}")
    logger.info(f"Kafka servers: {kafka_servers}")
    logger.info(f"Topic: {topic}")
    logger.info(f"Interval: {interval} seconds")
    
    # Create and run sensor
    sensor = MotionDetector(device_id, kafka_servers, topic)
    sensor.run_simulation(interval)

if __name__ == "__main__":
    main()

