# AITDR-Elastic - Quick Reference Card

## 🚀 Start Here

```bash
# System is already running! Verify:
curl http://localhost:8000/health    # Orchestrator
curl http://localhost:8001/health    # ML Scorer
curl http://localhost:5601           # Kibana
```

---

## 🔗 Service URLs

| Service | URL | Purpose |
|---------|-----|---------|
| **Kibana** | http://localhost:5601 | Dashboards & visualization |
| **Elasticsearch** | http://localhost:9200 | Data search & storage |
| **Orchestrator** | http://localhost:8000 | Alert management API |
| **ML Scorer** | http://localhost:8001 | Anomaly detection |
| **Kafka** | kafka:9092 | Event streaming |
| **Neo4j** | http://localhost:7474 | Graph database |

---

## 📡 API Endpoints Cheat Sheet

### Create Alert
```bash
curl -X POST http://localhost:8000/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "detector": "firewall",
    "severity": 8.5,
    "source_ip": "203.0.113.45",
    "dest_ip": "192.168.1.100"
  }'
```

### List Alerts
```bash
curl "http://localhost:8000/alerts?limit=20"
```

### Get Single Alert
```bash
curl http://localhost:8000/alerts/ALERT_ID
```

### Record Triage Decision
```bash
curl -X POST http://localhost:8000/triage \
  -H "Content-Type: application/json" \
  -d '{
    "alert_id": "ALERT_ID",
    "action": "approve",
    "comment": "Blocked IP"
  }'
```

### Get System Stats
```bash
curl http://localhost:8000/stats
```

### Score Event (ML)
```bash
curl -X POST http://localhost:8001/score \
  -H "Content-Type: application/json" \
  -d '{"features": [8.5, 42, 1.0], "event_id": "evt-123"}'
```

### Get ML Model Info
```bash
curl http://localhost:8001/model/info
```

### Ask Copilot
```bash
curl -X POST http://localhost:8000/copilot/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What are critical alerts?"}'
```

### Get Triage Suggestion
```bash
curl -X POST http://localhost:8000/copilot/triage \
  -H "Content-Type: application/json" \
  -d '{"alert_id": "ALERT_ID"}'
```

---

## 🔍 Kibana KQL Queries

```kql
# High severity alerts (last 24h)
severity > 8 AND @timestamp: last 24h

# All IDS events
detector: (suricata OR snort OR "network_ips")

# Specific attacker
source_ip: 203.0.113.45

# Port scans
event_type: port_scan

# Failed logins
event_type: (failed_login OR brute_force)

# ML anomalies
is_anomaly: true AND ml_score > 0.7

# Firewall blocks only
action: (DROP OR BLOCK OR REJECT)
```

---

## 🐳 Docker Commands

```bash
# View logs
docker logs -f infra-orchestrator-1      # Alert API
docker logs -f infra-ml_scorer-1         # ML Service
docker logs -f infra-logstash-1          # Log processing
docker logs -f infra-ingest_sim-1        # Event generator

# Check Kafka
docker exec infra-kafka-1 kafka-console-consumer \
  --bootstrap-server kafka:9092 \
  --topic events \
  --max-messages 5

# Monitor resource usage
docker stats

# Restart service
docker-compose -f infra/docker-compose.yml restart orchestrator

# View all containers
docker-compose -f infra/docker-compose.yml ps
```

---

## 📊 Elasticsearch Commands

```bash
# Get cluster health
curl http://localhost:9200/_cluster/health

# List all indices
curl http://localhost:9200/_cat/indices?v

# Search alerts
curl -X GET "http://localhost:9200/alerts/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {"match_all": {}},
    "size": 10
  }' | jq '.'

# Count documents
curl http://localhost:9200/alerts/_count

# Delete index
curl -X DELETE http://localhost:9200/alerts
```

---

## 🚀 Deploy Features

### 1. Enable OpenAI Copilot
```bash
# Add API key
echo "OPENAI_API_KEY=sk-your-key" >> .env

# Restart
docker-compose -f infra/docker-compose.yml restart copilot orchestrator

# Test
curl -X POST http://localhost:8000/copilot/ask \
  -d '{"query": "Analyze critical alerts", "use_llm": true}'
```

### 2. Connect Real IDS/IPS
```bash
# Suricata EVE output → Filebeat → Kafka → AITDR-Elastic
# See FEATURE_GUIDE.md for details
```

### 3. Scale Up
```bash
# Increase Kafka partitions
docker exec infra-kafka-1 kafka-topics \
  --alter --topic events \
  --bootstrap-server kafka:9092 \
  --partitions 12

# Increase Elasticsearch heap (in docker-compose.yml)
ES_JAVA_OPTS=-Xms4g -Xmx4g
```

---

## 🔧 Troubleshooting

| Problem | Fix |
|---------|-----|
| No events | `docker logs infra-logstash-1` → check for errors |
| High memory | Reduce Elasticsearch heap size |
| API down | `curl http://localhost:8000/health` → check container |
| Kafka queue | `docker logs infra-kafka-1` → check Zookeeper |
| ML timeout | Check service: `docker logs infra-ml_scorer-1` |

---

## 📚 Documentation Map

```
FEATURES_QUICKSTART.md        ← Start here! 30-min guide
    ↓
FEATURE_GUIDE.md              ← Detailed feature docs
    ↓
README.md                     ← Architecture & design
    ↓
ENHANCEMENT_SUMMARY.md        ← This project summary
    ↓
TROUBLESHOOT_DOCKER.md        ← Docker issues
```

---

## ✅ Daily Operations

```bash
# Morning standup
curl http://localhost:8000/stats          # Get alert counts
curl http://localhost:5601                # Check dashboards

# Monitor events
docker logs -f infra-ingest_sim-1         # Watch ingestion

# Process alerts
curl http://localhost:8000/alerts?limit=50  # Get pending

# Investigate incident
curl -X POST http://localhost:8000/copilot/ask \
  -d '{"query": "analyze: [your question]"}'

# Record decision
curl -X POST http://localhost:8000/triage \
  -d '{"alert_id": "[id]", "action": "approve"}'
```

---

## 🎯 Sample Workflows

### Workflow 1: Alert Triage
```bash
# 1. Get pending alerts
curl http://localhost:8000/alerts | jq '.alerts[0]'

# 2. Get triage suggestion
ALERT_ID=$(curl http://localhost:8000/alerts | jq -r '.alerts[0]._id')
curl -X POST http://localhost:8000/copilot/triage -d "{\"alert_id\": \"$ALERT_ID\"}"

# 3. Record decision
curl -X POST http://localhost:8000/triage \
  -d "{\"alert_id\": \"$ALERT_ID\", \"action\": \"approve\"}"
```

### Workflow 2: Threat Hunting
```bash
# 1. Ask Copilot
curl -X POST http://localhost:8000/copilot/ask \
  -d '{"query": "Find all malware-related alerts"}'

# 2. Analyze in Kibana
# Search: detector: (antivirus OR edr) AND is_anomaly: true

# 3. Create dashboard
# Kibana → Dashboard → Add malware timeline visualization
```

### Workflow 3: Deploy Changes
```bash
# Make code changes
git add .
git commit -m "Add new detection rule"

# Push to main (triggers CI/CD)
git push origin main

# Monitor
open https://github.com/YOUR_REPO/actions

# Verify production
ssh deploy@your-server.com
docker-compose -f /opt/aitdr-elastic/infra/docker-compose.yml ps
```

---

## 💡 Pro Tips

1. **Filter in Kibana**: Use KQL for faster queries than scrolling
2. **Create alerts programmatically**: Integrate your tools with `/alerts` endpoint
3. **Monitor ML scores**: Look for `is_anomaly: true` for unusual patterns
4. **Use Copilot for patterns**: Ask "what's unusual about..." for analysis help
5. **Set up alerts dashboard**: Create automated SOC dashboard in Kibana
6. **Version your config**: Track docker-compose.yml changes in git
7. **Backup indices**: `curl http://localhost:9200/_snapshot` for backup
8. **Scale Kafka**: More partitions = higher throughput

---

## 🔑 Environment Variables

```bash
# .env file
ES_URL=http://elasticsearch:9200
KAFKA_BOOTSTRAP=kafka:9092
OPENAI_API_KEY=sk-... (optional)
ML_SCORER_URL=http://ml_scorer:8001
COPILOT_URL=http://copilot:8002
```

---

## 📖 Quick Links

- **Full Feature Guide**: [FEATURE_GUIDE.md](FEATURE_GUIDE.md)
- **Quick Start**: [FEATURES_QUICKSTART.md](FEATURES_QUICKSTART.md)
- **Architecture**: [README.md](README.md)
- **Summary**: [ENHANCEMENT_SUMMARY.md](ENHANCEMENT_SUMMARY.md)

---

**Need Help?**
1. Check KQL queries in Kibana Discover
2. Review container logs with `docker logs`
3. Test endpoints with curl commands above
4. See FEATURE_GUIDE.md for detailed docs

**Happy threat hunting!** 🔐
