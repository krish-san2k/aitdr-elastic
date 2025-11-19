#!/usr/bin/env python3
"""
Script to generate embeddings and index documents into Elasticsearch
Useful for embedding alert descriptions and threat intelligence
"""

import os
import json
import argparse
import logging
from typing import List, Dict, Any
from elasticsearch import Elasticsearch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
ES_URL = os.getenv("ES_URL", "http://localhost:9200")

# Try to import embedding models
try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False
    logger.warning("sentence-transformers not installed - using simple embeddings")

try:
    import openai
    HAS_OPENAI = os.getenv("OPENAI_API_KEY") is not None
except ImportError:
    HAS_OPENAI = False


def get_embedding_model():
    """Initialize embedding model"""
    if HAS_OPENAI:
        logger.info("Using OpenAI embeddings")
        return "openai"
    elif HAS_SENTENCE_TRANSFORMERS:
        logger.info("Using sentence-transformers (all-MiniLM-L6-v2)")
        return SentenceTransformer('all-MiniLM-L6-v2')
    else:
        logger.warning("No embedding model available, using dummy embeddings")
        return None


def get_openai_embedding(text: str) -> List[float]:
    """Get embedding from OpenAI"""
    try:
        response = openai.Embedding.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response['data'][0]['embedding']
    except Exception as e:
        logger.error(f"OpenAI embedding error: {e}")
        return [0.0] * 1536


def get_local_embedding(model, text: str) -> List[float]:
    """Get embedding from local model"""
    try:
        embedding = model.encode(text, convert_to_tensor=False).tolist()
        # Pad or truncate to 1536 dims for consistency
        if len(embedding) < 1536:
            embedding.extend([0.0] * (1536 - len(embedding)))
        else:
            embedding = embedding[:1536]
        return embedding
    except Exception as e:
        logger.error(f"Local embedding error: {e}")
        return [0.0] * 1536


def get_embedding(model: Any, text: str) -> List[float]:
    """Get embedding for text using available model"""
    if model == "openai":
        return get_openai_embedding(text)
    elif model is not None:
        return get_local_embedding(model, text)
    else:
        # Dummy embedding
        import hashlib
        hash_val = hashlib.md5(text.encode()).hexdigest()
        dummy = []
        for i in range(0, 32, 2):
            dummy.append(int(hash_val[i:i+2], 16) / 256.0)
        dummy.extend([0.0] * (1536 - len(dummy)))
        return dummy[:1536]


def embed_documents(documents: List[Dict[str, Any]], 
                   es_client: Elasticsearch,
                   index_name: str,
                   text_field: str = "description") -> int:
    """
    Embed documents and index into Elasticsearch
    
    Args:
        documents: List of documents to embed
        es_client: Elasticsearch client
        index_name: Name of ES index
        text_field: Field containing text to embed
        
    Returns:
        Number of documents indexed
    """
    model = get_embedding_model()
    indexed_count = 0
    
    for i, doc in enumerate(documents):
        try:
            if text_field not in doc:
                logger.warning(f"Document {i} missing field '{text_field}', skipping")
                continue
            
            # Generate embedding
            text = doc[text_field]
            embedding = get_embedding(model, text)
            
            # Add embedding to document
            doc["embedding"] = embedding
            
            # Index document
            es_client.index(index=index_name, document=doc)
            indexed_count += 1
            
            if (i + 1) % 10 == 0:
                logger.info(f"Indexed {i + 1} documents...")
        
        except Exception as e:
            logger.error(f"Error indexing document {i}: {e}")
            continue
    
    logger.info(f"Successfully indexed {indexed_count}/{len(documents)} documents")
    return indexed_count


def embed_from_file(file_path: str, 
                   es_client: Elasticsearch,
                   index_name: str,
                   text_field: str = "description") -> None:
    """
    Read documents from JSON file and embed them
    
    Args:
        file_path: Path to JSON file (JSONL or array format)
        es_client: Elasticsearch client
        index_name: Name of ES index
        text_field: Field containing text to embed
    """
    documents = []
    
    try:
        with open(file_path, 'r') as f:
            content = f.read().strip()
            
            # Try parsing as JSONL first
            if content.count('\n') > 0:
                for line in content.split('\n'):
                    if line.strip():
                        documents.append(json.loads(line))
            else:
                # Try parsing as JSON array
                documents = json.loads(content)
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return
    
    logger.info(f"Loaded {len(documents)} documents from {file_path}")
    embed_documents(documents, es_client, index_name, text_field)


def create_sample_alerts() -> List[Dict[str, Any]]:
    """Create sample alerts for testing"""
    return [
        {
            "timestamp": "2024-01-15T10:00:00Z",
            "detector": "ids",
            "description": "SQL injection attempt detected",
            "severity": 8.5,
            "source_ip": "192.168.1.100"
        },
        {
            "timestamp": "2024-01-15T10:05:00Z",
            "detector": "edr",
            "description": "Suspicious process execution detected",
            "severity": 7.2,
            "source_ip": "192.168.1.101"
        },
        {
            "timestamp": "2024-01-15T10:10:00Z",
            "detector": "firewall",
            "description": "Brute force login attempts",
            "severity": 6.0,
            "source_ip": "203.0.113.50"
        },
        {
            "timestamp": "2024-01-15T10:15:00Z",
            "detector": "dlp",
            "description": "Sensitive data exfiltration attempt",
            "severity": 9.2,
            "source_ip": "192.168.1.102"
        },
        {
            "timestamp": "2024-01-15T10:20:00Z",
            "detector": "proxy",
            "description": "C2 communication detected",
            "severity": 9.5,
            "source_ip": "192.168.1.103"
        }
    ]


def create_sample_intel() -> List[Dict[str, Any]]:
    """Create sample threat intelligence for testing"""
    return [
        {
            "timestamp": "2024-01-15T08:00:00Z",
            "type": "ip",
            "value": "192.0.2.1",
            "confidence": 0.95,
            "description": "Known C2 server"
        },
        {
            "timestamp": "2024-01-15T08:30:00Z",
            "type": "domain",
            "value": "malicious.com",
            "confidence": 0.88,
            "description": "Phishing domain"
        },
        {
            "timestamp": "2024-01-15T09:00:00Z",
            "type": "hash",
            "value": "d41d8cd98f00b204e9800998ecf8427e",
            "confidence": 0.99,
            "description": "Malware hash (MD5)"
        },
        {
            "timestamp": "2024-01-15T09:30:00Z",
            "type": "file_path",
            "value": "/tmp/.hidden/payload.sh",
            "confidence": 0.85,
            "description": "Known malware deployment path"
        }
    ]


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Embed and index documents")
    parser.add_argument("--mode", choices=["sample", "file"], default="sample",
                       help="Mode: generate sample data or read from file")
    parser.add_argument("--file", type=str, help="Input JSON/JSONL file path")
    parser.add_argument("--index", type=str, default="alerts",
                       help="Elasticsearch index name")
    parser.add_argument("--text-field", type=str, default="description",
                       help="Field containing text to embed")
    parser.add_argument("--es-url", type=str, default=ES_URL,
                       help="Elasticsearch URL")
    
    args = parser.parse_args()
    
    # Connect to Elasticsearch
    try:
        es = Elasticsearch([args.es_url])
        es.ping()
        logger.info(f"Connected to Elasticsearch at {args.es_url}")
    except Exception as e:
        logger.error(f"Failed to connect to Elasticsearch: {e}")
        return
    
    # Process documents
    if args.mode == "sample":
        if args.index == "alerts":
            documents = create_sample_alerts()
        else:
            documents = create_sample_intel()
        
        logger.info(f"Creating {len(documents)} sample documents...")
        embed_documents(documents, es, args.index, args.text_field)
    
    elif args.mode == "file":
        if not args.file:
            logger.error("--file required for file mode")
            return
        embed_from_file(args.file, es, args.index, args.text_field)
    
    logger.info("Done!")


if __name__ == "__main__":
    main()
