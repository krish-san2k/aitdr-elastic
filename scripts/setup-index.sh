#!/usr/bin/env bash

# Script to set up Elasticsearch indices for aitdr-elastic
# Usage: bash scripts/setup-index.sh [ES_URL]

set -e

ES_URL=${1:-http://localhost:9200}

echo "Setting up Elasticsearch indices at $ES_URL..."

# Check if ES is available
if ! curl -s -f "$ES_URL/_cluster/health" > /dev/null; then
    echo "Error: Elasticsearch at $ES_URL is not available"
    exit 1
fi

echo "✓ Elasticsearch is available"

# Create alerts index
echo "Creating alerts index..."
curl -X PUT "$ES_URL/alerts" \
  -H 'Content-Type: application/json' \
  -d @infra/elastic/mappings/alerts_mapping.json
echo "✓ Alerts index created"

# Create intel index
echo "Creating intel index..."
curl -X PUT "$ES_URL/intel" \
  -H 'Content-Type: application/json' \
  -d @infra/elastic/mappings/intel_mapping.json
echo "✓ Intel index created"

# Create raw-logs template (for daily indices)
echo "Creating raw-logs index template..."
curl -X PUT "$ES_URL/_index_template/raw-logs" \
  -H 'Content-Type: application/json' \
  -d '{
    "index_patterns": ["raw-logs-*"],
    "template": {
      "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
      },
      "mappings": {
        "properties": {
          "timestamp": {"type": "date"},
          "source_ip": {"type": "ip"},
          "dest_ip": {"type": "ip"},
          "severity": {"type": "float"},
          "detector": {"type": "keyword"},
          "description": {"type": "text"},
          "message": {"type": "text"}
        }
      }
    }
  }'
echo "✓ Raw-logs template created"

# Create processed-alerts index
echo "Creating processed-alerts index..."
curl -X PUT "$ES_URL/processed-alerts" \
  -H 'Content-Type: application/json' \
  -d '{
    "mappings": {
      "properties": {
        "timestamp": {"type": "date"},
        "original_alert_id": {"type": "keyword"},
        "triage_action": {"type": "keyword"},
        "triage_timestamp": {"type": "date"},
        "triage_comment": {"type": "text"},
        "analyst": {"type": "keyword"}
      }
    }
  }'
echo "✓ Processed-alerts index created"

# List created indices
echo ""
echo "Indices created:"
curl -s "$ES_URL/_cat/indices?v" | head -20

echo ""
echo "✓ Setup complete!"
