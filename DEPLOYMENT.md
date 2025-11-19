# DEPLOYMENT.md

## Deployment & DevOps Guide for AITDR-Elastic

---

## Table of Contents
1. [Local Development Setup](#local-development-setup)
2. [Staging Deployment](#staging-deployment)
3. [Production Deployment](#production-deployment)
4. [GitHub Actions Setup](#github-actions-setup)
5. [Monitoring & Maintenance](#monitoring--maintenance)
6. [Disaster Recovery](#disaster-recovery)

---

## Local Development Setup

### Prerequisites
- Docker Desktop (v4.10+)
- Docker Compose (v2.0+)
- Git
- Bash/Zsh shell
- 4GB+ RAM available

### Initial Setup
```bash
git clone https://github.com/yourusername/aitdr-elastic.git
cd aitdr-elastic

# Copy environment
cp infra/env.example .env

# Start stack
bash scripts/quickstart.sh

# Or using make
make setup
make up
```

### Verification
```bash
# All services should be healthy
make health

# Should see 11 containers running
docker-compose -f infra/docker-compose.yml ps

# Indices should be created
curl http://localhost:9200/_cat/indices?v
```

---

## Staging Deployment

### Prerequisites (Staging Server)
- Ubuntu 20.04+ or similar
- Docker & Docker Compose installed
- 8GB+ RAM, 50GB+ disk
- SSH access configured
- Firewall rules configured

### Setup Steps

#### 1. Prepare Server
```bash
# SSH into staging server
ssh ubuntu@staging.example.com

# Create deployment directory
mkdir -p /opt/aitdr-elastic
cd /opt/aitdr-elastic

# Clone repo
git clone https://github.com/yourusername/aitdr-elastic.git .
```

#### 2. Configure Environment
```bash
# Copy template
cp infra/env.example .env

# Edit with staging values
nano .env
# Set OPENAI_API_KEY if needed
# Update JIRA_URL, EDR_API URLs
```

#### 3. Start Services
```bash
cd infra
docker-compose up -d

# Check health
docker-compose ps
```

#### 4. Initialize Indices
```bash
cd ..
bash scripts/setup-index.sh
```

#### 5. Verify Deployment
```bash
# Check logs
docker-compose logs -f elasticsearch

# Test API
curl http://localhost:8000/health
curl http://localhost:8001/health
```

### Nginx Reverse Proxy (Optional)
```bash
# Install Nginx
sudo apt-get install nginx-full

# Create config
sudo nano /etc/nginx/sites-available/aitdr-elastic
```

```nginx
upstream orchestrator {
    server 127.0.0.1:8000;
}

upstream kibana {
    server 127.0.0.1:5601;
}

server {
    listen 80;
    server_name aitdr-elastic.example.com;
    
    location / {
        proxy_pass http://kibana;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api/ {
        proxy_pass http://orchestrator;
    }
}
```

---

## Production Deployment

### Architecture
```
┌─────────────────────────────────────────────┐
│         Production Architecture              │
├─────────────────────────────────────────────┤
│ Load Balancer (optional: AWS ALB/ELB)       │
│         ↓                                     │
│ Multiple AITDR Instances (Docker Swarm/K8s)│
│         ↓                                     │
│ Managed Elasticsearch (AWS ES/Elastic Cloud)│
│ Managed Kafka (Confluent/AWS MSK)           │
│ Managed PostgreSQL (AWS RDS/Azure Database) │
│ Backup & Monitoring Infrastructure          │
└─────────────────────────────────────────────┘
```

### Pre-Production Checklist

#### Security
- [ ] Enable Elasticsearch security (`xpack.security.enabled=true`)
- [ ] Configure TLS/SSL certificates
- [ ] Set strong database passwords
- [ ] Enable audit logging
- [ ] Configure firewall rules
- [ ] Scan images with Trivy: `trivy image aitdr/orchestrator:latest`
- [ ] Use secrets manager (AWS Secrets, Azure KeyVault)

#### Infrastructure
- [ ] Use managed services (Elasticsearch, Kafka, PostgreSQL)
- [ ] Configure auto-scaling for services
- [ ] Set up load balancer (ELB/ALB)
- [ ] Configure CDN if needed
- [ ] Set up DNS records
- [ ] Configure SSL certificates (Let's Encrypt)

#### Monitoring
- [ ] Set up Prometheus & Grafana
- [ ] Configure CloudWatch/DataDog
- [ ] Set up alerts for critical metrics
- [ ] Configure log aggregation (ELK, Splunk)
- [ ] Set up uptime monitoring

#### Backup & Disaster Recovery
- [ ] Configure Elasticsearch snapshots to S3/GCS
- [ ] Set up database backups (automated)
- [ ] Document recovery procedures
- [ ] Test recovery in staging

### Production Deployment Options

#### Option 1: Docker Compose on VM (Simple)
```bash
# One large VM with Docker Compose
ssh ubuntu@prod.example.com

# Deploy
cd /opt/aitdr-elastic
git pull
docker-compose -f infra/docker-compose.yml up -d

# Monitor
docker-compose logs -f orchestrator
```

#### Option 2: Docker Swarm (Medium)
```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c infra/docker-compose.yml aitdr

# Check status
docker stack services aitdr
```

#### Option 3: Kubernetes (Advanced)
```bash
# Create Helm chart or use deployment YAML
helm install aitdr ./helm-chart \
  --values values-prod.yaml \
  --namespace production

# Check status
kubectl get deployments -n production
```

### Environment Configuration (Production)

```bash
# .env for production
ES_URL=https://es-prod.example.com:9200
OPENAI_API_KEY=sk-prod-key
KAFKA_BOOTSTRAP=kafka-prod-1:9092,kafka-prod-2:9092,kafka-prod-3:9092
POSTGRES_USER=aitdr_prod
POSTGRES_PASSWORD=VERY_STRONG_PASSWORD_HERE
NEO4J_PASSWORD=ANOTHER_STRONG_PASSWORD
DEBUG=false
LOG_LEVEL=INFO
```

---

## GitHub Actions Setup

### Prerequisites
- GitHub repository created
- Repository admin access
- Docker Hub account or container registry

### Step 1: Create Repository Secrets

Go to: **Settings → Secrets → New repository secret**

```
SSH_HOST = prod.example.com
SSH_USER = deploy
SSH_PRIVATE_KEY = <paste-your-private-key>
SSH_KEY_PASSPHRASE = <if-key-is-encrypted>
REMOTE_COMPOSE_DIR = /opt/aitdr-elastic

DOCKERHUB_USERNAME = your-username
DOCKERHUB_TOKEN = <docker-hub-token>

STAGING_HOST = staging.example.com
STAGING_USER = deploy

PROD_JIRA_URL = https://your-jira.atlassian.net
PROD_OPENAI_KEY = sk-...
```

### Step 2: Configure Workflows

The workflows are pre-configured but may need updates:

#### `.github/workflows/ci.yml` (Runs on PR)
- Checks out code
- Builds all images
- Runs tests
- Lints Python code

#### `.github/workflows/cd.yml` (Runs on main push)
- Builds & pushes images to Docker Hub
- SSH deploys to production

### Step 3: Test CI/CD

```bash
# Create a feature branch and commit
git checkout -b test-ci
echo "# Test" >> README.md
git add README.md
git commit -m "test ci"
git push origin test-ci

# Create Pull Request
# → CI should run, build images, run tests

# Merge to main
git checkout main
git merge test-ci
git push origin main

# → CD should run, push images, deploy
```

### Step 4: Monitor Workflows

Go to: **Actions → Select workflow → View runs**

---

## Monitoring & Maintenance

### Health Checks

#### Daily Checks
```bash
# Container status
docker-compose ps

# ES cluster health
curl http://localhost:9200/_cluster/health | python -m json.tool

# Disk usage
docker system df

# Service logs
docker-compose logs --tail=50 orchestrator
```

#### Weekly Checks
```bash
# Image updates
docker images | grep -i aitdr

# Test backup/restore
bash scripts/backup-es.sh && bash scripts/restore-es.sh

# Security scans
trivy image aitdr/ml_scorer:latest
```

### Metrics to Monitor

```yaml
Elasticsearch:
  - Cluster health (green/yellow/red)
  - Heap memory usage
  - Indexing rate
  - Query latency
  - Disk space

Services:
  - CPU usage
  - Memory usage
  - Request latency
  - Error rate
  - Uptime

Infrastructure:
  - Disk free space
  - Network bandwidth
  - Container restarts
  - Log volume
```

### Maintenance Tasks

#### Monthly
- [ ] Review and archive old logs
- [ ] Clean up Docker volumes
- [ ] Update dependencies
- [ ] Review security patches

#### Quarterly
- [ ] Full backup verification
- [ ] Disaster recovery drill
- [ ] Performance baseline review
- [ ] Cost optimization review

---

## Disaster Recovery

### Backup Strategy

#### Elasticsearch Snapshot
```bash
# Create snapshot repository
curl -X PUT "localhost:9200/_snapshot/s3-backup" \
  -H 'Content-Type: application/json' \
  -d'{
    "type": "s3",
    "settings": {
      "bucket": "my-es-backups",
      "region": "us-east-1",
      "base_path": "snapshots"
    }
  }'

# Create snapshot
curl -X PUT "localhost:9200/_snapshot/s3-backup/snapshot-1?wait_for_completion=true"

# List snapshots
curl -X GET "localhost:9200/_snapshot/s3-backup/_all"

# Restore
curl -X POST "localhost:9200/_snapshot/s3-backup/snapshot-1/_restore"
```

#### Database Backups
```bash
# PostgreSQL backup
docker-compose exec postgres pg_dump -U aitdr aitdr > backup.sql

# Restore
docker-compose exec -T postgres psql -U aitdr aitdr < backup.sql
```

### Recovery Procedures

#### Scenario 1: Single Service Failure
```bash
# Restart specific service
docker-compose restart orchestrator

# Or recreate
docker-compose up -d orchestrator
```

#### Scenario 2: Data Corruption
```bash
# Stop all services
docker-compose stop

# Restore Elasticsearch from snapshot
curl -X POST "localhost:9200/_snapshot/s3-backup/snapshot-1/_restore"

# Restore databases
docker-compose exec -T postgres psql -U aitdr aitdr < backup.sql

# Start services
docker-compose up -d
```

#### Scenario 3: Disk Full
```bash
# Check disk usage
df -h

# Clean Docker
docker system prune -a --volumes

# Or remove old logs manually
docker-compose exec elasticsearch \
  curl -X DELETE "localhost:9200/raw-logs-2024.01.*"
```

### RTO/RPO Targets

| Scenario | RTO | RPO |
|----------|-----|-----|
| Service restart | 5 min | 0 min |
| Data corruption | 30 min | 1 hour |
| Full datacenter failure | 4 hours | 1 hour |
| Ransomware/data loss | 24 hours | 24 hours |

---

## Scaling Considerations

### Horizontal Scaling
```yaml
# Multiple orchestrator instances
orchestrator-1:
  build: ../services/orchestrator
  # Load balanced via Nginx/HAProxy

orchestrator-2:
  build: ../services/orchestrator
  # Separate port or shared via network
```

### Vertical Scaling
```yaml
# Increase Elasticsearch heap
elasticsearch:
  environment:
    - ES_JAVA_OPTS=-Xms16g -Xmx16g  # For larger systems
```

### Database Scaling
- PostgreSQL: Use read replicas
- Elasticsearch: Use multi-node cluster
- Kafka: Use multiple brokers

---

## Troubleshooting Deployments

### Container Won't Start
```bash
# View logs
docker-compose logs orchestrator

# Check image exists
docker images | grep aitdr

# Rebuild
docker-compose build orchestrator
```

### DNS Resolution Issues
```bash
# Check network
docker network ls

# Inspect network
docker network inspect infra_default

# Restart networking
docker-compose down
docker-compose up -d
```

### Out of Disk Space
```bash
# Check usage
docker system df

# Remove dangling images/volumes
docker system prune -a

# Remove old data
docker-compose exec elasticsearch \
  curl -X DELETE "localhost:9200/raw-logs-2023.*"
```

---

## Quick Reference

### Essential Commands

```bash
# Development
make setup          # Initial setup
make up             # Start services
make down           # Stop services
make logs           # View logs

# Deployment
docker-compose -f infra/docker-compose.yml up -d
docker-compose -f infra/docker-compose.yml down

# Maintenance
docker system df                    # Disk usage
docker-compose ps                  # Status
docker-compose logs -f servicename  # Logs
curl http://localhost:9200/_health  # ES health

# Backup/Restore
bash scripts/backup-es.sh
bash scripts/restore-es.sh
```

---

## Support

For issues or questions:
- Check README.md
- Review logs: `docker-compose logs [service]`
- GitHub Issues
- Team Slack/Email

---

**Version**: 0.1.0  
**Last Updated**: January 2024
