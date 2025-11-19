"""
Ingest Simulator - Generates simulated security events and sends to Kafka
"""
import json
import time
import os
import logging
from datetime import datetime
from confluent_kafka import Producer
from faker import Faker
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
KAFKA_TOPIC = "events"

# Initialize Kafka producer
conf = {'bootstrap.servers': KAFKA_BOOTSTRAP}
producer = Producer(conf)

fake = Faker()


def generate_network_event():
    """Generate a simulated network security event"""
    source_ip = fake.ipv4()
    dest_ip = fake.ipv4()
    
    event_types = [
        "port_scan",
        "brute_force_attempt",
        "suspicious_dns",
        "malware_detected",
        "ddos_activity",
        "unauthorized_access",
        "data_exfiltration",
        "privilege_escalation"
    ]
    
    event_type = random.choice(event_types)
    severity_map = {
        "port_scan": 2.5,
        "brute_force_attempt": 6.0,
        "suspicious_dns": 4.0,
        "malware_detected": 9.0,
        "ddos_activity": 8.5,
        "unauthorized_access": 7.5,
        "data_exfiltration": 9.5,
        "privilege_escalation": 8.0
    }
    
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "source_ip": source_ip,
        "dest_ip": dest_ip,
        "source_port": random.randint(1024, 65535),
        "dest_port": random.choice([22, 23, 80, 443, 3306, 5432, 8080]),
        "severity": severity_map.get(event_type, 5.0),
        "detector": "network_ips",
        "description": f"{event_type} detected from {source_ip} to {dest_ip}",
        "protocol": random.choice(["TCP", "UDP"]),
        "bytes_transferred": random.randint(100, 10000000),
        "packets": random.randint(10, 10000)
    }
    
    return event


def generate_host_event():
    """Generate a simulated host security event"""
    hostnames = [f"server-{i}" for i in range(1, 10)]
    users = ["root", "admin", "user", "service_account"]
    
    host_events = [
        "failed_login",
        "privilege_escalation",
        "process_injection",
        "file_deletion",
        "registry_modification",
        "service_stopped"
    ]
    
    event_type = random.choice(host_events)
    severity_map = {
        "failed_login": 2.0,
        "privilege_escalation": 8.5,
        "process_injection": 9.0,
        "file_deletion": 5.0,
        "registry_modification": 6.0,
        "service_stopped": 4.0
    }
    
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "hostname": random.choice(hostnames),
        "user": random.choice(users),
        "severity": severity_map.get(event_type, 5.0),
        "detector": "host_edr",
        "description": f"{event_type} on {random.choice(hostnames)} by {random.choice(users)}",
        "process_name": random.choice(["svchost.exe", "powershell.exe", "cmd.exe", "explorer.exe"]),
        "process_id": random.randint(1000, 65535),
        "command_line": "sample command executed"
    }
    
    return event


def delivery_callback(err, msg):
    """Kafka delivery callback"""
    if err:
        logger.error(f"Message delivery failed: {err}")
    else:
        logger.info(f"Message delivered to {msg.topic()} [{msg.partition()}]")


def send_event(event):
    """Send event to Kafka"""
    try:
        producer.produce(
            topic=KAFKA_TOPIC,
            value=json.dumps(event),
            callback=delivery_callback
        )
        producer.poll(0)
    except Exception as e:
        logger.error(f"Error sending event: {e}")


def main():
    """Main simulation loop"""
    logger.info(f"Starting ingest simulator, sending to {KAFKA_BOOTSTRAP}")
    logger.info(f"Events will be sent to topic: {KAFKA_TOPIC}")
    
    event_count = 0
    
    try:
        while True:
            # Generate random event
            if random.random() < 0.6:
                event = generate_network_event()
            else:
                event = generate_host_event()
            
            # Send event
            send_event(event)
            event_count += 1
            
            if event_count % 10 == 0:
                logger.info(f"Sent {event_count} events. Last event: {event.get('description')}")
            
            # Random delay between 0.5 and 2 seconds
            time.sleep(random.uniform(0.5, 2.0))
    
    except KeyboardInterrupt:
        logger.info(f"Simulator stopped. Total events sent: {event_count}")
    finally:
        producer.flush()
        logger.info("Kafka producer flushed")


if __name__ == "__main__":
    main()
