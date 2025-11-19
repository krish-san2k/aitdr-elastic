# 🔧 Docker Image Resolution - Quick Fix

## Problem

```
Error: failed to resolve reference "docker.elastic.co/kibana/kibana:8.10.0"
```

This means Docker images from Elastic.co haven't been downloaded yet.

---

## Quick Fix (Choose One)

### Option 1: Quick Manual Fix (Fastest) ⚡

```bash
# 1. Navigate to project
cd /Users/krishna/Desktop/CareerGrowth/Coding/aitdr-elastic

# 2. Pull the base images first
bash scripts/pull-images.sh

# 3. Wait for all images to download (5-10 minutes)

# 4. Then start services
cd infra
docker-compose up -d

# 5. Wait for services to be healthy
# Watch for "Elasticsearch is healthy" message
```

---

### Option 2: One-Command Fix ⚡⚡

```bash
# This pulls images + builds + starts everything
cd /Users/krishna/Desktop/CareerGrowth/Coding/aitdr-elastic
bash scripts/quickstart.sh
```

(I've updated this script to pull images automatically)

---

### Option 3: Manual Step-by-Step

#### Step 1: Pull images
```bash
docker pull docker.elastic.co/elasticsearch/elasticsearch:8.10.0
docker pull docker.elastic.co/kibana/kibana:8.10.0
docker pull docker.elastic.co/logstash/logstash:8.10.0
docker pull docker.elastic.co/beats/filebeat:8.10.0
docker pull confluentinc/cp-zookeeper:7.4.1
docker pull confluentinc/cp-kafka:7.4.1
docker pull postgres:15
docker pull neo4j:5
docker pull python:3.11-slim
```

#### Step 2: Build custom images
```bash
cd infra
docker-compose build
```

#### Step 3: Start services
```bash
docker-compose up -d
```

---

## What Each Command Does

| Command | Purpose | Time |
|---------|---------|------|
| `bash scripts/pull-images.sh` | Download base images | 5-10 min |
| `docker-compose build` | Build custom service images | 3-5 min |
| `docker-compose up -d` | Start all 11 services | 1-2 min |
| `bash scripts/setup-index.sh` | Create indices | 30 sec |

---

## Testing It Works

Once services are running:

```bash
# Test Elasticsearch
curl http://localhost:9200/_cluster/health

# Test Kibana
open http://localhost:5601

# Test API
curl http://localhost:8000/stats
```

---

## Common Issues During Image Pull

### Issue: "Network timeout"
```bash
# Retry the pull with a longer timeout
docker pull docker.elastic.co/elasticsearch/elasticsearch:8.10.0 \
  --timeout 300

# Or use the script which retries automatically
bash scripts/pull-images.sh
```

### Issue: "Image not found"
```bash
# Make sure Docker is running
docker ps

# If error, restart Docker
osascript -e 'quit app "Docker"'
sleep 5
open /Applications/Docker.app
sleep 30

# Then try again
bash scripts/pull-images.sh
```

### Issue: "Disk space"
```bash
# Check disk space
df -h

# Clean up old images if needed
docker image prune -a
```

---

## My Recommendation

**Run this command and go make coffee:**

```bash
bash scripts/quickstart.sh
```

It will:
1. ✅ Pull all images (5-10 min)
2. ✅ Build custom images (3-5 min)
3. ✅ Start all services (1-2 min)
4. ✅ Create indices (30 sec)
5. ✅ Show you the URLs

Total time: **10-20 minutes** ☕

---

## Progress Indicator

You should see this sequence:

```
✓ Docker found
✓ Docker Compose found
✓ .env already exists

📥 Pulling Docker images...
Pulling: confluentinc/cp-zookeeper:7.4.1
  ✓ Downloaded
Pulling: docker.elastic.co/elasticsearch/elasticsearch:8.10.0
  ✓ Downloaded
...

🏗️  Building custom Docker images...
 ✓ orchestrator-image
 ✓ ml_scorer-image
 ✓ copilot-image
 ✓ ingest_simulator-image

🚀 Starting services...
 ✓ All services started

⏳ Waiting for Elasticsearch...
 ✓ Elasticsearch is healthy

📊 Creating indices...
 ✓ Indices created

╔════════════════════════════════════════════╗
║  ✓ AITDR-Elastic is Ready!                 ║
╚════════════════════════════════════════════╝

📍 Service URLs:
   Kibana → http://localhost:5601
   API    → http://localhost:8000
```

---

## Next Steps

Once you see "AITDR-Elastic is Ready!":

1. Open Kibana: http://localhost:5601
2. Test API: `curl http://localhost:8000/stats`
3. View logs: `make logs`

---

**Ready?** Run this:

```bash
bash scripts/quickstart.sh
```

☕ Go get coffee while it runs! 🚀
