
// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const pdfInput = document.getElementById('pdfInput');
const uploadStatus = document.getElementById('uploadStatus');
const questionInput = document.getElementById('questionInput');
const chunkTypeFilter = document.getElementById('chunkTypeFilter');
const askButton = document.getElementById('askButton');
const queryStatus = document.getElementById('queryStatus');
const answerContent = document.getElementById('answerContent');
const sourcesContent = document.getElementById('sourcesContent');
const confidenceContent = document.getElementById('confidenceContent');
const statsDetails = document.getElementById('statsDetails');
const actionStatus = document.getElementById('actionStatus');

// Initialize event listeners
document.addEventListener('DOMContentLoaded', function() {
    setupUploadEvents();
    setupQueryEvents();
    loadStats(); // Load stats on page load
});

// Upload functionality
function setupUploadEvents() {
    // Click to upload
    uploadArea.addEventListener('click', () => {
        pdfInput.click();
    });

    // File selection
    pdfInput.addEventListener('change', handleFileSelect);

    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });
}

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        handleFile(file);
    }
}

async function handleFile(file) {
    // Validate file type
    if (file.type !== 'application/pdf') {
        showStatus(uploadStatus, 'Please select a PDF file', 'error');
        return;
    }

    // Validate file size (50MB)
    if (file.size > 50 * 1024 * 1024) {
        showStatus(uploadStatus, 'File size must be less than 50MB', 'error');
        return;
    }

    showStatus(uploadStatus, 'Uploading and processing PDF...', 'info');

    const formData = new FormData();
    formData.append('pdf', file);

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (response.ok) {
            showStatus(uploadStatus, 
                `✅ Successfully processed: ${result.chunks_created} chunks created (${result.chunk_types.concept} concepts, ${result.chunk_types.question} questions, ${result.chunk_types.application} applications)`, 
                'success'
            );
            loadStats(); // Refresh stats
        } else {
            showStatus(uploadStatus, `❌ Error: ${result.error}`, 'error');
        }
    } catch (error) {
        showStatus(uploadStatus, `❌ Upload failed: ${error.message}`, 'error');
    }
}

// Query functionality
function setupQueryEvents() {
    questionInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            askQuestion();
        }
    });
}

async function askQuestion() {
    const question = questionInput.value.trim();
    
    if (!question) {
        showStatus(queryStatus, 'Please enter a question', 'error');
        return;
    }

    const chunkType = chunkTypeFilter.value;
    
    // Disable button and show loading
    askButton.disabled = true;
    askButton.innerHTML = '<span class="loading"></span> Searching...';
    showStatus(queryStatus, 'Searching for relevant information...', 'info');

    try {
        const response = await fetch('/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: question,
                chunk_type: chunkType,
                n_results: 5
            })
        });

        const result = await response.json();

        if (response.ok) {
            displayResults(result);
            showStatus(queryStatus, `✅ Found ${result.answers.length} relevant results`, 'success');
        } else {
            showStatus(queryStatus, `❌ Error: ${result.error}`, 'error');
        }
    } catch (error) {
        showStatus(queryStatus, `❌ Search failed: ${error.message}`, 'error');
    } finally {
        // Re-enable button
        askButton.disabled = false;
        askButton.innerHTML = 'Ask';
    }
}

function displayResults(result) {
    // Display answers
    if (result.answers && result.answers.length > 0) {
        answerContent.innerHTML = result.answers.map((answer, index) => `
            <div class="answer-item">
                <p>${answer}</p>
                <div class="answer-meta">
                    <span>Result ${index + 1}</span>
                    <span>Type: ${result.sources[index]?.chunk_type || 'unknown'}</span>
                </div>
            </div>
        `).join('');
    } else {
        answerContent.innerHTML = '<p class="placeholder">No answers found</p>';
    }

    // Display sources
    if (result.sources && result.sources.length > 0) {
        sourcesContent.innerHTML = result.sources.map((source, index) => `
            <div class="source-item">
                <div class="source-title">📚 ${source.source || 'Unknown Source'}</div>
                <div class="source-details">
                    Author: ${source.author || 'Unknown'}<br>
                    Type: ${source.chunk_type}<br>
                    Keywords: ${source.keywords || 'None'}<br>
                    Position: Chunk ${source.position + 1}
                </div>
            </div>
        `).join('');
    } else {
        sourcesContent.innerHTML = '<p class="placeholder">No source information available</p>';
    }

    // Display confidence scores
    if (result.confidence_scores && result.confidence_scores.length > 0) {
        confidenceContent.innerHTML = result.confidence_scores.map((score, index) => {
            const confidenceClass = score >= 0.7 ? 'high' : score >= 0.5 ? 'medium' : 'low';
            return `
                <div class="confidence-item">
                    <span>Result ${index + 1}</span>
                    <div class="confidence-bar">
                        <div class="confidence-fill ${confidenceClass}" style="width: ${score * 100}%"></div>
                    </div>
                    <span class="confidence-score">${(score * 100).toFixed(1)}%</span>
                </div>
            `;
        }).join('');
    } else {
        confidenceContent.innerHTML = '<p class="placeholder">No confidence scores available</p>';
    }
}

// Stats functionality
async function loadStats() {
    try {
        const response = await fetch('/stats');
        const stats = await response.json();

        if (response.ok) {
            displayStats(stats);
        } else {
            console.error('Failed to load stats:', stats.error);
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

function displayStats(stats) {
    if (stats.error) {
        statsDetails.innerHTML = `<p class="placeholder">Error loading statistics</p>`;
        return;
    }

    const chunkTypeDist = stats.chunk_type_distribution || {};
    const sourceDist = stats.source_distribution || {};

    statsDetails.innerHTML = `
        <div class="stats-details">
            <div class="stat-item">
                <div class="stat-value">${stats.total_chunks || 0}</div>
                <div class="stat-label">Total Chunks</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">${chunkTypeDist.concept || 0}</div>
                <div class="stat-label">Concepts</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">${chunkTypeDist.question || 0}</div>
                <div class="stat-label">Questions</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">${chunkTypeDist.application || 0}</div>
                <div class="stat-label">Applications</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">${Object.keys(sourceDist).length}</div>
                <div class="stat-label">Sources</div>
            </div>
        </div>
    `;
}

// Clear database functionality
async function clearDatabase() {
    if (!confirm('Are you sure you want to clear the entire database? This action cannot be undone.')) {
        return;
    }

    showStatus(actionStatus, 'Clearing database...', 'info');

    try {
        const response = await fetch('/clear', {
            method: 'DELETE'
        });

        const result = await response.json();

        if (response.ok) {
            showStatus(actionStatus, '✅ Database cleared successfully', 'success');
            loadStats(); // Refresh stats
            
            // Clear results
            answerContent.innerHTML = '<p class="placeholder">Your answers will appear here...</p>';
            sourcesContent.innerHTML = '<p class="placeholder">Source information will appear here...</p>';
            confidenceContent.innerHTML = '<p class="placeholder">Confidence scores will appear here...</p>';
        } else {
            showStatus(actionStatus, `❌ Error: ${result.error}`, 'error');
        }
    } catch (error) {
        showStatus(actionStatus, `❌ Clear operation failed: ${error.message}`, 'error');
    }
}

// Utility functions
function showStatus(element, message, type) {
    element.textContent = message;
    element.className = `status-${type}`;
    
    // Auto-hide success messages after 5 seconds
    if (type === 'success') {
        setTimeout(() => {
            element.textContent = '';
            element.className = '';
        }, 5000);
    }
}

// Add some sample questions for demonstration
const sampleQuestions = [
    "What is photosynthesis?",
    "How does cell division work?",
    "Explain the process of DNA replication",
    "What are the differences between mitosis and meiosis?",
    "How do enzymes function in biological systems?"
];

// Add sample questions button (optional enhancement)
function addSampleQuestions() {
    const querySection = document.querySelector('.query-section');
    const sampleDiv = document.createElement('div');
    sampleDiv.className = 'sample-questions';
    sampleDiv.innerHTML = `
        <p style="margin-bottom: 8px; color: #94a3b8;">Sample questions:</p>
        <div style="display: flex; flex-wrap: wrap; gap: 8px;">
            ${sampleQuestions.map(q => 
                `<button onclick="setQuestion('${q}')" style="font-size: 0.85rem; padding: 6px 12px;">${q}</button>`
            ).join('')}
        </div>
    `;
    querySection.appendChild(sampleDiv);
}

function setQuestion(question) {
    questionInput.value = question;
    askQuestion();
}

// Uncomment to enable sample questions
// addSampleQuestions();
