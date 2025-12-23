# AITDR-Elastic: AI-Driven Threat Detection & Response Platform

A comprehensive, containerized security operations platform combining Elasticsearch, Kafka, ML detection, and LLM-powered investigation tools for modern SOC operations.

**Status**: Enhanced Release with Advanced Features ✅

## 🆕 What's New

This project has been **fully enhanced** with production-ready features:

- ✅ **Real IDS/IPS Log Ingestion** - Parse Suricata, Snort, firewall logs, EDR events
- ✅ **Advanced Kibana Dashboards** - Security operations, network threat, alert analytics
- ✅ **Kafka Integration** - Connect multiple data sources in real-time
- ✅ **ML Anomaly Detection** - Isolation Forest algorithm for threat scoring
- ✅ **LLM Copilot** - AI-powered alert investigation and triage
- ✅ **CI/CD Pipeline** - Automated testing, building, and deployment

**📖 START HERE:** [FEATURES_QUICKSTART.md](FEATURES_QUICKSTART.md) - 30-minute feature guide

## 🔗 Documentation

| Document | Purpose |
|----------|---------|
| **[FEATURES_QUICKSTART.md](FEATURES_QUICKSTART.md)** | ⭐ Start here! Quick 30-min guide to all features |
| **[FEATURE_GUIDE.md](FEATURE_GUIDE.md)** | Detailed docs for each feature (550+ lines) |
| **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** | Cheat sheet with API endpoints & commands |
| **[ENHANCEMENT_SUMMARY.md](ENHANCEMENT_SUMMARY.md)** | Complete summary of enhancements |
| **[README.md](README.md)** | This file - Architecture & components |

## 📋 Table of Contents

- [What's New](#-whats-new)
- [Quick Start](#-quick-start)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Components](#-components)
- [Setup & Configuration](#-setup--configuration)
- [6-Week Implementation Roadmap](#-6-week-implementation-roadmap)
- [API Documentation](#-api-documentation)
- [Troubleshooting](#-troubleshooting)
- [CI/CD & Deployment](#-cicd--deployment)
- [Contributing](#-contributing)

---

## 🚀 Quick Start

### Prerequisites

- **Docker** & **Docker Compose** (v2.0+)
- **Git**
- **4GB+ RAM** (recommended)
- **Curl** (for testing)
- Python 3.11 (optional, for local development)

### 1. Clone & Setup

```bash
git clone https://github.com/yourusername/aitdr-elastic.git
cd aitdr-elastic

# Copy environment template
cp infra/env.example .env

# (Optional) Add OpenAI API key if you have one
# echo "OPENAI_API_KEY=sk-..." >> .env
```

### 2. Start the Stack

```bash
cd infra
docker-compose up --build
```

Wait for Elasticsearch to be healthy (~30-60 seconds). You'll see:
```
elasticsearch_1  | {"@timestamp":"2024-01-15T...","message":"started"}
```

### 3. Initialize Elasticsearch Indices

In a new terminal:

```bash
cd /path/to/aitdr-elastic
bash scripts/setup-index.sh
```

Expected output:
```
✓ Elasticsearch is available
✓ Alerts index created
✓ Intel index created
✓ Raw-logs template created
✓ Processed-alerts index created
```

### 4. Access Services

| Service | URL | Purpose |
|---------|-----|---------|
| **Kibana** | http://localhost:5601 | Visualization & dashboards |
| **Elasticsearch** | http://localhost:9200 | Data storage & search |
| **Orchestrator API** | http://localhost:8000 | Alert management |
| **ML Scorer** | http://localhost:8001 | Anomaly detection |
| **Kafka** | localhost:9092 | Event streaming |
| **Neo4j** | http://localhost:7474 | Graph database |
| **PostgreSQL** | localhost:5432 | Relational DB |

### 5. Test the Pipeline

#### Option A: Send Test Alert via API

```bash
curl -X POST http://localhost:8000/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "detector": "test_detector",
    "description": "Test alert for verification",
    "severity": 7.5,
    "source_ip": "192.168.1.1",
    "dest_ip": "192.168.1.2"
  }'
```

#### Option B: View Ingested Events

The ingest simulator automatically sends events to Kafka. View them in Kibana:
1. Go to http://localhost:5601
2. Click **Discover**
3. Select `raw-logs-*` index
4. View incoming events in real-time

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     AITDR-Elastic Platform                       │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│  Data Sources    │
├──────────────────┤
│ • IDS/IPS        │
│ • Firewall       │
│ • Endpoint EDR   │
│ • Cloud APIs     │
└────────┬─────────┘
         │
         ▼
    ┌─────────┐
    │  Kafka  │◄─────── Ingest Simulator (dev)
    └────┬────┘
         │
         ▼
    ┌─────────────────┐
    │  Logstash       │ ◄─── Parse & Enrich (Grok, GeoIP, etc.)
    └────┬────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│          Elasticsearch Cluster (Single-Node Dev)             │
├─────────────────────────────────────────────────────────────┤
│ • raw-logs-* (daily)  • alerts  • intel  • processed-alerts │
└────┬────────────────────┬──────────────────┬────────────────┘
     │                    │                  │
     ▼                    ▼                  ▼
┌──────────────┐  ┌────────────────┐  ┌──────────────┐
│   Kibana     │  │  Orchestrator  │  │  Copilot     │
│ Dashboards   │  │   (FastAPI)    │  │   (LLM)      │
└──────────────┘  └────────┬───────┘  └──────────────┘
                           │
                    ┌──────▼──────┐
                    │  ML Scorer  │
                    │ (FastAPI)   │
                    └─────────────┘

Databases:
┌──────────────┬──────────────┬──────────────┐
│ PostgreSQL   │   Neo4j      │  Elasticsearch
│ (HITL DB)    │ (Threat Map) │ (Logs/Alerts)
└──────────────┴──────────────┴──────────────┘
```

---

## 📁 Project Structure

```
aitdr-elastic/
│
├─ infra/                          # Infrastructure & configuration
│  ├─ docker-compose.yml           # Complete stack definition
│  ├─ env.example                  # Environment template
│  └─ elastic/
│     └─ mappings/
│        ├─ alerts_mapping.json    # Alert index structure
│        └─ intel_mapping.json     # Intel index structure
│
├─ services/                       # Microservices
│  ├─ orchestrator/                # Alert routing & triage
│  │  ├─ Dockerfile
│  │  ├─ app.py                    # FastAPI app
│  │  └─ requirements.txt
│  │
│  ├─ copilot/                     # LLM-powered assistant
│  │  ├─ Dockerfile
│  │  ├─ copilot.py                # Copilot logic
│  │  └─ requirements.txt
│  │
│  ├─ ml_scorer/                   # ML anomaly detection
│  │  ├─ Dockerfile
│  │  ├─ serve.py                  # FastAPI serving
│  │  └─ requirements.txt
│  │
│  └─ ingest_simulator/            # Event simulation (dev)
│     ├─ Dockerfile
│     ├─ send_events.py
│     └─ requirements.txt
│
├─ logstash/                       # Log processing pipeline
│  └─ pipeline.conf                # Grok patterns, enrichment
│
├─ filebeat/                       # Log collection agent
│  └─ filebeat.yml
│
├─ .github/
│  └─ workflows/
│     ├─ ci.yml                    # Build & test on PR
│     └─ cd.yml                    # Deploy on main push
│
├─ scripts/
│  ├─ setup-index.sh               # Create ES indices
│  └─ embed_and_index.py           # Generate embeddings
│
├─ README.md                       # This file
├─ .gitignore
└─ LICENSE
```

---

## 🔧 Components

### Orchestrator (`services/orchestrator/`)

**Role**: Central alert management and triage hub

**Endpoints**:
- `POST /alerts` - Create new alert
- `GET /alerts` - List alerts
- `GET /alerts/{id}` - Get alert details
- `POST /webhook/alerts` - Receive alerts from sources
- `POST /triage` - Record analyst triage action
- `GET /stats` - Platform statistics

**Example**:
```bash
# Create alert
curl -X POST http://localhost:8000/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "detector": "firewall",
    "description": "Brute force detected",
    "severity": 6.0,
    "source_ip": "10.0.0.5",
    "dest_ip": "10.0.0.1"
  }'

# List alerts
curl http://localhost:8000/alerts?limit=20
```

### Copilot (`services/copilot/`)

**Role**: LLM-powered SOC assistant providing triage suggestions

**Key Functions**:
- `answer(query)` - Answer questions using ES context + LLM
- `triage_alert(alert)` - Generate triage recommendations
- `search_alerts(query, k=5)` - Elasticsearch context retrieval
- Automatic context gathering from historical alerts & intel

**Example**:
```python
from copilot.copilot import answer

result = answer("Summarize critical alerts from last hour")
# Returns: {"response": "...", "alerts_found": 5, "context": {...}}
```

### ML Scorer (`services/ml_scorer/`)

**Role**: Anomaly detection using Isolation Forest

**Model**: Isolation Forest (scikit-learn)
- **Contamination**: 10% (adjust based on your baseline)
- **Features**: severity, detector hash, network activity indicators
- **Output**: anomaly_score (0-1), is_anomaly (boolean)

**Endpoints**:
- `POST /score` - Score single event
- `POST /batch_score` - Score multiple events
- `GET /model/info` - Model metadata

**Example**:
```bash
curl -X POST http://localhost:8001/score \
  -H "Content-Type: application/json" \
  -d '{
    "features": [6.0, 42, 1.0],
    "event_id": "alert-123"
  }'
```

### Ingest Simulator (`services/ingest_simulator/`)

**Role**: Generate realistic security events for dev/testing

**Generated Events**:
- Network: port scans, brute force, DDoS, suspicious DNS
- Host: privilege escalation, process injection, file deletion

**Event Rate**: 1-2 events/second (configurable)

**Output**: JSON → Kafka topic `events`

---

## ⚙️ Setup & Configuration

### Environment Variables

Edit `.env` (copy from `infra/env.example`):

```bash
# Elasticsearch
ES_URL=http://elasticsearch:9200

# OpenAI (optional, for LLM features)
OPENAI_API_KEY=sk-...

# Kafka
KAFKA_BOOTSTRAP=kafka:9092

# EDR Integration (optional)
EDR_API=http://your-edr-server
JIRA_URL=http://your-jira-server
```

### Elasticsearch Configuration

**Development** (default in docker-compose):
```yaml
environment:
  - discovery.type=single-node
  - ES_JAVA_OPTS=-Xms1g -Xmx1g  # Adjust for your hardware
```

**Production** (modify for your needs):
```yaml
environment:
  - ES_JAVA_OPTS=-Xms8g -Xmx8g
  - cluster.name=prod-cluster
  - node.name=es-node-1
```

### Index Customization

Modify `infra/elastic/mappings/alerts_mapping.json`:

```json
{
  "mappings": {
    "properties": {
      "your_field": {
        "type": "keyword|text|date|float|ip",
        "analyzer": "standard"
      }
    }
  }
}
```

Then reapply: `bash scripts/setup-index.sh`

---

## 📅 6-Week Implementation Roadmap

### **Week 1: Foundations** 🏗️
**Goal**: Get the full stack running locally

- [x] Set up Docker Compose with all services
- [ ] Verify Elasticsearch health & Kibana access
- [ ] Confirm Kafka ingestion
- [ ] Create basic Kibana dashboard for raw-logs
- [ ] Document setup in README

**Deliverable**: `docker-compose up` → Full stack healthy in 5 minutes

---

### **Week 2: Indexing & Enrichment** 📊
**Goal**: Implement alert aggregation and enrichment

- [ ] Design alert schema (severity levels, detector types, etc.)
- [ ] Implement Logstash enrichment (GeoIP, threat intel lookup)
- [ ] Create intel index and ingest sample threat feeds (CSV/STIX)
- [ ] Build Kibana dashboards:
  - Alerts by severity over time
  - Top source IPs
  - Detector coverage heatmap
- [ ] Implement alert deduplication logic

**Deliverable**: Enriched alerts in ES; analyst can view correlations in Kibana

---

### **Week 3: ML Detection** 🤖
**Goal**: Add anomaly detection to alert pipeline

- [ ] Train Isolation Forest on sample data
- [ ] Containerize ML scorer (FastAPI)
- [ ] Wire ML scorer to Logstash/Orchestrator
- [ ] Create "anomaly" field in alerts index
- [ ] Build alerts dashboard filtered by ML score
- [ ] Tune contamination parameter for your environment

**Deliverable**: ML-scored alerts in ES; analyst sees anomaly flags

---

### **Week 4: LLM Copilot** 🧠
**Goal**: Implement AI-assisted investigation

- [ ] Build Copilot service (LangChain or simple OpenAI integration)
- [ ] Implement context retrieval (similar alerts, historical patterns)
- [ ] Create `/triage` endpoint with LLM suggestions
- [ ] Build Streamlit UI for copilot chat
- [ ] Test with mock alerts and gather feedback

**Deliverable**: Analyst can ask "Investigate this alert" → get AI triage

---

### **Week 5: Orchestration & Human-in-the-Loop (HITL)** 👥
**Goal**: Enable analyst feedback & feedback loops

- [ ] Implement triage action recording (approve/reject/escalate)
- [ ] Build feedback collection → PostgreSQL
- [ ] Create analyst approval workflow
- [ ] Build UI for playbook configuration
- [ ] Implement "approved alert" → ticket creation logic

**Deliverable**: Full HITL loop; analyst feedback improves model

---

### **Week 6: CI/CD & Compliance** 🔒
**Goal**: Production-ready deployment & governance

- [ ] Complete GitHub Actions CI (build, test, push images)
- [ ] Implement CD pipeline (SSH deploy to staging server)
- [ ] Build compliance reporting (CERT-In template)
- [ ] Implement audit logging
- [ ] Security scan images (Trivy)
- [ ] Document runbooks & playbooks

**Deliverable**: GitHub Actions fully automated; deploy with git push

---

## 📡 API Documentation

### Orchestrator API (Port 8000)

#### Create Alert
```http
POST /alerts
Content-Type: application/json

{
  "detector": "firewall",
  "description": "Brute force login attempt",
  "severity": 6.5,
  "source_ip": "203.0.113.45",
  "dest_ip": "10.0.0.1",
  "references": ["CVE-2024-1234"]
}

Response: 201
{
  "status": "created",
  "alert_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "severity": 6.5
}
```

#### List Alerts
```http
GET /alerts?severity=high&limit=10

Response: 200
{
  "total": 245,
  "alerts": [
    {
      "_id": "...",
      "timestamp": "2024-01-15T10:05:00Z",
      "detector": "firewall",
      "description": "...",
      "severity": 6.5
    }
  ]
}
```

#### Record Triage
```http
POST /triage
Content-Type: application/json

{
  "alert_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "action": "approve",
  "comment": "Confirmed brute force attack, escalated to IR team"
}

Response: 200
{
  "status": "triaged",
  "alert_id": "...",
  "action": "approve",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Get Stats
```http
GET /stats

Response: 200
{
  "total_alerts": 1245,
  "processed_alerts": 892,
  "pending_alerts": 353,
  "es_connected": true
}
```

### ML Scorer API (Port 8001)

#### Score Event
```http
POST /score
Content-Type: application/json

{
  "features": [6.5, 42, 1.0],
  "event_id": "evt-12345"
}

Response: 200
{
  "event_id": "evt-12345",
  "anomaly_score": 0.72,
  "is_anomaly": true,
  "timestamp": "2024-01-15T10:05:00Z"
}
```

---

## 🐛 Troubleshooting

### Elasticsearch Won't Start

**Error**: `vm.max_map_count [65530] is too small`

**Solution** (Linux):
```bash
sudo sysctl -w vm.max_map_count=262144
```

**macOS**: Docker Desktop handles this automatically, but if needed:
```bash
docker-compose up -d
docker exec aitdr-elastic-elasticsearch-1 sysctl -w vm.max_map_count=262144
```

---

### No Events in Kibana

1. **Check Kafka**:
   ```bash
   docker-compose logs ingest_sim
   # Should see "Sent X events"
   ```

2. **Check Logstash**:
   ```bash
   docker-compose logs logstash
   # Should see "Elasticsearch" mentions
   ```

3. **Check indices**:
   ```bash
   curl http://localhost:9200/_cat/indices?v
   # Look for raw-logs-YYYY.MM.DD
   ```

---

### High Memory Usage

**Reduce Elasticsearch heap**:
```yaml
# infra/docker-compose.yml
elasticsearch:
  environment:
    - ES_JAVA_OPTS=-Xms512m -Xmx512m  # For laptops
```

Then: `docker-compose down && docker-compose up --build`

---

### OpenAI API Errors

**If Copilot service fails**:

1. Check API key: `echo $OPENAI_API_KEY`
2. Verify key format: Should start with `sk-`
3. Check quota: https://platform.openai.com/account/billing/overview
4. Use fallback (local responses):
   ```bash
   # Remove OPENAI_API_KEY from .env
   # Copilot will use local Elasticsearch search only
   ```

---

## 🚀 CI/CD & Deployment

### GitHub Actions Setup

1. **Create repository secrets**:
   ```bash
   Settings → Secrets → New
   - SSH_HOST: your-prod-server.com
   - SSH_USER: deploy
   - SSH_PRIVATE_KEY: (your SSH private key)
   - SSH_KEY: (fingerprint for known_hosts)
   - DOCKERHUB_USERNAME: your-username
   - DOCKERHUB_TOKEN: (Docker Hub token)
   - REMOTE_COMPOSE_DIR: /opt/aitdr-elastic
   ```

2. **CI Pipeline** (runs on every push):
   ```bash
   git push origin feature-branch
   # → .github/workflows/ci.yml triggers
   # → Builds images, runs tests
   ```

3. **CD Pipeline** (runs on main branch):
   ```bash
   git push origin main
   # → .github/workflows/cd.yml triggers
   # → Builds & pushes images to Docker Hub
   # → SSH deploys to production
   ```

### Local Image Build

```bash
# Build single service
docker build -t aitdr/ml_scorer:local services/ml_scorer/

# Build all services
cd infra
docker-compose build

# Test locally
docker run -p 8001:8001 aitdr/ml_scorer:local
```

---

## 📚 Further Reading

- [Elasticsearch Documentation](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
- [Logstash Pipeline Syntax](https://www.elastic.co/guide/en/logstash/current/pipeline.html)
- [FastAPI Tutorial](https://fastapi.tiangolo.com/)
- [Kafka Quickstart](https://kafka.apache.org/quickstart)
- [LangChain Documentation](https://python.langchain.com/)

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit: `git commit -am 'Add feature'`
4. Push: `git push origin feature/my-feature`
5. Open a Pull Request

---

## 📝 License

MIT License - see LICENSE file

---

## 💬 Support & Questions

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Email**: security-team@your-org.com

---

## 🎯 Roadmap (Future)

- [ ] Kubernetes deployment (Helm charts)
- [ ] Prometheus metrics & Grafana dashboards
- [ ] Slurm integration for incident response
- [ ] Advanced threat hunting with graph analysis
- [ ] SOAR playbook engine
- [ ] YARA/SIGMA rule integration
- [ ] Multi-tenancy support
- [ ] Compliance reporting automation (CERT-In, PCI-DSS)

---

**Last Updated**: January 2024  
**Version**: 0.1.0-alpha
