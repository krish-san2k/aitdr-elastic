#!/usr/bin/env bash

# Script to pull Docker images needed for aitdr-elastic
# Run this before docker-compose up

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Pulling Docker Images for AITDR-Elastic                   ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Define images to pull
IMAGES=(
    "confluentinc/cp-zookeeper:7.4.1"
    "confluentinc/cp-kafka:7.4.1"
    "docker.elastic.co/elasticsearch/elasticsearch:8.10.0"
    "docker.elastic.co/kibana/kibana:8.10.0"
    "docker.elastic.co/logstash/logstash:8.10.0"
    "docker.elastic.co/beats/filebeat:8.10.0"
    "postgres:15"
    "neo4j:5"
    "python:3.11-slim"
)

echo "📦 Pulling Elasticsearch Stack Images..."
echo ""

# Pull each image
for image in "${IMAGES[@]}"; do
    echo "Pulling: $image"
    docker pull "$image" || {
        echo "⚠️  Warning: Failed to pull $image"
        echo "This might be due to network issues, trying again..."
        sleep 2
        docker pull "$image" || echo "❌ Failed to pull $image"
    }
    echo ""
done

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  ✓ Image pulling complete!                                 ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Next, run:"
echo "  cd infra"
echo "  docker-compose up -d"
echo ""
