#!/usr/bin/env bash

# Quick start script for aitdr-elastic
# Usage: bash scripts/quickstart.sh

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║      AITDR-Elastic Quick Start                             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker."
    exit 1
fi
echo "✓ Docker found"

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose."
    exit 1
fi
echo "✓ Docker Compose found"

# Setup environment
echo ""
echo "⚙️  Setting up environment..."

if [ ! -f .env ]; then
    cp infra/env.example .env
    echo "✓ Created .env from template"
else
    echo "✓ .env already exists"
fi

# Pull base images
echo ""
echo "📥 Pulling Docker images (this may take 2-5 minutes)..."
bash scripts/pull-images.sh
echo ""

# Build custom service images
echo ""
echo "🏗️  Building custom Docker images (this may take 5-10 minutes)..."
cd infra
docker-compose build --quiet
cd ..
echo "✓ Images built"

# Start services
echo ""
echo "🚀 Starting services..."
cd infra
docker-compose up -d
cd ..
echo "✓ Services starting..."

# Wait for Elasticsearch
echo ""
echo "⏳ Waiting for Elasticsearch to be healthy (max 60 seconds)..."
TIMEOUT=60
START_TIME=$(date +%s)

while true; do
    if curl -s -f http://localhost:9200/_cluster/health &> /dev/null; then
        echo "✓ Elasticsearch is healthy"
        break
    fi
    
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    
    if [ $ELAPSED -gt $TIMEOUT ]; then
        echo "❌ Elasticsearch failed to start within timeout"
        echo ""
        echo "View logs: docker-compose -f infra/docker-compose.yml logs elasticsearch"
        exit 1
    fi
    
    echo "  Waiting... ($ELAPSED/$TIMEOUT seconds)"
    sleep 2
done

# Create indices
echo ""
echo "📊 Creating Elasticsearch indices..."
bash scripts/setup-index.sh > /dev/null 2>&1
echo "✓ Indices created"

# Summary
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║           ✓ AITDR-Elastic is Ready!                        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📍 Service URLs:"
echo "   Kibana          → http://localhost:5601"
echo "   Elasticsearch   → http://localhost:9200"
echo "   Orchestrator    → http://localhost:8000"
echo "   ML Scorer       → http://localhost:8001"
echo ""
echo "🧪 Next Steps:"
echo "   1. Open Kibana: http://localhost:5601"
echo "   2. Create index pattern for 'raw-logs-*'"
echo "   3. View ingest_sim events in real-time"
echo "   4. Test API: curl http://localhost:8000/stats"
echo ""
echo "📚 Documentation:"
echo "   - README.md - Full documentation"
echo "   - Makefile - Useful commands (make help)"
echo "   - infra/docker-compose.yml - Service configuration"
echo ""
echo "⛔ To stop services: docker-compose -f infra/docker-compose.yml down"
echo "🗑️  To clean everything: docker-compose -f infra/docker-compose.yml down -v"
echo ""
