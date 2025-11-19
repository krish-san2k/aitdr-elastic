#!/usr/bin/env bash

# IMMEDIATE ACTION: Run this to fix the issue
# This pulls all Docker images needed

set -e

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  🔧 AITDR-Elastic - Quick Fix                             ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "📦 Pulling Docker base images..."
echo "   (This will take 5-10 minutes depending on internet speed)"
echo ""

cd /Users/krishna/Desktop/CareerGrowth/Coding/aitdr-elastic

# Pull essential Elastic stack images
echo "▸ Pulling Elasticsearch..."
docker pull docker.elastic.co/elasticsearch/elasticsearch:8.10.0 &

echo "▸ Pulling Kibana..."
docker pull docker.elastic.co/kibana/kibana:8.10.0 &

echo "▸ Pulling Logstash..."
docker pull docker.elastic.co/logstash/logstash:8.10.0 &

echo "▸ Pulling Filebeat..."
docker pull docker.elastic.co/beats/filebeat:8.10.0 &

echo "▸ Pulling Zookeeper..."
docker pull confluentinc/cp-zookeeper:7.4.1 &

echo "▸ Pulling Kafka..."
docker pull confluentinc/cp-kafka:7.4.1 &

echo "▸ Pulling PostgreSQL..."
docker pull postgres:15 &

echo "▸ Pulling Neo4j..."
docker pull neo4j:5 &

echo "▸ Pulling Python..."
docker pull python:3.11-slim &

# Wait for all pulls to complete
wait

echo ""
echo "✓ All images downloaded!"
echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  ✓ Now run:                                               ║"
echo "║                                                           ║"
echo "║  bash scripts/quickstart.sh                              ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
