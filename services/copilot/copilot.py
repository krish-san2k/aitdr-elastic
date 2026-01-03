"""
Copilot Service - LLM-powered SOC assistant with Elasticsearch integration
"""
from elasticsearch import Elasticsearch
import os
import json
import logging
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
ES_URL = os.getenv("ES_URL", "http://localhost:9200")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize Elasticsearch
try:
    es = Elasticsearch([ES_URL])
    es_connected = es.ping()
    logger.info(f"Connected to Elasticsearch: {ES_URL}")
except Exception as e:
    logger.error(f"Failed to connect to Elasticsearch: {e}")
    es_connected = False
    es = None

# Initialize OpenAI (optional)
openai = None
try:
    if OPENAI_API_KEY:
        from openai import OpenAI
        openai = OpenAI(api_key=OPENAI_API_KEY)
        logger.info("OpenAI API configured")
    else:
        logger.warning("OPENAI_API_KEY not set - using local responses only")
except Exception as e:
    logger.warning(f"OpenAI not configured: {e}")
    openai = None


def search_alerts(query: str, k: int = 5) -> List[Dict[str, Any]]:
    """
    Search for relevant alerts in Elasticsearch
    
    Args:
        query: Search query string
        k: Number of results to return
        
    Returns:
        List of alert documents
    """
    if not es_connected:
        logger.warning("Elasticsearch not connected")
        return []
    
    try:
        # Try different search strategies
        search_body = {
            "query": {
                "bool": {
                    "should": [
                        {"match": {"description": {"query": query, "boost": 2}}},
                        {"match": {"detector": query}},
                        {"match_all": {}}
                    ]
                }
            },
            "size": k
        }
        
        resp = es.search(index="alerts*", body=search_body)
        results = [hit["_source"] for hit in resp["hits"]["hits"]]
        logger.info(f"Found {len(results)} alerts for query: {query}")
        return results
    except Exception as e:
        logger.error(f"Error searching alerts: {e}")
        return []


def search_intel(query: str, k: int = 5) -> List[Dict[str, Any]]:
    """
    Search for relevant intelligence in Elasticsearch
    
    Args:
        query: Search query string
        k: Number of results to return
        
    Returns:
        List of intel documents
    """
    if not es_connected:
        logger.warning("Elasticsearch not connected")
        return []
    
    try:
        search_body = {
            "query": {
                "bool": {
                    "should": [
                        {"match": {"value": query}},
                        {"match": {"description": query}},
                        {"match": {"tags": query}}
                    ]
                }
            },
            "size": k
        }
        
        resp = es.search(index="intel*", body=search_body)
        results = [hit["_source"] for hit in resp["hits"]["hits"]]
        logger.info(f"Found {len(results)} intel docs for query: {query}")
        return results
    except Exception as e:
        logger.error(f"Error searching intel: {e}")
        return []


def generate_response_local(query: str, context: Dict[str, Any]) -> str:
    """
    Generate response using local logic (no LLM)
    """
    alerts = context.get("alerts", [])
    intel_docs = context.get("intel", [])
    
    response = f"Query: {query}\n\n"
    
    if alerts:
        response += f"Found {len(alerts)} relevant alerts:\n"
        for i, alert in enumerate(alerts[:3], 1):
            response += f"  {i}. [{alert.get('severity', 'N/A')}] {alert.get('description', 'N/A')}\n"
    else:
        response += "No relevant alerts found.\n"
    
    if intel_docs:
        response += f"\nFound {len(intel_docs)} relevant intel items:\n"
        for i, doc in enumerate(intel_docs[:3], 1):
            response += f"  {i}. [{doc.get('type', 'N/A')}] {doc.get('value', 'N/A')}\n"
    
    return response


def generate_response_llm(query: str, context: Dict[str, Any]) -> str:
    """
    Generate response using OpenAI LLM
    """
    if not openai or not OPENAI_API_KEY:
        return generate_response_local(query, context)
    
    try:
        alerts = context.get("alerts", [])
        intel_docs = context.get("intel", [])
        
        # Format context for LLM
        context_text = "Context from Elasticsearch:\n\n"
        
        if alerts:
            context_text += "Recent Alerts:\n"
            for alert in alerts[:5]:
                context_text += f"- {alert.get('description', 'N/A')} (Severity: {alert.get('severity', 'N/A')})\n"
        
        if intel_docs:
            context_text += "\nRelevant Intelligence:\n"
            for doc in intel_docs[:5]:
                context_text += f"- {doc.get('value', 'N/A')} (Type: {doc.get('type', 'N/A')})\n"
        
        # Call OpenAI with modern API (v1.0+)
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a Security Operations Center (SOC) Copilot. Your role is to analyze security alerts and intelligence, provide triage recommendations, and help analysts investigate incidents. Be concise and actionable."
                },
                {
                    "role": "user",
                    "content": f"{context_text}\n\nQuestion: {query}"
                }
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error calling OpenAI: {e}")
        return generate_response_local(query, context)


def answer(query: str, use_llm: bool = True) -> Dict[str, Any]:
    """
    Answer a query using context from Elasticsearch and optionally LLM
    
    Args:
        query: User question
        use_llm: Whether to use LLM for response generation
        
    Returns:
        Dictionary with answer and supporting context
    """
    # Search for context
    alerts = search_alerts(query, k=5)
    intel_docs = search_intel(query, k=5)
    
    context = {
        "alerts": alerts,
        "intel": intel_docs
    }
    
    # Generate response
    if use_llm and openai and OPENAI_API_KEY:
        response_text = generate_response_llm(query, context)
    else:
        response_text = generate_response_local(query, context)
    
    return {
        "query": query,
        "response": response_text,
        "alerts_found": len(alerts),
        "intel_found": len(intel_docs),
        "context": {
            "alerts": [{"description": a.get("description"), "severity": a.get("severity")} for a in alerts],
            "intel": [{"value": d.get("value"), "type": d.get("type")} for d in intel_docs]
        }
    }


def triage_alert(alert: Dict[str, Any]) -> Dict[str, Any]:
    """
    Provide triage suggestion for an alert
    """
    query = f"alert about {alert.get('description', 'unknown')}"
    result = answer(query, use_llm=True)
    
    return {
        "alert_id": alert.get("_id", "unknown"),
        "description": alert.get("description", "Unknown"),
        "severity": alert.get("severity", "Unknown"),
        "triage_suggestion": result["response"],
        "related_alerts": result["alerts_found"],
        "related_intel": result["intel_found"]
    }


def main():
    """Main function for testing"""
    logger.info("Starting Copilot Service...")
    
    # Test queries
    test_queries = [
        "Summarize critical alerts in the last hour",
        "Show me brute force attempts",
        "What are the latest threats?"
    ]
    
    for query in test_queries:
        logger.info(f"\nQuery: {query}")
        result = answer(query, use_llm=OPENAI_API_KEY is not None)
        logger.info(f"Response: {result['response'][:200]}...")


if __name__ == "__main__":
    main()
