// State management
let sampleQuestions = [];
let isLoading = false;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadSampleQuestions();
    checkHealth();
    setInterval(checkHealth, 30000); // Check health every 30 seconds
});

/**
 * Load sample questions from the backend
 */
function loadSampleQuestions() {
    fetch('/api/samples')
        .then(response => response.json())
        .then(data => {
            sampleQuestions = data.questions;
            renderSampleQuestions();
        })
        .catch(error => {
            console.error('Failed to load sample questions:', error);
            // Use hardcoded samples as fallback
            renderSampleQuestions([
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
            ]);
        });
}

/**
 * Render sample questions to the UI
 */
function renderSampleQuestions(questions = sampleQuestions) {
    const samplesGrid = document.getElementById('samplesGrid');
    samplesGrid.innerHTML = '';

    questions.forEach(question => {
        const btn = document.createElement('button');
        btn.className = 'sample-btn';
        btn.textContent = question;
        btn.onclick = () => {
            document.getElementById('questionInput').value = question;
            askQuestion();
        };
        samplesGrid.appendChild(btn);
    });
}

/**
 * Handle Enter key press in input
 */
function handleKeyPress(event) {
    if (event.key === 'Enter' && !isLoading) {
        askQuestion();
    }
}

/**
 * Ask the Copilot a question
 */
async function askQuestion() {
    const query = document.getElementById('questionInput').value.trim();

    if (!query) {
        showError('Please enter a question');
        return;
    }

    if (isLoading) {
        return;
    }

    isLoading = true;
    disableUI();
    showLoading();
    clearError();

    try {
        const response = await fetch('/api/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `Server error: ${response.status}`);
        }

        const data = await response.json();
        displayResults(data);

    } catch (error) {
        console.error('Error:', error);
        showError(error.message || 'Failed to get response from Copilot');
    } finally {
        isLoading = false;
        enableUI();
        hideLoading();
    }
}

/**
 * Display results in the UI
 */
function displayResults(data) {
    hideEmptyState();
    showResults();

    // Update title
    document.getElementById('queryTitle').textContent = `Results for: "${data.query}"`;

    // Update metrics
    document.getElementById('alertsMetric').textContent = data.alerts_found || 0;
    document.getElementById('intelMetric').textContent = data.intel_found || 0;

    // Display response
    const responseText = document.getElementById('responseText');
    responseText.textContent = data.response || 'No response';

    // Display alerts if available
    const context = data.context || {};
    const alerts = context.alerts || [];
    const intel = context.intel || [];

    if (alerts.length > 0) {
        displayAlerts(alerts);
    } else {
        document.getElementById('alertsDetails').classList.add('hidden');
    }

    if (intel.length > 0) {
        displayIntel(intel);
    } else {
        document.getElementById('intelDetails').classList.add('hidden');
    }
}

/**
 * Display alerts in the results
 */
function displayAlerts(alerts) {
    const alertsList = document.getElementById('alertsList');
    alertsList.innerHTML = '';

    alerts.forEach(alert => {
        const item = document.createElement('div');
        item.className = 'list-item';
        item.innerHTML = `
            <strong>[${alert.severity || 'N/A'}]</strong> ${alert.description || 'No description'}
        `;
        alertsList.appendChild(item);
    });

    document.getElementById('alertsDetails').classList.remove('hidden');
}

/**
 * Display intel in the results
 */
function displayIntel(intelItems) {
    const intelList = document.getElementById('intelList');
    intelList.innerHTML = '';

    intelItems.forEach(item => {
        const element = document.createElement('div');
        element.className = 'list-item';
        element.innerHTML = `
            <strong>[${item.type || 'Unknown'}]</strong> ${item.value || 'No value'}
        `;
        intelList.appendChild(element);
    });

    document.getElementById('intelDetails').classList.remove('hidden');
}

/**
 * Show loading state
 */
function showLoading() {
    document.getElementById('loadingContainer').classList.remove('hidden');
    document.getElementById('resultsContainer').classList.add('hidden');
    document.getElementById('emptyState').classList.add('hidden');
}

/**
 * Hide loading state
 */
function hideLoading() {
    document.getElementById('loadingContainer').classList.add('hidden');
}

/**
 * Show results container
 */
function showResults() {
    document.getElementById('resultsContainer').classList.remove('hidden');
    document.getElementById('loadingContainer').classList.add('hidden');
}

/**
 * Show empty state
 */
function hideEmptyState() {
    document.getElementById('emptyState').classList.add('hidden');
}

/**
 * Show error message
 */
function showError(message) {
    const errorContainer = document.getElementById('errorContainer');
    const errorText = document.getElementById('errorText');

    errorText.textContent = message;
    errorContainer.classList.remove('hidden');
    document.getElementById('resultsContainer').classList.add('hidden');
    document.getElementById('loadingContainer').classList.add('hidden');
}

/**
 * Clear error message
 */
function clearError() {
    document.getElementById('errorContainer').classList.add('hidden');
}

/**
 * Clear results
 */
function clearResults() {
    document.getElementById('resultsContainer').classList.add('hidden');
    document.getElementById('emptyState').classList.remove('hidden');
    document.getElementById('questionInput').value = '';
}

/**
 * Disable UI elements during loading
 */
function disableUI() {
    document.getElementById('questionInput').disabled = true;
    document.getElementById('askButton').disabled = true;
    document.querySelectorAll('.sample-btn').forEach(btn => {
        btn.disabled = true;
    });
}

/**
 * Enable UI elements
 */
function enableUI() {
    document.getElementById('questionInput').disabled = false;
    document.getElementById('askButton').disabled = false;
    document.querySelectorAll('.sample-btn').forEach(btn => {
        btn.disabled = false;
    });
}

/**
 * Check health of services
 */
function checkHealth() {
    fetch('/api/health')
        .then(response => {
            const isHealthy = response.status === 200;
            updateHealthIndicator(isHealthy);
        })
        .catch(error => {
            console.error('Health check failed:', error);
            updateHealthIndicator(false);
        });
}

/**
 * Update health indicator
 */
function updateHealthIndicator(isHealthy) {
    const indicator = document.getElementById('healthIndicator');
    const text = document.getElementById('healthText');

    if (isHealthy) {
        indicator.classList.add('connected');
        text.textContent = 'Connected';
    } else {
        indicator.classList.remove('connected');
        text.textContent = 'Disconnected';
    }
}
