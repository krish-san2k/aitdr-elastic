# AITDR-Elastic Complete Feature Guide

This guide covers all advanced features and how to use them effectively.

## Table of Contents
1. [Real IDS/IPS Log Ingestion](#real-idsips-log-ingestion)
2. [Kibana Dashboards](#kibana-dashboards)
3. [Kafka Integration](#kafka-integration)
4. [ML Scorer & Anomaly Detection](#ml-scorer--anomaly-detection)
5. [LLM Copilot Features](#llm-copilot-features)
6. [CI/CD Pipeline](#cicd-pipeline)

---

## Real IDS/IPS Log Ingestion

### Overview
The system now supports real security logs from:
- **Suricata/Snort** IDS/IPS (EVE JSON format)
- **Firewall logs** (pF, iptables, etc.)
- **Windows EDR** (Sysmon, osquery)
- **Custom sources** (via Logstash filters)

### Using the Real Log Generator

The `real_ids_logs.py` script generates realistic security events that mimic actual IDS/IPS alerts:

```bash
# Already running in Docker, but you can also run manually:
docker exec infra-ingest_sim-1 python real_ids_logs.py

# Or if running locally:
cd services/ingest_simulator
python real_ids_logs.py
```

**Generated Events Include:**
- Suricata IDS alerts with real signatures
- Brute force attempts (SSH, HTTP)
- Malware detections
- Port scans and exploits
- Firewall blocks
- Windows EDR events (process execution, registry changes, network connections)

### Sample Suricata Alert Format

```json
{
  "timestamp": "2024-01-15T10:05:23Z",
  "src_ip": "203.0.113.45",
  "dest_ip": "192.168.1.105",
  "src_port": 45672,
  "dest_port": 3306,
  "proto": "TCP",
  "alert": {
    "signature": "ET POLICY Known P2P Application",
    "category": "Suspicious Network Traffic",
    "severity": 3,
    "signature_id": 2560003
  },
  "source": "suricata",
  "risk_score": 7.5
}
```

### Ingesting Real Logs (Integration Guide)

To ingest actual IDS/IPS logs from your systems:

#### Option 1: Filebeat (Log Files)

**Step 1:** Configure Filebeat on your IDS/IPS system:

```yaml
# /etc/filebeat/filebeat.yml
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /var/log/suricata/eve.json  # Suricata
      - /var/log/snort/alerts.json  # Snort
      - /var/log/firewall/pf.log    # Firewall

output.kafka:
  enabled: true
  hosts:
    - "your-kafka-broker:9092"
  topic: "events"
  codec.json:
    pretty: false
```

**Step 2:** Restart Filebeat:
```bash
sudo systemctl restart filebeat
```

#### Option 2: Kafka Producer (Programmatic)

```python
from confluent_kafka import Producer
import json

producer = Producer({'bootstrap.servers': 'your-kafka-broker:9092'})

# Send alert
alert = {
    "timestamp": "2024-01-15T10:05:23Z",
    "src_ip": "203.0.113.45",
    "dest_ip": "192.168.1.105",
    "alert": {
        "signature": "Malicious Activity Detected",
        "severity": 1
    },
    "source": "suricata"
}

producer.produce('events', json.dumps(alert))
producer.flush()
```

#### Option 3: HTTP Webhook

```bash
# Send alert via API
curl -X POST http://localhost:8000/webhook/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2024-01-15T10:05:23Z",
    "src_ip": "203.0.113.45",
    "dest_ip": "192.168.1.105",
    "alert": {
      "signature": "Malicious Activity",
      "severity": 1
    },
    "source": "external_tool"
  }'
```

### Logstash Enrichment

The enhanced Logstash pipeline now:
- **Parses Suricata EVE JSON** - Extracts key fields automatically
- **GeoIP Enrichment** - Adds geographic location for IPs
- **Risk Scoring** - Calculates risk based on alert severity
- **Alert Deduplication** - Groups similar alerts together

View enrichment in action:
```bash
# Monitor Logstash processing
docker logs -f infra-logstash-1 | grep -i "geoip\|severity\|risk"
```

---

## Kibana Dashboards

### Quick Start

1. **Access Kibana:** http://localhost:5601
2. **Create Index Pattern:**
   - Menu → Stack Management → Index Patterns
   - Name: `raw-logs-*`
   - Time field: `@timestamp`
   - Click "Create"

### Building Your Dashboards

#### Dashboard 1: Security Operations Overview

**Step 1:** Create visualization for "Alerts Timeline"

```
Visualization Type: Line Chart
Data Source: alerts-*
Time Interval: Hourly
Metric: Count
Split by: severity (stacked)
```

**Step 2:** Create "Threat Severity Distribution"

```
Visualization Type: Pie Chart
Data Source: raw-logs-*
Metric: Count
Bucket by: severity
```

**Step 3:** Create "Top Attack Sources"

```
Visualization Type: Bar Chart
Data Source: raw-logs-*
Y-axis: Count
X-axis: src_ip (top 10)
```

#### Dashboard 2: Network Security

**Visualizations needed:**
- **Source-Destination Matrix** (Heatmap)
  ```
  Data: raw-logs-*
  Row: src_ip (top 20)
  Column: dest_port (top 10)
  Value: Count
  ```

- **Protocol Distribution** (Donut)
  ```
  Data: raw-logs-*
  Bucket: protocol
  ```

- **Geo Map** (World Map)
  ```
  Data: raw-logs-*
  Coordinates: geoip_src.location
  Size: Count
  Color: severity
  ```

#### Dashboard 3: Alert Analytics

**Key visualizations:**
- **Alerts by Detector** (Bar)
- **Alert Response Time** (Gauge)
- **Unprocessed Alerts** (Big Number)
- **ML Anomaly Score Distribution** (Histogram)

### Sample Kibana Queries (KQL)

```
# High-severity alerts in last 24h
severity > 7 AND timestamp: last 24h

# Brute force attempts
event_type: "brute_force" AND src_port: (22 OR 3389)

# Anomalies detected by ML
is_anomaly: true AND ml_score > 0.7

# Port scan activity
event_type: "port_scan" AND src_ip: *

# Outbound malware traffic
detector: "antivirus" AND severity: (8 OR 9)

# Failed logins by user
event_type: "failed_login" AND user: *
```

### Exporting Dashboard as Report

```bash
# Navigate to Dashboard → Share → Export as PDF
# Or via API:
curl http://localhost:5601/api/reporting/generate/dashboard/dashboard-id
```

---

## Kafka Integration

### Architecture

```
Producers → Kafka Topic "events" → Logstash → Elasticsearch
  ↓
- Filebeat (log files)
- Real IDS/IPS systems
- Custom scripts
- HTTP API
```

### Kafka Producer Examples

#### Python - Send Security Alert

```python
from confluent_kafka import Producer
import json
from datetime import datetime

producer = Producer({'bootstrap.servers': 'kafka:9092'})

def send_alert(detector, severity, source_ip, dest_ip):
    alert = {
        "timestamp": datetime.utcnow().isoformat(),
        "detector": detector,
        "severity": severity,
        "source_ip": source_ip,
        "dest_ip": dest_ip,
        "event_type": "security_alert"
    }
    producer.produce('events', json.dumps(alert))
    producer.flush()

# Example usage
send_alert(
    detector="firewall",
    severity=8.5,
    source_ip="203.0.113.45",
    dest_ip="192.168.1.100"
)
```

#### Bash - Send Event from CLI

```bash
#!/bin/bash
KAFKA_HOST=${1:-localhost:9092}

# Install kafkacat if needed
# brew install kafkacat (macOS)
# apt-get install kafkacat (Linux)

EVENT=$(cat <<EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "detector": "firewall",
  "severity": 8.5,
  "source_ip": "203.0.113.45",
  "dest_ip": "192.168.1.100",
  "description": "Suspicious outbound connection"
}
EOF
)

echo "$EVENT" | kafkacat -b "$KAFKA_HOST" -t events -P
```

#### Java - Kafka Event Producer

```java
import org.apache.kafka.clients.producer.*;
import org.json.JSONObject;
import java.time.Instant;

Properties props = new Properties();
props.put("bootstrap.servers", "kafka:9092");
props.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
props.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");

KafkaProducer<String, String> producer = new KafkaProducer<>(props);

JSONObject alert = new JSONObject()
    .put("timestamp", Instant.now().toString())
    .put("detector", "ids")
    .put("severity", 8.5)
    .put("source_ip", "203.0.113.45")
    .put("dest_ip", "192.168.1.100");

ProducerRecord<String, String> record = new ProducerRecord<>(
    "events", 
    alert.toString()
);

producer.send(record);
producer.close();
```

### Kafka Monitoring

```bash
# List topics
docker exec infra-kafka-1 kafka-topics --list --bootstrap-server kafka:9092

# Monitor topic traffic
docker exec infra-kafka-1 kafka-console-consumer \
  --bootstrap-server kafka:9092 \
  --topic events \
  --from-beginning \
  --max-messages 20

# Check consumer group
docker exec infra-kafka-1 kafka-consumer-groups \
  --bootstrap-server kafka:9092 \
  --group logstash \
  --describe

# Get topic stats
docker exec infra-kafka-1 kafka-topics \
  --describe \
  --topic events \
  --bootstrap-server kafka:9092
```

---

## ML Scorer & Anomaly Detection

### Overview

The ML Scorer uses **Isolation Forest** to detect anomalous security events:
- **Anomaly Score:** 0-1 (higher = more anomalous)
- **Features:** severity, detector, network patterns
- **Contamination:** 10% (adjust for your environment)

### Testing ML Scorer

```bash
# Send event for scoring
curl -X POST http://localhost:8001/score \
  -H "Content-Type: application/json" \
  -d '{
    "features": [8.5, 42, 1.0],
    "event_id": "alert-001"
  }'

# Response:
{
  "event_id": "alert-001",
  "anomaly_score": 0.72,
  "is_anomaly": true,
  "timestamp": "2024-01-15T10:05:00Z"
}
```

### Batch Scoring

```bash
curl -X POST http://localhost:8001/batch_score \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      {"features": [8.5, 42, 1.0], "event_id": "evt-001"},
      {"features": [2.0, 5, 0.1], "event_id": "evt-002"},
      {"features": [9.0, 88, 1.0], "event_id": "evt-003"}
    ]
  }'
```

### ML Integration with Orchestrator

Alerts automatically flow through ML scoring:

```
1. Alert received at /alerts or /webhook/alerts
2. Orchestrator extracts features
3. ML Scorer scores event
4. Anomaly score stored in Elasticsearch
5. Available in Kibana dashboards
```

### Training the Model

```bash
# The model trains on historical data
# Access ML Scorer logs:
docker logs -f infra-ml_scorer-1 | grep -i "train\|model"

# To retrain with new data:
# (Modify services/ml_scorer/serve.py and rebuild)
docker-compose -f infra/docker-compose.yml up --build ml_scorer
```

### ML Model Information

```bash
curl http://localhost:8001/model/info

# Response:
{
  "model_type": "Isolation Forest",
  "contamination": 0.1,
  "n_estimators": 100,
  "max_samples": 256,
  "features": ["severity", "detector_id", "has_network_info"],
  "threshold": 0.5
}
```

### Fine-tuning Anomaly Detection

Edit `services/ml_scorer/serve.py`:

```python
# Increase contamination to detect more anomalies
iso_forest = IsolationForest(
    contamination=0.15,  # 15% of events are anomalous
    n_estimators=150,
    max_samples=512
)

# Adjust threshold
ANOMALY_THRESHOLD = 0.6  # Higher = stricter detection
```

---

## LLM Copilot Features

### Setup: Adding OpenAI API Key

```bash
# Get OpenAI API key from https://platform.openai.com/api-keys
# Add to .env:
echo "OPENAI_API_KEY=sk-your-api-key-here" >> .env

# Restart services:
docker-compose -f infra/docker-compose.yml restart copilot orchestrator
```

### Copilot Endpoints

#### 1. Ask a Question

```bash
curl -X POST http://localhost:8000/copilot/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Summarize critical alerts from the last hour"
  }'

# Response:
{
  "query": "Summarize critical alerts from the last hour",
  "response": "Found 5 critical alerts in the last hour...",
  "alerts_found": 5,
  "intel_found": 3,
  "context": {...}
}
```

#### 2. Get Triage Recommendation

```bash
curl -X POST http://localhost:8000/copilot/triage \
  -H "Content-Type: application/json" \
  -d '{
    "alert_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
  }'

# Response:
{
  "alert_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "description": "Brute force login attempt",
  "severity": 6.5,
  "triage_suggestion": "This appears to be a legitimate brute force attack on the SSH service. Recommended action: Block source IP 203.0.113.45 for 24 hours and enable MFA.",
  "related_alerts": 12,
  "related_intel": 4
}
```

#### 3. Analyze Multiple Alerts

```bash
curl -X POST http://localhost:8000/copilot/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "alert_ids": ["alert-001", "alert-002", "alert-003"],
    "analysis_type": "correlation"
  }'
```

### Copilot Query Examples

```bash
# Investigation queries
"What's unusual about alerts from 203.0.113.45?"
"Find related alerts to this SQL injection attempt"
"Summarize the incident from the last 2 hours"
"Compare today's alert volume with yesterday"
"What known malware signatures were triggered?"
"Show me the attack chain for this infection"
"What's the risk level of this threat?"
"Who else might be affected by this vulnerability?"
```

### Using Copilot in Workflows

#### Example 1: Automated Triage Loop

```python
import requests
import json

ORCHESTRATOR_URL = "http://localhost:8000"

# 1. Get pending alerts
alerts = requests.get(f"{ORCHESTRATOR_URL}/alerts?processed=false").json()

# 2. Get Copilot triage for each
for alert in alerts["alerts"]:
    triage = requests.post(
        f"{ORCHESTRATOR_URL}/copilot/triage",
        json={"alert_id": alert["_id"]}
    ).json()
    
    print(f"Alert: {alert['description']}")
    print(f"Triage: {triage['triage_suggestion']}")
    
    # 3. Store recommendation
    requests.post(
        f"{ORCHESTRATOR_URL}/triage",
        json={
            "alert_id": alert["_id"],
            "action": "analyze",
            "comment": triage['triage_suggestion']
        }
    )
```

#### Example 2: Threat Hunting with Copilot

```bash
#!/bin/bash
# Hunt for specific threat

QUERY="Analyze all alerts involving data exfiltration in the last 24 hours"

curl -X POST http://localhost:8000/copilot/ask \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"$QUERY\"}" | jq '.response'
```

### Copilot Context Sources

Copilot automatically searches:
- **Alerts:** alerts-* indices (historical alerts)
- **Intelligence:** intel* indices (threat feeds, IOCs)
- **Raw Logs:** raw-logs-* indices (full event context)

To add custom intelligence:

```bash
# Index threat intelligence
curl -X POST http://localhost:9200/intel/_doc \
  -H "Content-Type: application/json" \
  -d '{
    "value": "203.0.113.45",
    "type": "known_c2_server",
    "description": "Known C2 command and control server",
    "tags": ["malware", "apt28"],
    "last_seen": "2024-01-15T10:00:00Z"
  }'
```

---

## CI/CD Pipeline

### GitHub Actions Workflow

The project includes automated CI/CD pipelines for:
- **Building** Docker images
- **Testing** services
- **Deploying** to production

### Setup Instructions

#### Step 1: Create GitHub Secrets

Go to **Settings → Secrets and variables → Actions** and add:

```
SSH_HOST              = your-prod-server.com
SSH_USER              = deploy
SSH_PRIVATE_KEY       = (your SSH private key)
DOCKERHUB_USERNAME    = your-dockerhub-username
DOCKERHUB_TOKEN       = (Docker Hub access token)
REMOTE_COMPOSE_DIR    = /opt/aitdr-elastic
```

#### Step 2: Configure Workflows

The CI/CD workflows are in `.github/workflows/`:

- **`ci.yml`** - Runs on every push
  - Builds Docker images
  - Runs tests
  - Scans security vulnerabilities

- **`cd.yml`** - Runs on push to `main` branch
  - Pushes images to Docker Hub
  - Deploys to production via SSH

#### Step 3: Deploy to Production

```bash
# 1. Push to main branch (triggers CD)
git push origin main

# 2. Monitor GitHub Actions
# Go to Actions tab in your repository

# 3. Verify deployment
ssh deploy@your-prod-server.com
cd /opt/aitdr-elastic
docker-compose ps
```

### Manual Deployment

If not using GitHub Actions:

```bash
# 1. Build and push images
cd infra
docker-compose build
docker tag aitdr/orchestrator:local your-registry/orchestrator:v1.0
docker push your-registry/orchestrator:v1.0

# 2. Deploy to remote server
ssh deploy@your-prod-server.com << 'EOF'
cd /opt/aitdr-elastic
docker-compose pull
docker-compose up -d
docker-compose logs -f
EOF
```

### Testing Before Deployment

```bash
# Run orchestrator tests
cd services/orchestrator
python -m pytest tests.py -v

# Run ML scorer tests
cd services/ml_scorer
python -m pytest tests.py -v

# Run integration tests
cd infra
docker-compose up -d
sleep 30
curl http://localhost:8000/stats
curl http://localhost:8001/model/info
```

### Monitoring Deployed Services

```bash
# Check service health
curl http://your-prod-server:8000/health
curl http://your-prod-server:8001/health

# View logs
ssh deploy@your-prod-server.com
docker-compose -f /opt/aitdr-elastic/infra/docker-compose.yml logs orchestrator -f

# Check resource usage
docker stats
```

---

## Advanced Integration Scenarios

### Scenario 1: Splunk Integration

Splunk → Kafka → AITDR-Elastic:

```bash
# Configure Splunk output to Kafka:
# Settings → Data inputs → HTTP Event Collector
# → Send to Kafka via HTTP route

# In AITDR-Elastic:
# 1. Kafka receives events
# 2. Logstash parses
# 3. Elasticsearch indexes
# 4. Kibana visualizes
```

### Scenario 2: Automated Incident Response

```bash
# Create playbook with Copilot + Orchestrator
1. Alert triggers
2. Copilot analyzes
3. Risk score calculated
4. If risk > 8.0:
   - Create incident ticket
   - Alert security team
   - Isolate host (manual confirmation)
   - Block source IP
```

### Scenario 3: Machine Learning Pipeline

```bash
# Daily ML model retraining:
1. Collect events from past 30 days
2. Extract features
3. Train Isolation Forest
4. Evaluate performance
5. Deploy new model if improvement > 5%
```

---

## Performance Tips

### Elasticsearch Tuning

```bash
# Increase heap for large deployments
# Edit docker-compose.yml:
environment:
  - ES_JAVA_OPTS=-Xms4g -Xmx4g
```

### Index Lifecycle Management

```bash
# Create ILM policy for log rotation
curl -X PUT http://localhost:9200/_ilm/policy/logs-policy \
  -H "Content-Type: application/json" \
  -d '{
    "policy": {
      "phases": {
        "hot": {"min_age": "0d", "actions": {}},
        "warm": {"min_age": "30d", "actions": {"set_priority": {"priority": 50}}},
        "delete": {"min_age": "90d", "actions": {"delete": {}}}
      }
    }
  }'
```

### Kafka Performance

```bash
# Increase partitions for throughput
docker exec infra-kafka-1 kafka-topics \
  --alter --topic events \
  --bootstrap-server kafka:9092 \
  --partitions 12
```

---

## Troubleshooting

### No Events in Kibana?

```bash
# 1. Check Kafka has messages
docker exec infra-kafka-1 kafka-console-consumer \
  --bootstrap-server kafka:9092 \
  --topic events \
  --max-messages 5

# 2. Check Logstash is processing
docker logs -f infra-logstash-1 | grep -i "elasticsearch"

# 3. Verify indices exist
curl http://localhost:9200/_cat/indices?v

# 4. Check for errors
curl http://localhost:9200/_cluster/health
```

### ML Scorer Not Responding?

```bash
# Check ML scorer logs
docker logs -f infra-ml_scorer-1

# Test endpoint
curl http://localhost:8001/health

# Check if model is loaded
curl http://localhost:8001/model/info
```

### Copilot Not Using OpenAI?

```bash
# Check if API key is set
docker exec infra-copilot-1 env | grep OPENAI

# View Copilot logs
docker logs -f infra-copilot-1 | grep -i "openai"

# Test locally
curl -X POST http://localhost:8000/copilot/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'
```

---

## Next Steps

1. **Load Real Data** - Connect your IDS/IPS systems
2. **Customize Dashboards** - Build SOC-specific visualizations
3. **Fine-tune ML** - Adjust anomaly detection for your environment
4. **Enable LLM** - Add OpenAI API key for Copilot
5. **Set up CI/CD** - Configure GitHub Actions for your repo
6. **Create Runbooks** - Document your incident response procedures

---

**Last Updated:** January 2024  
**For questions:** See README.md or TROUBLESHOOT.md
