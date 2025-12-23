"""
Real IDS/IPS Log Generator - Generates realistic Suricata/Snort-like logs
This module simulates real security events that would come from actual IDS/IPS systems
"""
import json
import time
import os
import logging
from datetime import datetime, timedelta
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

# Realistic alert categories and signatures
ALERT_CATEGORIES = {
    "Potential Corporate Privacy Breach": 1,  # Severity 1 (critical)
    "Suspicious Command Execution": 1,
    "Malware Command and Control Traffic": 1,
    "Known Malware": 1,
    "Network Trojan": 1,
    "Phishing Attempt": 2,  # Severity 2 (high)
    "Suspicious Login Attempt": 2,
    "Potential Intrusion Attempt": 2,
    "Exploit Attempt": 2,
    "Port Scan": 3,  # Severity 3 (medium)
    "Brute Force Login": 3,
    "Unusual User Activity": 3,
    "Suspicious Network Traffic": 3,
}

ALERT_SIGNATURES = {
    "ET POLICY Dropbox.com Offsite File Backup": 3,
    "ET TROJAN Suspicious Powershell.exe Execution": 1,
    "ET MALWARE Suspicious User-Agent": 1,
    "ET CNC Known C2 Server": 1,
    "ET DOS SYN Flood Attack": 2,
    "ET SHELLCODE Possible Shellcode Detection": 1,
    "ET PHISHING Suspicious Email Attachment": 2,
    "ET SCAN Aggressive Scanning": 3,
    "ET POLICY Known P2P Application": 3,
    "ET RECONNAISSANCE Port Scan": 3,
    "ET EXPLOIT Possible SQL Injection Attempt": 2,
    "ET EXPLOIT Possible Directory Traversal": 2,
    "ET POLICY SSH Brute Force": 2,
    "ET INAPPROPRIATE Possible Compromise": 1,
}

# Common ports for different attack types
COMPROMISED_PORTS = [
    22,    # SSH
    23,    # Telnet
    3306,  # MySQL
    5432,  # PostgreSQL
    6379,  # Redis
    27017, # MongoDB
    8080,  # HTTP Alt
    3389,  # RDP
    445,   # SMB
    139,   # NetBIOS
]

EXTERNAL_IPS = [
    "203.0.113.",    # TEST-NET-3
    "198.51.100.",   # TEST-NET-2
    "192.0.2.",      # TEST-NET-1
    "10.20.30.",     # Internal range
    "172.16.",       # Internal range
]

INTERNAL_IPS = [
    "192.168.1.",
    "192.168.2.",
    "10.0.0.",
    "10.0.1.",
    "172.20.",
]


def generate_external_ip():
    """Generate a realistic external IP"""
    prefix = random.choice(EXTERNAL_IPS)
    return f"{prefix}{random.randint(0, 255)}"


def generate_internal_ip():
    """Generate a realistic internal IP"""
    prefix = random.choice(INTERNAL_IPS)
    return f"{prefix}{random.randint(1, 254)}"


def generate_suricata_eve_event():
    """
    Generate a realistic Suricata EVE JSON format event
    Mimics real IDS/IPS alert format
    """
    event_type = random.choice(["brute_force", "malware", "exploit", "scan", "phishing"])
    
    if random.random() < 0.7:  # 70% external -> internal attacks
        src_ip = generate_external_ip()
        dest_ip = generate_internal_ip()
    else:  # 30% internal -> external (data exfiltration)
        src_ip = generate_internal_ip()
        dest_ip = generate_external_ip()
    
    src_port = random.choice([80, 443, 53, 22, 123]) if random.random() < 0.3 else random.randint(1024, 65535)
    dest_port = random.choice(COMPROMISED_PORTS)
    
    signature, severity = random.choice(list(ALERT_SIGNATURES.items()))
    category, cat_severity = random.choice(list(ALERT_CATEGORIES.items()))
    
    # Map severity to float score
    severity_score = 10.0 - (severity * 2.5)
    
    event = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "flow_id": random.randint(1000000000, 9999999999),
        "pcap_cnt": random.randint(1, 100000),
        "event_type": event_type,
        "severity": severity,
        "src_ip": src_ip,
        "src_port": src_port,
        "dest_ip": dest_ip,
        "dest_port": dest_port,
        "proto": random.choice(["TCP", "UDP"]),
        "tx_id": random.randint(0, 100),
        "alert": {
            "action": "alert",
            "gid": 1,
            "signature_id": random.randint(1000000, 9999999),
            "rev": random.randint(1, 10),
            "signature": signature,
            "category": category,
            "severity": severity,
        },
        "http": {
            "hostname": fake.domain_name(),
            "url": fake.url(),
            "http_user_agent": random.choice([
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "curl/7.68.0",
                "python-requests/2.25.1",
                "nmap/7.91",
            ]),
            "http_content_type": "application/json",
        } if random.random() < 0.5 else {},
        "dns": {
            "query": fake.domain_name(),
            "type": "A",
            "rcode": "NOERROR",
            "authorities": [],
        } if random.random() < 0.3 else {},
        "ssh": {
            "client": "OpenSSH_7.4",
            "server": "OpenSSH_7.4",
            "version": 2,
        } if dest_port == 22 and random.random() < 0.4 else {},
        "source": "suricata",
        "description": f"{signature} from {src_ip} to {dest_ip}",
        "risk_score": severity_score,
    }
    
    return event


def generate_firewall_log():
    """Generate realistic firewall log"""
    src_ip = generate_internal_ip() if random.random() < 0.5 else generate_external_ip()
    dest_ip = generate_external_ip() if random.random() < 0.5 else generate_internal_ip()
    
    actions = ["ALLOW", "DROP", "REJECT", "BLOCK"]
    action = random.choice(actions)
    severity = 2 if action == "DROP" else 3
    
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "src_ip": src_ip,
        "src_port": random.randint(1024, 65535),
        "dest_ip": dest_ip,
        "dest_port": random.choice(COMPROMISED_PORTS + [80, 443]),
        "protocol": random.choice(["TCP", "UDP"]),
        "action": action,
        "rule_id": random.randint(1000, 9999),
        "rule_name": f"FW-RULE-{random.randint(1, 1000)}",
        "severity": severity,
        "bytes_in": random.randint(100, 1000000),
        "bytes_out": random.randint(100, 1000000),
        "detector": "firewall",
        "source": "firewall",
        "description": f"{action} traffic from {src_ip}:{random.randint(1024, 65535)} to {dest_ip}:{random.choice(COMPROMISED_PORTS)}",
    }
    
    return event


def generate_host_log():
    """Generate realistic host EDR log"""
    users = ["SYSTEM", "Administrator", "user", "SERVICE", "LOCAL SERVICE"]
    hostnames = [f"server-{i}" for i in range(1, 20)]
    
    event_types = [
        "Process Create",
        "Registry Set Value",
        "File Create",
        "Network Connection",
        "Module Load",
        "Pipe Created",
    ]
    
    event_type = random.choice(event_types)
    severity = random.choice([2, 3, 3, 4])
    
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "hostname": random.choice(hostnames),
        "user": random.choice(users),
        "event_type": event_type,
        "severity": severity,
        "source_ip": generate_internal_ip(),
        "detector": "edr",
        "source": "windows_edr",
    }
    
    if event_type == "Process Create":
        event.update({
            "process_id": random.randint(100, 65535),
            "process_name": random.choice([
                "svchost.exe",
                "powershell.exe",
                "cmd.exe",
                "explorer.exe",
                "rundll32.exe",
                "regsvcs.exe",
                "certutil.exe",
            ]),
            "command_line": f"powershell.exe -Command Get-Item -Path C:\\Users\\*",
            "parent_process": "explorer.exe",
            "description": f"Suspicious process execution: {event['process_name']}",
        })
    elif event_type == "Network Connection":
        event.update({
            "process_name": "svchost.exe",
            "dest_ip": generate_external_ip(),
            "dest_port": random.choice([443, 8080, 4444, 5555]),
            "protocol": "TCP",
            "description": f"Outbound connection to {event['dest_ip']}:{event['dest_port']}",
        })
    
    return event


def delivery_callback(err, msg):
    """Kafka delivery callback"""
    if err:
        logger.error(f"Message delivery failed: {err}")
    else:
        logger.debug(f"Message delivered to {msg.topic()}")


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
    """Main simulation loop generating realistic security events"""
    logger.info(f"Starting Real IDS/IPS Log Simulator")
    logger.info(f"Kafka broker: {KAFKA_BOOTSTRAP}, Topic: {KAFKA_TOPIC}")
    
    event_count = 0
    suricata_count = 0
    firewall_count = 0
    edr_count = 0
    
    try:
        while True:
            # Mix of event types
            rand = random.random()
            
            if rand < 0.5:  # 50% Suricata IDS events
                event = generate_suricata_eve_event()
                suricata_count += 1
            elif rand < 0.75:  # 25% Firewall logs
                event = generate_firewall_log()
                firewall_count += 1
            else:  # 25% Host EDR logs
                event = generate_host_log()
                edr_count += 1
            
            send_event(event)
            event_count += 1
            
            if event_count % 10 == 0:
                logger.info(
                    f"Sent {event_count} events | "
                    f"Suricata: {suricata_count}, Firewall: {firewall_count}, EDR: {edr_count} | "
                    f"Last: {event.get('description', 'N/A')[:60]}"
                )
            
            # Random delay to simulate realistic event rate
            time.sleep(random.uniform(0.2, 1.5))
    
    except KeyboardInterrupt:
        logger.info(f"\nSimulator stopped. Total events sent: {event_count}")
        logger.info(f"  Suricata: {suricata_count}")
        logger.info(f"  Firewall: {firewall_count}")
        logger.info(f"  EDR: {edr_count}")
    finally:
        producer.flush()
        logger.info("Kafka producer flushed")


if __name__ == "__main__":
    main()
