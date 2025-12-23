# AITDR-Elastic - Feature Quick Start Guide

Get up and running with all advanced features in 30 minutes!

## Quick Links
- 🎯 [Real IDS/IPS Logs](#real-idsips-logs) - Ingest actual security logs
- 📊 [Kibana Dashboards](#kibana-dashboards) - Create meaningful visualizations
- 🚀 [Kafka Integration](#kafka-integration) - Send events from external sources
- 🤖 [ML Anomaly Detection](#ml-anomaly-detection) - Automatic threat scoring
- 🧠 [LLM Copilot](#llm-copilot) - AI-powered threat investigation
- 🔄 [CI/CD Pipeline](#cicd-pipeline) - Automated deployment

---

## Real IDS/IPS Logs

### ✅ What's Running Now
Your system is already ingesting simulated Suricata/Snort events:
- 50% **IDS alerts** (malware, exploits, scans)
- 25% **Firewall logs** (blocks, drops, connections)
- 25% **EDR events** (process execution, registry changes)

### View Events in Kibana

```bash
# 1. Open Kibana
open http://localhost:5601

# 2. Create Index Pattern
- Menu → Stack Management → Index Patterns
- Create: raw-logs-*
- Time field: @timestamp

# 3. View Discovery
- Click "Discover"
- Select "raw-logs-*"
- See live events streaming in
```

### Send Your Own Events

#### Option A: Simple curl command
```bash
curl -X POST http://localhost:8000/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "detector": "firewall",
    "description": "Suspicious outbound connection to 203.0.113.45:443",
    "severity": 8.5,
    "source_ip": "192.168.1.100",
    "dest_ip": "203.0.113.45"
  }'
```

#### Option B: Python script
```python
import requests
import json

def send_alert(detector, severity, description, src_ip, dest_ip):
    url = "http://localhost:8000/alerts"
    payload = {
        "detector": detector,
        "severity": severity,
        "description": description,
        "source_ip": src_ip,
        "dest_ip": dest_ip
    }
    response = requests.post(url, json=payload)
    return response.json()

# Example
result = send_alert(
    detector="ids",
    severity=9.0,
    description="SQL Injection attempt detected",
    src_ip="203.0.113.50",
    dest_ip="192.168.1.50"
)
print(result)
```

#### Option C: Real IDS/IPS System Integration

For **Suricata**:
```bash
# Enable EVE JSON output
nano /etc/suricata/suricata.yaml

# Add:
eve-log:
  enabled: yes
  filetype: regular
  filename: eve.json
  types:
    - alert
    - http
    - dns
    - tls

# Start filebeat on IDS server to ship logs to your Kafka broker
```

For **Snort 3**:
```bash
# Configure output plugin
vim /etc/snort/snort.lua

# Set JSON alert output to Kafka topic "events"
```

---

## Kibana Dashboards

### Create Your First Dashboard

#### Step 1: Build Alert Timeline Visualization
```
1. Navigate to Kibana → Visualize Library → Create visualization
2. Select: Line Chart
3. Data Source: raw-logs-*
4. Y-axis: Count
5. X-axis: @timestamp (Hourly)
6. Split Series: severity
7. Click "Save"
```

#### Step 2: Build Top Threats Visualization
```
1. Create → Vertical Bar Chart
2. Data: raw-logs-*
3. Y-axis: Count
4. X-axis: detector (Top 10)
5. Save: "Top Attack Detectors"
```

#### Step 3: Create Dashboard
```
1. Create → Dashboard
2. Add previous 2 visualizations
3. Add: Pie chart for severity distribution
4. Add: Map for geographic source IPs
5. Save: "Security Operations Dashboard"
```

### Sample KQL Queries to Use

Paste these in Kibana Discover → KQL:

```kql
# Critical alerts (last 24h)
severity > 8 AND @timestamp: last 24h

# All IDS alerts
detector: (suricata OR snort OR "network_ips")

# Specific attacker IP
source_ip: 203.0.113.45

# Port scans detected
event_type: port_scan

# Failed logins
event_type: "failed_login" OR event_type: "brute_force"

# Anomalies detected by ML
is_anomaly: true AND ml_score > 0.7

# Outbound traffic to unusual ports
dest_port > 5000 AND dest_port < 65535
```

### Export Dashboard

```bash
# Share → Generate PDF Report
# Or via API:
curl http://localhost:5601/api/reporting/generate/dashboard/YOUR_DASHBOARD_ID
```

---

## Kafka Integration

### Check Kafka Status

```bash
# See incoming events
docker exec infra-kafka-1 kafka-console-consumer \
  --bootstrap-server kafka:9092 \
  --topic events \
  --from-beginning \
  --max-messages 10

# Monitor topic stats
docker exec infra-kafka-1 kafka-topics \
  --describe \
  --topic events \
  --bootstrap-server kafka:9092
```

### Send Events to Kafka

#### From Your Application (Python)
```python
from confluent_kafka import Producer
import json
from datetime import datetime

# Connect to Kafka
producer = Producer({
    'bootstrap.servers': 'your-kafka-broker:9092'
})

# Create event
event = {
    "timestamp": datetime.utcnow().isoformat(),
    "detector": "custom_detector",
    "severity": 7.0,
    "source_ip": "203.0.113.100",
    "dest_ip": "192.168.1.50",
    "description": "Custom security event"
}

# Send to Kafka
producer.produce('events', json.dumps(event))
producer.flush()
```

#### From Command Line
```bash
# Install kafkacat
brew install kafkacat  # macOS
apt-get install kafkacat  # Linux

# Send event
echo '{
  "timestamp": "2024-01-15T10:05:00Z",
  "detector": "custom",
  "severity": 7.0,
  "source_ip": "203.0.113.100",
  "dest_ip": "192.168.1.50"
}' | kafkacat -b your-kafka-broker:9092 -t events -P
```

---

## ML Anomaly Detection

### Test ML Scorer

```bash
# Check ML model status
curl http://localhost:8001/model/info

# Expected response:
{
  "model_type": "Isolation Forest",
  "contamination": 0.1,
  "n_estimators": 100,
  "status": "ready"
}

# Score an event
curl -X POST http://localhost:8001/score \
  -H "Content-Type: application/json" \
  -d '{
    "features": [8.5, 42, 1.0],
    "event_id": "test-event-001"
  }'

# Response:
{
  "event_id": "test-event-001",
  "anomaly_score": 0.75,
  "is_anomaly": true,
  "timestamp": "2024-01-15T10:05:00Z"
}
```

### View ML Scores in Elasticsearch

```bash
# Find anomalies
curl -X GET "http://localhost:9200/alerts/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "bool": {
        "must": [{"term": {"is_anomaly": true}}]
      }
    },
    "size": 10
  }' | jq '.'
```

### Kibana Visualization for ML Scores

```
1. Create new visualization
2. Type: Histogram
3. Data: alerts
4. X-axis: ml_score
5. Title: "ML Anomaly Score Distribution"
```

---

## LLM Copilot

### Setup (Optional but Recommended)

```bash
# 1. Get OpenAI API key
# Go to https://platform.openai.com/api-keys
# Create new secret key

# 2. Add to .env
echo "OPENAI_API_KEY=sk-your-key-here" >> .env

# 3. Restart services
docker-compose -f infra/docker-compose.yml restart orchestrator copilot
```

### Ask Questions to Copilot

```bash
# Query 1: Summarize alerts
curl -X POST http://localhost:8000/copilot/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the critical alerts in the last hour?"
  }'

# Query 2: Investigate attack
curl -X POST http://localhost:8000/copilot/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Analyze all suspicious activity from 203.0.113.45"
  }'

# Query 3: Find correlations
curl -X POST http://localhost:8000/copilot/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me related malware detection alerts"
  }'
```

### Get Alert Triage Suggestions

```bash
# Step 1: Get an alert ID
curl http://localhost:8000/alerts?limit=1 | jq '.alerts[0]._id'

# Step 2: Ask Copilot to triage it
curl -X POST http://localhost:8000/copilot/triage \
  -H "Content-Type: application/json" \
  -d '{
    "alert_id": "YOUR_ALERT_ID_HERE"
  }'

# Response includes:
# - Description
# - Severity
# - Triage suggestion
# - Related alerts count
# - ML anomaly score
```

### Example Copilot Queries

```
"What's unusual about alerts from the finance department?"
"Summarize the incident from the last 2 hours"
"Are there any known malware signatures in recent alerts?"
"What's the pattern of brute force attempts today?"
"Compare alert volume with yesterday"
"Which systems are most targeted?"
```

---

## CI/CD Pipeline

### GitHub Actions Setup

#### Step 1: Create GitHub Secrets

In your GitHub repository:
1. Settings → Secrets and variables → Actions
2. Create these secrets:

```
SSH_HOST              your-server.com
SSH_USER              deploy
SSH_PRIVATE_KEY       (your private key content)
DOCKERHUB_USERNAME    your-docker-username
DOCKERHUB_TOKEN       (Docker Hub access token)
REMOTE_COMPOSE_DIR    /opt/aitdr-elastic
```

#### Step 2: Deploy with Git

```bash
# Make changes to code
git add .
git commit -m "Add new feature"

# Push to main (triggers CI/CD)
git push origin main

# Monitor in GitHub → Actions tab
```

#### Step 3: Verify Deployment

```bash
# Check build status
open https://github.com/YOUR_USERNAME/aitdr-elastic/actions

# View logs when build completes
# Status will show: ✅ All tests passed → Images pushed
```

### Manual Deploy (Without GitHub)

```bash
# Build images locally
cd infra
docker-compose build

# Push to Docker Hub
docker tag aitdr-orchestrator your-username/aitdr-orchestrator:v1.0
docker push your-username/aitdr-orchestrator:v1.0

# Deploy to remote server
ssh deploy@your-server.com << 'EOF'
cd /opt/aitdr-elastic
docker-compose pull
docker-compose up -d
EOF
```

---

## Complete Workflow Example

### Scenario: Investigate a Brute Force Attack

```bash
# 1. Event arrives
# → Ingest Simulator generates brute_force event
# → Event sent to Kafka topic "events"

# 2. Processing
# → Logstash parses and enriches
# → Elasticsearch indexes in raw-logs-YYYY.MM.dd

# 3. Alerting
# → High-severity event created in alerts index
# → ML Scorer runs anomaly detection
# → is_anomaly: true if unusual pattern

# 4. Visualization
# → Kibana dashboard shows new alert
# → Map visualization highlights source IP

# 5. Investigation
# → Analyst asks Copilot:
curl -X POST http://localhost:8000/copilot/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Analyze brute force attempts from 203.0.113.45"
  }'

# 6. Triage
# → Copilot suggests: "Block IP for 24 hours"
# → Analyst records decision:
curl -X POST http://localhost:8000/triage \
  -H "Content-Type: application/json" \
  -d '{
    "alert_id": "alert-xyz",
    "action": "approve",
    "comment": "Blocked source IP, enabled MFA"
  }'

# 7. Feedback
# → ML model learns from analyst decision
# → Similar alerts refined for future
```

---

## Troubleshooting

### No events in Kibana?
```bash
# Check Kafka has data
docker exec infra-kafka-1 kafka-console-consumer \
  --bootstrap-server kafka:9092 \
  --topic events \
  --max-messages 5

# Check Logstash logs
docker logs -f infra-logstash-1
```

### Copilot not responding?
```bash
# Check if service is running
curl http://localhost:8000/health

# Check logs
docker logs -f infra-copilot-1
```

### ML Scorer errors?
```bash
# Check model status
curl http://localhost:8001/model/info

# View logs
docker logs -f infra-ml_scorer-1
```

### High memory usage?
```bash
# Reduce Elasticsearch heap
docker exec infra-elasticsearch-1 \
  sysctl -w vm.max_map_count=262144
```

---

## Next Steps

1. ✅ **Real Logs**: Connect your IDS/IPS system (Suricata, Snort, etc.)
2. ✅ **Dashboards**: Build SOC-specific dashboards in Kibana
3. ✅ **Kafka**: Send events from SIEM, EDR, or custom tools
4. ✅ **ML**: Fine-tune anomaly detection for your environment
5. ✅ **Copilot**: Enable OpenAI for intelligent triage
6. ✅ **CI/CD**: Set up automated deployment

## Full Documentation

- See [FEATURE_GUIDE.md](FEATURE_GUIDE.md) for detailed documentation
- See [README.md](README.md) for architecture and setup
- See [TROUBLESHOOT.md](TROUBLESHOOT_DOCKER.md) for common issues

---

**Questions or issues?** Create an issue in GitHub or refer to the main documentation files.
