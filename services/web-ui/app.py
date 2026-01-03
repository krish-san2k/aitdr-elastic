"""
Web UI for AITDR Copilot SOC Assistant
"""
from flask import Flask, render_template, jsonify, request
import requests
import os
import logging
from typing import Dict, Any

app = Flask(__name__, static_folder='static', template_folder='templates')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://localhost:8000")
COPILOT_ASK_ENDPOINT = f"{ORCHESTRATOR_URL}/copilot/ask"
COPILOT_TRIAGE_ENDPOINT = f"{ORCHESTRATOR_URL}/copilot/triage"

# Sample questions for the UI
SAMPLE_QUESTIONS = [
    "What are the most critical security alerts?",
    "Show me SQL injection attempts",
    "What brute force attacks have occurred?",
    "Which IPs are performing suspicious activities?",
    "Summarize alerts from the last hour",
    "What are the latest security threats?",
    "Show me failed login attempts",
    "What port scanning activities detected?",
    "List all high-severity alerts",
    "What network intrusions have been detected?"
]


@app.route('/')
def index():
    """Serve the main UI page"""
    return render_template('index.html', sample_questions=SAMPLE_QUESTIONS)


@app.route('/api/ask', methods=['POST'])
def ask_copilot():
    """
    API endpoint to ask Copilot a question
    """
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'Query cannot be empty'}), 400
        
        logger.info(f"Processing query: {query}")
        
        # Call the copilot service
        response = requests.post(
            COPILOT_ASK_ENDPOINT,
            json={'query': query},
            timeout=30
        )
        
        if response.status_code != 200:
            logger.error(f"Copilot API error: {response.status_code} - {response.text}")
            return jsonify({'error': 'Failed to get response from Copilot service'}), 500
        
        result = response.json()
        logger.info(f"Copilot response received: {result['alerts_found']} alerts found")
        
        return jsonify(result), 200
        
    except requests.exceptions.Timeout:
        logger.error("Copilot API timeout")
        return jsonify({'error': 'Request timeout - Copilot service not responding'}), 504
    except requests.exceptions.ConnectionError:
        logger.error("Failed to connect to Copilot API")
        return jsonify({'error': 'Failed to connect to Copilot service'}), 503
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        response = requests.get(f"{ORCHESTRATOR_URL}/health", timeout=5)
        is_healthy = response.status_code == 200
    except:
        is_healthy = False
    
    return jsonify({
        'status': 'healthy' if is_healthy else 'unhealthy',
        'orchestrator': 'connected' if is_healthy else 'disconnected'
    }), 200 if is_healthy else 503


@app.route('/api/samples', methods=['GET'])
def get_samples():
    """Get sample questions"""
    return jsonify({'questions': SAMPLE_QUESTIONS}), 200


if __name__ == '__main__':
    logger.info(f"Starting Web UI on port 5000")
    logger.info(f"Orchestrator URL: {ORCHESTRATOR_URL}")
    app.run(host='0.0.0.0', port=5000, debug=False)
